import '../styles/main.css';

// Get API base URL (adjust for your deployment)
const API_BASE = window.location.origin.replace('/admin', '') || 'http://localhost:8000';

// Prevent multiple initializations
if (window.__DASHBOARD_INITIALIZED__) {
    console.warn('Dashboard already initialized, skipping...');
} else {
    window.__DASHBOARD_INITIALIZED__ = true;

// Dark mode functionality
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.classList.toggle('dark', savedTheme === 'dark');
    updateThemeToggleIcon(savedTheme);
}

function toggleTheme() {
    const isDark = document.documentElement.classList.contains('dark');
    document.documentElement.classList.toggle('dark');
    const newTheme = isDark ? 'light' : 'dark';
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

// Make functions globally available
window.toggleTheme = toggleTheme;

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
        window.location.href = '/admin/login.html';
    }
}

window.logout = logout;

// Check auth status on page load (only once)
let authCheckPerformed = false;

async function checkAuth() {
    if (authCheckPerformed) return;
    authCheckPerformed = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/me`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            const logoutBtn = document.getElementById('logout-btn');
            if (logoutBtn) {
                logoutBtn.classList.remove('hidden');
            }
        } else {
            // Only redirect if we're not already on the login page
            if (!window.location.pathname.includes('login.html')) {
                window.location.href = '/admin/login.html';
            }
        }
    } catch (error) {
        console.error('Auth check error:', error);
        // For development, allow access but hide logout button
        // Don't redirect on network errors to allow local development
    }
}

// Only check auth when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', checkAuth);
} else {
    checkAuth();
}

// Tab switching
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tab = button.getAttribute('data-tab');
        
        // Update buttons
        document.querySelectorAll('.tab-button').forEach(b => {
            b.classList.remove('active', 'border-primary-500', 'text-primary-600', 'dark:text-primary-400');
            b.classList.add('border-transparent');
        });
        button.classList.add('active', 'border-primary-500', 'text-primary-600', 'dark:text-primary-400');
        button.classList.remove('border-transparent');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        const targetTab = document.getElementById(`${tab}-tab`);
        if (targetTab) {
            targetTab.classList.remove('hidden');
            targetTab.classList.add('active');
        }
        
        // Load data when switching tabs
        if (tab === 'conversations') {
            loadConversations();
        } else if (tab === 'results') {
            loadResults();
        }
    });
});

// Manual trigger form
const triggerForm = document.getElementById('trigger-form');
if (triggerForm) {
    triggerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const phoneNumber = document.getElementById('phone-number').value;
        const triggerType = document.getElementById('trigger-type').value;
        const statusDiv = document.getElementById('trigger-status');
        
        statusDiv.className = 'p-4 rounded-lg mb-4';
        statusDiv.textContent = 'Sending...';
        statusDiv.classList.add('bg-blue-50', 'dark:bg-blue-900/20', 'text-blue-700', 'dark:text-blue-400', 'border', 'border-blue-200', 'dark:border-blue-800');
        statusDiv.classList.remove('hidden');
        
        try {
            const response = await fetch(`${API_BASE}/api/admin/trigger`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone_number: phoneNumber, trigger_type: triggerType })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                statusDiv.className = 'p-4 rounded-lg mb-4 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800 animate-slide-in';
                statusDiv.textContent = `Trigger sent! Conversation ID: ${data.conversation_id}`;
                triggerForm.reset();
            } else {
                statusDiv.className = 'p-4 rounded-lg mb-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 animate-slide-in';
                statusDiv.textContent = `Error: ${data.detail || 'Failed to send trigger'}`;
            }
        } catch (error) {
            statusDiv.className = 'p-4 rounded-lg mb-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 animate-slide-in';
            statusDiv.textContent = `Error: ${error.message}`;
        }
    });
}

// CSV upload form
const csvForm = document.getElementById('csv-form');
if (csvForm) {
    csvForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fileInput = document.getElementById('csv-file');
        const triggerType = document.getElementById('csv-trigger-type').value;
        const file = fileInput.files[0];
        const statusDiv = document.getElementById('trigger-status');
        
        if (!file) {
            statusDiv.className = 'p-4 rounded-lg mb-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 animate-slide-in';
            statusDiv.textContent = 'Please select a CSV file';
            statusDiv.classList.remove('hidden');
            return;
        }
        
        statusDiv.className = 'p-4 rounded-lg mb-4 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800';
        statusDiv.textContent = 'Uploading and processing...';
        statusDiv.classList.remove('hidden');
        
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
                statusDiv.className = 'p-4 rounded-lg mb-4 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800 animate-slide-in';
                statusDiv.textContent = `CSV processed! ${data.successful} successful, ${data.failed} failed out of ${data.triggers_created} total.`;
                csvForm.reset();
            } else {
                statusDiv.className = 'p-4 rounded-lg mb-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 animate-slide-in';
                statusDiv.textContent = `Error: ${data.detail || 'Failed to process CSV'}`;
            }
        } catch (error) {
            statusDiv.className = 'p-4 rounded-lg mb-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 animate-slide-in';
            statusDiv.textContent = `Error: ${error.message}`;
        }
    });
}

// Load conversations
async function loadConversations() {
    const listDiv = document.getElementById('conversations-list');
    if (!listDiv) return;
    
    listDiv.innerHTML = '<div class="text-center py-12 text-gray-500 dark:text-gray-400">Loading conversations...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/conversations?limit=50`);
        const data = await response.json();
        
        if (data.conversations && data.conversations.length > 0) {
            listDiv.innerHTML = data.conversations.map(conv => {
                const lastMessage = conv.messages[conv.messages.length - 1];
                const lastMessageText = lastMessage ? 
                    (lastMessage.content.substring(0, 50) + (lastMessage.content.length > 50 ? '...' : '')) : 
                    'No messages';
                
                const statusBadgeClass = conv.status === 'active' 
                    ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400' 
                    : 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400';
                
                return `
                    <div class="p-4 mb-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg border-l-4 border-primary-500 hover:bg-gray-100 dark:hover:bg-slate-700 cursor-pointer transform hover:translate-x-1 transition-all" onclick="viewConversation('${conv.conversation_id}')">
                        <h3 class="font-semibold text-gray-900 dark:text-white mb-2">${conv.phone_number}</h3>
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">${lastMessageText}</p>
                        <div class="flex flex-wrap gap-3 text-xs text-gray-500 dark:text-gray-400">
                            <span>${conv.messages.length} messages</span>
                            <span class="px-2 py-1 rounded ${statusBadgeClass} font-semibold uppercase">${conv.status}</span>
                            ${conv.trigger_type ? `<span>Trigger: ${conv.trigger_type}</span>` : ''}
                            <span>${new Date(conv.updated_at).toLocaleString()}</span>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            listDiv.innerHTML = '<div class="text-center py-12 text-gray-500 dark:text-gray-400">No conversations yet</div>';
        }
    } catch (error) {
        listDiv.innerHTML = `<div class="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800">Error loading conversations: ${error.message}</div>`;
    }
}

window.loadConversations = loadConversations;

// View conversation detail
async function viewConversation(conversationId) {
    const modal = document.getElementById('conversation-modal');
    const detailDiv = document.getElementById('conversation-detail');
    
    if (!modal || !detailDiv) return;
    
    detailDiv.innerHTML = '<div class="text-center py-12 text-gray-500 dark:text-gray-400">Loading conversation...</div>';
    modal.classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/conversations/${conversationId}`);
        const conv = await response.json();
        
        const statusBadgeClass = conv.status === 'active' 
            ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400' 
            : 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400';
        
        detailDiv.innerHTML = `
            <div class="mb-6 space-y-2 pb-6 border-b border-gray-200 dark:border-slate-700">
                <p class="text-gray-700 dark:text-gray-300"><strong>Phone:</strong> ${conv.phone_number}</p>
                <p class="text-gray-700 dark:text-gray-300"><strong>Status:</strong> <span class="px-2 py-1 rounded text-xs font-semibold uppercase ${statusBadgeClass}">${conv.status}</span></p>
                <p class="text-gray-700 dark:text-gray-300"><strong>Created:</strong> ${new Date(conv.created_at).toLocaleString()}</p>
                ${conv.trigger_type ? `<p class="text-gray-700 dark:text-gray-300"><strong>Trigger:</strong> ${conv.trigger_type}</p>` : ''}
            </div>
            <h3 class="text-xl font-bold mb-4 text-gray-900 dark:text-white">Messages</h3>
            <div class="space-y-4">
                ${conv.messages.map(msg => {
                    const isUser = msg.role === 'user';
                    return `
                        <div class="p-4 rounded-lg ${isUser ? 'bg-primary-50 dark:bg-primary-900/20 ml-auto max-w-[80%] border-l-4 border-primary-500' : 'bg-gray-50 dark:bg-slate-700/50 mr-auto max-w-[80%] border-r-4 border-gray-400 dark:border-slate-500'}">
                            <div class="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2 uppercase">${isUser ? '👤 Student' : '🤖 Assistant'}</div>
                            <div class="text-gray-900 dark:text-white whitespace-pre-wrap">${msg.content}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400 mt-2">${new Date(msg.timestamp).toLocaleString()}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } catch (error) {
        detailDiv.innerHTML = `<div class="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800">Error loading conversation: ${error.message}</div>`;
    }
}

