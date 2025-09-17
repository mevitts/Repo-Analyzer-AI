# Atlas

## Introduction

**Atlas** is a powerful tool designed to help developers quickly understand and navigate complex codebases. By leveraging cutting-edge AI technologies, this application provides a suite of features that go beyond traditional code analysis. From generating high-level summaries to visualizing code architecture in an **Atlas Viewer** and enabling semantic search, Atlas is your intelligent guide to any GitHub repository.

While the long-term vision for Atlas is to be a comprehensive onboarding tool, its current strengths lie in providing a unique, visual, and searchable perspective of a repository. Instead of spending days manually sifting through files, you can get a comprehensive overview in minutes.

**Note:** This project was developed as a prototype for the **Qdrant Hackathon**, which means the primary goal was to quickly build and demonstrate a functional proof-of-concept. As a result, some features are more mature than others.

---

## Core Features

* **Repository Ingestion:** Simply provide a GitHub URL, and the application will fetch, process, and analyze the entire repository, creating embeddings with the **Jina API**.
* **Interactive Code Atlas Viewer:** Visualize the entire codebase as an interactive graph. Nodes represent files and code chunks, while edges illustrate their relationships, helping you to identify clusters of functionality and critical components.
* **Semantic Search:** Go beyond simple keyword searches. You can use keywords and short phrases to find the most relevant code snippets, even if they don't contain the exact words you used.
* **Chunk-Level Atlas (Experimental):** Dive deep into the code by exploring individual code chunks and their relationships within a file in a dedicated Atlas Viewer.

---

## Architecture Overview

Atlas is built with a modern, decoupled architecture, consisting of a Python backend and a JavaScript frontend.

* **Backend:**
    * **Framework:** **FastAPI** provides a robust and efficient API for handling all backend operations.
    * **Code Analysis:** **ASTChunk** is used to intelligently parse code into meaningful chunks (functions, classes, etc.).
    * **Vector Database:** **Qdrant** stores vector embeddings of the code chunks, which is the foundation for our semantic search and analysis capabilities.
    * **AI Integration:** **Google's Gemini** models are used for code summarization and analysis, and the **Jina API** is used for creating embeddings.
* **Frontend:**
    * **Framework:** The user interface is a vanilla **JavaScript** application built with modern tooling, including **Vite** for a fast and efficient development experience.
    * **Visualization:** **Cytoscape.js** is used to render the interactive **Atlas Viewer**, providing a powerful and intuitive way to explore the repository's structure.
    * **API Communication:** The frontend communicates with the backend via a well-defined REST API.

---

## Current Status & Known Issues

This project is currently in a proof-of-concept stage and is under active development. While the core functionality is in place, there are some known limitations:

* **Summarization is a work in progress:** The AI-powered summarization feature is not yet fully functional. The current implementation struggles to generate consistently accurate and coherent summaries. This is a complex task that requires further refinement of the underlying language models and prompting strategies.
* **Chunk-level Atlas viewing is not perfect:** The ability to visualize and interact with individual code chunks in the Atlas Viewer is still experimental and is currently being fixed. While it can provide valuable insights, the connections and relationships between chunks are not always represented perfectly. Further work is needed to improve the accuracy and usability of this feature.
* **AST limitations:** The current implementation uses **ASTChunk**, which is powerful but has its limitations. Future versions could explore other static analysis tools or even dynamic analysis to provide a more comprehensive understanding of the code.

---

## What is it helpful for?

Despite the current limitations, Atlas is already a valuable tool for:

* **Rapidly understanding new codebases:** Get a high-level overview of a project's structure and key components in a fraction of the time it would take to do so manually.
* **Onboarding new developers:** Help new team members get up to speed quickly by providing them with an interactive map of the codebase via the Atlas Viewer.
* **Identifying code clusters and dependencies:** The Atlas Viewer makes it easy to see how different parts of the system are connected, which can be invaluable for refactoring and maintenance.
* **Discovering relevant code with semantic search:** Find code snippets related to a specific feature or functionality, even if you don't know the exact keywords to search for.

---

## Getting Started

### Prerequisites

* **Docker:** For running the Qdrant vector database.
* **Python 3.10+:** For the backend.
* **Node.js and npm:** For the frontend.

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/mevitts/repo-analyzer-ai.git](https://github.com/mevitts/repo-analyzer-ai.git)
    cd repo-analyzer-ai
    ```
2.  **Set up environment variables:**
    * Create a `.env` file in the root of the project and add the following:
        ```
        GITHUB_TOKEN=your_github_personal_access_token
        JINA_API_KEY=your_jina_api_key
        GOOGLE_API_KEY=your_google_api_key
        ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Start the Qdrant vector database:**
    ```bash
    docker run -p 6333:6333 qdrant/qdrant
    ```
5.  **Start the backend server:**
    ```bash
    uvicorn src.backend.api.main:app --reload
    ```

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install npm dependencies:**
    ```bash
    npm install
    ```
3.  **Start the frontend development server:**
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

---

## Future Work

* **Improve summarization quality:** This is the highest priority for future development. We will be experimenting with different language models, prompt engineering techniques, and fine-tuning to improve the accuracy and coherence of the generated summaries.
* **Enhance chunk-level Atlas viewing:** We plan to improve the accuracy of the chunk-level Atlas Viewer and add more features for exploring the relationships between code chunks.
* **Add support for more languages:** We will be adding support for other popular programming languages, such as Java, C#, and Go.
* **Integrate with IDEs:** We are exploring the possibility of creating plugins for popular IDEs like VS Code and JetBrains to bring the power of Atlas directly into your development workflow.
* **Improve performance:** We will be working to optimize the performance of the application, particularly for very large repositories.

I am excited about the future of Atlas and believe that it has the potential to revolutionize the way developers interact with and understand code. We welcome your feedback and contributions!