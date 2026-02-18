import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Toaster } from './components/ui/toast'
import { toast } from 'sonner'
import Header from './components/layout/Header'
import Navigation from './components/layout/Navigation'
import TestChatTab from './components/chat/TestChatTab'
import TriggerTab from './components/forms/TriggerTab'
import ConversationsTab from './components/conversations/ConversationsTab'
import ResultsTab from './components/conversations/ResultsTab'
import LoginPage from './LoginPage'
import { API_BASE } from './config/api'

// Helper function to check if we're on the login page
const isOnLoginPage = () => {
  const path = window.location.pathname
  return (
    path.includes('login.html') || 
    path.endsWith('/login') || 
    path === '/login' ||
    path === '/admin/login' ||
    path === '/admin/login/' ||
    path.includes('/login')
  )
}

// Helper function to get the correct login path
const getLoginPath = () => {
  const path = window.location.pathname
  const origin = window.location.origin
  const port = window.location.port
  
  // If deployed on Amplify, use simple paths
  if (origin.includes('amplifyapp.com')) {
    return '/login.html'
  }
  
  // In Vite dev (port 3000), paths work differently
  if (port === '3000' || origin.includes(':3000')) {
    // Vite dev server - use simple path
    return '/admin/login.html'
  }
  
  // Production or FastAPI served - use relative path
  if (path.includes('/admin') || path.startsWith('/admin')) {
    return '/admin/login.html'
  }
  
  // Default
  return '/login.html'
}

function App() {
  const [activeTab, setActiveTab] = useState('test')
  const [authenticated, setAuthenticated] = useState(false)
  const [authChecked, setAuthChecked] = useState(false)
  const checkingAuth = useRef(false)
  const redirectAttempted = useRef(false)

  // If on login page, render LoginPage component directly
  // This handles the case where Vite serves index.html for all routes in dev mode
  if (isOnLoginPage()) {
    return <LoginPage />
  }

  useEffect(() => {
    initTheme()
    
    // Check auth for main dashboard
    checkAuth()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Redirect to login if not authenticated after check
  useEffect(() => {
    if (authChecked && !authenticated && !redirectAttempted.current) {
      const currentPath = window.location.pathname
      
      console.log('[Auth] Not authenticated, redirecting to login...', { 
        authChecked, 
        authenticated, 
        currentPath
      })
      
      redirectAttempted.current = true
      // For Amplify, use simple paths
      const isAmplify = window.location.origin.includes('amplifyapp.com')
      const loginPath = isAmplify ? '/login.html' : getLoginPath()
      
      // Immediate redirect
      try {
        window.location.replace(loginPath)
        console.log('[Auth] Redirected to:', loginPath)
      } catch (error) {
        console.error('[Auth] Redirect failed:', error)
        window.location.href = loginPath
      }
    }
  }, [authChecked, authenticated])

  function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light'
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  async function checkAuth() {
    // Prevent multiple simultaneous checks using ref
    if (checkingAuth.current || authChecked) return
    checkingAuth.current = true
    
    try {
      const response = await fetch(`${API_BASE}/api/auth/me`, {
        credentials: 'include',
        signal: AbortSignal.timeout(5000) // 5 second timeout
      })
      
      setAuthChecked(true)
      checkingAuth.current = false
      
      if (response.ok) {
        console.log('[Auth] Authentication successful')
        setAuthenticated(true)
      } else {
        // Not authenticated - set to false, redirect will happen via useEffect
        console.log('[Auth] Not authenticated, response status:', response.status, 'Will redirect...')
        setAuthenticated(false)
      }
    } catch (error) {
      // If backend is not available, show a message instead of infinite retries
      setAuthChecked(true)
      checkingAuth.current = false
      
      // Only log error, don't spam console
      if (error.name !== 'AbortError') {
        console.warn('Backend server not available. Running in offline mode.')
      }
      
      // For development: allow access even if backend is down, but show warning
      setAuthenticated(true) // Temporarily allow access for testing
      
      // Only show error toast once if we're not already on login page
      if (!isOnLoginPage()) {
        // Show user-friendly error but don't spam toasts
        setTimeout(() => {
          toast.error('Running in offline mode. Some features may not work. Please ensure the backend is running for full functionality.', {
            duration: 8000,
          })
        }, 500)
      }
    }
  }

  async function handleLogout() {
    try {
      const response = await fetch(`${API_BASE}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      })
      
      if (response.ok || response.status === 401) {
        const isAmplify = window.location.origin.includes('amplifyapp.com')
        const loginPath = isAmplify ? '/login.html' : getLoginPath()
        window.location.href = loginPath
      }
    } catch (error) {
      console.error('Logout error:', error)
      const isAmplify = window.location.origin.includes('amplifyapp.com')
      const loginPath = isAmplify ? '/login.html' : getLoginPath()
      window.location.href = loginPath
    }
  }

  function toggleTheme() {
    const isDark = document.documentElement.classList.contains('dark')
    if (isDark) {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    } else {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    }
  }

  if (!authChecked) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Checking authentication...</p>
        </div>
      </div>
    )
  }

  if (!authenticated && authChecked) {
    const isAmplify = window.location.origin.includes('amplifyapp.com')
    const loginPath = isAmplify ? '/login.html' : getLoginPath()
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4 max-w-md">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-4"
          >
            <p className="text-muted-foreground mb-2 text-lg font-medium">Not authenticated.</p>
            <p className="text-sm text-muted-foreground mb-4">
              Redirecting to login...
            </p>
            <a 
              href={loginPath}
              className="text-primary hover:underline inline-block px-4 py-2 border border-primary rounded-md hover:bg-primary/10 transition-colors"
              onClick={(e) => {
                e.preventDefault()
                window.location.href = loginPath
              }}
            >
              Click here if you're not redirected automatically
            </a>
          </motion.div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 transition-colors">
      <Toaster />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
        <Header onLogout={handleLogout} onToggleTheme={toggleTheme} />
        <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
        
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'test' && <TestChatTab />}
          {activeTab === 'trigger' && <TriggerTab />}
          {activeTab === 'conversations' && <ConversationsTab />}
          {activeTab === 'results' && <ResultsTab />}
        </motion.div>
      </div>
    </div>
  )
}

export default App
