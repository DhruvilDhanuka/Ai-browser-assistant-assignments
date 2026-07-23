from app.AgentsForModules.pendingAnswers import register_question, get_answer
from langchain.tools import tool
from playwright.sync_api import sync_playwright
from langchain_classic.agents import AgentExecutor, create_react_agent
from langsmith import Client
from langchain_groq import ChatGroq
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.prompts import PromptTemplate
import shutil
import json
from app.models_db.UserProfile import UserProfile, Documents
from app.models_db.Commands import Commands
import os
from app.database import Base, SessionLocal, get_db
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.attributes import flag_modified
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai
from google.genai import types as genai_types
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


SOURCE_PROFILE = r"C:\Users\ACER\AppData\Local\Google\Chrome\User Data"
AGENT_PROFILE = r"C:\Users\ACER\AppData\Local\AgentChromeProfile"

EXTRACTION_SCRIPT = r"""
() => {
  function getLabelText(el) {
    if (el.id) {
      const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (lbl && lbl.innerText.trim()) return lbl.innerText.trim();
    }
    const parentLabel = el.closest('label');
    if (parentLabel && parentLabel.innerText.trim()) return parentLabel.innerText.trim();

    const ariaLabel = el.getAttribute('aria-label');
    if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();

    const labelledBy = el.getAttribute('aria-labelledby');
    if (labelledBy) {
      const text = labelledBy
        .split(' ')
        .map(id => document.getElementById(id)?.innerText || '')
        .join(' ')
        .trim();
      if (text) return text;
    }

    if (el.placeholder && el.placeholder.trim()) return el.placeholder.trim();

    let node = el;
    for (let depth = 0; depth < 3 && node; depth++) {
      const prev = node.previousElementSibling;
      if (prev) {
        const text = prev.innerText?.trim();
        if (text && text.length < 200) return text;
      }
      node = node.parentElement;
    }
    return null;
  }

  function getOptions(el) {
    if (el.tagName === 'SELECT') {
      return Array.from(el.options).map(o => ({ value: o.value, text: o.innerText.trim() }));
    }
    return null;
  }

  const selector = 'input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]), select, textarea';
  const elements = Array.from(document.querySelectorAll(selector));

  return elements.map(el => {
    if (!el.dataset.ffId) {
      el.dataset.ffId = 'ff-' + Math.random().toString(36).slice(2, 10);
    }
    return {
      ffId: el.dataset.ffId,
      tag: el.tagName.toLowerCase(),
      type: el.type || null,
      name: el.name || null,
      htmlId: el.id || null,
      required: !!el.required,
      label: getLabelText(el),
      placeholder: el.placeholder || null,
      options: getOptions(el),
    };
  });
}
"""

# --- single-call field mapper: replaces per-field agent reasoning entirely ---

FIELD_MAPPER_PROMPT = """You are a form-field mapper for a personal browser assistant.

Given a list of detected form fields, the user's saved profile, and their uploaded documents, decide which fields you can confidently fill, and which need to be asked about.

Respond ONLY with JSON matching this schema:
{
  "filled": {"<ffId>": "<value>", ...},
  "missing_text": [{"ffId": "<ffId>", "label": "<short label for saving to profile>", "question": "<question to ask the user>"}],
  "missing_file": [{"ffId": "<ffId>", "doc_type": "<expected doc_type>", "question": "<question to ask the user>"}]
}

Rules:
- Only put a field in "filled" if you are reasonably confident about the match to the profile or documents.
- Split full names into first/last name fields if the form has separate fields.
- For dropdown/select fields, use the option's "value" if present, otherwise its "text".
- For radio/checkbox fields, "value" should be "true" to select it, or omit the field entirely if it shouldn't be selected.
- For file-upload fields, check the user's documents for a matching doc_type; if found, put the document's exact path in "filled". If no match exists, put it in "missing_file" instead.
- Do not fabricate any information not present in the profile or documents.
- Every field must appear in exactly one of "filled", "missing_text", or "missing_file" — never leave a field out entirely, and never put one field in more than one place.

Only output valid JSON. No extra text.
"""


