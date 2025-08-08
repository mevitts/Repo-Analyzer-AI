import { CONFIG, debugLog } from './config.js';

export class APIService {
    constructor() {
        this.websocket = null;
    }

    async analyzeRepository(owner, repo) {
        debugLog('Making API request:', { owner, repo });
        const response = await fetch(`${CONFIG.API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': import.meta.env.VITE_FRONTEND_API_KEY
            },
            body: JSON.stringify({ owner, repo })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        debugLog('API response received:', data);
        return data;
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