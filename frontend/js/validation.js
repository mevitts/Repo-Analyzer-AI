import { CONFIG, debugLog } from './config.js';

export class ValidationService {
    static isValidGitHubUrl(url) {
        return CONFIG.GITHUB_URL_PATTERN.test(url) && url.length <= CONFIG.MAX_URL_LENGTH;
    }

    static parseGitHubUrl(url) {
        const match = url.match(/^https:\/\/github\.com\/([^\/]+)\/([^\/]+)$/);
        if (match) {
            return {
                owner: match[1],
                repo: match[2]
            };
        }
        return { owner: null, repo: null };
    }

    static validateGitHubUrlInput(inputElement) {
        const url = inputElement.value.trim();
        const isValid = this.isValidGitHubUrl(url);
        if (url && !isValid) {
            inputElement.style.borderColor = '#dc2626';
            inputElement.style.boxShadow = '0 0 0 3px rgba(220, 38, 38, 0.1)';
        } else {
            inputElement.style.borderColor = '';
            inputElement.style.boxShadow = '';
        }
        debugLog('URL validation result:', { url, isValid });
        return isValid;
    }
} 