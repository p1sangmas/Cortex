// Cortex - ChatGPT Style Logic (Interactions Fixed)

// Global Variables
const API_BASE_URL = 'http://localhost:8080/api';
let sessionId = Date.now().toString();
let currentRagMode = 'agentic'; // Default to Agentic

// DOM Elements
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const chatMessages = document.getElementById('chat-messages');
const emptyState = document.getElementById('empty-state');
const fileUpload = document.getElementById('file-upload');
const docCountEl = document.getElementById('doc-count');

// Toggle Elements
const modelSelectorBtn = document.getElementById('model-selector-btn');
const modelDropdown = document.getElementById('model-dropdown');
const currentModelText = document.getElementById('current-model-text');
const viewDocsBtn = document.getElementById('view-docs-btn');
const documentsModal = document.getElementById('documents-modal');
const modalFileList = document.getElementById('modal-file-list');
const modalOverlay = document.getElementById('modal-overlay');

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    sessionId = generateSessionId();
    console.log('Session ID:', sessionId);

    checkSystemStatus();
    updateProcessedFilesList();
    setupEventListeners();
    setupDragAndDrop();

    // Set initial model state
    updateModelUI(currentRagMode);
});

function setupEventListeners() {
    // Chat Input
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Enable send button when typing
    chatInput.addEventListener('input', () => {
        if (chatInput.value.trim().length > 0) {
            sendBtn.removeAttribute('disabled');
        } else {
            sendBtn.setAttribute('disabled', 'true');
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    // File Upload
    fileUpload.addEventListener('change', handleFileUpload);

    // Clear KB
    const clearKbBtn = document.getElementById('clear-kb-btn');
    if (clearKbBtn) {
        clearKbBtn.addEventListener('click', clearKnowledgeBase);
    }

    // Model Selector Logic
    if (modelSelectorBtn) {
        modelSelectorBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            modelDropdown.classList.toggle('hidden');
        });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (modelDropdown && !modelDropdown.classList.contains('hidden') && !modelSelectorBtn.contains(e.target)) {
            modelDropdown.classList.add('hidden');
        }
    });

    // Model Options
    const modelOptions = document.querySelectorAll('.model-option');
    modelOptions.forEach(option => {
        option.addEventListener('click', () => {
            const value = option.dataset.value;
            currentRagMode = value;
            updateModelUI(value);
            modelDropdown.classList.add('hidden');
        });
    });

    // View Documents Button
    if (viewDocsBtn) {
        viewDocsBtn.addEventListener('click', () => {
            updateModalFileList();
            openModal('documents-modal');
        });
    }

    // User Session Modal
    const userBtn = document.getElementById('user-btn-trigger');
    if (userBtn) {
        userBtn.addEventListener('click', () => {
            document.getElementById('session-id-display').textContent = sessionId;
            openModal('user-modal');
        });
    }
}

// Helper to copy Session ID
function copySessionId() {
    const text = document.getElementById('session-id-display').textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Session ID copied!', 'success');
    });
}

function updateModelUI(mode) {
    // Update Text
    currentModelText.textContent = mode === 'traditional' ? 'Cortex' : 'Cortex Agentic';

    // Update Selected Class in Dropdown
    document.querySelectorAll('.model-option').forEach(opt => {
        const checkIcon = opt.querySelector('.check-icon');
        if (opt.dataset.value === mode) {
            opt.classList.add('selected');
            if (checkIcon) checkIcon.classList.remove('hidden');
        } else {
            opt.classList.remove('selected');
            if (checkIcon) checkIcon.classList.add('hidden');
        }
    });
}

function setupDragAndDrop() {
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Modal Drop Zone specific logic
    const modalDropZone = document.getElementById('modal-drop-zone');
    if (modalDropZone) {
        ['dragenter', 'dragover'].forEach(eventName => {
            modalDropZone.addEventListener(eventName, (e) => {
                preventDefaults(e); // Prevent default for dragover to allow drop
                modalDropZone.classList.add('dragover');
            }, false);
        });
        ['dragleave', 'drop'].forEach(eventName => {
            modalDropZone.addEventListener(eventName, (e) => {
                preventDefaults(e); // Prevent default for drop
                modalDropZone.classList.remove('dragover');
            }, false);
        });
        modalDropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles({
                target: {
                    files: files
                }
            });
        });
    }
}


