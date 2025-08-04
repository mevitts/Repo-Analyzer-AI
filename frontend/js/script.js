const form = document.getElementById('analyze-form');
const repoUrlInput = document.getElementById('repo-url');
const analyzeBtn = document.getElementById('analyze-btn');
const loading = document.getElementById('loading');
const thinkingContainer = document.getElementById('thinking-container');
const thinkingLog = document.getElementById('thinking-log');
const resultsContainer = document.getElementById('results-container');
const reportContent = document.getElementById('report-content');

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8888' 
    : 'https://cedar-router-466020-s9.uc.r.appspot.com';
let websocket = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('[testing] Frontend initialized');
    form.addEventListener('submit', handleFormSubmit);
    repoUrlInput.addEventListener('input', validateGitHubUrl);
});

async function handleFormSubmit(event) {
    event.preventDefault();
    console.log('[testing] Form submitted');
    const repoUrl = repoUrlInput.value.trim();
    if (!isValidGitHubUrl(repoUrl)) {
        showError('Please enter a valid GitHub repository URL');
        return;
    }
    const { owner, repo } = parseGitHubUrl(repoUrl);
    if (!owner || !repo) {
        showError('Could not parse repository information from URL');
        return;
    }
    console.log('[testing] Parsed repository:', { owner, repo });
    clearResults();
    showLoading();
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ owner, repo })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('[testing] API response received:', data);
        hideLoading();
        if (data.report) {
            displayReport(data.report);
        } else {
            showError('No report data received from server');
        }
        if (data.session_id) {
            connectWebSocket(data.session_id);
        }
    } catch (error) {
        console.error('[testing] Error during analysis:', error);
        hideLoading();
        showError(`Analysis failed: ${error.message}`);
    }
}

function isValidGitHubUrl(url) {
    const githubUrlPattern = /^https:\/\/github\.com\/[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+$/;
    return githubUrlPattern.test(url) && url.length <= 200;
}

function parseGitHubUrl(url) {
    const match = url.match(/^https:\/\/github\.com\/([^\/]+)\/([^\/]+)$/);
    if (match) {
        return {
            owner: match[1],
            repo: match[2]
        };
    }
    return { owner: null, repo: null };
}

function validateGitHubUrl() {
    const url = repoUrlInput.value.trim();
    const isValid = isValidGitHubUrl(url);
    if (url && !isValid) {
        repoUrlInput.style.borderColor = '#dc2626';
    } else {
        repoUrlInput.style.borderColor = '#e5e7eb';
    }
}

function clearResults() {
    thinkingLog.innerHTML = '';
    reportContent.innerHTML = '';
    thinkingContainer.classList.add('hidden');
    resultsContainer.classList.add('hidden');
}

function showLoading() {
    loading.classList.remove('hidden');
    analyzeBtn.disabled = true;
}

function hideLoading() {
    loading.classList.add('hidden');
    analyzeBtn.disabled = false;
}

function displayReport(markdownContent) {
    try {
        const htmlContent = marked.parse(markdownContent);
        reportContent.innerHTML = htmlContent;
        resultsContainer.classList.remove('hidden');
        console.log('[testing] Report displayed successfully');
    } catch (error) {
        console.error('[testing] Error parsing markdown:', error);
        showError('Error displaying report');
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    form.parentNode.insertBefore(errorDiv, form.nextSibling);
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
    console.log('[testing] Error displayed:', message);
}

function addThinkingLogEntry(message) {
    const entry = document.createElement('div');
    entry.className = 'thinking-log-entry';
    entry.textContent = message;
    thinkingLog.appendChild(entry);
    thinkingLog.scrollTop = thinkingLog.scrollHeight;
}

function showThinkingContainer() {
    thinkingContainer.classList.remove('hidden');
}

function connectWebSocket(sessionId) {
    console.log('[testing] Connecting to WebSocket for session:', sessionId);
    const wsUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? `ws://localhost:8888/ws/${sessionId}`
        : `wss://cedar-router-466020-s9.uc.r.appspot.com/ws/${sessionId}`;
    websocket = new WebSocket(wsUrl);
    websocket.onopen = function(event) {
        console.log('[testing] WebSocket connected');
        showThinkingContainer();
        addThinkingLogEntry('Connected to analysis stream...');
    };
    websocket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('[testing] WebSocket message received:', data);
            if (data.type === 'agent_event') {
                const message = formatEventMessage(data);
                addThinkingLogEntry(message);
            }
        } catch (error) {
            console.error('[testing] Error parsing WebSocket message:', error);
        }
    };
    websocket.onerror = function(error) {
        console.error('[testing] WebSocket error:', error);
        addThinkingLogEntry('Connection error occurred');
    };
    websocket.onclose = function(event) {
        console.log('[testing] WebSocket closed');
        addThinkingLogEntry('Analysis stream ended');
    };
}

function formatEventMessage(eventData) {
    const agentName = eventData.agent_name || 'Unknown Agent';
    const eventType = eventData.event_type || 'Event';
    const message = eventData.message || '';
    return `${agentName}: ${eventType} - ${message}`;
} 