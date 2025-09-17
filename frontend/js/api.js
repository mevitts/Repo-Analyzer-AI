import { CONFIG, debugLog } from './config.js';

export class APIService {
    constructor() {
        this.websocket = null;
    }

    async listCollections() {
        // Calls the backend /collections endpoint
        const response = await fetch(`${CONFIG.API_BASE_URL}/collections`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`Failed to list collections: ${response.statusText}`);
        return await response.json();
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

        async ingestRepo(repoId, fileContents = null) {
            debugLog('API Call: ingestRepo', { repoId });
            const body = fileContents
                ? JSON.stringify({ repo_id: repoId, file_contents: fileContents })
                : JSON.stringify({ repo_id: repoId });
            const response = await fetch(`${CONFIG.API_BASE_URL}/ingest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body
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

        async atlasCluster(repoId) {
        debugLog('API Call: atlasCluster', { repoId });
        const response = await fetch(`${CONFIG.API_BASE_URL}/atlas_cluster?repo_id=${encodeURIComponent(repoId)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error('Failed to cluster for atlas');
        return await response.json();
        }

    connectWebSocket(sessionId, onMessage, onOpen, onError, onClose) {
        debugLog('Connecting to WebSocket for session:', sessionId);
        const wsUrl = `${CONFIG.WS_BASE_URL}/ws/${sessionId}`;
        this.websocket = new WebSocket(wsUrl);
        this.websocket.onopen = event => {
            debugLog('WebSocket connected');
            if (onOpen) onOpen(event);
        };
        this.websocket.onmessage = event => {
            try {
                const data = JSON.parse(event.data);
                debugLog('WebSocket message received:', data);
                if (data.type === 'agent_event') {
                    const message = this.formatEventMessage(data);
                    if (onMessage) onMessage(message);
                }
            } catch (error) {
                console.error('[testing] Error parsing WebSocket message:', error);
            }
        };
        this.websocket.onerror = error => {
            console.error('[testing] WebSocket error:', error);
            if (onError) onError(error);
        };
        this.websocket.onclose = event => {
            debugLog('WebSocket closed');
            if (onClose) onClose(event);
        };
    }

    formatEventMessage(eventData) {
        const agentName = eventData.agent_name || 'Unknown Agent';
        const eventType = eventData.event_type || 'Event';
        const message = eventData.message || '';
        return `${agentName}: ${eventType} - ${message}`;
    }

    closeWebSocket() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
            debugLog('WebSocket connection closed');
        }
    }

    isWebSocketConnected() {
        return this.websocket && this.websocket.readyState === WebSocket.OPEN;
    }
}