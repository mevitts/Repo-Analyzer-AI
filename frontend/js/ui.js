import { debugLog } from './config.js';
import { CONFIG } from './config.js';
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

    displaySearchResults(results) {
        const resultsContainer = this.elements.searchResults;
        resultsContainer.innerHTML = '';
        if (!results || !results.points || results.points.length === 0) {
            resultsContainer.innerHTML = '<p>No results found.</p>';
            return;
        }
        let htmlContent = '';
        results.points.forEach(point => {
            htmlContent += `
                <div class="search-result-item">
                    <strong>File:</strong> ${point.payload.filepath} (Score: ${point.score ? point.score.toFixed(4) : 'N/A'})
                    <pre><code>${point.payload.excerpt || 'No excerpt available.'}</code></pre>
                </div>
            `;
        });
        resultsContainer.innerHTML = htmlContent;
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
        const colorMap = {};
        let colorIdx = 0;
        const palette = ['#00b894', '#0984e3', '#fdcb6e', '#e17055', '#6c5ce7', '#00cec9', '#d35400', '#636e72'];
        const elements = [];
        if (atlasPack.nodes) {
            for (const node of atlasPack.nodes) {
                let color = colorMap[node.dirpath];
                if (!color) {
                    color = palette[colorIdx % palette.length];
                    colorMap[node.dirpath] = color;
                    colorIdx++;
                }
                elements.push({
                    data: {
                        id: node.id,
                        label: node.label,
                        filepath: node.filepath,
                        dirpath: node.dirpath,
                        cluster_id: node.cluster_id,
                        loc: node.loc,
                        chunk_count: node.chunk_count,
                        vector: node.vector,
                    },
                    classes: `cluster-${node.cluster_id}`,
                    style: {
                        'background-color': color,
                        'width': Math.max(24, Math.sqrt(node.loc || 10) * 2),
                        'height': Math.max(24, Math.sqrt(node.loc || 10) * 2),
                        'border-width': node.label === 'main.py' ? 4 : 1,
                        'border-color': node.label === 'main.py' ? '#e17055' : '#222'
                    }
                });
            }
        }
        // Fix: define edgeSet before using it
        const edgeSet = new Set();
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
            let infoHtml = `<h4>${nodeData.label}</h4>
                <p><strong>File:</strong> ${nodeData.filepath}</p>
                <p><strong>Cluster ID:</strong> ${nodeData.cluster_id}</p>`;

            // Show chunk-specific info if present
            if ('start_line_no' in nodeData && 'end_line_no' in nodeData) {
                infoHtml += `<p><strong>Lines:</strong> ${nodeData.start_line_no}–${nodeData.end_line_no}</p>`;
            }
            if ('excerpt' in nodeData && nodeData.excerpt) {
                infoHtml += `<pre style="max-height:120px;overflow:auto;"><code>${nodeData.excerpt}</code></pre>`;
            }
            if (nodeData.vector && Array.isArray(nodeData.vector)) {
                const norm = Math.sqrt(nodeData.vector.reduce((a, b) => a + b * b, 0));
                infoHtml += `<p><strong>Vector norm:</strong> ${norm.toFixed(3)}</p>`;
            }
            // For file-level nodes, show file-level info
            if ('loc' in nodeData) {
                infoHtml += `<p><strong>Lines of Code:</strong> ${nodeData.loc}</p>`;
            }
            if ('chunk_count' in nodeData) {
                infoHtml += `<p><strong>Chunks:</strong> ${nodeData.chunk_count}</p>`;
            }
            this.elements.atlasSidebar.innerHTML = infoHtml;

            // Position sidebar near node as before...
            const pos = evt.target.renderedPosition();
            const sidebar = this.elements.atlasSidebar;
            sidebar.style.display = 'block';
            sidebar.style.position = 'absolute';
            sidebar.style.left = `${pos.x + 60}px`;
            sidebar.style.top = `${pos.y + 80}px`;
            sidebar.style.zIndex = 100;
        });

        cy.on('dblclick', 'node', async (evt) => {
            const nodeData = evt.target.data();
            const repoId = nodeData.repo_id || window.app?.repoId || window.currentRepoId;
            console.log('[Atlas Debug] Double-clicked node:', nodeData, 'repoId:', repoId);
            if (!nodeData.filepath || !repoId) return;
            this.elements.atlasSidebar.innerHTML = `<p>Loading file-level atlas...</p>`;
            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}/file_atlas`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        repo_id: repoId,
                        filepath: nodeData.filepath
                    })
                });
                const data = await response.json();
                console.log('[Atlas Debug] file_atlas response:', data);
                if (data.atlas_pack && data.atlas_pack.nodes && data.atlas_pack.nodes.length > 0) {
                    this.showChunkAtlas(data.atlas_pack);
                } else {
                    this.elements.atlasSidebar.innerHTML = `<p>No chunk-level atlas available.</p>`;
                }
            } catch (err) {
                console.error('[Atlas Debug] Error loading chunk-level atlas:', err);
                this.elements.atlasSidebar.innerHTML = `<p>Error loading chunk-level atlas.</p>`;
            }
        });

        cy.on('tap', (evt) => {
            if (evt.target === cy) {
                this.elements.atlasSidebar.style.display = 'none';
            }
        });
    }

    showChunkAtlas(atlasPack) {
        const modal = document.getElementById('chunk-atlas-modal');
        modal.classList.remove('hidden');
        this.renderAtlas(atlasPack, document.getElementById('chunk-atlas-graph'));
        document.getElementById('close-chunk-atlas').onclick = () => {
            modal.classList.add('hidden');
        };
    }
}