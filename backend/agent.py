import os
import sys
import logging
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("agent")

current_dir = os.path.dirname(os.path.abspath(__file__))
server_path = os.path.join(current_dir, "mcp_server.py")

mcp_env = os.environ.copy()
mcp_env["PYTHONUNBUFFERED"] = "1"
mcp_env["PYTHONPATH"] = current_dir

mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["-u", server_path],
            env=mcp_env
        ),
        timeout=60.0 
    )
)

# Create the ADK Agent - Optimization: No external LLM tool calls
github_card_agent = Agent(
    name="github_card_agent",
    model="gemini-flash-latest", # Use stable alias
    instruction=(
        "You are a GitHub profile analyst and dev card generator. "
        "Strictly follow this optimized workflow to save API quota:\n"
        "1. Call scrape_github with the username.\n"
        "2. ANALYZE the data yourself to determine:\n"
        "   - developer_vibe (1 sentence personality)\n"
        "   - top_skills (list of 3)\n"
        "   - fun_fact (clever inference)\n"
        "   - card_theme (one of: hacker, builder, researcher, designer, open-source-hero)\n"
        "3. Call generate_card_html with the original data AND your analysis results.\n"
        "4. Call save_card with the result.\n"
        "Never use external tools for analysis; your internal reasoning is sufficient."
    ),
    tools=[mcp_toolset]
)

if __name__ == "__main__":
    import asyncio
    from google.adk.runners import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.genai import types
    
    async def test():
        print("Testing optimized agent...")
        runner = Runner(
            agent=github_card_agent,
            app_name="github_card_app",
            session_service=InMemorySessionService(),
            auto_create_session=True
        )
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=types.Content(parts=[types.Part(text="torvalds")])
        ):
            if event.content:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
        print("\n--- Test Complete ---")

    asyncio.run(test())
