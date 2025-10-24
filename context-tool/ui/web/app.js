// Context Tool - Frontend JavaScript

const API_BASE = '/api';
let currentSelection = null;
let ws = null;
let reconnectInterval = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Context Tool initialized');

    // Load stats
    await loadStats();

    // Set up text selection monitoring
    const demoText = document.getElementById('demoText');
    demoText.addEventListener('mouseup', handleTextSelection);
    demoText.addEventListener('touchend', handleTextSelection);

    // Connect to WebSocket for real-time updates
    connectWebSocket();
});

// WebSocket connection for real-time updates
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    console.log('Connecting to WebSocket:', wsUrl);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }

        // Show system mode indicator if enabled
        showSystemModeIndicator();
    };

    ws.onmessage = (event) => {
        const result = JSON.parse(event.data);

        // Display the result
        if (result.source === 'system') {
            // Mark as system selection
            displayContext(result, true);
        } else {
            displayContext(result, false);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting...');
        hideSystemModeIndicator();

        // Attempt to reconnect after 3 seconds
        if (!reconnectInterval) {
            reconnectInterval = setInterval(() => {
                connectWebSocket();
            }, 3000);
        }
    };
}

// Show indicator that system mode is active
function showSystemModeIndicator() {
    // Check if we're receiving system broadcasts
    const indicator = document.createElement('div');
    indicator.id = 'system-mode-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-size: 14px;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    indicator.innerHTML = '🔍 System Mode Active - Copy text anywhere!';

    // Only show if not already present
    if (!document.getElementById('system-mode-indicator')) {
        document.body.appendChild(indicator);
    }
}

function hideSystemModeIndicator() {
    const indicator = document.getElementById('system-mode-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Load database statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();

        const statsEl = document.getElementById('stats');
        statsEl.innerHTML = `
            <div class="stat-card">
                <div class="number">${stats.contacts}</div>
                <div class="label">Contacts</div>
            </div>
            <div class="stat-card">
                <div class="number">${stats.snippets}</div>
                <div class="label">Snippets</div>
            </div>
            <div class="stat-card">
                <div class="number">${stats.projects}</div>
                <div class="label">Projects</div>
            </div>
            <div class="stat-card">
                <div class="number">${stats.abbreviations || 0}</div>
                <div class="label">Abbreviations</div>
            </div>
            <div class="stat-card">
                <div class="number">${stats.relationships}</div>
                <div class="label">Links</div>
            </div>
        `;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Handle text selection
function handleTextSelection() {
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();

    if (selectedText.length > 0) {
        console.log('Selected text:', selectedText);
        currentSelection = selectedText;
        analyzeText(selectedText);
    }
}

// Analyze selected text
async function analyzeText(text) {
    const displayEl = document.getElementById('contextDisplay');

    // Show loading state
    displayEl.innerHTML = '<div class="loading">Analyzing...</div>';

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            throw new Error('Analysis failed');
        }

        const result = await response.json();
        displayContext(result);

    } catch (error) {
        console.error('Analysis error:', error);
        displayEl.innerHTML = `
            <div class="context-section">
                <h3>Error</h3>
                <div class="context-content" style="color: #d32f2f;">
                    Failed to analyze text. Please try again.
                </div>
            </div>
        `;
    }
}

