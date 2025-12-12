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

const API_BASE = window.location.origin.replace('/admin', '') || 'http://localhost:8000'

// DEV MODE: Bypass authentication for development
const DEV_MODE = true // Set to false in production

function App() {
  const [activeTab, setActiveTab] = useState('test')
  const [authenticated, setAuthenticated] = useState(DEV_MODE) // Auto-authenticate in dev
  const [authChecked, setAuthChecked] = useState(DEV_MODE) // Skip check in dev
  const checkingAuth = useRef(false)

  useEffect(() => {
    initTheme()
    
    // In dev mode, skip all auth checks
    if (DEV_MODE) {
      console.log('[DEV MODE] Authentication bypassed')
      return
    }
    
    // Skip auth check if we're on the login page
    if (!window.location.pathname.includes('login.html')) {
      checkAuth()
    } else {
      setAuthChecked(true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Redirect to login if not authenticated after check
  useEffect(() => {
    // Skip redirect in dev mode
    if (DEV_MODE) return
    
    if (authChecked && !authenticated && !window.location.pathname.includes('login.html')) {
      window.location.replace('/admin/login.html')
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
        setAuthenticated(true)
      } else {
        // Not authenticated - the useEffect will handle redirect
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
      if (!window.location.pathname.includes('login.html')) {
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
        window.location.href = '/admin/login.html'
      }
    } catch (error) {
      console.error('Logout error:', error)
      window.location.href = '/admin/login.html'
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
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">Not authenticated.</p>
          <p className="text-sm text-muted-foreground">Redirecting to login...</p>
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