// --- Core Logic ---

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // UI Updates
    chatInput.value = '';
    chatInput.style.height = 'auto'; // Reset height
    emptyState.classList.add('hidden'); // Hide empty state

    // Add User Message
    addMessage(text, 'user');

    // Show Typing Indicator
    const typingIndicator = addTypingIndicator();

    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: text,
                session_id: sessionId,
                mode: currentRagMode // Use top bar variable
            })
        });

        const data = await response.json();

        // Remove typing indicator
        if (typingIndicator) typingIndicator.remove();

        if (data.error) {
            addMessage(`Error: ${data.error}`, 'assistant', null, true);
        } else {
            addMessage(data.answer, 'assistant', data);
        }

    } catch (error) {
        if (typingIndicator) typingIndicator.remove();
        addMessage("Sorry, I couldn't connect to the server.", 'assistant', null, true);
        console.error(error);
    }
}

function addMessage(text, role, metadata = null, isError = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;

    // Avatar
    const avatar = document.createElement('div');
    avatar.className = `avatar ${role}`;
    avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

    // Content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (isError) {
        contentDiv.style.color = 'var(--danger-color)';
        contentDiv.textContent = text;
    } else {
        // Parse Markdown
        marked.setOptions({
            highlight: function(code, lang) {
                const language = highlight.getLanguage(lang) ? lang : 'plaintext';
                return highlight.highlight(code, {
                    language
                }).value;
            },
            langPrefix: 'hljs language-'
        });

        contentDiv.innerHTML = marked.parse(text);

        // --- Extended Metadata (Visualize Logic) ---
        if (role === 'assistant' && metadata) {

            // Confidence tag removed as requested

            // Meta Actions Container (Side-by-Side Buttons)
            const metaActionsDiv = document.createElement('div');
            metaActionsDiv.className = 'meta-actions';

            // 2. Reasoning Trace (Enhanced with meaningful info)
            if (metadata.reasoning_trace && metadata.reasoning_trace.length > 0) {
                const traceDiv = document.createElement('details');
                traceDiv.open = false;
                // traceDiv.style.marginTop removed in favor of CSS class

                // Filter out skip_tool steps
                const filteredTrace = metadata.reasoning_trace.filter(step => step.step !== 'skip_tool');

                const stepsHtml = filteredTrace.map((step) => {
                    let icon = 'fa-search';
                    let label = '';
                    let description = '';
                    let cssClass = 'reasoning-query';

                    // Format each step based on its type
                    if (step.step === 'query_analysis') {
                        icon = 'fa-brain';
                        label = '1. Query Analysis';
                        description = `Complexity: <strong>${step.complexity || 'N/A'}</strong>, Intent: <strong>${step.intent || 'N/A'}</strong>`;
                        cssClass = 'reasoning-query';
                    } else if (step.step === 'tool_selection') {
                        icon = 'fa-cogs';
                        label = '2. Tool Selection';
                        if (step.tools && step.tools.length > 0) {
                            const toolsList = step.tools.map(t => `<strong>${t.name}</strong>`).join(', ');
                            description = `Selected: ${toolsList}`;
                        } else {
                            description = `Selected tools: ${step.selected_tools || 'N/A'}`;
                        }
                        cssClass = 'reasoning-query';
                    } else if (step.step === 'execution_plan') {
                        icon = 'fa-project-diagram';
                        label = '3. Execution Plan';
                        description = `Strategy: <strong>${step.strategy || 'N/A'}</strong>, Tools: ${step.tool_count || 0}`;
                        cssClass = 'reasoning-query';
                    } else if (step.step === 'execute_tool') {
                        icon = 'fa-play-circle';
                        label = `▶ Execute Tool`;
                        description = `Running <strong>${step.tool || 'unknown'}</strong>`;
                        cssClass = 'reasoning-tool';
                    } else if (step.step === 'tool_success') {
                        icon = 'fa-check-circle';
                        label = `✓ Tool Success`;
                        description = `<strong>${step.tool || 'unknown'}</strong> returned ${step.citations_count || 0} results`;
                        cssClass = 'reasoning-tool';
                    } else if (step.step === 'tool_failure') {
                        icon = 'fa-exclamation-circle';
                        label = `✗ Tool Failed`;
                        description = `<strong>${step.tool || 'unknown'}</strong>: ${step.error || 'Unknown error'}`;
                        cssClass = 'reasoning-tool';
                    } else {
                        // Fallback for any other step types
                        icon = 'fa-info-circle';
                        label = step.step || step.action || 'Unknown';
                        description = JSON.stringify(step).substring(0, 100);
                        cssClass = 'reasoning-query';
                    }

                    return `
                        <div class="reasoning-step ${cssClass}">
                            <div class="step-header">
                                <i class="fas ${icon}"></i>
                                ${label}
                            </div>
                            <div class="step-content">
                                ${description}
                            </div>
                        </div>
                    `;
                }).join('');

                traceDiv.innerHTML = `
                    <summary><i class="fas fa-brain"></i> View Reasoning Process</summary>
                    <div class="reasoning-container">
                        ${stepsHtml}
                    </div>
                `;
                contentDiv.appendChild(metaActionsDiv); // Append container to content
                metaActionsDiv.appendChild(traceDiv); // Append detail to container
            }

            // 3. Evaluation Metrics (Circular)
            if (metadata.evaluation) {
                const evalDiv = document.createElement('details');
                // evalDiv.style.marginTop removed in favor of CSS class

                const metricsHtml = Object.entries(metadata.evaluation)
                    .filter(([k]) => k !== 'total_score' && k !== 'response_time')
                    .map(([k, v]) => {
                        const percent = (v * 100).toFixed(0);
                        const degrees = (v * 360).toFixed(0) + 'deg';

                        return `
                            <div class="metric-circle-container">
                                <div class="metric-circle" style="--degrees: ${degrees}">
                                    <span class="metric-value">${percent}%</span>
                                </div>
                                <span class="metric-label">${k.replace(/_/g, ' ')}</span>
                            </div>
                         `;
                    }).join('');

                evalDiv.innerHTML = `
                    <summary><i class="fas fa-chart-pie"></i> Evaluation Metrics</summary>
                    <div style="display:flex; gap:16px; margin-top:10px; flex-wrap:wrap; justify-content:center;">
                        ${metricsHtml}
                    </div>
                `;

                // Ensure container exists if reasoning wasn't present
                if (!contentDiv.contains(metaActionsDiv)) {
                    contentDiv.appendChild(metaActionsDiv);
                }
                metaActionsDiv.appendChild(evalDiv);
            }

            // 4. Sources (De-duplicated & Hidden Relevance)
            if (metadata.sources && metadata.sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.style.marginTop = '1.5rem';
                sourcesDiv.style.borderTop = '1px solid var(--border-color)';
                sourcesDiv.style.paddingTop = '1rem';

                const sourcesTitle = document.createElement('div');
                sourcesTitle.style.fontWeight = '600';
                sourcesTitle.style.marginBottom = '0.5rem';
                sourcesTitle.innerHTML = '<i class="fas fa-book-open"></i> Sources';
                sourcesDiv.appendChild(sourcesTitle);

                const sourcesGrid = document.createElement('div');
                sourcesGrid.className = 'sources-grid';

                // Deduplicate
                const seenSources = new Set();
                const uniqueSources = [];
                metadata.sources.forEach(source => {
                    const fname = source.document || source.original_filename || 'Unknown Document';
                    if (!seenSources.has(fname)) {
                        seenSources.add(fname);
                        uniqueSources.push(source);
                    }
                });

                uniqueSources.forEach((source) => {
                    let fname = source.document || source.original_filename || 'Unknown Document';

                    const card = document.createElement('div');
                    card.className = 'source-card';
                    card.innerHTML = `
                        <div class="source-header" title="${fname}">
                            <i class="fas fa-file-alt"></i> ${fname}
                        </div>
                        <div class="source-meta">
                             ${source.page ? `<span class="tag tag-secondary">Pg ${source.page}</span>` : ''}
                        </div>
                    `;
                    sourcesGrid.appendChild(card);
                });
                sourcesDiv.appendChild(sourcesGrid);
                contentDiv.appendChild(sourcesDiv);
            }

            // 5. Feedback Form
            const feedbackDiv = document.createElement('div');
            feedbackDiv.style.marginTop = '1rem';
            feedbackDiv.style.display = 'flex';
            feedbackDiv.style.gap = '10px';
            feedbackDiv.style.alignItems = 'center';
            feedbackDiv.innerHTML = `
                <button class="feedback-btn" data-rating="1" style="background:none; border:none; cursor:pointer; font-size:1rem; color:var(--text-secondary); hover:color:var(--text-primary);"><i class="fas fa-thumbs-up"></i></button>
                <button class="feedback-btn" data-rating="0" style="background:none; border:none; cursor:pointer; font-size:1rem; color:var(--text-secondary); hover:color:var(--text-primary);"><i class="fas fa-thumbs-down"></i></button>
            `;

            const btns = feedbackDiv.querySelectorAll('.feedback-btn');
            btns.forEach(btn => {
                btn.addEventListener('click', function() {
                    const rating = this.dataset.rating;
                    submitFeedback(text, metadata.answer, rating);
                    feedbackDiv.innerHTML = '<span style="font-size: 0.8rem; color: var(--primary-color);">Thanks for your feedback!</span>';
                });
            });

            contentDiv.appendChild(feedbackDiv);
        }
    }

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(contentDiv);

    chatMessages.appendChild(msgDiv);

    // Scroll to bottom
    if (chatMessages) {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
}

