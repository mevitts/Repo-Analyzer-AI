Repo Navigator: A Step-by-Step Frontend Development GuideThis document outlines the phased development plan for the Repo Navigator frontend. The backend is considered stable and provides all necessary endpoints. The goal is to rapidly refactor the existing frontend foundation and build a feature-complete Minimum Viable Product (MVP) suitable for a hackathon demo.Target Audience: Human developers and AI development agents.Guiding Principles:Incremental Builds: Each phase results in a testable, demonstrable feature.Speed & Impact: Prioritize features that deliver the most value and "wow" factor quickly.Refactor, Don't Rebuild: The existing frontend structure is solid. We will modify it, not discard it.Phase 0: Foundation & Backend AlignmentGoal: Synchronize the existing frontend code with the finalized backend API and prepare the HTML structure for all planned features.

Step 0.1: Refactor the API Service (frontend/js/api.js)Task: Update the APIService class to include methods for each required backend endpoint. The previous analyzeRepository method is now obsolete and should be replaced by a series of more granular calls.File to Modify: frontend/js/api.jsReasoning: This alignment is critical. It ensures that the frontend speaks the same language as the backend. By creating a dedicated method for each API call, we keep our code clean, modular, and easy to debug.Implementation:Replace the contents of the APIService class with the following:import { CONFIG, debugLog } from './config.js';

export class APIService {
    constructor() {
        this.websocket = null;
    }

    async loadRepo(owner, repo) {
        debugLog('API Call: loadRepo', { owner, repo });
        const response = await fetch(`${CONFIG.API_BASE_URL}/load_repo?repo_id=${repo}&owner=${owner}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`Failed to load repo: ${response.statusText}`);
        return await response.json();
    }

    async ingestRepo() {
        debugLog('API Call: ingestRepo');
        const response = await fetch(`${CONFIG.API_BASE_URL}/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`Failed to ingest repo: ${response.statusText}`);
        return await response.json();
    }