// Display context analysis results
function displayContext(result, isSystemSelection = false) {
    const displayEl = document.getElementById('contextDisplay');
    let html = '';

    // Selected Text
    const sourceLabel = isSystemSelection ?
        '<span class="badge" style="background: #4CAF50;">System Selection</span>' : '';

    html += `
        <div class="context-section">
            <h3>Selected Text ${sourceLabel}</h3>
            <div class="context-content">
                <strong>"${result.selected_text}"</strong>
            </div>
        </div>
    `;

    // Abbreviation Match (show prominently)
    if (result.abbreviation) {
        const abbr = result.abbreviation;
        const examples = abbr.examples ? JSON.parse(abbr.examples) : [];
        const related = abbr.related ? JSON.parse(abbr.related) : [];
        const links = abbr.links ? JSON.parse(abbr.links) : [];

        html += `
            <div class="context-section" style="background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%); border-left: 4px solid #667eea; padding: 16px; border-radius: 8px;">
                <h3 style="margin-top: 0;">Abbreviation</h3>
                <div class="context-content">
                    <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">
                        ${abbr.abbr} = ${abbr.full}
                    </div>
                    ${abbr.definition ? `
                        <div style="margin: 12px 0; padding: 12px; background: white; border-radius: 6px;">
                            ${abbr.definition}
                        </div>
                    ` : ''}
                    ${abbr.category ? `
                        <div style="margin-top: 8px;">
                            <span class="badge" style="background: #667eea; color: white;">${abbr.category}</span>
                        </div>
                    ` : ''}
                    ${examples.length > 0 ? `
                        <div style="margin-top: 12px;">
                            <strong>Examples:</strong> ${examples.join(', ')}
                        </div>
                    ` : ''}
                    ${related.length > 0 ? `
                        <div style="margin-top: 12px;">
                            <strong>Related:</strong> ${related.join(', ')}
                        </div>
                    ` : ''}
                    ${links.length > 0 ? `
                        <div style="margin-top: 12px;">
                            <strong>Learn more:</strong><br/>
                            ${links.map(link => `<a href="${link}" target="_blank" style="display: block; margin-top: 4px; color: #667eea;">${link}</a>`).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // Detected Type
    if (result.detected_type) {
        html += `
            <div class="context-section">
                <h3>Detected Type</h3>
                <div class="context-content">
                    <span class="badge">${result.detected_type.replace('_', ' ')}</span>
                </div>
            </div>
        `;
    }

    // Smart Context
    if (result.smart_context) {
        html += `
            <div class="context-section">
                <h3>Context</h3>
                <div class="context-content">
                    ${result.smart_context}
                </div>
            </div>
        `;
    }

    // Insights
    if (result.insights && result.insights.length > 0) {
        html += `
            <div class="context-section">
                <h3>Insights</h3>
                <div class="context-content">
                    ${result.insights.map(insight => `
                        <div class="insight">${insight}</div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Exact Matches
    if (result.exact_matches && result.exact_matches.length > 0) {
        html += `
            <div class="context-section">
                <h3>Exact Matches</h3>
                <div class="context-content">
                    ${result.exact_matches.map(match => renderMatch(match)).join('')}
                </div>
            </div>
        `;
    }

    // Semantic Matches
    if (result.semantic_matches && result.semantic_matches.length > 0) {
        html += `
            <div class="context-section">
                <h3>Semantically Similar</h3>
                <div class="context-content">
                    ${result.semantic_matches.map(match => `
                        <div class="match-item">
                            <div><strong>${match.type}</strong> (${Math.round(match.similarity * 100)}% similar)</div>
                            <div style="margin-top: 4px; color: #666;">${match.text}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Related Items
    if (result.related_items && result.related_items.length > 0) {
        html += `
            <div class="context-section">
                <h3>Related via Knowledge Graph</h3>
                <div class="context-content">
                    ${result.related_items.map(item => `
                        <div class="match-item">
                            <div><strong>${item.type}</strong> - ${item.relationship}</div>
                            <div style="margin-top: 4px; color: #666;">
                                ${item.data.name || item.data.text || 'Unknown'}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Actions
    if (result.actions && result.actions.length > 0) {
        html += `
            <div class="context-section">
                <h3>Suggested Actions</h3>
                <div class="actions">
                    ${result.actions.map(action => `
                        <button class="action-btn" onclick="handleAction('${action.type}', '${escapeHtml(action.value)}')">
                            ${action.label}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }

    displayEl.innerHTML = html;
}

// Render a match item
function renderMatch(match) {
    const data = match.data;
    const type = match.type;

    let content = '';

    if (type === 'contact') {
        content = `
            <div class="match-item">
                <div><strong>Contact: ${data.name || 'Unknown'}</strong></div>
                ${data.email ? `<div>📧 ${data.email}</div>` : ''}
                ${data.role ? `<div>👔 ${data.role}</div>` : ''}
                ${data.last_contact ? `<div>💬 ${data.last_contact}</div>` : ''}
                ${data.next_event ? `<div>📅 ${data.next_event}</div>` : ''}
            </div>
        `;
    } else if (type === 'snippet') {
        content = `
            <div class="match-item">
                <div><strong>Snippet:</strong></div>
                <div style="margin-top: 4px; color: #666;">${data.text || 'No text'}</div>
                ${data.saved_date ? `<div style="margin-top: 4px; font-size: 12px; color: #999;">Saved: ${data.saved_date}</div>` : ''}
            </div>
        `;
    } else if (type === 'project') {
        content = `
            <div class="match-item">
                <div><strong>Project: ${data.name || 'Unknown'}</strong></div>
                ${data.status ? `<div>Status: ${data.status}</div>` : ''}
                ${data.description ? `<div style="margin-top: 4px; color: #666;">${data.description}</div>` : ''}
            </div>
        `;
    }

    return content;
}

// Handle action button click
function handleAction(type, value) {
    if (type === 'url') {
        window.open(value, '_blank');
    } else if (type === 'copy') {
        navigator.clipboard.writeText(value).then(() => {
            alert(`Copied: ${value}`);
        });
    } else if (type === 'action') {
        if (value === 'save_snippet') {
            saveSnippet(currentSelection);
        } else {
            alert(`Action: ${value}`);
        }
    }
}

// Save current selection as snippet
async function saveSnippet(text) {
    try {
        const response = await fetch(`${API_BASE}/save-snippet`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                tags: [],
                source: 'web-demo'
            })
        });

        if (response.ok) {
            const result = await response.json();
            alert(`Snippet saved! ID: ${result.id}`);
            loadStats(); // Refresh stats
        } else {
            alert('Failed to save snippet');
        }
    } catch (error) {
        console.error('Save error:', error);
        alert('Failed to save snippet');
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
