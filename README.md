# Northstar Homes Sales Agent

AI conversational sales bot for **Northstar Homes — Project Northstar One** (Sector 79, Gurugram). Built for the Huvo AI Forward Deployed Engineer assignment.

Focus: **prompt engineering**, **agent behavior**, multilingual conversation (English / Hindi / Hinglish), lead qualification, simulated site-visit booking, and post-conversation analytics.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, Python 3.11+ |
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Framer Motion |
| LLM | OpenRouter API (`google/gemma-4-26b-a4b-it:free`) |
| Memory | In-memory session store per conversation |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- OpenRouter API key ([openrouter.ai](https://openrouter.ai))

### 1. Environment Setup

```bash
cp .env.example backend/.env
# Edit backend/.env and add your OPENROUTER_API_KEY
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI routes
│   │   ├── config.py            # Settings from .env
│   │   ├── schemas.py           # Pydantic models
│   │   ├── prompts/
│   │   │   └── system_prompt.txt  # Final system prompt
│   │   └── services/
│   │       ├── llm.py           # OpenRouter client + extraction
│   │       ├── booking.py       # Site visit simulator
│   │       ├── analytics.py     # Post-chat analytics
│   │       └── session_store.py # In-memory sessions
│   └── tests/
│       └── test_scenarios.py
├── frontend/
│   ├── app/                     # Next.js App Router
│   ├── components/              # Chat UI components
│   └── lib/api.ts               # API client
├── docs/
│   └── TEST_CASES.md            # Manual test scenarios
└── .env.example
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/sessions` | Create session + greeting |
| `POST` | `/api/chat` | Send message, get reply + slots |
| `POST` | `/api/sessions/{id}/end` | End conversation + analytics |
| `GET` | `/api/sessions/{id}` | Get session state |
| `PATCH` | `/api/sessions/{id}/booking-mode` | Toggle success/fail for demo |
| `GET` | `/api/health` | Health check |

## System Prompt

The final prompt lives at [`backend/app/prompts/system_prompt.txt`](backend/app/prompts/system_prompt.txt).

It covers:
- Natural conversation (chat + voice-ready style)
- Customer qualification (config, budget, timeline)
- English, Hindi, and Hinglish
- Objection handling (price, location, comparison)
- Busy / uninterested customers
- Contact-later requests
- Opt-out (immediate respect)
- Unknown questions (no hallucination)
- Site visit booking + failure recovery
- Human escalation
- Proper conversation ending
- Hard rule: never invent prices, discounts, or availability

## Features

- **Multilingual chat** — mirrors English, Hindi, or Hinglish
- **Live lead sidebar** — configuration, budget, interest, visit status update in real time
- **Booking simulator** — toggle Success/Fail in sidebar for demo
- **Post-conversation analytics** — structured lead dossier on "End Conversation"
- **Suggestion chips** — quick-start prompts for demo scenarios

## Running Tests

```bash
cd backend
pytest tests/test_scenarios.py -v
```

See [`docs/TEST_CASES.md`](docs/TEST_CASES.md) for manual test scenarios.

## Key Assumptions

- Site visit booking is **simulated** (no real calendar/CRM integration)
- Only stated project facts are "truth" (2/3 BHK prices, location)
- Session memory is **in-memory** (lost on server restart)
- Slot extraction uses **fast rule-based heuristics** during chat (one LLM call per turn); analytics still uses LLM at end
- Voice is **not implemented**; prompt is voice-ready for future use

## Known Limitations

- Free OpenRouter models may have rate limits and variable latency
- No persistent database — sessions don't survive restarts
- Slot extraction depends on LLM JSON output quality
- No authentication or multi-user support
- No actual telephony or voice interface

## AI Tools Used

- **Cursor** — development, code generation
- **OpenRouter** — LLM inference (`google/gemma-4-26b-a4b-it:free`)
