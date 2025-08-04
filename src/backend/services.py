import uuid
import json
from google.genai.types import Content, Part
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from src.backend.agents import root_agent

class AnalysisService:
    def __init__(self):
        self.runner = Runner(
            app_name="Repo_Analysis",
            session_service=InMemorySessionService(),
            agent=root_agent
        )
        self.active_connections = {}

    async def analyze_repository(self, owner: str, repo: str, session_id: str = None):
        if not session_id:
            session_id = f"session-{uuid.uuid4()}"
        user_id = "user"
        initial_state_data = {
            "owner": owner,
            "repo": repo
        }
        initial_message = Content(role="user", parts=[Part(text="Please start the analysis of the repository.")])
        await self.runner.session_service.create_session(
            app_name="Repo_Analysis",
            user_id=user_id,
            session_id=session_id,
            state=initial_state_data
        )
        final_analysis = "Error: Analysis could not be completed."
        try:
            events = self.runner.run_async(
                user_id=user_id, session_id=session_id, new_message=initial_message
            )
            websocket = self.active_connections.get(session_id)
            async for event in events:
                if websocket:
                    try:
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
            final_session = await self.runner.session_service.get_session(
                app_name=self.runner.app_name, user_id=user_id, session_id=session_id
            )
            if final_session and "analysis_results" in final_session.state:
                final_analysis = final_session.state["analysis_results"]
        except Exception as e:
            final_analysis = f"An error occurred during pipeline execution: {e}"
        return {
            "report": str(final_analysis).strip().replace("```markdown", "").replace("```", "").strip(),
            "session_id": session_id
        }

    def add_websocket_connection(self, session_id: str, websocket):
        self.active_connections[session_id] = websocket

    def remove_websocket_connection(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id] 