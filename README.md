# Judgement

Indian trick-taking card game (also known as Kachuful). Play against AI opponents or with friends online.

## System Requirements

- **Python** 3.9+
- **Node.js** 18+
- **OS:** macOS, Windows, Linux

## Install & Play

```bash
# One-time setup (installs all dependencies)
./setup

# Play
./play
```

Opens as a desktop window if [pywebview](https://pywebview.flowrl.com/) is available, otherwise opens in your browser at `http://localhost:8000`.

### Manual Install

```bash
pip3 install -r backend/requirements.txt
pip3 install pywebview          # optional — desktop window mode
cd frontend && npm install && npm run build && cd ..
./play
```

## How to Play

- **Quick Play** — instant game against AI opponents
- **Create Game** — set up a lobby, choose variant and players
- **Join Game** — enter a join code to play with friends

### Rules

- Standard 52-card deck. Trump suit rotates each round
- Each round: bid how many tricks you'll win, then play
- Must follow lead suit if able. Highest trump wins, else highest of lead suit
- Hit your bid = positive points. Miss = negative points

### Dealing Variants

| Variant | Rounds | Max Players |
|---------|--------|-------------|
| 10 → 1 | 10 | 5 |
| 8 → 1 → 8 | 16 | 6 |
| 10 → 1 → 10 | 20 | 5 |

## Development

```bash
./scripts/dev.sh              # Backend with hot reload
cd frontend && npm run dev    # Frontend dev server
python3 -m pytest backend/tests/ -v   # Run tests (190)
```

## Tech Stack

- **Backend:** Python 3.9, FastAPI, WebSockets
- **Frontend:** React 19, TypeScript, Vite
- **Desktop:** pywebview (optional)
- **AI:** Three difficulty levels (easy, medium, hard)
