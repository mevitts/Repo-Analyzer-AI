import { debugLog } from './config.js';

export class UIService {
    constructor() {
        this.elements = {
            form: document.getElementById('analyze-form'),
            repoUrlInput: document.getElementById('repo-url'),
            ingestBtn: document.getElementById('ingest-btn'),
            summarizeBtn: document.getElementById('summarize-btn'),
            atlasBtn: document.getElementById('atlas-btn'),
            searchBtn: document.getElementById('search-btn'),
            loading: document.getElementById('loading'),
            thinkingContainer: document.getElementById('thinking-container'),
            thinkingLog: document.getElementById('thinking-log'),
            resultsContainer: document.getElementById('results-container'),
            reportContent: document.getElementById('report-content'),
            viewAtlasBtn: document.getElementById('view-atlas-btn'),
            atlasContainer: document.getElementById('atlas-container'),
            atlasSidebar: document.getElementById('atlas-sidebar'),
            searchContainer: document.getElementById('search-container'),
            searchInput: document.getElementById('search-input'),
            searchResults: document.getElementById('search-results'),
        };
    }

    // UI state management for main flow
    showInitialState() {
        this.hideAllViews();
        this.elements.ingestBtn.classList.remove('hidden');
        this.elements.summarizeBtn.classList.add('hidden');
        this.elements.atlasBtn.classList.add('hidden');
        this.elements.searchBtn.classList.add('hidden');
    }

    showPostIngestState() {
        this.hideAllViews();
        this.elements.ingestBtn.classList.add('hidden');
        this.elements.summarizeBtn.classList.remove('hidden');
        this.elements.atlasBtn.classList.remove('hidden');
        this.elements.searchBtn.classList.remove('hidden');
    }

    showSummaryView() {
        this.hideAllViews();
        this.elements.resultsContainer.classList.remove('hidden');
    }

    showAtlasView() {
        this.hideAllViews();
        this.elements.atlasContainer.classList.remove('hidden');
    }

    showSearchView() {
        this.hideAllViews();
        this.elements.searchContainer.classList.remove('hidden');
    }

    hideAllViews() {
        this.elements.resultsContainer.classList.add('hidden');
        this.elements.atlasContainer.classList.add('hidden');
        this.elements.searchContainer.classList.add('hidden');
    }

    clearResults() {
    if (this.elements.thinkingLog) this.elements.thinkingLog.innerHTML = '';
    if (this.elements.reportContent) this.elements.reportContent.innerHTML = '';
    if (this.elements.thinkingContainer) this.elements.thinkingContainer.classList.add('hidden');
    if (this.elements.resultsContainer) this.elements.resultsContainer.classList.add('hidden');
    debugLog('Results cleared');
    }

    showLoading() {
        this.elements.loading.classList.remove('hidden');
        if (this.elements.ingestBtn) this.elements.ingestBtn.disabled = true;
        debugLog('Loading state shown');
    }

    hideLoading() {
        this.elements.loading.classList.add('hidden');
        if (this.elements.ingestBtn) this.elements.ingestBtn.disabled = false;
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

    displaySummary(repoSummary) {
        const { title, overview, sections } = repoSummary;
        let html = `<h2>${title}</h2>`;
        html += `<p>${overview}</p>`;
        if (sections && sections.length) {
            html += '<ul>';
            sections.forEach(sec => {
                html += `<li><strong>${sec.title}:</strong> ${sec.summary}</li>`;
            });
            html += '</ul>';
        }
        this.elements.reportContent.innerHTML = html;
        this.elements.resultsContainer.classList.remove('hidden');
        this.showViewAtlasButton();
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

    showViewAtlasButton() {
        const btn = document.getElementById('view-atlas-btn');
        if (btn) btn.classList.remove('hidden');
    }

    renderAtlas(atlasPack) {
        this.showAtlasView();
        const elements = [];
        const clusterColors = {};
        let colorIdx = 0;
        const palette = [
            '#00ff88', '#3a6ea5', '#c1440e', '#c2b280', '#e2d9c3', '#f5ecd7', '#c2b280', '#c1440e'
        ];
        const edgeSet = new Set();
        if (atlasPack.nodes) {
            for (const node of atlasPack.nodes) {
                let color = '#00ff88';
                if (node.cluster_id !== undefined && node.cluster_id !== null) {
                    if (!clusterColors[node.cluster_id]) {
                        clusterColors[node.cluster_id] = palette[colorIdx % palette.length];
                        colorIdx++;
                    }
                    color = clusterColors[node.cluster_id];
                }
                elements.push({
                    data: {
                        id: node.id,
                        label: node.label,
                        filepath: node.filepath,
                        cluster_id: node.cluster_id,
                        score: node.score,
                        excerpt: node.excerpt
                    },
                    classes: `cluster-${node.cluster_id}`,
                    style: { 'background-color': color }
                });
            }
        }
        if (atlasPack.edges) {
            for (const edge of atlasPack.edges) {
            const key = [edge.source, edge.target].sort().join('--');
                    if (!edgeSet.has(key)) {
                        elements.push({ data: edge });
                        edgeSet.add(key);
                    }
        }
    }
    console.log('[Atlas Debug] Nodes:', atlasPack.nodes.length, 'Edges:', atlasPack.edges.length);

        const cy = cytoscape({
            container: document.getElementById('atlas-graph'),
            elements,
            layout: { 
                name: 'cose', 
                animate: true, 
                fit: true,
                padding: 30,
                idealEdgeLength: edge => 100 * (1 - edge.data('weight')),
                edgeElasticity: edge => 100 * (1 - edge.data('weight')), 
                nodeRepulsion: 400000,
                numIter: 1000
            },
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': 'data(background-color)',
                        'label': 'data(label)',
                        'width': 24,
                        'height': 24,
                        'font-size': 10
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 'mapData(weight, 0.8, 1.0, 1, 8)',
                        'line-color': '#333333',
                        'curve-style': 'bezier'
                    }
                }
            ],
            userPanningEnabled: true,
            userZoomingEnabled: true,
            boxSelectionEnabled: false,
            autoungrabify: true,
        });

        cy.on('tap', 'node', (evt) => {
            const nodeData = evt.target.data();
            console.log('[Atlas Debug] Node clicked:', nodeData);
            this.elements.atlasSidebar.innerHTML = `
                <h4>${nodeData.label || nodeData.id}</h4>
                <p><strong>File:</strong> ${nodeData.filepath || ''}</p>
                <p><strong>Cluster ID:</strong> ${nodeData.cluster_id || ''}</p>
                <p><strong>Score (Distance):</strong> ${typeof nodeData.score === 'number' ? nodeData.score.toFixed(4) : ''}</p>
                <pre style="max-height:300px;overflow:auto;background:#222;color:#eee;padding:8px;border-radius:6px;"><code>${nodeData.excerpt ? nodeData.excerpt.replace(/</g, "&lt;").replace(/>/g, "&gt;") : 'No excerpt available.'}</code></pre>
            `;
        });
    }
}