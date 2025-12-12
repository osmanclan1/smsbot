import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Toaster } from './components/ui/toast'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Input } from './components/ui/input'
import { Button } from './components/ui/button'
import { 
  GraduationCap, 
  Send, 
  Bot, 
  User, 
  LogOut, 
  Moon, 
  Sun, 
  Sparkles,
  MessageCircle,
  Trash2
} from 'lucide-react'
import AuthPage from './AuthPage'

const API_BASE = window.location.origin.replace('/student', '') || 'http://localhost:8000'

// Helper function to check if we're on the login page
const isOnLoginPage = () => {
  const path = window.location.pathname
  return (
    path.includes('login.html') || 
    path.endsWith('/login') || 
    path === '/login' ||
    path === '/student/login' ||
    path.includes('/login')
  )
}

function App() {
  const [authenticated, setAuthenticated] = useState(false)
  const [authChecked, setAuthChecked] = useState(false)
  const [user, setUser] = useState(null)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi! 👋 I'm your Oakton College assistant. I can help you with:\n\n• Registration & enrollment\n• Tuition & payment options\n• Financial aid questions\n• Academic deadlines\n• And much more!\n\nWhat can I help you with today?" }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef(null)
  const checkingAuth = useRef(false)

  // If on login page, render AuthPage directly
  if (isOnLoginPage()) {
    return <AuthPage />
  }

  useEffect(() => {
    initTheme()
    checkAuth()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light'
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
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

  async function checkAuth() {
    if (checkingAuth.current || authChecked) return
    checkingAuth.current = true
    
    try {
      const response = await fetch(`${API_BASE}/api/student/auth/me`, {
        credentials: 'include',
        signal: AbortSignal.timeout(5000)
      })
      
      setAuthChecked(true)
      checkingAuth.current = false
      
      if (response.ok) {
        const data = await response.json()
        setAuthenticated(true)
        setUser(data)
      } else {
        setAuthenticated(false)
        // Redirect to login
        window.location.href = '/student/login.html'
      }
    } catch (error) {
      setAuthChecked(true)
      checkingAuth.current = false
      console.warn('Auth check failed:', error.message)
      // Redirect to login on error
      window.location.href = '/student/login.html'
    }
  }

  async function handleLogout() {
    try {
      await fetch(`${API_BASE}/api/student/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      })
    } catch (error) {
      console.error('Logout error:', error)
    }
    window.location.href = '/student/login.html'
  }

  function scrollToBottom() {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  async function sendMessage() {
    if (!input.trim() || loading) return
    
    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)
    
    try {
      const response = await fetch(`${API_BASE}/api/student/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: userMessage }),
        signal: AbortSignal.timeout(30000)
      })
      
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }
      
      const data = await response.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
      
    } catch (error) {
      console.error('Chat error:', error)
      let errorMessage = 'Sorry, I encountered an error. Please try again.'
      
      if (error.name === 'AbortError') {
        errorMessage = 'Request timed out. Please try again.'
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage = 'Could not connect to the server. Please check your connection.'
      }
      
      setMessages(prev => [...prev, { role: 'assistant', content: errorMessage }])
      toast.error('Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  function clearChat() {
    setMessages([
      { role: 'assistant', content: "Hi! 👋 I'm your Oakton College assistant. What can I help you with today?" }
    ])
    toast.success('Chat cleared')
  }

  // Loading state
  if (!authChecked) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Not authenticated - this shouldn't show as we redirect, but just in case
  if (!authenticated) {
    return <AuthPage />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 transition-colors">
      <Toaster />
      
      {/* Header */}
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden shadow-lg"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary/90 to-secondary opacity-90" />
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-white/20" />
        
        <div className="relative z-10 p-4 md:p-6">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20">
                <GraduationCap className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl md:text-2xl font-bold text-white flex items-center gap-2">
                  Student Assistant
                  <Sparkles className="h-4 w-4 text-white/80 animate-pulse" />
                </h1>
                <p className="text-white/80 text-sm">
                  {user?.name ? `Welcome, ${user.name}` : `Welcome, ${user?.username}`}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                className="h-9 w-9 bg-white/10 hover:bg-white/20 text-white border border-white/20"
              >
                <Sun className="h-4 w-4 hidden dark:block" />
                <Moon className="h-4 w-4 block dark:hidden" />
              </Button>
              <Button
                variant="ghost"
                onClick={handleLogout}
                className="h-9 px-3 bg-white/10 hover:bg-white/20 text-white border border-white/20"
              >
                <LogOut className="h-4 w-4 mr-2" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main Chat Area */}
      <div className="max-w-4xl mx-auto p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-2 shadow-xl">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <MessageCircle className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Chat with AI Assistant</CardTitle>
                    <CardDescription>
                      Ask me anything about Oakton College
                    </CardDescription>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={clearChat}
                  className="h-9 w-9"
                  title="Clear chat"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Messages */}
              <div className="border-2 rounded-xl p-4 h-[500px] overflow-y-auto bg-gradient-to-b from-muted/30 to-background">
                <div className="space-y-4">
                  <AnimatePresence mode="popLayout">
                    {messages.map((msg, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        {msg.role === 'assistant' && (
                          <div className="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border-2 border-primary/20">
                            <Bot className="h-4 w-4 text-primary" />
                          </div>
                        )}
                        <div className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm ${
                          msg.role === 'user' 
                            ? 'bg-gradient-to-br from-primary to-primary/90 text-primary-foreground' 
                            : 'bg-card border-2 text-card-foreground'
                        }`}>
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                        </div>
                        {msg.role === 'user' && (
                          <div className="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border-2 border-primary/20">
                            <User className="h-4 w-4 text-primary" />
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  
                  {loading && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex gap-3 justify-start"
                    >
                      <div className="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border-2 border-primary/20">
                        <Bot className="h-4 w-4 text-primary animate-pulse" />
                      </div>
                      <div className="bg-card border-2 rounded-2xl px-4 py-3 shadow-sm">
                        <div className="flex gap-1.5">
                          <motion.div 
                            className="w-2 h-2 bg-muted-foreground/50 rounded-full"
                            animate={{ y: [0, -8, 0] }}
                            transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                          />
                          <motion.div 
                            className="w-2 h-2 bg-muted-foreground/50 rounded-full"
                            animate={{ y: [0, -8, 0] }}
                            transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                          />
                          <motion.div 
                            className="w-2 h-2 bg-muted-foreground/50 rounded-full"
                            animate={{ y: [0, -8, 0] }}
                            transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                          />
                        </div>
                      </div>
                    </motion.div>
                  )}
                  
                  <div ref={chatEndRef} />
                </div>
              </div>
              
              {/* Input */}
              <div className="flex gap-3">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                  placeholder="Type your question..."
                  disabled={loading}
                  className="flex-1 h-12 text-base border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
                <Button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="h-12 px-6 bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 shadow-lg hover:shadow-xl transition-all duration-200"
                >
                  <Send className="h-5 w-5" />
                </Button>
              </div>
              
              {/* Quick Actions */}
              <div className="flex flex-wrap gap-2 pt-2">
                {[
                  'How do I register for classes?',
                  'What are the payment options?',
                  'When is the drop deadline?',
                  'Financial aid status'
                ].map((question, idx) => (
                  <Button
                    key={idx}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setInput(question)
                    }}
                    className="text-xs border-2 hover:border-primary/50 hover:bg-primary/5"
                    disabled={loading}
                  >
                    {question}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}

export default App
