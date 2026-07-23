"""Quick diagnostic: does the email agent actually call tools, or does it Final Answer immediately?"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from langchain.tools import tool
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
)

@tool
def update_status(status: str) -> str:
    """Log a status update visible to the user in real time."""
    print(f"  [TOOL CALLED] update_status: {status}")
    return "Status updated"

@tool
def resolve_recipient_tool(recipient: str) -> str:
    """Resolve a recipient name or group name (e.g. 'team', 'Arjun') into actual email address(es). Returns a comma-separated list of emails, or asks the user if the recipient is unknown."""
    print(f"  [TOOL CALLED] resolve_recipient_tool: {recipient}")
    return "test@example.com"

@tool
def draft_email_tool(intent: str) -> str:
    """Generate an email subject and body from a stated intent. Returns JSON: {"subject": ..., "body": ...}"""
    print(f"  [TOOL CALLED] draft_email_tool: {intent}")
    return '{"subject": "Congratulations!", "body": "Dear Son, Congratulations on your selection in IIT Bombay!"}'

@tool
def confirm_send_tool(to_subject_body: str) -> str:
    """Show the drafted email to the user and wait for their approval before sending."""
    print(f"  [TOOL CALLED] confirm_send_tool: {to_subject_body}")
    return "approved"

@tool
def send_email_tool(to_subject_body: str) -> str:
    """Actually send the email via Gmail."""
    print(f"  [TOOL CALLED] send_email_tool: {to_subject_body}")
    return "Email sent"

@tool
def list_unread_tool() -> str:
    """Fetch unread emails for summarization."""
    return "[]"

@tool
def get_thread_tool(query: str) -> str:
    """Find and fetch a message thread."""
    return "No matching thread found"

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

agent = create_react_agent(llm, tools, prompt)

executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    handle_parsing_errors=True,
    memory=memory,
)

print("=" * 60)
print("Running agent with email command...")
print("=" * 60)

result = executor.invoke({"input": "send an email to my son for congratulating him for selection in iit bombay"})
print("\n" + "=" * 60)
print("RESULT:", result["output"])
print("=" * 60)
