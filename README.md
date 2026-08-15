# NOQUE — AI-Powered Legacy Codebase Explainer & Modernizer

> **HackOrbit | PS-06** — Built for the Google Developer Group hackathon.

NOQUE takes a legacy codebase (ZIP upload or GitHub URL) and uses **Google Gemini 3.6 Flash** to automatically generate:

1. 🧠 **Natural Language Explanations** — Module & function-level summaries with confidence scores.
2. 🕸️ **Dependency Graph** — Interactive force-directed visualization of imports and function calls.
3. 🧪 **Unit Tests** — Auto-generated pytest/jest tests with a >60% coverage verification loop.
4. 🔄 **Modernized Code** — Refactored to modern standards with breaking change warnings.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite, TailwindCSS, Monaco Editor, React Force Graph |
| Backend | Python + FastAPI, Tree-sitter, Google Gemini API |
| Database | PostgreSQL (via Docker) |
| Languages Supported | Python, JavaScript |

## Quick Start

### 1. Start PostgreSQL
```bash
docker compose up -d
```

### 2. Start the Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your GEMINI_API_KEY here
uvicorn main:app --reload --port 8000
```

### 3. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** and upload a ZIP of your legacy codebase!

## Project Structure

```
noque/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Environment settings
│   ├── db.py                    # PostgreSQL connection
│   ├── routers/
│   │   └── jobs.py              # REST API endpoints
│   ├── models/
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── schemas.py           # Pydantic request/response schemas
│   └── services/
│       ├── gemini_client.py     # Gemini API client
│       ├── parser.py            # Tree-sitter code parser
│       ├── explainer.py         # AI explanation service
│       ├── refactorer.py        # AI refactoring service
│       ├── test_generator.py    # Test gen + coverage loop
│       └── pipeline.py          # Main processing orchestrator
├── frontend/
│   └── src/
│       ├── api.js               # Axios API client
│       ├── App.jsx              # Root component + routing
│       ├── pages/
│       │   ├── UploadPage.jsx   # ZIP upload + GitHub URL
│       │   └── ResultsPage.jsx  # 4-tab results dashboard
│       └── components/
│           ├── ExplanationTab.jsx
│           ├── DependencyGraphTab.jsx
│           ├── TestsTab.jsx
│           └── RefactorTab.jsx
├── docker-compose.yml           # PostgreSQL container
└── README.md
```

## License

MIT
