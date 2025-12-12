// Get API base URL (adjust for your deployment)
const API_BASE = window.location.origin.replace('/admin', '') || 'http://localhost:8000';

// Dark mode functionality
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeToggleIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeToggleIcon(newTheme);
}

function updateThemeToggleIcon(theme) {
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.textContent = theme === 'dark' ? '☀️' : '🌓';
    }
}

// Initialize theme on load
initTheme();

// Logout functionality
async function logout() {
    try {
        const response = await fetch(`${API_BASE}/api/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok || response.status === 401) {
            window.location.href = '/admin/login.html';
        } else {
            console.error('Logout failed');
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Redirect anyway
        window.location.href = '/admin/login.html';
    }
}

// Check auth status on page load
async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/api/auth/me`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            // Show logout button if authenticated
            const logoutBtn = document.getElementById('logout-btn');
            if (logoutBtn) {
                logoutBtn.style.display = 'block';
            }
        } else {
            // Not authenticated, redirect to login
            window.location.href = '/admin/login.html';
        }
    } catch (error) {
        console.error('Auth check error:', error);
        // For development, allow access but hide logout button
        // In production, redirect to login
        // window.location.href = '/admin/login.html';
    }
}

// Check auth on page load
checkAuth();

// Tab switching
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tab = button.getAttribute('data-tab');
        
        // Update buttons
        document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
        button.classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(`${tab}-tab`).classList.add('active');
        
        // Load data when switching tabs
        if (tab === 'conversations') {
            loadConversations();
        } else if (tab === 'results') {
            loadResults();
        }
    });
});

// Manual trigger form
document.getElementById('trigger-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const phoneNumber = document.getElementById('phone-number').value;
    const triggerType = document.getElementById('trigger-type').value;
    
    const statusDiv = document.getElementById('trigger-status');
    statusDiv.className = 'status-message';
    statusDiv.textContent = 'Sending...';
    statusDiv.classList.add('loading');
    statusDiv.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/trigger`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone_number: phoneNumber,
                trigger_type: triggerType
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            statusDiv.className = 'status-message success';
            statusDiv.textContent = `Trigger sent! Conversation ID: ${data.conversation_id}`;
            document.getElementById('trigger-form').reset();
        } else {
            statusDiv.className = 'status-message error';
            statusDiv.textContent = `Error: ${data.detail || 'Failed to send trigger'}`;
        }
    } catch (error) {
        statusDiv.className = 'status-message error';
        statusDiv.textContent = `Error: ${error.message}`;
    }
});

// CSV upload form
document.getElementById('csv-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('csv-file');
    const triggerType = document.getElementById('csv-trigger-type').value;
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a CSV file');
        return;
    }
    
    const statusDiv = document.getElementById('trigger-status');
    statusDiv.className = 'status-message';
    statusDiv.textContent = 'Uploading and processing...';
    statusDiv.classList.add('loading');
    statusDiv.style.display = 'block';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('trigger_type', triggerType);
        
        const response = await fetch(`${API_BASE}/api/admin/trigger/csv`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            statusDiv.className = 'status-message success';
            statusDiv.textContent = `CSV processed! ${data.successful} successful, ${data.failed} failed out of ${data.triggers_created} total.`;
            document.getElementById('csv-form').reset();
        } else {
            statusDiv.className = 'status-message error';
            statusDiv.textContent = `Error: ${data.detail || 'Failed to process CSV'}`;
        }
    } catch (error) {
        statusDiv.className = 'status-message error';
        statusDiv.textContent = `Error: ${error.message}`;
    }
});

// Load conversations
async function loadConversations() {
    const listDiv = document.getElementById('conversations-list');
    listDiv.innerHTML = '<div class="loading">Loading conversations...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/conversations?limit=50`);
        const data = await response.json();
        
        if (data.conversations && data.conversations.length > 0) {
            listDiv.innerHTML = data.conversations.map(conv => {
                const lastMessage = conv.messages[conv.messages.length - 1];
                const lastMessageText = lastMessage ? 
                    (lastMessage.content.substring(0, 50) + (lastMessage.content.length > 50 ? '...' : '')) : 
                    'No messages';
                
                return `
                    <div class="conversation-item" onclick="viewConversation('${conv.conversation_id}')">
                        <h3>${conv.phone_number}</h3>
                        <p>${lastMessageText}</p>
                        <div class="meta">
                            <span>${conv.messages.length} messages</span>
                            <span class="status-badge ${conv.status}">${conv.status}</span>
                            ${conv.trigger_type ? `<span>Trigger: ${conv.trigger_type}</span>` : ''}
                            <span>${new Date(conv.updated_at).toLocaleString()}</span>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            listDiv.innerHTML = '<div class="empty">No conversations yet</div>';
        }
    } catch (error) {
        listDiv.innerHTML = `<div class="status-message error">Error loading conversations: ${error.message}</div>`;
    }
}

// View conversation detail
async function viewConversation(conversationId) {
    const modal = document.getElementById('conversation-modal');
    const detailDiv = document.getElementById('conversation-detail');
    
    detailDiv.innerHTML = '<div class="loading">Loading conversation...</div>';
    modal.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/conversations/${conversationId}`);
        const conv = await response.json();
        
        detailDiv.innerHTML = `
            <div style="margin-bottom: 20px;">
                <p><strong>Phone:</strong> ${conv.phone_number}</p>
                <p><strong>Status:</strong> <span class="status-badge ${conv.status}">${conv.status}</span></p>
                <p><strong>Created:</strong> ${new Date(conv.created_at).toLocaleString()}</p>
                ${conv.trigger_type ? `<p><strong>Trigger:</strong> ${conv.trigger_type}</p>` : ''}
            </div>
            <h3>Messages</h3>
            ${conv.messages.map(msg => `
                <div class="message ${msg.role}">
                    <div class="role">${msg.role === 'user' ? '👤 Student' : '🤖 Assistant'}</div>
                    <div class="content">${msg.content}</div>
                    <div class="timestamp">${new Date(msg.timestamp).toLocaleString()}</div>
                </div>
            `).join('')}
        `;
    } catch (error) {
        detailDiv.innerHTML = `<div class="status-message error">Error loading conversation: ${error.message}</div>`;
    }
}

