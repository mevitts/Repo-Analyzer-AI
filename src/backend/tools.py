import os
import requests
import base64
from google.adk.tools import ToolContext
from google.cloud import secretmanager

def get_secret(secret_id: str, project_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PROJECT_ID = "cedar-router-466020-s9"

try:
    github_token = get_secret("GITHUB_TOKEN", PROJECT_ID)
    google_api_key = get_secret("GOOGLE_API_KEY", PROJECT_ID)
    GITHUB_TOKEN = github_token
    print("Successfully accessed secrets from Google Cloud Secret Manager")
except Exception as e:
    print(f"Error accessing secrets: {e}")
    print("Falling back to environment variables...")


def list_files(repo: str, owner: str) -> dict:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1", headers=headers)
        response.raise_for_status()
        tree = response.json().get('tree', [])
        files = [item['path'] for item in tree if item['type'] == 'blob']
        return {"status": "success", "files": files}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_file_contents(repo: str, file_path: str, owner: str) -> dict:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}", headers=headers)
        response.raise_for_status()
        content = response.json().get('content', '')
        decoded_content = base64.b64decode(content).decode('utf-8')
        return {"status": "success", "content": decoded_content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def save_selected_files(files: list[str], tool_context: ToolContext) -> dict:
    tool_context.state["selected_files_list"] = files
    tool_context.state["all_file_contents"] = {}
    return {"status": "success", "files_saved": len(files)}

def fetch_all_content(tool_context: ToolContext) -> dict:
    try:
        owner = tool_context.state.get("owner")
        repo = tool_context.state.get("repo")
        files_to_read = tool_context.state.get("selected_files_list", [])
        if not owner or not repo:
            return {"status": "error", "message": "Owner or repo not found in state."}
        all_content = {}
        print(f"Tool: Fetching content for {len(files_to_read)} files...")
        for path in files_to_read:
            result = get_file_contents(repo=repo, file_path=path, owner=owner)
            all_content[path] = result.get("content", f"Error: {result.get('message')}")
        tool_context.state["all_file_contents"] = all_content
        print("Tool: Finished fetching all file contents.")
        return {"status": "success", "files_fetched": len(all_content)}
    except Exception as e:
        print(f"FATAL ERROR in fetch_all_content tool: {e}")
        return {"status": "error", "message": f"A fatal error occurred: {e}"}