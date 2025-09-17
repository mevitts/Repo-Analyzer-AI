import { CONFIG, debugLog } from './config.js';
import { ValidationService } from './validation.js';
import { UIService } from './ui.js';
import { APIService } from './api.js';

let currentRepoId = null;

export class RepositoryAnalyzerApp {
    constructor() {
        this.ui = new UIService();
        this.api = new APIService();
        this.initialize();
    }

    initialize() {
        debugLog('Frontend initialized');
        const ingestBtn = document.getElementById('ingest-btn');
        const summarizeBtn = document.getElementById('summarize-btn');
        const atlasBtn = document.getElementById('atlas-btn');
        const searchBtn = document.getElementById('search-btn');
        const repoUrlInput = document.getElementById('repo-url');

        // Initial UI state
        this.ui.showInitialState();

        // Ingest button
        if (ingestBtn) {
            ingestBtn.addEventListener('click', async () => {
                ingestBtn.disabled = true;
                this.ui.showLoading();
                const { repoUrl } = this.ui.getFormData();
                if (!ValidationService.isValidGitHubUrl(repoUrl)) {
                    this.ui.showError('Please enter a valid GitHub repository URL');
                    ingestBtn.disabled = false;
                    this.ui.hideLoading();
                    return;
                }
                const { owner, repo } = ValidationService.parseGitHubUrl(repoUrl);
                try {
                    // Always load from GitHub and set file_contents in backend state
                    const loadResult = await this.api.loadRepo(owner, repo);
                    if (loadResult.status !== 'success') throw new Error(loadResult.message || 'Failed to load repo');
                    // Pass file_contents directly to ingest
                    const fileContents = loadResult.file_contents;
                    const ingestResult = await this.api.ingestRepo(repo, fileContents);
                    if (ingestResult.status !== 'success') throw new Error(ingestResult.message || 'Failed to ingest repo');
                    this.currentRepoId = repo;
                    this.ui.hideLoading();
                    this.ui.showPostIngestState();
                } catch (error) {
                    this.ui.hideLoading();
                    this.ui.showError(`Ingest failed: ${error.message}`);
                }
                ingestBtn.disabled = false;
            });
        }

        // Summarize button
        if (summarizeBtn) {
            summarizeBtn.addEventListener('click', async () => {
                summarizeBtn.disabled = true;
                this.ui.showLoading();
                try {
                    const { repoUrl } = this.ui.getFormData();
                    const { repo } = ValidationService.parseGitHubUrl(repoUrl);
                    const summaryResult = await this.api.summarizeRepo(repo);
                    this.ui.hideLoading();
                    if (!summaryResult.repo_summary) throw new Error('No summary returned');
                    this.ui.displaySummary(summaryResult.repo_summary);
                    this.ui.showSummaryView();
                } catch (error) {
                    this.ui.hideLoading();
                    this.ui.showError(`Summarize failed: ${error.message}`);
                }
                summarizeBtn.disabled = false;
            });
        }

        // Atlas button
        if (atlasBtn) {
            atlasBtn.addEventListener('click', async () => {
                atlasBtn.disabled = true;
                this.ui.showLoading();
                try {
                    const { repoUrl } = this.ui.getFormData();
                    const { repo } = ValidationService.parseGitHubUrl(repoUrl);
                    // Run clustering for atlas if needed
                    await this.api.atlasCluster(repo);
                    const atlasData = await this.api.getAtlasPack(repo);
                    this.ui.hideLoading();
                    this.ui.renderAtlas(atlasData.atlas_pack);
                    this.ui.showAtlasView();
                } catch (error) {
                    this.ui.hideLoading();
                    this.ui.showError(`Atlas failed: ${error.message}`);
                }
                atlasBtn.disabled = false;
            });
        }

        // Search button
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.ui.showSearchView();
            });
        }
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.handleSearch();
                }
            });
        }
        const searchRunBtn = document.getElementById('search-run-btn');
        if (searchRunBtn) {
            searchRunBtn.addEventListener('click', () => {
                this.handleSearch();
            });
        }

        debugLog('Event listeners attached');
    }

    // handleFormSubmit is no longer used in new flow

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

    async handleSearch() {
        const query = document.getElementById('search-input').value;
        if (!query || !this.repoId) return;

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

    handleInputValidation(event) {
        ValidationService.validateGitHubUrlInput(event.target);
    }

    connectWebSocket(sessionId) {
        this.api.connectWebSocket(
            sessionId,
            message => {
                this.ui.addThinkingLogEntry(message);
            },
            () => {
                this.ui.showThinkingContainer();
                this.ui.addThinkingLogEntry('Connected to analysis stream...');
            },
            error => {
                this.ui.addThinkingLogEntry('Connection error occurred');
            },
            () => {
                this.ui.addThinkingLogEntry('Analysis stream ended');
            }
        );
    }

    destroy() {
        this.api.closeWebSocket();
        debugLog('Application destroyed');
    }

    get repoId() {
        // Derive repoId from UI or state as needed
        const { repoUrl } = this.ui.getFormData();
        const parsed = ValidationService.parseGitHubUrl(repoUrl);
        return parsed && parsed.repo ? parsed.repo : null;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new RepositoryAnalyzerApp();
});

async function handleLoadRepo(owner, repo) {
    const result = await apiService.loadRepo(owner, repo);
    if (result.status === 'success') {
        currentRepoId = repo; // Store the repoId for later use
        // Enable ingest button, etc.
    }
}

async function handleIngest() {
    if (!currentRepoId) {
        uiService.showError('No repo loaded. Please load a repo first.');
        return;
    }
    await apiService.ingestRepo(currentRepoId);
}

document.getElementById('ingest-btn').addEventListener('click', async () => {
    showAtlasLoading('Ingesting repository...');
    await ingestRepository();
    showAtlasLoading('Ingestion complete. You may now render the Atlas.');
});

document.getElementById('render-atlas-btn').addEventListener('click', async () => {
    showAtlasLoading('Rendering Atlas...');
    await renderAtlasFromBackend();
    // Remove loading message after renderAtlas is done
    const loadingMsg = document.getElementById('atlas-loading-msg');
    if (loadingMsg) loadingMsg.remove();
});