    async summarizeRepo(repoId) {
        debugLog('API Call: summarizeRepo', { repoId });
        const response = await fetch(`${CONFIG.API_BASE_URL}/summarize_repo?repo_id=${repoId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`Failed to summarize repo: ${response.statusText}`);
        return await response.json();
    }

    async getAtlasPack(repoId) {
        debugLog('API Call: getAtlasPack', { repoId });
        const response = await fetch(`${CONFIG.API_BASE_URL}/atlas_pack?repo_id=${repoId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`Failed to get atlas pack: ${response.statusText}`);
        return await response.json();
    }

    async search(query, repoId) {
        debugLog('API Call: search', { query, repoId });
        const response = await fetch(`${CONFIG.API_BASE_URL}/search?query=${encodeURIComponent(query)}&repo_id=${repoId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`Search failed: ${response.statusText}`);
        return await response.json();
    }

    // ... (Your existing WebSocket methods can remain here) ...
}
Step 0.2: Update the HTML Structure (frontend/index.html)Task: Add placeholder containers for the new UI views (Atlas and Search). These will be hidden by default and shown programmatically.File to Modify: frontend/index.htmlReasoning: Preparing the DOM structure now makes it easier to manage UI states later. We can simply toggle the visibility of these containers as the user navigates the app.Implementation:Add the atlas-container and search-container divs inside the main container. Also, add a button for the Atlas view and a dedicated thinking-log for progress updates.<!DOCTYPE html>
<html lang="en">
<head>
    <!-- ... your head content ... -->
    <title>Repo Navigator</title>
    <link rel="stylesheet" href="style.css">
    <!-- Add Cytoscape.js for Phase 2 -->
    <script src="[https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js](https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js)"></script>
</head>    
<body>
    <div class="container">
        <header>
            <h1>Repo Navigator</h1>
            <p>Generate summaries, visualize codebases, and perform semantic search.</p>
        </header>
        
        <form id="analyze-form">
            <!-- ... your input group ... -->
        </form>

        <div id="loading" class="loading hidden">
            <div class="spinner"></div>
            <div id="thinking-log" class="thinking-log-entry"></div>
        </div>

        <!-- Summary View -->
        <div id="results-container" class="results-container hidden">
            <h3>Analysis Report</h3>
            <div id="report-content"></div>
            <button id="view-atlas-btn" class="hidden">View Atlas</button>
        </div>

        <!-- Atlas View -->
        <div id="atlas-container" class="atlas-container hidden">
            <h3>Repository Atlas</h3>
            <div id="atlas-graph" style="width: 100%; height: 500px; border: 1px solid var(--border-color); border-radius: 12px;"></div>
            <div id="atlas-sidebar"></div>
        </div>

        <!-- Search View -->
        <div id="search-container" class="search-container hidden">
             <h3>Semantic Search</h3>
             <input type="text" id="search-input" placeholder="Search for code logic, e.g., 'user authentication logic'">
             <div id="search-results"></div>
        </div>
    </div>

    <script src="[https://cdn.jsdelivr.net/npm/marked/marked.min.js](https://cdn.jsdelivr.net/npm/marked/marked.min.js)"></script>
    <script type="module" src="js/app.js"></script>
</body>
</html> 
Phase 1: Implement the Core Feature - Repo SummaryGoal: Enable the primary user workflow: enter a GitHub URL and receive a generated repository summary.Step 1.1: Implement the Chained API Workflow (frontend/js/app.js)Task: Modify the handleFormSubmit function to orchestrate the new, multi-step analysis process (Load -> Ingest -> Summarize).File to Modify: frontend/js/app.jsReasoning: The analysis is a sequence of dependent steps. Chaining the calls with await ensures they execute in the correct order. Providing real-time feedback via the thinking log dramatically improves the user experience during this potentially long-running process.Implementation:// In frontend/js/app.js, inside the RepositoryAnalyzerApp class

async handleFormSubmit(event) {
    event.preventDefault();
    debugLog('Form submitted');
    const { repoUrl } = this.ui.getFormData();
    
    if (!ValidationService.isValidGitHubUrl(repoUrl)) {
        this.ui.showError('Please enter a valid GitHub repository URL');
        return;
    }
    const { owner, repo } = ValidationService.parseGitHubUrl(repoUrl);
    this.repoId = repo; // Store repoId for later use

    this.ui.clearResults();
    this.ui.showLoading();

    try {
        this.ui.updateThinkingLog('Step 1/3: Loading repository files...');
        await this.api.loadRepo(owner, repo);

        this.ui.updateThinkingLog('Step 2/3: Ingesting and embedding code...');
        await this.api.ingestRepo();

        this.ui.updateThinkingLog('Step 3/3: Generating summary...');
        const summaryData = await this.api.summarizeRepo(repo);
        
        this.ui.hideLoading();
        this.ui.displaySummary(summaryData);

    } catch (error) {
        console.error('Error during analysis:', error);
        this.ui.hideLoading();
        this.ui.showError(`Analysis failed: ${error.message}`);
    }
}
Step 1.2: Implement the Summary Display (frontend/js/ui.js)Task: Create a new function, displaySummary, in the UIService to dynamically generate and inject the summary HTML into the DOM.File to Modify: frontend/js/ui.jsReasoning: Separating UI manipulation into the UIService keeps the main application logic in app.js clean. This function is responsible for translating the JSON data from the API into a human-readable format.Implementation:// In frontend/js/ui.js, inside the UIService class

updateThinkingLog(message) {
    // This is a new helper for the loading indicator
    this.elements.thinkingLog.textContent = message;
}

displaySummary(summaryData) {
    debugLog('Displaying summary', summaryData);
    const { repo_summary, clusters } = summaryData;
    
    let htmlContent = `<h2>${repo_summary.title || 'Repository Overview'}</h2>`;
    htmlContent += marked.parse(repo_summary.overview || 'No overview available.');

    htmlContent += '<h3>Code Clusters Identified:</h3><ul>';
    clusters.forEach(cluster => {
        htmlContent += `<li><strong>${cluster.title}:</strong> ${cluster.summary}</li>`;
    });
    htmlContent += '</ul>';

    this.elements.reportContent.innerHTML = htmlContent;
    this.elements.resultsContainer.classList.remove('hidden');
    document.getElementById('view-atlas-btn').classList.remove('hidden'); // Show button to enter Phase 2
    document.getElementById('search-container').classList.remove('hidden'); // Show search bar for Phase 3
}
Checkpoint 1: The application is now functional. A user can enter a URL, see a multi-step progress indicator, and receive a full repository summary.

Phase 2: Implement the "Wow" Factor - The Atlas VisualizationGoal: Create a memorable and interactive graph visualization of the repository's code structure.Step 2.1: Implement the Atlas View Logic (app.js & ui.js)Task: Add the logic to fetch the Atlas data and render it using Cytoscape.js.Files to Modify: frontend/js/app.js, frontend/js/ui.jsReasoning: This feature provides a powerful, non-linear way to explore the codebase. Cytoscape.js is chosen for its balance of power and ease of use, making it ideal for a hackathon. The click-to-inspect functionality is key to making the graph useful, not just decorative.Implementation:In frontend/js/app.js, add the event listener and handler:// In RepositoryAnalyzerApp class in app.js

initialize() {
    // ... existing listeners ...
    document.getElementById('view-atlas-btn').addEventListener('click', this.handleViewAtlas.bind(this));
}

async handleViewAtlas() {
    this.ui.updateThinkingLog('Building repository atlas...');
    this.ui.showLoading();
    try {
        const atlasData = await this.api.getAtlasPack(this.repoId);
        this.ui.hideLoading();
        this.ui.renderAtlas(atlasData.atlas_pack);
    } catch (error) {
        this.ui.hideLoading();
        this.ui.showError(`Could not build Atlas: ${error.message}`);
    }
}
In frontend/js/ui.js, create the renderAtlas function:// In UIService class in ui.js

renderAtlas(atlasPack) {
    this.elements.resultsContainer.classList.add('hidden'); // Hide summary view
    this.elements.atlasContainer.classList.remove('hidden'); // Show atlas view

    const cy = cytoscape({
        container: document.getElementById('atlas-graph'),
        elements: atlasPack,
        layout: { name: 'cose' },
        style: [
            { selector: 'node', style: { 'background-color': '#00ff88', 'label': 'data(label)' } },
            { selector: 'edge', style: { 'width': 1, 'line-color': '#333333', 'curve-style': 'bezier' } }
        ]
    });

    cy.on('tap', 'node', (evt) => {
        const nodeData = evt.target.data();
        this.elements.atlasSidebar.innerHTML = `
            <h4>${nodeData.label}</h4>
            <p><strong>File:</strong> ${nodeData.filepath}</p>
            <p><strong>Cluster ID:</strong> ${nodeData.cluster_id}</p>
            <p><strong>Score (Distance):</strong> ${nodeData.score.toFixed(4)}</p>
        `;
    });
}
Phase 3: Implement the Utility - Semantic SearchGoal: Add a practical, powerful search feature that allows users to find relevant code snippets using natural language queries.Step 3.1: Implement Search UI and Logic (app.js & ui.js)Task: Hook up the search input to the /search API endpoint and render the results.Files to Modify: frontend/js/app.js, frontend/js/ui.jsReasoning: This feature directly showcases the power of the vector embeddings stored in Qdrant. It moves beyond simple keyword search to true semantic understanding, which is a key differentiator.Implementation:In frontend/js/app.js, add the event listener and handler:// In RepositoryAnalyzerApp class in app.js

initialize() {
    // ... existing listeners ...
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            this.handleSearch();
        }
    });
}

async handleSearch() {
    const query = document.getElementById('search-input').value;
    if (!query || !this.repoId) return;

    this.ui.updateThinkingLog(`Searching for "${query}"...`);
    this.ui.showLoading();

    try {
        const searchData = await this.api.search(query, this.repoId);
        this.ui.hideLoading();
        this.ui.displaySearchResults(searchData.results);
    } catch (error) {
        this.ui.hideLoading();
        this.ui.showError(`Search failed: ${error.message}`);
    }
}
In frontend/js/ui.js, create the displaySearchResults function:// In UIService class in ui.js

displaySearchResults(results) {
    const resultsContainer = this.elements.searchResults;
    resultsContainer.innerHTML = ''; // Clear previous results

    if (!results || results.points.length === 0) {
        resultsContainer.innerHTML = '<p>No results found.</p>';
        return;
    }

    let htmlContent = '<ul>';
    results.points.forEach(point => {
        htmlContent += `
            <li>
                <strong>File:</strong> ${point.payload.filepath} (Score: ${point.score.toFixed(4)})
                <pre><code>${point.payload.excerpt || 'No excerpt available.'}</code></pre>
            </li>
        `;
    });
    htmlContent += '</ul>';
    resultsContainer.innerHTML = htmlContent;
}
Phase 4: Polish & DeployGoal: Refine the user experience and prepare the application for demonstration.Tasks:Refine User Flow: Add buttons to switch between the Summary, Atlas, and Search views easily. Ensure a consistent state.Styling: Apply styles from style.css to the new Atlas and Search containers to ensure a cohesive look and feel.Error Handling: Double-check that all try...catch blocks provide clear, user-friendly error messages via ui.showError().Deployment: Follow the instructions for your chosen platform (Firebase Hosting or Google App Engine). Since you are using Vite, run npm run build in the frontend directory to generate the static files in the dist folder, which you will then deploy.
