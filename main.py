<<<<<<< HEAD
from src.backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888) 
    
=======
import os
import uuid
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from agents import root_agent
import google.genai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")
genai.Client(api_key=GOOGLE_API_KEY)

if not os.getenv("GITHUB_TOKEN"):
    raise ValueError("GITHUB_TOKEN not found in .env file.")


class RepoInput(BaseModel):
    owner: str
    repo: str
    
app = FastAPI()

runner = Runner(
    app_name="Repo_Analysis",
    session_service=InMemorySessionService(),
    agent=root_agent
)

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
        async for event in events:
            pass
        
        final_session = await runner.session_service.get_session(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )

        if final_session and "analysis_results" in final_session.state:
            final_analysis = final_session.state["analysis_results"]

    except Exception as e:
        final_analysis = f"An error occurred during pipeline execution: {e}"

    return {"report": str(final_analysis).strip().replace("```markdown", "").replace("```", "").strip()}


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
        print("\n--- ✅ Local Test Succeeded: Final Report ---")
        print(str(final_analysis).strip().replace("```markdown", "").replace("```", "").strip())
    else:
        print("\n--- ❌ Local Test Failed ---")
        print("Dumping final state for debugging:")
        print(final_session.state if final_session else "No session found.")

if __name__ == "__main__":
    asyncio.run(test_pipeline_locally())
>>>>>>> 89f974fa8c9c5ebca981103561fb77154912bc04
