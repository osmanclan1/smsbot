import '../styles/main.css';

const API_BASE = window.location.origin.replace('/admin', '') || 'http://localhost:8000';

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.classList.toggle('dark', savedTheme === 'dark');
}

initTheme();

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error-message');
    const loginButton = document.getElementById('login-button');
    
    errorDiv.classList.add('hidden');
    errorDiv.textContent = '';
    
    loginButton.disabled = true;
    loginButton.textContent = 'Logging in...';
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            window.location.href = '/admin/';
        } else {
            errorDiv.textContent = data.detail || 'Login failed. Please check your credentials.';
            errorDiv.classList.remove('hidden');
            loginButton.disabled = false;
            loginButton.textContent = 'Login';
        }
    } catch (error) {
        errorDiv.textContent = `Error: ${error.message}. Please try again.`;
        errorDiv.classList.remove('hidden');
        loginButton.disabled = false;
        loginButton.textContent = 'Login';
    }
}

window.handleLogin = handleLogin;
