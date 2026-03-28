# Judgement

A web-based card game built with Python (FastAPI) and React (TypeScript).

Supports both multiplayer (real-time via WebSockets) and single-player (vs AI) modes.

## Project Structure

```
judgement/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── game/     # Game logic and rules
│   │   ├── ai/       # AI opponent logic
│   │   ├── api/      # REST and WebSocket endpoints
│   │   └── models/   # Data models
│   ├── tests/
│   └── requirements.txt
├── frontend/         # React TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   └── package.json
└── README.md
```

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## License

MIT