window.viewConversation = viewConversation;

// Close conversation modal
function closeConversationModal() {
    const modal = document.getElementById('conversation-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

window.closeConversationModal = closeConversationModal;

// Load results
async function loadResults() {
    const listDiv = document.getElementById('results-list');
    if (!listDiv) return;
    
    listDiv.innerHTML = '<div class="text-center py-12 text-gray-500 dark:text-gray-400">Loading results...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/results?limit=50`);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            listDiv.innerHTML = data.results.map(result => {
                const typeColors = {
                    paid: 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400',
                    registered: 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400',
                    resolved: 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400',
                    escalated: 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400'
                };
                const typeClass = typeColors[result.result_type] || 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
                
                return `
                    <div class="p-4 mb-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg border-l-4 border-green-500">
                        <h3 class="font-semibold text-gray-900 dark:text-white mb-2">Conversation: ${result.conversation_id.substring(0, 8)}...</h3>
                        ${result.phone_number ? `<p class="text-sm text-gray-700 dark:text-gray-300 mb-2"><strong>Phone:</strong> ${result.phone_number}</p>` : ''}
                        <p class="text-sm text-gray-700 dark:text-gray-300 mb-2">
                            <strong>Result Type:</strong> 
                            <span class="px-3 py-1 rounded text-xs font-semibold uppercase ${typeClass} ml-2">${result.result_type}</span>
                        </p>
                        <p class="text-sm text-gray-700 dark:text-gray-300 mb-2"><strong>Time:</strong> ${new Date(result.created_at).toLocaleString()}</p>
                        ${result.metadata && Object.keys(result.metadata).length > 0 ? 
                            `<pre class="text-xs bg-gray-100 dark:bg-slate-800 p-3 rounded mt-2 overflow-x-auto">${JSON.stringify(result.metadata, null, 2)}</pre>` : ''}
                    </div>
                `;
            }).join('');
        } else {
            listDiv.innerHTML = '<div class="text-center py-12 text-gray-500 dark:text-gray-400">No results yet</div>';
        }
    } catch (error) {
        listDiv.innerHTML = `<div class="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800">Error loading results: ${error.message}</div>`;
    }
}

