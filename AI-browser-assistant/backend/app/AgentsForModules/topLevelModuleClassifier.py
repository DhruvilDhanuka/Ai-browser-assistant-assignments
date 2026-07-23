from google import genai
import json
from google.genai import types
# from app.AgentsForModules.calendar_manager import calendar_manager
# from app.AgentsForModules.docs_summarize import docs_summarize
from app.AgentsForModules.email_sender import EmailSender as Email_Sender
from app.AgentsForModules.form_filler import Form_Filler
# from app.AgentsForModules.general_jarvis import general_jarvis
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


client = genai.Client(api_key=API_KEY)


SYSTEM_PROMPT = """
You are the top-level intent router for a personal browser assistant with these modules:

- "form_filling": filling out/submitting forms (jobs, hackathons, courses, Google Forms, applications)
- "email": drafting, sending, replying to, or summarising emails
- "summarization": summarising a page, article, URL, or comparing multiple pages
- "calendar": checking availability, adding events, finding free slots, recurring schedules
- "general": simple browser actions not tied to a module above — navigate, search, click, open a site

Convert the user's command into JSON matching this schema:
{"modules": ["<module_1>", "<module_2>", ...],
 "actions": [
    {"module": "<one of the module names above>", "sub_command": "<a focused, standalone, complete instruction for JUST this module's part of the task>"}
  ],
 "steps": ["<human-readable step 1>", "<step 2>", ...]}

Rules:
- "modules" lists every distinct module this command touches, in the order they should run. A single-module command still has exactly one entry.
- Each action's "sub_command" must be a complete, standalone instruction that module's own agent can act on directly, including any concrete detail relevant to it (URLs, recipients, dates, etc. — pull these out of the original command yourself). It should read like a clean instruction to a human assistant, not a fragment.
- If a later step depends on something an earlier step will discover (e.g. a deadline found while filling a form), phrase it explicitly, e.g. "Add the application deadline you find on the form to my calendar."
- If any detail is ambiguous or missing, phrase the sub_command so the module's own agent knows to ask the user directly — do not guess or invent values.
- Also in actions keep the modules in series on which they should execute 
Examples:

User: "apply to this internship, add the deadline to my calendar, and email my mentor that I applied"
Output: {"modules": ["form_filling", "calendar", "email"], "actions": [
    {"module": "form_filling", "sub_command": "Apply to this internship using my saved profile."},
    {"module": "calendar", "sub_command": "Add the application deadline found on the internship form to my calendar."},
    {"module": "email", "sub_command": "Email my mentor letting them know I applied to this internship."}
  ], "steps": ["Fill and submit the application form", "Extract the deadline and add it to calendar", "Email mentor confirming the application"]}

User: "fill this hackathon form for me: https://example.com/apply"
Output: {"modules": ["form_filling"], "actions": [{"module": "form_filling", "sub_command": "Fill out and submit the hackathon application form at https://example.com/apply using my saved profile."}], "steps": ["Navigate to the form", "Detect fields", "Fill from profile", "Ask for anything missing", "Preview and submit"]}

User: "summarise this page"
Output: {"modules": ["summarization"], "actions": [{"module": "summarization", "sub_command": "Summarise the current page."}], "steps": ["Extract page content", "Generate structured summary"]}

User: "what's my next free 2-hour slot this week"
Output: {"modules": ["calendar"], "actions": [{"module": "calendar", "sub_command": "Find my next free 2-hour slot this week."}], "steps": ["Read calendar", "Find matching free slot"]}

User: "go to amazon and search for wireless headphones"
Output: {"modules": ["general"], "actions": [{"module": "general", "sub_command": "Go to amazon.com and search for wireless headphones."}], "steps": ["Open amazon.com", "Search for wireless headphones"]}

User: "send this to him"
Output: {"modules": ["email"], "actions": [{"module": "email", "sub_command": "Send an email about 'this' — ask the user who the recipient is, since it's unclear."}], "steps": ["Ask the user who to send it to", "Draft and confirm the email"]}

Only output valid JSON. No extra text.
"""


def parse_intent(user_cmd: str) -> dict:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_cmd,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",  # forces clean JSON, no extra text
        ),
    )
    return json.loads(response.text)


def load_modules(user_cmd: str, user_id: int, task_id: int) -> dict:
    """
    Classifies the user's command into one or more modules, then dispatches
    a focused sub_command to each module's own agent in order.

    No clarification handling happens here — each module's own agent has its
    own ask_user_tool to resolve ambiguity mid-task, so the classifier's only
    job is routing + splitting the command, not validating it.
    """
    intent_parsed = parse_intent(user_cmd)
    actions = intent_parsed.get("actions", [])

    results = []
    for action in actions:
        module = action.get("module")
        sub_command = action.get("sub_command", user_cmd)

        if module == "form_filling":
            agent = Form_Filler()
            result = agent.run(user_id, task_id, sub_command)
        elif module == "email":
            agent = Email_Sender()
            result = agent.run(user_id, task_id, sub_command)
        elif module == "summarization":
            result = None  # not built yet
        elif module == "calendar":
            result = None  # not built yet
        elif module == "general":
            result = None  # not built yet
        else:
            result = None

        results.append({
            "module": module,
            "sub_command": sub_command,
            "result": result,
        })

    return {"results": results}
