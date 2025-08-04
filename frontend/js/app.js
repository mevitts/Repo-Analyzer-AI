import { CONFIG, debugLog } from './config.js';
import { ValidationService } from './validation.js';
import { UIService } from './ui.js';
import { APIService } from './api.js';

export class RepositoryAnalyzerApp {
    constructor() {
        this.ui = new UIService();
        this.api = new APIService();
        this.initialize();
    }

    initialize() {
        debugLog('Frontend initialized');
        this.ui.elements.form.addEventListener('submit', this.handleFormSubmit.bind(this));
        this.ui.elements.repoUrlInput.addEventListener('input', this.handleInputValidation.bind(this));
        debugLog('Event listeners attached');
    }

    async handleFormSubmit(event) {
        event.preventDefault();
        debugLog('Form submitted');
        const { repoUrl } = this.ui.getFormData();
        if (!ValidationService.isValidGitHubUrl(repoUrl)) {
            this.ui.showError('Please enter a valid GitHub repository URL');
            return;
        }
        const { owner, repo } = ValidationService.parseGitHubUrl(repoUrl);
        if (!owner || !repo) {
            this.ui.showError('Could not parse repository information from URL');
            return;
        }
        debugLog('Parsed repository:', { owner, repo });
        this.ui.clearResults();
        this.ui.showLoading();
        try {
            const data = await this.api.analyzeRepository(owner, repo);
            this.ui.hideLoading();
            if (data.report) {
                this.ui.displayReport(data.report);
            } else {
                this.ui.showError('No report data received from server');
            }
            if (data.session_id) {
                this.connectWebSocket(data.session_id);
            }
        } catch (error) {
            console.error('[testing] Error during analysis:', error);
            this.ui.hideLoading();
            this.ui.showError(`Analysis failed: ${error.message}`);
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
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new RepositoryAnalyzerApp();
}); 