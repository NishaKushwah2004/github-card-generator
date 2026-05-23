import os
import json
import httpx
import logging
import sys
from google import genai
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Force all logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("mcp_server")

# Initialize FastMCP
mcp = FastMCP("GitHubDevCard")

# Configure Gemini
client_gemini = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
# Using alias confirmed available in list_models.py
MODEL_ID = "gemini-flash-latest" 

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Fetches MINIMAL GitHub statistics for a given user."""
    logger.info(f"Scraping GitHub for user: {username}")
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"} if os.getenv("GITHUB_TOKEN") else {}
    async with httpx.AsyncClient() as client:
        # Fetch user profile
        user_res = await client.get(f"https://api.github.com/users/{username}", headers=headers)
        if user_res.status_code != 200:
            return {"error": f"User not found"}
        u = user_res.json()

        # Fetch repos - limit to 30 for token efficiency
        repos_res = await client.get(f"https://api.github.com/users/{username}/repos?sort=stars&per_page=30", headers=headers)
        repos_data = repos_res.json() if repos_res.status_code == 200 else []

    # Process repos - Minimal data for Agent analysis
    top_repos = []
    langs = {}
    for r in sorted(repos_data, key=lambda x: x.get("stargazers_count", 0), reverse=True)[:5]:
        top_repos.append({
            "n": r.get("name"),
            "s": r.get("stargazers_count"),
            "l": r.get("language"),
            "d": (r.get("description") or "")[:50] # Trim description
        })
        l = r.get("language")
        if l: langs[l] = langs.get(l, 0) + 1

    return {
        "name": u.get("name") or username,
        "avatar": u.get("avatar_url"),
        "bio": (u.get("bio") or "")[:100],
        "repos_count": u.get("public_repos"),
        "followers": u.get("followers"),
        "top_projects": top_repos,
        "languages": langs
    }

@mcp.tool()
def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generates a self-contained HTML string for a beautiful dev card."""
    logger.info(f"Generating HTML for {username}")
    theme = analysis.get("card_theme", "builder")
    
    themes = {
        "hacker": "background: #0d1117; color: #58a6ff; border: 1px solid #30363d;",
        "builder": "background: #ffffff; color: #24292f; border: 1px solid #d0d7de;",
        "researcher": "background: #f6f8fa; color: #0969da; border: 1px solid #afb8c1;",
        "designer": "background: linear-gradient(135deg, #f0f2f5, #e6e9f0); color: #1a1d23; border: 1px solid #cfd4db;",
        "open-source-hero": "background: #f0fff4; color: #1a7f37; border: 1px solid #2da44e;"
    }
    
    style = themes.get(theme, themes["builder"])
    skills_html = "".join([f'<span style="padding: 2px 8px; margin-right: 5px; border-radius: 12px; font-size: 0.8rem; background: rgba(0,0,0,0.1);">{s}</span>' for s in analysis.get("top_skills", [])])
    
    repos_html = "".join([f'<li><strong>{r["n"]}</strong> (⭐{r["s"]}) - {r["l"]}</li>' for r in github_data.get("top_projects", [])[:3]])

    html = f"""
    <div style="width: 400px; padding: 20px; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; {style}">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <img src="{github_data.get('avatar')}" style="width: 60px; height: 60px; border-radius: 50%; margin-right: 15px;" />
            <div>
                <h2 style="margin: 0;">{github_data.get('name')}</h2>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.8;">@{username}</p>
            </div>
        </div>
        <p style="font-style: italic; margin-bottom: 15px;">"{analysis.get('developer_vibe')}"</p>
        <div style="margin-bottom: 15px;">{skills_html}</div>
        <div style="display: flex; gap: 20px; font-size: 0.9rem; margin-bottom: 15px;">
            <span><strong>{github_data.get('repos_count')}</strong> Repos</span>
            <span><strong>{github_data.get('followers')}</strong> Followers</span>
        </div>
        <div style="font-size: 0.85rem;">
            <p style="margin-bottom: 5px; font-weight: bold;">Top Projects:</p>
            <ul style="margin: 0; padding-left: 20px;">{repos_html}</ul>
        </div>
        <p style="font-size: 0.75rem; margin-top: 15px; text-align: right; opacity: 0.6;">Fun Fact: {analysis.get('fun_fact')}</p>
    </div>
    """
    return html

@mcp.tool()
def save_card(username: str, html: str) -> str:
    """Saves the HTML card to the static/cards directory."""
    logger.info(f"Saving card for {username}")
    current_dir = Path(__file__).parent.absolute()
    static_path = current_dir / "static" / "cards"
    static_path.mkdir(parents=True, exist_ok=True)
    
    file_path = static_path / f"{username}.html"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return f"/static/cards/{username}.html"

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)
    mcp.run()
