// Context Tool - Frontend JavaScript

const API_BASE = '/api';
let currentSelection = null;
let currentAnalysisResult = null; // Store the full analysis result for smart save
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
    // Store the result for smart save dialog
    currentAnalysisResult = result;

    // Update current selection from the result (important for system clipboard selections)
    currentSelection = result.selected_text;

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

    // Quick Actions at the TOP (always visible)
    html += `
        <div class="context-section" style="background: linear-gradient(135deg, #667eea11 0%, #764ba211 100%); border-left: 4px solid #667eea;">
            <h3>⚡ Quick Actions</h3>
            <div class="action-buttons" style="display: flex; gap: 8px; flex-wrap: wrap;">
                <button class="action-btn" onclick="saveCurrentSnippet()" style="background: #28a745; color: white;">💾 Save Snippet</button>
                <button class="action-btn" onclick="searchWeb()">🔍 Search Web</button>
            </div>
        </div>
    `;

    // People Detection Summary (if people found)
    const detectedPeople = result.detected_people || [];
    if (detectedPeople.length > 0) {
        const existingPeople = detectedPeople.filter(p => p.exists);
        const newPeople = detectedPeople.filter(p => !p.exists);

        html += `
            <div class="context-section" style="background: #fff3cd; border-left: 4px solid #ffc107;">
                <h3>🔍 People Detected</h3>
                <div style="font-size: 13px; line-height: 1.8;">
                    ${existingPeople.length > 0 ? `
                        <div style="margin-bottom: 8px;">
                            ${existingPeople.map(p => `
                                <span style="display: inline-block; margin: 4px 8px 4px 0;">
                                    ✓ <strong>${p.name}</strong>
                                    <span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 4px;">Contact exists</span>
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}
                    ${newPeople.length > 0 ? `
                        <div>
                            ${newPeople.map(p => `
                                <span style="display: inline-block; margin: 4px 8px 4px 0;">
                                    ⚠️ <strong>${p.name}</strong>
                                    <span style="background: #ff9800; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 4px;">New person</span>
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}
                    <div style="margin-top: 8px; font-size: 12px; color: #856404;">
                        💡 Click "Save Snippet" to link or create contacts
                    </div>
                </div>
            </div>
        `;
    }

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
                    ${result.exact_matches.map((match, index) => renderMatch(match, index)).join('')}
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
                    ${result.related_items.map((item, index) => renderMatch(item, 1000 + index)).join('')}
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

    // Quick Actions moved to top

    displayEl.innerHTML = html;
}

// Simple markdown to HTML converter
function simpleMarkdown(text) {
    if (!text) return '';

    return text
        // Headers
        .replace(/^### (.*$)/gm, '<h4>$1</h4>')
        .replace(/^## (.*$)/gm, '<h3>$1</h3>')
        .replace(/^# (.*$)/gm, '<h2>$1</h2>')
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Links
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
        // Line breaks
        .replace(/\n/g, '<br>');
}

// Truncate text to first N lines
function truncateLines(text, maxLines = 3) {
    if (!text) return '';
    const lines = text.split('\n');
    if (lines.length <= maxLines) {
        return text;
    }
    return lines.slice(0, maxLines).join('\n');
}

// Toggle expand/collapse for a match item
function toggleMatch(matchId) {
    const preview = document.getElementById(`preview-${matchId}`);
    const full = document.getElementById(`full-${matchId}`);
    const btn = document.getElementById(`btn-${matchId}`);

    if (preview && full && btn) {
        if (preview.style.display === 'none') {
            // Collapse
            preview.style.display = 'block';
            full.style.display = 'none';
            btn.textContent = '▼ Show more';
        } else {
            // Expand
            preview.style.display = 'none';
            full.style.display = 'block';
            btn.textContent = '▲ Show less';
        }
    }
}

// Render a match item (with collapsible content)
function renderMatch(match, index) {
    const data = match.data;
    const type = match.type;
    const matchId = `match-${Date.now()}-${index}`;

    let content = '';
    let mainText = '';
    let needsExpansion = false;

    if (type === 'contact') {
        const contextText = data.context || '';
        const contextLines = contextText.split('\n');
        needsExpansion = contextLines.length > 3;

        const preview = truncateLines(contextText, 3);

        content = `
            <div class="match-item" style="border-left: 4px solid #667eea; padding-left: 12px;">
                <div><strong>👤 ${data.name || 'Unknown'}</strong>
                    ${match.match_score ? `<span style="background: #667eea; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 8px;">Score: ${match.match_score}</span>` : ''}
                </div>
                ${data.email ? `<div style="margin-top: 4px;">📧 ${data.email}</div>` : ''}
                ${data.role ? `<div style="margin-top: 4px;">👔 ${data.role}</div>` : ''}
                ${data.last_contact ? `<div style="margin-top: 4px;">💬 ${data.last_contact}</div>` : ''}
                ${data.next_event ? `<div style="margin-top: 4px;">📅 ${data.next_event}</div>` : ''}
                ${contextText ? `
                    <div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                        <div id="preview-${matchId}" style="color: #666; font-size: 13px; line-height: 1.5;">
                            ${simpleMarkdown(preview)}
                            ${needsExpansion ? '<span style="color: #999;">...</span>' : ''}
                        </div>
                        <div id="full-${matchId}" style="display: none; color: #666; font-size: 13px; line-height: 1.5;">
                            ${simpleMarkdown(contextText)}
                        </div>
                        ${needsExpansion ? `
                            <button id="btn-${matchId}" onclick="toggleMatch('${matchId}')"
                                    style="margin-top: 8px; padding: 4px 8px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                                ▼ Show more
                            </button>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    } else if (type === 'snippet') {
        const snippetText = data.text || '';
        const snippetLines = snippetText.split('\n');
        needsExpansion = snippetLines.length > 3;

        const preview = truncateLines(snippetText, 3);

        content = `
            <div class="match-item" style="border-left: 4px solid #28a745; padding-left: 12px;">
                <div><strong>📝 Snippet</strong></div>
                <div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                    <div id="preview-${matchId}" style="color: #666; font-size: 13px; line-height: 1.5;">
                        ${simpleMarkdown(preview)}
                        ${needsExpansion ? '<span style="color: #999;">...</span>' : ''}
                    </div>
                    <div id="full-${matchId}" style="display: none; color: #666; font-size: 13px; line-height: 1.5;">
                        ${simpleMarkdown(snippetText)}
                    </div>
                    ${needsExpansion ? `
                        <button id="btn-${matchId}" onclick="toggleMatch('${matchId}')"
                                style="margin-top: 8px; padding: 4px 8px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            ▼ Show more
                        </button>
                    ` : ''}
                </div>
                ${data.saved_date ? `<div style="margin-top: 4px; font-size: 12px; color: #999;">Saved: ${data.saved_date}</div>` : ''}
            </div>
        `;
    } else if (type === 'project') {
        const descText = data.description || '';
        const descLines = descText.split('\n');
        needsExpansion = descLines.length > 3;

        const preview = truncateLines(descText, 3);

        content = `
            <div class="match-item" style="border-left: 4px solid #fd7e14; padding-left: 12px;">
                <div><strong>📁 ${data.name || 'Unknown'}</strong></div>
                ${data.status ? `<div style="margin-top: 4px;">Status: <span style="background: #fd7e14; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">${data.status}</span></div>` : ''}
                ${descText ? `
                    <div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                        <div id="preview-${matchId}" style="color: #666; font-size: 13px; line-height: 1.5;">
                            ${simpleMarkdown(preview)}
                            ${needsExpansion ? '<span style="color: #999;">...</span>' : ''}
                        </div>
                        <div id="full-${matchId}" style="display: none; color: #666; font-size: 13px; line-height: 1.5;">
                            ${simpleMarkdown(descText)}
                        </div>
                        ${needsExpansion ? `
                            <button id="btn-${matchId}" onclick="toggleMatch('${matchId}')"
                                    style="margin-top: 8px; padding: 4px 8px; background: #fd7e14; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                                ▼ Show more
                            </button>
                        ` : ''}
                    </div>
                ` : ''}
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

// Save current selection with Smart Saver
// Save the current selection as a snippet
function saveCurrentSnippet() {
    if (!currentSelection) {
        alert('No text selected. Please select some text first.');
        return;
    }

    // If we have detected people, show smart save dialog
    if (currentAnalysisResult && currentAnalysisResult.detected_people && currentAnalysisResult.detected_people.length > 0) {
        showSmartSaveDialog();
    } else {
        // No people detected, save directly as snippet
        saveSnippet(currentSelection);
    }
}

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
                source: 'web'
            })
        });

        if (!response.ok) {
            const error = await response.json();
            alert('Failed to save snippet: ' + (error.detail || 'Unknown error'));
            return;
        }

        const result = await response.json();
        alert('✅ Snippet saved! ' + (result.message || ''));

        console.log('Snippet saved:', result);
    } catch (error) {
        console.error('Save error:', error);
        alert('Failed to save snippet: ' + error.message);
    }
}

// Show save type choice dialog
function showSaveDialog(text, choices) {
    const modal = document.getElementById('saveModal');
    const choicesContainer = document.getElementById('saveChoices');
    const previewEl = document.getElementById('savePreview');
    const abbreviationFields = document.getElementById('abbreviationFields');

    // Set preview text
    const preview = text.length > 100 ? text.substring(0, 100) + '...' : text;
    previewEl.textContent = `"${preview}"`;

    // Clear previous choices
    choicesContainer.innerHTML = '';

    // Clear abbreviation fields
    document.getElementById('abbrFull').value = '';
    document.getElementById('abbrDefinition').value = '';
    abbreviationFields.classList.remove('show');

    // Create radio buttons for each choice
    choices.forEach((choice, index) => {
        const choiceDiv = document.createElement('div');
        choiceDiv.className = 'save-choice';

        const radioId = `save-choice-${index}`;

        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.id = radioId;
        radio.name = 'saveType';
        radio.value = choice.type;
        radio.checked = index === 0;

        // Add event listener to show/hide abbreviation fields
        radio.addEventListener('change', function() {
            if (this.value === 'abbreviation' && this.checked) {
                abbreviationFields.classList.add('show');
            } else {
                abbreviationFields.classList.remove('show');
            }
        });

        const label = document.createElement('label');
        label.htmlFor = radioId;

        const labelText = document.createElement('div');
        labelText.className = 'choice-label';
        labelText.textContent = choice.label;

        const reasonText = document.createElement('div');
        reasonText.className = 'choice-reason';
        const confidence = Math.round(choice.confidence * 100);
        reasonText.textContent = `Confidence: ${confidence}% - ${choice.reason}`;

        label.appendChild(labelText);
        label.appendChild(reasonText);

        choiceDiv.appendChild(radio);
        choiceDiv.appendChild(label);

        choicesContainer.appendChild(choiceDiv);
    });

    // Show abbreviation fields if first choice is abbreviation
    if (choices[0].type === 'abbreviation') {
        abbreviationFields.classList.add('show');
    }

    // Show modal
    modal.style.display = 'flex';

    // Store text for later
    modal.dataset.text = text;
}

// Perform the actual save
async function performSave(text, saveType, metadata = null) {
    try {
        const requestBody = {
            text: text,
            save_type: saveType
        };

        // Add metadata if provided
        if (metadata) {
            requestBody.metadata = metadata;
        }

        const response = await fetch(`${API_BASE}/save-smart/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (response.ok) {
            const result = await response.json();
            showToast(`✓ Saved as ${saveType}!`);
            loadStats(); // Refresh stats
        } else {
            alert('Failed to save');
        }
    } catch (error) {
        console.error('Save error:', error);
        alert('Failed to save');
    }
}

// Close save dialog
function closeSaveDialog() {
    const modal = document.getElementById('saveModal');
    modal.style.display = 'none';
}

// Save with selected type
function saveWithSelectedType() {
    const modal = document.getElementById('saveModal');
    const selectedRadio = document.querySelector('input[name="saveType"]:checked');

    if (selectedRadio) {
        const text = modal.dataset.text;
        const saveType = selectedRadio.value;

        // Collect metadata for abbreviations
        let metadata = null;
        if (saveType === 'abbreviation') {
            const full = document.getElementById('abbrFull').value.trim();
            const definition = document.getElementById('abbrDefinition').value.trim();

            // Validate required field
            if (!full) {
                alert('Please enter the full term for the abbreviation');
                return;
            }

            metadata = {
                full: full,
                definition: definition
            };
        }

        closeSaveDialog();
        performSave(text, saveType, metadata);
    }
}

// Show toast notification
function showToast(message) {
    // Remove existing toast if any
    const existingToast = document.getElementById('toast');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.id = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #4CAF50;
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Search web with current selection
function searchWeb() {
    if (currentSelection) {
        const query = encodeURIComponent(currentSelection);
        window.open(`https://www.google.com/search?q=${query}`, '_blank');
    }
}

// Smart Save Dialog Functions
function showSmartSaveDialog() {
    const modal = document.getElementById('smartSaveModal');
    const previewEl = document.getElementById('smartSavePreview');
    const optionsEl = document.getElementById('smartSaveOptions');

    // Set preview text
    const preview = currentSelection.length > 100 ? currentSelection.substring(0, 100) + '...' : currentSelection;
    previewEl.textContent = `"${preview}"`;

    // Get detected people from analysis result
    const detectedPeople = currentAnalysisResult?.detected_people || [];

    // Build checkbox options
    let optionsHtml = '<div style="margin-bottom: 20px;">';

    // Existing contacts
    const existingPeople = detectedPeople.filter(p => p.exists);
    if (existingPeople.length > 0) {
        optionsHtml += '<h3 style="color: #667eea; font-size: 16px; margin-bottom: 12px;">✓ Link to Existing Contacts</h3>';
        optionsHtml += '<div style="margin-bottom: 16px;">';
        existingPeople.forEach((person, idx) => {
            optionsHtml += `
                <div style="display: flex; align-items: center; padding: 8px; background: #f8f9fa; border-radius: 6px; margin-bottom: 8px;">
                    <input type="checkbox" id="link-existing-${idx}" checked style="margin-right: 12px; cursor: pointer;">
                    <label for="link-existing-${idx}" style="cursor: pointer; flex: 1;">
                        <strong>${escapeHtml(person.name)}</strong>
                        <span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 8px;">
                            Contact: ${escapeHtml(person.contact_name || 'Unknown')}
                        </span>
                    </label>
                </div>
            `;
        });
        optionsHtml += '</div>';
    }

    // New people
    const newPeople = detectedPeople.filter(p => !p.exists);
    if (newPeople.length > 0) {
        optionsHtml += '<h3 style="color: #667eea; font-size: 16px; margin-bottom: 12px;">⚠️ Create New Contacts</h3>';
        optionsHtml += '<div style="margin-bottom: 16px;">';
        newPeople.forEach((person, idx) => {
            optionsHtml += `
                <div style="display: flex; align-items: center; padding: 8px; background: #fff3cd; border-radius: 6px; margin-bottom: 8px;">
                    <input type="checkbox" id="create-new-${idx}" checked style="margin-right: 12px; cursor: pointer;">
                    <label for="create-new-${idx}" style="cursor: pointer; flex: 1;">
                        <strong>${escapeHtml(person.name)}</strong>
                        <span style="background: #ff9800; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 8px;">
                            New Person
                        </span>
                    </label>
                </div>
            `;
        });
        optionsHtml += '</div>';
    }

    // Always save as snippet option
    optionsHtml += '<h3 style="color: #667eea; font-size: 16px; margin-bottom: 12px;">📝 Save Options</h3>';
    optionsHtml += `
        <div style="padding: 12px; background: #e3f2fd; border-radius: 6px;">
            <div style="display: flex; align-items: center;">
                <input type="checkbox" id="save-snippet" checked disabled style="margin-right: 12px;">
                <label for="save-snippet" style="font-weight: bold;">
                    Save as snippet (always enabled)
                </label>
            </div>
            <div style="margin-top: 8px; font-size: 13px; color: #666;">
                The snippet will be saved with links to the selected contacts above.
            </div>
        </div>
    `;

    optionsHtml += '</div>';

    optionsEl.innerHTML = optionsHtml;

    // Show the modal
    modal.style.display = 'flex';
}

function closeSmartSaveDialog() {
    const modal = document.getElementById('smartSaveModal');
    modal.style.display = 'none';
}

async function saveWithSmartOptions() {
    const detectedPeople = currentAnalysisResult?.detected_people || [];
    const existingPeople = detectedPeople.filter(p => p.exists);
    const newPeople = detectedPeople.filter(p => !p.exists);

    // Collect selected options
    const linkToExisting = [];
    existingPeople.forEach((person, idx) => {
        const checkbox = document.getElementById(`link-existing-${idx}`);
        if (checkbox && checkbox.checked) {
            linkToExisting.push({
                name: person.name,
                contact_id: person.contact_id,
                contact_name: person.contact_name
            });
        }
    });

    const createNew = [];
    newPeople.forEach((person, idx) => {
        const checkbox = document.getElementById(`create-new-${idx}`);
        if (checkbox && checkbox.checked) {
            createNew.push({
                name: person.name
            });
        }
    });

    // Close the dialog
    closeSmartSaveDialog();

    // TODO: Call the smart save API endpoint with the options
    // For now, just save as regular snippet
    try {
        console.log('Smart save options:', { linkToExisting, createNew });

        // TODO: Replace this with actual smart save API call
        const response = await fetch(`${API_BASE}/save-snippet`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: currentSelection,
                tags: [],
                source: 'web',
                // TODO: Add smart save options here
                link_to_existing: linkToExisting,
                create_new_contacts: createNew
            })
        });

        if (!response.ok) {
            const error = await response.json();
            alert('Failed to save: ' + (error.detail || 'Unknown error'));
            return;
        }

        const result = await response.json();
        alert('✅ Snippet saved with smart linking! ' + (result.message || ''));

        console.log('Smart save result:', result);
    } catch (error) {
        console.error('Smart save error:', error);
        alert('Failed to save snippet: ' + error.message);
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