// Close conversation modal
function closeConversationModal() {
    document.getElementById('conversation-modal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('conversation-modal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// Load results
async function loadResults() {
    const listDiv = document.getElementById('results-list');
    listDiv.innerHTML = '<div class="loading">Loading results...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/results?limit=50`);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            listDiv.innerHTML = data.results.map(result => {
                return `
                    <div class="result-item">
                        <h3>Conversation: ${result.conversation_id.substring(0, 8)}...</h3>
                        ${result.phone_number ? `<p><strong>Phone:</strong> ${result.phone_number}</p>` : ''}
                        <p><strong>Result Type:</strong> <span class="result-type ${result.result_type}">${result.result_type}</span></p>
                        <p><strong>Time:</strong> ${new Date(result.created_at).toLocaleString()}</p>
                        ${result.metadata && Object.keys(result.metadata).length > 0 ? 
                            `<p><strong>Details:</strong> ${JSON.stringify(result.metadata, null, 2)}</p>` : ''}
                    </div>
                `;
            }).join('');
        } else {
            listDiv.innerHTML = '<div class="empty">No results yet</div>';
        }
    } catch (error) {
        listDiv.innerHTML = `<div class="status-message error">Error loading results: ${error.message}</div>`;
    }
}

// Test Chat functionality
let chatHistory = [];
const TEST_PHONE = '+15555551234';

// Sample questions
const sampleQuestions = [
    "What are my payment options?",
    "How much does tuition cost?",
    "When does registration open?",
    "How do I apply for financial aid?",
    "What is EZ Pay?",
    "When is the payment deadline?",
    "How do I register for classes?",
    "What happens if I don't pay on time?",
    "How do I contact the enrollment center?",
    "What are important dates for fall semester?"
];

// Initialize sample questions buttons
function initSampleQuestions() {
    const container = document.getElementById('sample-questions');
    if (!container) return;
    
    container.innerHTML = sampleQuestions.map(q => 
        `<button class="btn btn-secondary" style="font-size: 0.9em; padding: 8px 12px;" onclick="askSampleQuestion('${q.replace(/'/g, "\\'")}')">${q}</button>`
    ).join('');
}

// Ask a sample question
function askSampleQuestion(question) {
    document.getElementById('chat-input').value = question;
    sendTestMessage();
}

// Send test message
async function sendTestMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage('user', message);
    input.value = '';
    
    // Show loading
    const loadingId = addChatMessage('assistant', 'Thinking...');
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/test-chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone_number: TEST_PHONE,
                message: message
            })
        });
        
        const data = await response.json();
        
        // Remove loading message
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        
        // Add bot response
        if (data.response) {
            addChatMessage('assistant', data.response);
        } else {
            addChatMessage('assistant', 'Sorry, I encountered an error.');
        }
        
        // Scroll to bottom
        scrollChatToBottom();
        
    } catch (error) {
        // Remove loading message
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        
        addChatMessage('assistant', `Error: ${error.message}`);
    }
}

// Add message to chat
function addChatMessage(role, text) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `chat-message ${role}`;
    messageDiv.style.cssText = `
        margin-bottom: 15px;
        padding: 12px;
        border-radius: 8px;
        max-width: 80%;
        ${role === 'user' ? 
            'background: #667eea; color: white; margin-left: auto; text-align: right;' : 
            'background: white; border: 1px solid #ddd;'}
    `;
    
    const roleLabel = role === 'user' ? '👤 You' : '🤖 Bot';
    messageDiv.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 5px; font-size: 0.9em; opacity: 0.9;">${roleLabel}</div>
        <div>${text.replace(/\n/g, '<br>')}</div>
    `;
    
    container.appendChild(messageDiv);
    scrollChatToBottom();
    
    return messageId;
}

// Scroll chat to bottom
function scrollChatToBottom() {
    const container = document.getElementById('chat-container');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// Clear chat
function clearChat() {
    const container = document.getElementById('chat-messages');
    if (container) {
        container.innerHTML = '';
        chatHistory = [];
    }
    
    // Add welcome message
    addChatMessage('assistant', 'Hi! I\'m here to help with any questions about Oakton Community College. How can I assist you today?');
}

// Load conversations on page load if on that tab
if (document.getElementById('conversations-tab').classList.contains('active')) {
    loadConversations();
}

// Initialize test chat if on that tab
if (document.getElementById('test-tab').classList.contains('active')) {
    initSampleQuestions();
    clearChat(); // This will show welcome message
}

// Also initialize when switching to test tab
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tab = button.getAttribute('data-tab');
        if (tab === 'test') {
            initSampleQuestions();
            if (chatHistory.length === 0) {
                clearChat();
            }
        }
    });
});

