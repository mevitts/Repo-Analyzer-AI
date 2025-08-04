## Repo Analyzer AI
A multi-agent AI pipeline built with Google's ADK that performs a comprehensive, architectural analysis of a software repository.

## About The Project
This project creates a system of multiple AI agents to provide a holistic understanding of the given GitHub repository. These agents select key files, fetch their content, and syntehsize their understanding of into a detailed report suitable for developers and technical leaders.

The application is built as a web service using FastAPI and is deployed as a scalable, serverless container on Google Cloud Run.

**Core Features**
- **Intelligent File Selection:** An file selection agent is given the repository's `README.md` file to grasp an understanding of the overall functionality, then chooses what it believes to be the most relevant files.

- **Automated Content Fetching:** A dedicated agent uses the GitHub API to extract the content from each of the selected files.

- **Holistic Code Synthesis:** A final, expert agent analyzes the complete context of all fetched files to generate a comprehensive markdown report covering:
-   Overall Summary
-   Technology Stack & Dependencies
-   Architecture & Data Flow 
-   Code Quality & Potential Improvements

- **Cloud-Native API:** The entire pipeline is exposed via a secure, scalable REST API deployed on Google Cloud Run.

## How to Use the Deployed API

**Endpoint**: `POST https://repo-analyzer-service-66124000276.us-central1.run.app/analyze`

**Example Body**:

```
JSON

{
    "owner": "github_username",
    "repo": "repository_name"
}
```

**Example `curl` Command:**
```
Bash

curl -X POST  https://repo-analyzer-service-66124000276.us-central1.run.app/analyze \
-H "Content-Type: application/json" \
-d '{
    "owner": "google",
    "repo": "generative-ai-python"
}'
```

## Local Development Setup
To run and test the project on your local machine, follow these steps.

**1. Clone the repository**
```
Bash

git clone https://github.com/mevitts/Repo-Analyzer-AI.git
cd Repo-Analyzer-AI
```

**2. Create and activate a virtual environment**
```
Bash

python -m venv .venv
source .venv/bin/activate  # On Windows, use: .\.venv\Scripts\activate
```

**3. Install dependencies**
```
Bash

pip install -r requirements.txt
```

**4. Create your environment file**

- Create a file named` .env` in the root of the project.
- Add your secret keys to this file:

```
Code snippet

GOOGLE_API_KEY="your_google_api_key_here"
GITHUB_TOKEN="your_github_personal_access_token_here"
```

**5. Run the local server**
```
Bash

uvicorn main:app --reload
```


## Future Roadmap

**1. Simple Web Frontend**
The highest priority next step is to build a user-friendly web interface, at its most basica level consisting of a form where users can input a repository owner and name. The page will then call the deployed API and render the returned markdown report for easy viewing.

**2. Repository Comparison Agent**
A major feature extension will be the ability to compare two repositories. For example, if a user is looking to compare their project to its inspiration or analyze how their project might have diverged from a similar one, this agent will generates a report highlighting the key differences in architecture, dependencies, and logic rather than just a line by line comparison.

**3. Repository Health Score**
Another idea is to add a scoring agent to the pipeline to give a grade for the repository. This agent will evaluate the repo against a defined grading scale (e.g., presence of a Dockerfile, test coverage, dependency freshness, coherency) to generate an overall for the repository.

**4. Interactive RAG Q&A**
The most advanced evolution of this project is to turn it into an interactive Q&A bot. This involves a shift to a Retrieval-Augmented Generation (RAG) architecture:
This would be useful to help users get specific knowledge about the repository (e.g., "How is authentication handled?"). The system will retrieve the most relevant code chunks from the database and use an LLM to generate a precise, context-aware answer.
