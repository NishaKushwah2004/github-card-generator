import os
import logging
import sys
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from agent import github_card_agent
import uvicorn
from pathlib import Path

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("backend")

app = FastAPI(title="GitHub Dev Card Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ADK Services
session_service = InMemorySessionService()

# Create a Runner
runner = Runner(
    agent=github_card_agent,
    app_name="github_card_app",
    session_service=session_service,
    auto_create_session=True
)

# Ensure static directories exist
STATIC_CARDS_DIR = Path("static/cards")
STATIC_CARDS_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files to serve the generated cards
app.mount("/static", StaticFiles(directory="static"), name="static")

class CardRequest(BaseModel):
    username: str

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/generate")
async def generate_card(request: CardRequest):
    username = request.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    session_id = f"session_{username}"
    user_id = "default_user"
    
    # Retry mechanism for MCP session creation instability
    max_retries = 3
    retry_delay = 1.0 # seconds

    for attempt in range(max_retries):
        agent_response_text = ""
        card_url = None
        
        try:
            logger.info(f"Generating card for {username} (Attempt {attempt + 1})")
            
            # Run the agent through the runner
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(parts=[types.Part(text=f"Generate a dev card for {username}")])
            ):
                if event.content:
                    for part in event.content.parts:
                        if part.text:
                            agent_response_text += part.text
            
            # Verify file creation
            card_file = STATIC_CARDS_DIR / f"{username}.html"
            if card_file.exists():
                card_url = f"/static/cards/{username}.html"
                with open(card_file, "r", encoding="utf-8") as f:
                    card_html = f.read()
                
                logger.info(f"Successfully generated card for {username}")
                return {
                    "status": "success",
                    "username": username,
                    "card_url": card_url,
                    "card_html": card_html
                }

            else:
                logger.warning(f"Attempt {attempt + 1}: Card file not found after agent run.")
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=500, detail="Card generation failed to save file.")
        
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed with error: {e}", exc_info=True)
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                # Exponential backoff
                retry_delay *= 2
            else:
                # Provide a more detailed error message to the client on final failure
                raise HTTPException(status_code=500, detail=f"MCP Error after {max_retries} attempts: {str(e)}")

@app.get("/card/{username}")
async def get_card(username: str):
    card_file = STATIC_CARDS_DIR / f"{username}.html"
    if not card_file.exists():
        raise HTTPException(status_code=404, detail="Card not found")
    
    with open(card_file, "r", encoding="utf-8") as f:
        return {"html": f.read()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
