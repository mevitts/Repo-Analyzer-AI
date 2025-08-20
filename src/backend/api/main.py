from fastapi import FastAPI
from src.backend.qdrant_client import get_qdrant_client
from src.backend.api.routes import router

app = FastAPI()
app.state.qdrant = get_qdrant_client()
app.include_router(router)