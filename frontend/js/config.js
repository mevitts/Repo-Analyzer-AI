
export const CONFIG = {
    FRONTEND_API_KEY: '', // Replace with your actual API key
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:8888' 
        : 'https://repo-analyzer-ai-66124000276.us-east5.run.app',
    
    WS_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'ws://localhost:8888'
        : 'wss://repo-analyzer-ai-66124000276.us-east5.run.app',
    
    GITHUB_URL_PATTERN: /^https:\/\/github\.com\/[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+$/,
    MAX_URL_LENGTH: 200,
    
    ERROR_DISPLAY_DURATION: 5000,
    THINKING_LOG_MAX_HEIGHT: 300,
    
    DEBUG: true
};

export const debugLog = (message, data = null) => {
    if (CONFIG.DEBUG) {
        console.log(`[testing] ${message}`, data || '');
    }
}; 