function addTypingIndicator() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant';

    const avatar = document.createElement('div');
    avatar.className = 'avatar assistant';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = `
        <div class="typing-indicator">
            <span style="color: var(--text-secondary); font-size: 0.9rem; margin-right: 8px;">Thinking</span>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(content);
    chatMessages.appendChild(msgDiv);

    // Scroll to bottom
    if (chatMessages) {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }

    return msgDiv;
}

// --- File Handling ---

function handleFileUpload(e) {
    handleFiles(e);
}

function handleFiles(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    // Clear "no documents" message if it exists
    const noDocsMsg = modalFileList.querySelector('.no-docs-message');
    if (noDocsMsg) {
        noDocsMsg.remove();
    }


    for (let file of files) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showToast(`Skipping ${file.name}: Only PDFs allowed`, 'warning');
            continue;
        }
        addOrUpdateFileInModal(file, 'processing');
        uploadFile(file);
    }

    fileUpload.value = '';
}

function generateFileId(filename) {
    return `file-${filename.replace(/[^a-zA-Z0-9]/g, '-')}`;
}


function addOrUpdateFileInModal(file, status, message = '') {
    const fileId = generateFileId(file.filename || file.name);
    let fileItem = document.getElementById(fileId);

    if (!fileItem) {
        fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.id = fileId;
        modalFileList.appendChild(fileItem);
    }

    let statusHTML = '';
    switch (status) {
        case 'processing':
            statusHTML = `
                <div class="file-status">
                    <i class="fas fa-spinner spinner"></i>
                    <span>Processing...</span>
                </div>
            `;
            break;
        case 'success':
            statusHTML = `
                <div class="file-status success">
                    <i class="fas fa-check-circle"></i>
                    <span>Processed</span>
                </div>
            `;
            break;
        case 'error':
            statusHTML = `
                <div class="file-status error" title="${message}">
                    <i class="fas fa-exclamation-circle"></i>
                    <span>Failed</span>
                </div>
            `;
            break;
    }

    fileItem.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px;">
            <i class="fas fa-file-pdf" style="color: var(--danger-color);"></i>
            <span class="file-name" style="font-weight:500;" title="${file.filename || file.name}">${file.filename || file.name}</span>
        </div>
        ${statusHTML}
    `;
}


