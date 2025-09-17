import os
import requests
import base64
from typing import Optional, Set
import logging
#from google.adk.tools import ToolContext
#from google.cloud import secretmanager
from src.backend.utils.chunking_utils import chunk_repo
from src.backend.config import GITHUB_TOKEN, PROJECT_ID

import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

'''
def get_secret(secret_id: str, project_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

try:
    github_token = get_secret("GITHUB_TOKEN", PROJECT_ID)
    #google_api_key = get_secret("GOOGLE_API_KEY", PROJECT_ID)
    GITHUB_TOKEN = github_token
    #print("Successfully accessed secrets from Google Cloud Secret Manager")
except Exception as e:
    print(f"Error accessing secrets: {e}")
    print("Falling back to environment variables...")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
'''

#filters through
def list_files(repo: str, owner: str,
    exclude_folders: Optional[Set[str]] = None,
    exclude_extensions: Optional[Set[str]] = None,
    include_files: Optional[Set[str]] = None
) -> dict:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    if exclude_folders is None:
        exclude_folders = {'node_modules', '__pycache__', 'dist', 'build', 'out', 'target', 'vendor'}
    if exclude_extensions is None:
        exclude_extensions = {'.png', '.jpg', '.gif', '.ico', '.exe', '.dll', '.class', '.o', '.so'}
    if include_files is None:
        include_files = {'README.md', 'CONTRIBUTING.md', 'CHANGELOG.md',
                         'Dockerfile', 'docker-compose.yml', '.env',
                         'package.json', 'package-lock.json',
                         'requirements.txt', 'Pipfile', 'setup.py', 'pyproject.toml',
                         'pom.xml', 'build.gradle', 'Gemfile', 'Gemfile.lock',
                         'Cargo.toml'}

    logger.info(f"Successfully filtered files for repo {repo}")
    try:
        # Get default branch
        repo_resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
        repo_resp.raise_for_status()
        repo_info = repo_resp.json()
        default_branch = repo_info.get("default_branch", "main")

        response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1", headers=headers)
        response.raise_for_status()
        logger.info(f"Successfully fetched file tree for repo {repo}")

        tree = response.json().get('tree', [])
        files = [item['path'] for item in tree if item['type'] == 'blob']
        logger.info(f"Successfully extracted {len(files)} files from repo {repo}")

        context_files = {item['path'] for item in tree if item['path'] in include_files}
        files = [file for file in files if not any(folder in file.split('/') for folder in exclude_folders)]

        logger.info(f"Successfully filtered files for repo {repo}")
        return {"status": "success", "files": files}
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
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

'''
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
'''
