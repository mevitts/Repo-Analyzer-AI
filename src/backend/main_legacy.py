import os
import uuid
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from agents import root_agent
import google.genai as genai

load_dotenv()

# Try to get API key from Secret Manager first, fallback to environment variable
try:
    from tools import get_secret
    PROJECT_ID = "cedar-router-466020-s9"
    GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY", PROJECT_ID)
    print("Using Google API key from Secret Manager")
except Exception as e:
    print(f"Could not access Secret Manager: {e}")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in .env file or Secret Manager.")

genai.Client(api_key=GOOGLE_API_KEY)


class RepoInput(BaseModel):
    owner: str
    repo: str
    
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:5500", 
        "http://127.0.0.1:5500",
        "https://cedar-router-466020-s9.uc.r.appspot.com",  # Update with your actual deployed URL
        "https://cedar-router-466020-s9.web.app",  # Firebase hosting URL if using Firebase
        "https://cedar-router-466020-s9.firebaseapp.com"  # Alternative Firebase URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections = {}

runner = Runner(
    app_name="Repo_Analysis",
    session_service=InMemorySessionService(),
    agent=root_agent
)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        if session_id in active_connections:
            del active_connections[session_id]

@app.post("/analyze")
async def analyze_repository(data: RepoInput):
    user_id = "user"
    session_id = f"session-{uuid.uuid4()}"
    
    initial_state_data = {
        "owner": data.owner,
        "repo": data.repo
    }

    initial_message = Content(role="user", parts=[Part(text="Please start the analysis of the repository.")])

    await runner.session_service.create_session(
        app_name="Repo_Analysis", 
        user_id=user_id, 
        session_id=session_id, 
        state=initial_state_data
    )
    
    final_analysis = "Error: Analysis could not be completed."
    
    try:
        events = runner.run_async(
            user_id=user_id, session_id=session_id, new_message=initial_message
        )
        
        # Stream events to WebSocket if connection exists
        websocket = active_connections.get(session_id)
        
        async for event in events:
            if websocket:
                try:
                    # Extract relevant information from the event
                    event_data = {
                        "type": "agent_event",
                        "timestamp": str(event.timestamp) if hasattr(event, 'timestamp') else None,
                        "agent_name": getattr(event, 'agent_name', 'Unknown'),
                        "event_type": type(event).__name__,
                        "message": str(event)
                    }
                    await websocket.send_text(json.dumps(event_data))
                except Exception as e:
                    print(f"[testing] WebSocket send error: {e}")
        
        final_session = await runner.session_service.get_session(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )

        if final_session and "analysis_results" in final_session.state:
            final_analysis = final_session.state["analysis_results"]

    except Exception as e:
        final_analysis = f"An error occurred during pipeline execution: {e}"

    return {"report": str(final_analysis).strip().replace("```markdown", "").replace("```", "").strip(), "session_id": session_id}


async def test_pipeline_locally():
    """A simple function to run the agent pipeline locally for testing."""
    print("--- Starting Local Test Run ---")
    
    # Use the same setup as your API endpoint
    user_id = "local-test-user"
    session_id = f"session-{uuid.uuid4()}"
    
    # Hardcode your test repository here
    initial_state_data = {
        "owner": "google",
        "repo": "generative-ai-python"
    }

    initial_message = Content(role="user", parts=[Part(text="Start analysis.")])

    # Create a session for the test run
    await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state_data
    )
    
    # Run the pipeline and get the final result
    events = runner.run_async(
        user_id=user_id, session_id=session_id, new_message=initial_message
    )
    async for event in events:
        pass # Let the pipeline run to completion

    final_session = await runner.session_service.get_session(
        app_name=runner.app_name, user_id=user_id, session_id=session_id
    )

    if final_session and "analysis_results" in final_session.state:
        final_analysis = final_session.state["analysis_results"]
        print("\n Local Test Succeeded: Final Report")
        print(str(final_analysis).strip().replace("```markdown", "").replace("```", "").strip())
    else:
        print("\n Local Test Failed")
        print("Dumping final state for debugging:")
        print(final_session.state if final_session else "No session found.")

if __name__ == "__main__":
    asyncio.run(test_pipeline_locally())