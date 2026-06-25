from google import genai

from google.genai import types

client = genai.Client(api_key="API_KEY")


SYSTEM_PROMPT = """
You are an intent parser for a browser assistant.
Convert user commands into JSON matching this schema:
{"needs_clarification": true|false,
 "clarification_question": "<question to ask the user, or null>",
 "actions": [
    {"action": "navigate"|"fill_form"|"email"|"summarize"|"click", "target_url": "<url or null>", "data": {<relevant key-values>}}
  ],
 "steps": ["<human-readable step 1>", "<step 2>", ...]}

If a command requires multiple sequential actions, include each as a separate object in the "actions" array, in execution order. Even single-action commands must be wrapped in the array.

If the command references something ambiguous (an unnamed person like "him"/"her"/"them", a vague target like "this" with no clear referent, a missing destination, or any detail you cannot reasonably infer from the command alone), set "needs_clarification" to true, write a specific question in "clarification_question", and leave "actions" and "steps" as empty arrays. Do NOT guess or invent placeholder values for missing critical information.

Examples:

User: "go to amazon and search for wireless headphones"
Output: {"needs_clarification": false, "clarification_question": null, "actions": [{"action": "navigate", "target_url": "amazon.com", "data": {"search_query": "wireless headphones"}}], "steps": ["Open amazon.com", "Search for wireless headphones"]}

User: "apply to digicroz intern on linkedin"
Output: {"needs_clarification": false, "clarification_question": null, "actions": [
    {"action": "navigate", "target_url": "linkedin.com", "data": {"search_query": "digicroz intern"}},
    {"action": "click", "target_url": null, "data": {"target": "matching job posting"}},
    {"action": "fill_form", "target_url": null, "data": {}}
  ], "steps": ["Navigate to linkedin.com", "Search for 'digicroz intern'", "Click the matching job posting", "Fill out and submit the application form"]}

User: "send this to him"
Output: {"needs_clarification": true, "clarification_question": "Who would you like this sent to? Please provide a name or email address.", "actions": [], "steps": []}

Only output valid JSON. No extra text.
"""


def parse_intent(user_cmd: str) -> dict:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=user_cmd,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",  # forces clean JSON, no extra text
        ),
    )
    return response.text


print(parse_intent("apply to digicroz intern on linkedin"))