window.loadResults = loadResults;

// Test Chat functionality
let chatHistory = [];
const TEST_PHONE = '+15555551234';

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

function initSampleQuestions() {
    const container = document.getElementById('sample-questions');
    if (!container) return;
    
    container.innerHTML = sampleQuestions.map(q => 
        `<button class="px-4 py-2 text-sm bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-300 dark:hover:bg-slate-600 transition-colors" onclick="askSampleQuestion('${q.replace(/'/g, "\\'")}')">${q}</button>`
    ).join('');
}

window.initSampleQuestions = initSampleQuestions;

function askSampleQuestion(question) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = question;
        sendTestMessage();
    }
}

window.askSampleQuestion = askSampleQuestion;

async function sendTestMessage() {
    const input = document.getElementById('chat-input');
    if (!input) return;
    
    const message = input.value.trim();
    if (!message) return;
    
    addChatMessage('user', message);
    input.value = '';
    
    const loadingId = addChatMessage('assistant', 'Thinking...');
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/test-chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone_number: TEST_PHONE, message: message })
        });
        
        const data = await response.json();
        
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        
        if (data.response) {
            addChatMessage('assistant', data.response);
        } else {
            addChatMessage('assistant', 'Sorry, I encountered an error.');
        }
        
        scrollChatToBottom();
    } catch (error) {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        addChatMessage('assistant', `Error: ${error.message}`);
    }
}

window.sendTestMessage = sendTestMessage;

function addChatMessage(role, text) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    
    const isUser = role === 'user';
    messageDiv.className = `mb-4 p-4 rounded-xl max-w-[80%] animate-fade-in ${
        isUser 
            ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white ml-auto text-right' 
            : 'bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 mr-auto text-left'
    }`;
    
    const roleLabel = isUser ? '👤 You' : '🤖 Bot';
    messageDiv.innerHTML = `
        <div class="text-xs font-semibold mb-2 opacity-90">${roleLabel}</div>
        <div class="whitespace-pre-wrap">${text.replace(/\n/g, '<br>')}</div>
    `;
    
    container.appendChild(messageDiv);
    scrollChatToBottom();
    
    return messageId;
}

function scrollChatToBottom() {
    const container = document.getElementById('chat-container');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

function clearChat() {
    const container = document.getElementById('chat-messages');
    if (container) {
        container.innerHTML = '';
        chatHistory = [];
    }
    addChatMessage('assistant', 'Hi! I\'m here to help with any questions about Oakton Community College. How can I assist you today?');
}

window.clearChat = clearChat;

// Initialize on page load (only once)
let initialized = false;

function initializePage() {
    if (initialized) return;
    initialized = true;
    
    const testTab = document.getElementById('test-tab');
    const conversationsTab = document.getElementById('conversations-tab');
    
    if (testTab && (testTab.classList.contains('active') || !testTab.classList.contains('hidden'))) {
        initSampleQuestions();
        clearChat();
    }
    
    if (conversationsTab && (conversationsTab.classList.contains('active') || !conversationsTab.classList.contains('hidden'))) {
        loadConversations();
    }
}

// Only initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePage);
} else {
    initializePage();
}

} // End of initialization guard
