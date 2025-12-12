import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Input } from './components/ui/input'
import { Button } from './components/ui/button'
import { GraduationCap, LogIn, Lock, User as UserIcon, Mail, UserPlus, ArrowLeft } from 'lucide-react'
import { toast } from 'sonner'
import { Toaster } from './components/ui/toast'

const API_BASE = window.location.origin.replace('/student', '') || 'http://localhost:8000'

export default function AuthPage() {
  const [mode, setMode] = useState('login') // 'login' or 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)

  // Initialize theme
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light'
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [])

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE}/api/student/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      })

      const data = await response.json()

      if (response.ok) {
        toast.success('Login successful!')
        window.location.href = '/student/'
      } else {
        toast.error(data.detail || 'Login failed. Please check your credentials.')
      }
    } catch (error) {
      toast.error(`Error: ${error.message}. Please try again.`)
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    
    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }
    
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters')
      return
    }
    
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE}/api/student/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ 
          username, 
          password,
          email: email || undefined,
          name: name || undefined
        })
      })

      const data = await response.json()

      if (response.ok) {
        toast.success('Registration successful! Welcome!')
        window.location.href = '/student/'
      } else {
        toast.error(data.detail || 'Registration failed. Please try again.')
      }
    } catch (error) {
      toast.error(`Error: ${error.message}. Please try again.`)
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setUsername('')
    setPassword('')
    setConfirmPassword('')
    setEmail('')
    setName('')
  }

  const switchMode = (newMode) => {
    resetForm()
    setMode(newMode)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
      <Toaster />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-md"
      >
        <Card className="border-2 shadow-2xl">
          <CardHeader className="space-y-1 text-center pb-6">
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.1 }}
              className="flex justify-center mb-4"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
                <div className="relative p-4 rounded-2xl bg-gradient-to-br from-primary/10 to-secondary/10 border-2 border-primary/20">
                  <GraduationCap className="h-8 w-8 text-primary" />
                </div>
              </div>
            </motion.div>
            <CardTitle className="text-3xl font-bold gradient-text">
              Student Portal
            </CardTitle>
            <CardDescription className="text-base mt-2">
              Oakton Community College
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <AnimatePresence mode="wait">
              {mode === 'login' ? (
                <motion.div
                  key="login"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                >
                  <form onSubmit={handleLogin} className="space-y-5">
                    <div className="space-y-2">
                      <label htmlFor="username" className="text-sm font-semibold flex items-center gap-2">
                        <UserIcon className="h-4 w-4" />
                        Username
                      </label>
                      <Input
                        id="username"
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                        autoFocus
                        autoComplete="username"
                        className="h-11 border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                        placeholder="Enter your username"
                      />
                    </div>
                    <div className="space-y-2">
                      <label htmlFor="password" className="text-sm font-semibold flex items-center gap-2">
                        <Lock className="h-4 w-4" />
                        Password
                      </label>
                      <Input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        autoComplete="current-password"
                        className="h-11 border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                        placeholder="Enter your password"
                      />
                    </div>
                    <Button 
                      type="submit" 
                      className="w-full h-11 bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 shadow-lg hover:shadow-xl transition-all duration-200 font-medium" 
                      disabled={loading}
                    >
                      <LogIn className="h-4 w-4 mr-2" />
                      {loading ? 'Logging in...' : 'Login'}
                    </Button>
                  </form>
                  
                  <div className="mt-6 pt-6 border-t text-center">
                    <p className="text-sm text-muted-foreground mb-3">
                      Don't have an account?
                    </p>
                    <Button 
                      variant="outline" 
                      onClick={() => switchMode('register')}
                      className="w-full h-10 border-2"
                    >
                      <UserPlus className="h-4 w-4 mr-2" />
                      Create Account
                    </Button>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="register"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                      <label htmlFor="reg-username" className="text-sm font-semibold flex items-center gap-2">
                        <UserIcon className="h-4 w-4" />
                        Username *
                      </label>
                      <Input
                        id="reg-username"
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                        autoFocus
                        autoComplete="username"
                        className="h-11 border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                        placeholder="Choose a username"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="reg-name" className="text-sm font-semibold flex items-center gap-2">
                        <UserIcon className="h-4 w-4" />
                        Full Name
                      </label>
                      <Input
                        id="reg-name"
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        autoComplete="name"
                        className="h-11 border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                        placeholder="Your full name (optional)"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="reg-email" className="text-sm font-semibold flex items-center gap-2">
                        <Mail className="h-4 w-4" />
                        Email
                      </label>
                      <Input
                        id="reg-email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="email"
                        className="h-11 border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                        placeholder="Your email (optional)"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="reg-password" className="text-sm font-semibold flex items-center gap-2">
                        <Lock className="h-4 w-4" />
                        Password *
                      </label>
                      <Input
                        id="reg-password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        autoComplete="new-password"
                        className="h-11 border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                        placeholder="Create a password (min 6 chars)"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="reg-confirm" className="text-sm font-semibold flex items-center gap-2">
                        <Lock className="h-4 w-4" />
                        Confirm Password *
                      </label>
                      <Input
                        id="reg-confirm"
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        autoComplete="new-password"
                        className="h-11 border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                        placeholder="Confirm your password"
                      />
                    </div>
                    
                    <Button 
                      type="submit" 
                      className="w-full h-11 bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 shadow-lg hover:shadow-xl transition-all duration-200 font-medium" 
                      disabled={loading}
                    >
                      <UserPlus className="h-4 w-4 mr-2" />
                      {loading ? 'Creating Account...' : 'Create Account'}
                    </Button>
                  </form>
                  
                  <div className="mt-6 pt-6 border-t text-center">
                    <Button 
                      variant="ghost" 
                      onClick={() => switchMode('login')}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Back to Login
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
        
        <p className="text-center text-xs text-muted-foreground mt-4">
          Need help? Contact the Student Services Office
        </p>
      </motion.div>
    </div>
  )
}