async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', new Blob([file], {
        type: 'application/pdf'
    }), file.name);

    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.error) {
            console.error('Upload failed:', data.error);
            addOrUpdateFileInModal(file, 'error', data.error);
        } else {
            console.log('Upload success:', data);
            addOrUpdateFileInModal(file, 'success');
            await updateProcessedFilesList(); // Refresh the main list
        }
    } catch (err) {
        console.error(err);
        addOrUpdateFileInModal(file, 'error', 'Connection error');
    }
}


// Global processed files array to store state
let processedFiles = [];

async function updateProcessedFilesList() {
    try {
        const response = await fetch(`${API_BASE_URL}/files`);
        const data = await response.json();

        if (data.files) {
            processedFiles = data.files;
            docCountEl.textContent = processedFiles.length;
        }

    } catch (err) {
        console.error("Failed to load files", err);
    }
}

function updateModalFileList() {
    modalFileList.innerHTML = '';

    if (processedFiles.length === 0) {
        modalFileList.innerHTML = '<div class="no-docs-message" style="text-align:center; padding: 20px; color: var(--text-secondary);">No documents uploaded yet.</div>';
        return;
    }

    processedFiles.forEach(file => {
        addOrUpdateFileInModal(file, 'success');
    });
}


// Modal Helpers
function openModal(modalId) {
    document.getElementById('modal-overlay').classList.remove('hidden');
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModals() {
    document.getElementById('modal-overlay').classList.add('hidden');
    document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
}
window.closeModals = closeModals; // Expose to global for onclick

async function clearKnowledgeBase() {
    if (!confirm("Are you sure you want to clear the entire Knowledge Base?")) return;

    try {
        await fetch(`${API_BASE_URL}/collection`, {
            method: 'DELETE'
        });
        processedFiles = [];
        docCountEl.textContent = '0';
        updateModalFileList();
        showToast("Knowledge Base cleared.", 'success');
        closeModals();

    } catch (err) {
        console.error(err);
        showToast("Failed to clear knowledge base.", 'error');
    }
}

async function submitFeedback(query, answer, rating) {
    try {
        await fetch(`${API_BASE_URL}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query,
                answer,
                rating,
                session_id: sessionId
            })
        });
        console.log('Feedback submitted');
    } catch (err) {
        console.error('Error submitting feedback', err);
    }
}

async function checkSystemStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        const data = await response.json();
        const embedModelEl = document.getElementById('embed-model');
        const ollamaStatusEl = document.getElementById('ollama-status');

        if (data.collection?.embedding_model && embedModelEl) {
            embedModelEl.textContent = data.collection.embedding_model;
        }
        if (ollamaStatusEl) {
            ollamaStatusEl.textContent = data.ollama_available ? 'Available' : 'Not Detected';
            ollamaStatusEl.style.color = data.ollama_available ? 'var(--primary-color)' : 'var(--danger-color)';
        }

    } catch (err) {
        console.error("System status check failed", err);
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.style.padding = '12px 20px';
    toast.style.borderRadius = '6px';
    toast.style.color = '#fff';
    toast.style.fontSize = '0.9rem';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
    toast.style.display = 'flex';
    toast.style.alignItems = 'center';
    toast.style.gap = '10px';
    toast.style.animation = 'fadeIn 0.3s ease-out';

    const colors = {
        success: '#10a37f',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    toast.style.backgroundColor = colors[type] || colors.info;

    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'times-circle';
    if (type === 'warning') icon = 'exclamation-triangle';

    toast.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Generate Session ID
function generateSessionId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}