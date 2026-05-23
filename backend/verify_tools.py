import asyncio
import os
import logging
import sys
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from agent import github_card_agent
from pathlib import Path

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("test_verify")

async def main():
    username = "NishaKushwah2004"
    print(f"--- Testing end-to-end for {username} ---")
    
    # Initialize Runner
    runner = Runner(
        agent=github_card_agent,
        app_name="github_card_app",
        session_service=InMemorySessionService(),
        auto_create_session=True
    )
    
    agent_response_text = ""
    
    try:
        print(f"Step 1-4: Running Agent workflow (Scrape -> Analyze -> Generate -> Save)...")
        async for event in runner.run_async(
            user_id="test_user",
            session_id=f"test_{username}",
            new_message=types.Content(parts=[types.Part(text=f"Generate a dev card for {username}")])
        ):
            if event.content:
                for part in event.content.parts:
                    if part.text:
                        agent_response_text += part.text
        
        print("\nAgent Response:")
        print(agent_response_text)
        
        # Verify file creation
        static_path = Path("static/cards") / f"{username}.html"
        if static_path.exists():
            print(f"\nSUCCESS: Card generated and saved to {static_path}")
        else:
            print(f"\nFAILED: Card file not found at {static_path}")

    except Exception as e:
        print(f"\nFAILED: Error during agent execution: {e}")

    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(main())
