import { debugLog } from './config.js';

export class UIService {
    constructor() {
        this.elements = {
            form: document.getElementById('analyze-form'),
            repoUrlInput: document.getElementById('repo-url'),
            analyzeBtn: document.getElementById('analyze-btn'),
            loading: document.getElementById('loading'),
            thinkingContainer: document.getElementById('thinking-container'),
            thinkingLog: document.getElementById('thinking-log'),
            resultsContainer: document.getElementById('results-container'),
            reportContent: document.getElementById('report-content')
        };
    }

    clearResults() {
        this.elements.thinkingLog.innerHTML = '';
        this.elements.reportContent.innerHTML = '';
        this.elements.thinkingContainer.classList.add('hidden');
        this.elements.resultsContainer.classList.add('hidden');
        debugLog('Results cleared');
    }

    showLoading() {
        this.elements.loading.classList.remove('hidden');
        this.elements.analyzeBtn.disabled = true;
        debugLog('Loading state shown');
    }

    hideLoading() {
        this.elements.loading.classList.add('hidden');
        this.elements.analyzeBtn.disabled = false;
        debugLog('Loading state hidden');
    }

    displayReport(markdownContent) {
        try {
            const htmlContent = marked.parse(markdownContent);
            this.elements.reportContent.innerHTML = htmlContent;
            this.elements.resultsContainer.classList.remove('hidden');
            debugLog('Report displayed successfully');
        } catch (error) {
            console.error('[testing] Error parsing markdown:', error);
            this.showError('Error displaying report');
        }
    }

    showError(message) {
        const existingErrors = document.querySelectorAll('.error');
        existingErrors.forEach(error => error.remove());
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = message;
        this.elements.form.parentNode.insertBefore(errorDiv, this.elements.form.nextSibling);
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
        debugLog('Error displayed:', message);
    }

    addThinkingLogEntry(message) {
        const entry = document.createElement('div');
        entry.className = 'thinking-log-entry';
        entry.textContent = message;
        this.elements.thinkingLog.appendChild(entry);
        this.elements.thinkingLog.scrollTop = this.elements.thinkingLog.scrollHeight;
        debugLog('Thinking log entry added:', message);
    }

    showThinkingContainer() {
        this.elements.thinkingContainer.classList.remove('hidden');
        debugLog('Thinking container shown');
    }

    getFormData() {
        const repoUrl = this.elements.repoUrlInput.value.trim();
        return { repoUrl };
    }

    setFormData(url) {
        this.elements.repoUrlInput.value = url;
    }
} 