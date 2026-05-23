# github-card-generator

# 🃏 GitHub Dev Card Generator

A full-stack AI-powered web application that generates beautiful, personalized developer cards from any public GitHub profile. Built with Google ADK (Agent Development Kit), FastAPI, and a clean dark-mode frontend.

---

## ✨ What It Does

Enter any GitHub username and the app will:

1. Fetch the user's public GitHub profile and repository data
2. Analyze their top languages, projects, and activity using an AI agent
3. Generate a stylized HTML "dev card" with a personalized vibe, top skills, and fun fact
4. Serve the card for download or sharing

---

## 🏗️ Architecture

The project is split into two services:

### Backend (`/backend`)

A **FastAPI** server that orchestrates an AI agent workflow via Google ADK.

| File | Purpose |
|---|---|
| `main.py` | FastAPI app — exposes `/generate`, `/card/{username}`, `/health` endpoints; serves generated card HTML files via `/static` |
| `agent.py` | Defines the Google ADK `Agent` using Gemini Flash; wires it to the MCP toolset |
| `mcp_server.py` | MCP server (FastMCP) exposing three tools: `scrape_github`, `generate_card_html`, `save_card` |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container build using `python:3.12-slim` and `uv` for fast dependency installation |

### Frontend (`/frontend`)

A single-page HTML application served via **nginx**.

| File | Purpose |
|---|---|
| `index.html` | Full UI — input form, skeleton loader, card preview, share/download actions |
| `Dockerfile` | nginx-based container; substitutes `BACKEND_URL` env variable at runtime |

---

## 🤖 Agent Workflow

The AI agent follows a strict 4-step pipeline:

```
1. scrape_github(username)       → Fetch profile + top repos from GitHub API
2. [Internal analysis]           → Agent determines vibe, top skills, fun fact, theme
3. generate_card_html(...)       → Builds a self-contained HTML card string
4. save_card(username, html)     → Writes card to static/cards/{username}.html
```

The agent (`github_card_agent`) runs on **Gemini Flash** and is explicitly instructed to perform analysis internally (without extra LLM calls) to minimize API quota usage.

---

## 🛠️ MCP Tools

The MCP server (`mcp_server.py`) exposes these tools to the agent:

### `scrape_github(username: str) → dict`
Fetches minimal GitHub data: name, avatar, bio, public repo count, followers, top 5 repos by stars, and language breakdown (capped at 30 repos to stay token-efficient).

### `generate_card_html(username, github_data, analysis) → str`
Builds a self-contained HTML `<div>` card. Supports five themes: `hacker`, `builder`, `researcher`, `designer`, `open-source-hero`.

The `analysis` dict must contain:
- `developer_vibe` — one-sentence personality
- `top_skills` — list of 3 skill labels
- `fun_fact` — clever inference
- `card_theme` — one of the five theme keys

### `save_card(username: str, html: str) → str`
Writes the card HTML to `static/cards/{username}.html` and returns the relative URL path.

---

## 🌐 API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/generate` | Generate a dev card for `{ "username": "..." }` |
| `GET` | `/card/{username}` | Retrieve a previously generated card's HTML |
| `GET` | `/static/cards/{username}.html` | Serve the card file directly |

The `/generate` endpoint includes a **retry mechanism** (3 attempts, exponential backoff) to handle MCP session instability.

---

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose (or run services manually)
- A [Google AI API key](https://aistudio.google.com/) (for Gemini)
- Optionally, a [GitHub personal access token](https://github.com/settings/tokens) (raises rate limits from 60 to 5000 req/hr)

### Environment Variables

Create a `.env` file in `/backend`:

```env
GOOGLE_API_KEY=your_google_api_key_here
GITHUB_TOKEN=your_github_token_here   # optional but recommended
```

### Running with Docker

```bash
# Backend
cd backend
docker build -t devcard-backend .
docker run -p 8080:8080 --env-file .env devcard-backend

# Frontend (in another terminal)
cd frontend
docker build -t devcard-frontend .
docker run -p 80:80 -e BACKEND_URL=http://localhost:8080 devcard-frontend
```

Then open `http://localhost` in your browser.

### Running Locally (without Docker)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
```

Open `frontend/index.html` directly in your browser, or serve it with any static file server, pointing `BACKEND_URL` at `http://localhost:8080`.

---

## 🧪 Testing

```bash
# End-to-end agent test (from /backend)
python verify_tools.py

# Quick agent smoke test
python agent.py

# List available Gemini models
python list_models.py
```

---

## 📦 Dependencies

### Backend

| Package | Role |
|---|---|
| `fastapi` + `uvicorn` | HTTP server |
| `google-adk` | Agent orchestration framework |
| `google-genai` | Gemini API client |
| `mcp` | Model Context Protocol server/client |
| `httpx` | Async HTTP for GitHub API calls |
| `pydantic` | Request validation |
| `python-dotenv` | `.env` loading |

### Frontend

- Vanilla HTML/CSS/JS — zero framework dependencies
- `html2canvas` (CDN) — PNG export
- nginx (Docker) — static file serving with env substitution

---

## 📁 Project Structure

```
├── backend/
│   ├── agent.py           # ADK agent definition
│   ├── main.py            # FastAPI server
│   ├── mcp_server.py      # MCP tools (scrape, generate, save)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── verify_tools.py    # E2E test script
│   └── list_models.py     # Model listing utility
└── frontend/
    ├── index.html          # Single-page UI
    └── Dockerfile          # nginx + envsubst
```

---

## 🎨 Card Themes

| Theme | Style |
|---|---|
| `hacker` | Dark background, blue accent — terminal aesthetic |
| `builder` | Clean white, GitHub-inspired — professional |
| `researcher` | Light gray, blue text — academic |
| `designer` | Soft gradient, refined typography |
| `open-source-hero` | Green tones, open-source spirit |

---

## ⚠️ Known Limitations

- Cards are saved to the local filesystem; they don't persist across container restarts without a volume mount.
- GitHub API unauthenticated requests are limited to 60/hour. Add a `GITHUB_TOKEN` for production use.
- The MCP stdio transport can occasionally have session initialization instability — the retry logic in `main.py` mitigates this.

---

## 📄 License

MIT