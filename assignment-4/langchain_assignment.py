from langchain.tools import tool
from playwright.sync_api import sync_playwright
from langchain_classic.agents import AgentExecutor, create_react_agent
from langsmith import Client
from langchain_groq import ChatGroq
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.prompts import PromptTemplate

client = Client()

playwright_instance = sync_playwright().start()
browser = playwright_instance.chromium.launch(headless=False, slow_mo=500)
page = browser.new_page()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key="API_KEY"
)


@tool
def navigate_to(url: str):
    """Navigate the browser to the given URL if the given URL is not complete intelligently add https:// or required marups in the URL itself do not fuck around here . After navigating, ALWAYS call get_page_content to see the page before doing anything else."""
    if not url.startswith("http"):
        url = "https://" + url
    page.goto(url)
    return f"Navigated to {url}"


@tool
def wait_for_user() -> str:
    """Call this when a CAPTCHA or login is detected on the page that requires human intervention."""
    input("⚠️  Human input needed (CAPTCHA/login). Complete it in the browser then press Enter here to continue...")
    return "User completed manual step. Continuing..."


@tool
def click_element(selector: str):
    """Click an element identified by CSS selector"""
    try:
        page.click(selector, timeout=5000)
        return f"Clicked on {selector}"
    except Exception as e:
        return f"Could not click {selector}: {str(e)}. Action may already be completed."


@tool
def get_page_content() -> str:
    """Get the current page's interactive elements with their selectors. Always call this after navigating to find the right selectors."""
    page.wait_for_load_state("networkidle")
    elements = page.evaluate("""() => {
        const results = [];
        const selectors = ['input', 'textarea', 'button', 'a', 'select'];
        selectors.forEach(tag => {
            document.querySelectorAll(tag).forEach(el => {
                results.push({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    text: el.innerText?.slice(0, 50) || '',
                    class: el.className?.slice(0, 30) || ''
                });
            });
        });
        return results.slice(0, 30);
    }""")
    return str(elements)


@tool
def type_text(selector_and_text: str) -> str:
    """Type text into an input field and press Enter. Input format: 'selector|||text' e.g. 'textarea[name=q]|||AI news'"""
    parts = selector_and_text.split("|||")
    selector = parts[0].strip()
    text = parts[1].strip()
    page.fill(selector, text)
    page.keyboard.press("Enter")
    return f"Typed '{text}' into {selector} and pressed Enter. Form submitted, no need to click any button."


tools = [navigate_to, click_element,
         type_text, get_page_content, wait_for_user]

# ReAct prompt that supports chat_history

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=False  # False because our prompt uses string format not messages
)


prompt = PromptTemplate.from_template("""You are a browser automation agent like Jarvis. You execute what the user asks naturally.

Important rules:
- When given a site name like "youtube" or "google", always convert it to a proper URL like "https://www.youtube.com" or "https://www.google.com"
- When user says "go back", use navigate_to with the previous page's URL from chat history
- Execute ONLY what the user explicitly asks, do not take extra actions
- After navigating ALWAYS call get_page_content before doing anything else

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
    memory=memory
)

# Multi-turn conversation loop
print("Browser Agent Ready! Type 'quit' to exit.")
while True:
    user_input = input("\nYou: ")
    if user_input.lower() == "quit":
        break
    try:
        result = executor.invoke({"input": user_input})
        print(f"\nAgent: {result['output']}")
    except Exception as e:
        print(f"\nAgent hit an error: {str(e)}")
        print("You can continue giving commands.")

browser.close()
playwright_instance.stop()
