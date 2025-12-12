import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Input } from './components/ui/input'
import { Button } from './components/ui/button'
import { MessageSquare, LogIn, Lock, User as UserIcon } from 'lucide-react'
import { toast } from 'sonner'
import { Toaster } from './components/ui/toast'

const API_BASE = window.location.origin.replace('/admin', '') || 'http://localhost:8000'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
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
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      })

      const data = await response.json()

      if (response.ok) {
        toast.success('Login successful!')
        window.location.href = '/admin/'
      } else {
        toast.error(data.detail || 'Login failed. Please check your credentials.')
      }
    } catch (error) {
      toast.error(`Error: ${error.message}. Please try again.`)
    } finally {
      setLoading(false)
    }
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
                  <MessageSquare className="h-8 w-8 text-primary" />
                </div>
              </div>
            </motion.div>
            <CardTitle className="text-3xl font-bold gradient-text">
              SMS Bot Admin
            </CardTitle>
            <CardDescription className="text-base mt-2">
              Oakton Community College
            </CardDescription>
          </CardHeader>
          <CardContent>
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
                  onKeyPress={(e) => e.key === 'Enter' && handleLogin(e)}
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
            <p className="text-center text-xs text-muted-foreground mt-6 pt-6 border-t">
              Authorized access only
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
