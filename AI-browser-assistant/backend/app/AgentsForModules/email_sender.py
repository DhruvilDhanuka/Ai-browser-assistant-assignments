from app.AgentsForModules.pendingAnswers import register_question, get_answer
from langchain.tools import tool
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai
from google.genai import types as genai_types
import base64
from email.mime.text import MIMEText
import json
import os
from sqlalchemy.orm.attributes import flag_modified
from app.database import SessionLocal
from app.models_db.UserProfile import UserProfile
from app.models_db.Commands import Commands
from app.models_db.gmail_creds import GmailCredentials, ContactGroup
from app.services.gmail_auth import main as get_gmail_service  # the helper from earlier
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DRAFT_PROMPT = """You write professional emails from a short stated intent.

Respond ONLY with JSON:
{"subject": "<subject line>", "body": "<full email body, plain text, professional tone, no placeholders>"}

Only output valid JSON. No extra text."""


def generate_draft(intent: str, sender_name: str) -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Sender's name: {sender_name}\nIntent: {intent}",
        config=genai_types.GenerateContentConfig(
            system_instruction=DRAFT_PROMPT,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


class EmailSender:

    def __init__(self):
        self.executor = None
        self.user_id = None
        self.task_id = None

    def _append_status(self, message: str):

        db = SessionLocal()

        try:
            userCommand = db.query(Commands).filter(
                Commands.task_id == self.task_id).first()

            if (userCommand is None):
                return

            statusList  = userCommand.status or []
            statusList.append(message)
            userCommand.status = statusList
            flag_modified(userCommand, "status")
            db.commit()
        finally:
            db.close()

    def setup(self, user_id: int, task_id: int):
        self.user_id = user_id
        self.task_id = task_id

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GEMINI_API_KEY,
        )

        db = SessionLocal()
        try:
            user_profile = db.query(UserProfile).filter(
                UserProfile.id == user_id).first()
            self.sender_name = user_profile.Name if user_profile else "the user"

            groups_row = db.query(ContactGroup).filter(
                ContactGroup.user_id == user_id).first()
            self.groups = groups_row.groups_with_number if groups_row else {}
        finally:
            db.close()

        @tool
        def update_status(status: str) -> str:
            """Log a status update visible to the user in real time."""
            self._append_status(status)
            return "Status updated"

        @tool
        def resolve_recipient_tool(recipient: str):
            """Resolve a recipient name or group name (e.g. 'team', 'Arjun') into actual email address(es). Returns a comma-separated list of emails, or asks the user if the recipient is unknown."""
            if recipient in self.groups:
                return ", ".join(self.groups[recipient])

            if "@" in recipient:
                return recipient

            self._append_status(
                f"ASKING_USER::I don't recognize '{recipient}' — what's their email address?")
            event = register_question(self.task_id)
            event.wait()
            answer = get_answer(self.task_id)
            self._append_status(f"User answered: {answer}")
            return answer

        @tool
        def draft_email_tool(intent: str) -> str:
            """Generate an email subject and body from a stated intent. Returns JSON: {"subject": ..., "body": ...}"""
            self._append_status("Drafting Email")
            draft = generate_draft(intent, self.sender_name)

            return json.dumps(draft)

        @tool
        def confirm_send_tool(to_subject_body: str) -> str:
            """Show the drafted email to the user and wait for their approval before sending. Input format: 'to|||subject|||body'. Returns 'approved' or the user's edited version as JSON, or 'rejected' if they cancel."""
            to, subject, body = to_subject_body.split("|||", 2)
            self._append_status(f"CONFIRM_SEND::{to}|||{subject}|||{body}")

            event = register_question(self.task_id)
            event.wait()
            decision = get_answer(self.task_id)
            self._append_status(f"User decision: {decision}")
            return decision

        @tool
        def send_email_tool(to_subject_body: str) -> str:
            """Actually send the email via Gmail. ONLY call this after confirm_send_tool returned approval. Input format: 'to|||subject|||body'."""
            to, subject, body = to_subject_body.split("|||", 2)

            db = SessionLocal()
            try:
                service = get_gmail_service(db, self.user_id)
            finally:
                db.close()

            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            service.users().messages().send(
                userId="me", body={"raw": raw}).execute()
            self._append_status(f"Email sent to {to}")
            return f"Email sent to {to}"

        @tool
        def list_unread_tool() -> str:
            """Fetch unread emails for summarization. Returns a JSON list of {from, subject, snippet}."""
            db = SessionLocal()
            try:
                service = get_gmail_service(db, self.user_id)
            finally:
                db.close()

            results = service.users().messages().list(
                userId="me", q="is:unread", maxResults=20).execute()
            messages = results.get("messages", [])

            summaries = []
            for m in messages:
                msg = service.users().messages().get(userId="me", id=m["id"], format="metadata",
                                                     metadataHeaders=["From", "Subject"]).execute()
                headers = {h["name"]: h["value"]
                           for h in msg["payload"]["headers"]}
                summaries.append({
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "snippet": msg.get("snippet", ""),
                })
            return json.dumps(summaries)

        @tool
        def get_thread_tool(query: str) -> str:
            """Find and fetch a message thread by sender name or subject keyword, for thread-aware replies. Returns the thread's messages as JSON."""

            db = SessionLocal()
            try:
                service = get_gmail_service(db, self.user_id)
            finally:
                db.close()

            results = service.users().messages().list(
                userId="me", q=query, maxResults=1).execute()

            messages = results.get("messages", [])
            if not messages:
                return "No matching thread found"

            thread_id = service.users().messages().get(
                userId="me", id=messages[0]["id"]).execute()["threadId"]
            thread = service.users().threads().get(userId="me", id=thread_id).execute()

            parsed = []
            for msg in thread["messages"]:
                headers = {h["name"]: h["value"]
                           for h in msg["payload"]["headers"]}
                parsed.append({
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "snippet": msg.get("snippet", ""),
                })
            return json.dumps(parsed)

        tools = [update_status, resolve_recipient_tool, draft_email_tool,
                 confirm_send_tool, send_email_tool, list_unread_tool, get_thread_tool]

        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=False)

        prompt = PromptTemplate.from_template("""You are an email assistant. You draft, send, reply to, and summarize emails on the user's behalf.
        Important rules:
        - Resolve the recipient using resolve_recipient_tool before drafting anything.
        - Always draft with draft_email_tool, then ALWAYS call confirm_send_tool before send_email_tool — NEVER call send_email_tool without a prior confirm_send_tool approval.
        - If confirm_send_tool returns 'rejected', do not send — stop and report that the user cancelled.
        - For replies, use get_thread_tool first to read context before drafting.
        - For "summarise unread emails" requests, use list_unread_tool and summarize the results directly — no need to draft or send anything.
        - After every meaningful step, call update_status with a short description.

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
            max_iterations=10,
            handle_parsing_errors=True,
            memory=memory,
        )

    def run(self, user_id: int, task_id: int, user_input: str) -> str:
        if self.executor is None:
            self.setup(user_id, task_id)

        result = self.executor.invoke({"input": user_input})
        return result["output"]
