import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import google.genai as genai
from src.backend.config import GOOGLE_API_KEY, CORS_ORIGINS
from src.backend.models import RepoInput
from src.backend.services import AnalysisService
from google.genai.types import Content, Part

genai.Client(api_key=GOOGLE_API_KEY)

app = FastAPI(title="Repository Analyzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analysis_service = AnalysisService()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    analysis_service.add_websocket_connection(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        analysis_service.remove_websocket_connection(session_id)

@app.post("/analyze")
async def analyze_repository(data: RepoInput):
    return await analysis_service.analyze_repository(data.owner, data.repo)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Repository Analyzer API is running"}

async def test_pipeline_locally():
    print("Starting Local Test Run")
    user_id = "local-test-user"
    session_id = f"session-{uuid.uuid4()}"
    initial_state_data = {
        "owner": "google",
        "repo": "generative-ai-python"
    }
    initial_message = Content(role="user", parts=[Part(text="Start analysis.")])
    await analysis_service.runner.session_service.create_session(
        app_name=analysis_service.runner.app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state_data
    )
    events = analysis_service.runner.run_async(
        user_id=user_id, session_id=session_id, new_message=initial_message
    )
    async for event in events:
        pass
    final_session = await analysis_service.runner.session_service.get_session(
        app_name=analysis_service.runner.app_name, user_id=user_id, session_id=session_id
    )
    if final_session and "analysis_results" in final_session.state:
        final_analysis = final_session.state["analysis_results"]
        print("\nLocal Test Succeeded: Final Report")
        print(str(final_analysis).strip().replace("```markdown", "").replace("```", "").strip())
    else:
        print("\nLocal Test Failed")
        print("Dumping final state for debugging:")
        print(final_session.state if final_session else "No session found.")

if __name__ == "__main__":
    asyncio.run(test_pipeline_locally()) 