def map_profile_to_fields(fields: list[dict], profile_str: str, documents_str: str) -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)
    payload = json.dumps({
        "fields": fields,
        "profile": json.loads(profile_str),
        "documents": json.loads(documents_str),
    })
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=payload,
        config=genai_types.GenerateContentConfig(
            system_instruction=FIELD_MAPPER_PROMPT,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


class Form_Filler:

    def __init__(self):
        self.client = Client()
        self.playwright_instance = None
        self.browser = None
        self.page = None
        self.executor = None
        self.context = None
        self.user_profile_str = None
        self.user_documents_str = None

    def clone_profile_if_needed(self):
        if os.path.exists(AGENT_PROFILE):
            return  # already cloned successfully

        try:
            shutil.copytree(
                os.path.join(SOURCE_PROFILE, "Profile 2"),
                os.path.join(AGENT_PROFILE, "Default"),
                ignore=shutil.ignore_patterns(
                    "Singleton*",   # these mark a profile as "in use" — copying them
                    "lockfile",     # tricks Playwright's Chrome into thinking another
                    "*.lock",       # instance owns this profile dir
                    "LOCK",
                ),
            )

            # Critical: without this, Chrome can't decrypt the copied cookies/passwords
            shutil.copy2(
                os.path.join(SOURCE_PROFILE, "Local State"),
                os.path.join(AGENT_PROFILE, "Local State"),
            )
        except Exception as e:
            shutil.rmtree(AGENT_PROFILE, ignore_errors=True)
            raise

    def detect_fields(self, page) -> list[dict]:
        all_fields = []
        for frame in page.frames:
            try:
                fields = frame.evaluate(EXTRACTION_SCRIPT)
            except Exception:
                continue
            for f in fields:
                f["frameUrl"] = frame.url
            all_fields.extend(fields)
        return all_fields

    # --- shared plain-Python helpers, callable from anywhere (not LangChain tools) ---

    def _append_status(self, message: str):
        db = SessionLocal()
        try:
            task = db.query(Commands).filter(
                Commands.task_id == self.task_id).first()
            if task is None:
                return
            current = task.status or []
            current.append(message)
            task.status = current
            flag_modified(task, "status")
            db.commit()
        finally:
            db.close()

    def _fill_field(self, ff_id: str, value: str) -> str:
        for frame in self.page.frames:
            locator = frame.locator(f'[data-ff-id="{ff_id}"]')
            if locator.count() == 0:
                continue

            tag = locator.evaluate("el => el.tagName.toLowerCase()")
            field_type = locator.evaluate("el => el.type || ''")

            if tag == "select":
                try:
                    locator.select_option(value=value)
                except Exception:
                    locator.select_option(label=value)
            elif field_type == "checkbox":
                if value.lower() in ("true", "yes", "1"):
                    locator.check()
                else:
                    locator.uncheck()
            elif field_type == "file":
                locator.set_input_files(value)
            elif field_type == "radio":
                locator.check()
            else:
                locator.fill(value)

            return f"Filled {ff_id} with '{value}'"

        return f"Could not find field {ff_id} on the page"

    def _ask_user_text(self, label: str, question: str) -> str:
        self._append_status(f"ASKING_USER::{question}")

        event = register_question(self.task_id)
        event.wait()
        answer = get_answer(self.task_id)

        self._append_status(f"User answered: {answer}")

        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter(
                UserProfile.id == self.user_id).first()
            extra = profile.extra_info or {}
            extra[label] = answer
            profile.extra_info = extra
            db.commit()
        finally:
            db.close()

        return answer

    def _ask_user_file(self, doc_type: str, question: str) -> str:
        self._append_status(f"ASKING_USER_FILE::{question}|||{doc_type}")

        event = register_question(self.task_id)
        event.wait()
        path = get_answer(self.task_id)

        self._append_status(f"User uploaded: {path}")

        db = SessionLocal()
        try:
            user_profile_documents = db.query(Documents).filter(
                Documents.user_id == self.user_id).first()
            if user_profile_documents is None:
                user_profile_documents = Documents(
                    user_id=self.user_id, docs=[])
                db.add(user_profile_documents)

            docs_row = user_profile_documents.docs or []
            docs_row.append({
                "doc_type": doc_type,
                "path": path,
                "filename": path.split('/')[-1],
            })
            user_profile_documents.docs = docs_row
            db.commit()
        finally:
            db.close()

        return path

    def setup(self, user_id: int, task_id: int):
        self.playwright_instance = sync_playwright().start()
        self.clone_profile_if_needed()
        self.user_id = user_id
        self.task_id = task_id

        self.context = self.playwright_instance.chromium.launch_persistent_context(
            user_data_dir=AGENT_PROFILE,
            channel="chrome",
            headless=False,
            slow_mo=400,
            args=["--profile-directory=Profile 2"],
        )
        self.page = self.context.new_page()

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GEMINI_API_KEY,
        )

        db = SessionLocal()
        try:
            user_profile = db.query(UserProfile).filter(
                UserProfile.id == user_id).first()
            if user_profile is None:
                raise ValueError(f"No profile found for user_id: {user_id}")

            documents_user = db.query(Documents).filter(
                Documents.user_id == user_id).first()
            docs_list = documents_user.docs if documents_user else []

            self.user_profile_str = json.dumps({
                "Name": user_profile.Name,
                "Email": user_profile.Email,
                "Contact_number": user_profile.Contact_number,
                "College": user_profile.College,
                "Skills": user_profile.Skills,
                "extra_info": user_profile.extra_info,
            })

            self.user_documents_str = json.dumps({
                "user_id": user_id,
                "docs": docs_list,
            })

        finally:
            db.close()

        @tool
        def wait_for_user() -> str:
            """Call this when a CAPTCHA or login is detected on the page that requires human intervention."""
            input("Human input needed (CAPTCHA/login). Complete it in the browser then press Enter here to continue...")
            return "User completed manual step. Continuing..."

        @tool
        def navigate_to(url: str) -> str:
            """Navigate the browser to the given URL. If incomplete, intelligently add https:// After navigating, ALWAYS call auto_fill_form_tool next."""
            if not url.startswith("http"):
                url = "https://" + url
            self.page.goto(url)
            return f"Navigated to {url}"

        @tool
        def detect_fields_tool() -> str:
            """Detect every fillable field on the current page, including inside iframes. Only use this directly if you need to re-inspect the page after auto_fill_form_tool has already run — auto_fill_form_tool already calls this internally."""
            fields = self.detect_fields(self.page)
            return json.dumps(fields, indent=2)

        @tool
        def auto_fill_form_tool() -> str:
            """Detects every field on the current page, matches ALL of them to the user's profile and documents in a single batch operation, fills everything confidently matched, and asks the user (via the frontend) for anything missing — including file uploads. Call this ONCE right after navigating to a form. Do NOT call detect_fields_tool or fill_field_tool separately when using this — this tool does both internally."""
            fields = self.detect_fields(self.page)
            self._append_status(f"Detected {len(fields)} fields")

            mapping = map_profile_to_fields(
                fields, self.user_profile_str, self.user_documents_str)

            filled_count = 0
            for ff_id, value in mapping.get("filled", {}).items():
                result = self._fill_field(ff_id, value)
                self._append_status(result)
                filled_count += 1

            for item in mapping.get("missing_text", []):
                answer = self._ask_user_text(item["label"], item["question"])
                result = self._fill_field(item["ffId"], answer)
                self._append_status(result)
                filled_count += 1

            for item in mapping.get("missing_file", []):
                path = self._ask_user_file(item["doc_type"], item["question"])
                result = self._fill_field(item["ffId"], path)
                self._append_status(result)
                filled_count += 1

            return (
                f"Auto-filled {filled_count} fields total "
                f"({len(mapping.get('missing_text', []))} asked as text, "
                f"{len(mapping.get('missing_file', []))} asked as file uploads)."
            )

        @tool
        def fill_field_tool(ff_id_and_value: str) -> str:
            """Fill a single field directly by ffId. Input format: 'ffId|||value'. Only use this outside of auto_fill_form_tool, e.g. to correct one field afterward."""
            parts = ff_id_and_value.split("|||")
            ff_id, value = parts[0].strip(), parts[1].strip()
            return self._fill_field(ff_id, value)

        @tool
        def ask_user_tool(label_and_question: str) -> str:
            """Ask the user a text question directly. Input format: 'label|||question'. Only use this outside of auto_fill_form_tool."""
            label, question = label_and_question.split('|||')
            label, question = label.strip(), question.strip()
            return self._ask_user_text(label, question)

        @tool
        def ask_user_file_tool(doc_type_and_question: str) -> str:
            """Ask the user to upload a document directly. Input format: 'doc_type|||question'. Only use this outside of auto_fill_form_tool."""
            doc_type, question = doc_type_and_question.split("|||")
            doc_type, question = doc_type.strip(), question.strip()
            return self._ask_user_file(doc_type, question)

        @tool
        def update_status(status: str) -> str:
            """When you do anything that updates the activity on the browser, use this to log a status update visible to the user in real time."""
            self._append_status(status)
            return "Status updated"

        tools = [
            navigate_to,
            wait_for_user,
            detect_fields_tool,
            auto_fill_form_tool,
            fill_field_tool,
            ask_user_tool,
            ask_user_file_tool,
            update_status,
        ]

        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=False)

        prompt = PromptTemplate.from_template("""You are a form-filling agent. You navigate to forms and fill them using the user's saved profile — asking the user only when something genuinely can't be inferred.

        Important rules:
        - After navigating, ALWAYS call auto_fill_form_tool exactly once — it handles field detection, profile matching, filling, and asking about missing information (including file uploads) all in one step.
        - Do NOT call detect_fields_tool or fill_field_tool individually unless auto_fill_form_tool reports a specific field that still needs correction afterward.
        - After auto_fill_form_tool completes, call update_status once with a short summary, then give your Final Answer.
        - Never fabricate information not present in the user's profile or documents.

        You have access to the following tools:
        {tools}

        Use the following format:
        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        Previous conversation history:
        {chat_history}

        Begin!

        Question: {input}
        Thought:{agent_scratchpad}""")

        agent = create_react_agent(self.llm, tools, prompt)

        self.executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=8,
            handle_parsing_errors=True,
            memory=memory,
        )

    def run(self, user_id: int, task_id: int, user_input: str) -> str:
        if self.executor is None:
            self.setup(user_id, task_id)

        full_input = f"""User profile: {self.user_profile_str}
                    User documents: {self.user_documents_str}
                    Task: {user_input}"""

        result = self.executor.invoke({"input": full_input})
        return result["output"]

    def close(self):
        if self.context is not None:
            self.context.close()
        if self.playwright_instance is not None:
            self.playwright_instance.stop()
