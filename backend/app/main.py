from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import rest, websocket
from backend.app.game_manager import GameManager

app = FastAPI(title="Judgement Card Game", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared game manager instance
game_manager = GameManager()
rest.set_manager(game_manager)
websocket.set_manager(game_manager)

app.include_router(rest.router)
app.include_router(rest.lobby_router)
app.include_router(websocket.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
