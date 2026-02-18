import React, { useState, useEffect } from 'react'
import { Moon, Sun, LogOut, MessageSquare, Sparkles } from 'lucide-react'
import { Button } from '../ui/button'
import { motion } from 'framer-motion'

export default function Header({ onLogout, onToggleTheme }) {
  const [isDark, setIsDark] = useState(() => 
    document.documentElement.classList.contains('dark')
  )
  
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains('dark'))
    })
    
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    })
    
    return () => observer.disconnect()
  }, [])
  
  return (
    <motion.header 
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="relative group overflow-hidden rounded-2xl shadow-2xl mb-8"
    >
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary/90 to-secondary opacity-90 dark:opacity-95" />
      <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-white/20 dark:via-white/5 dark:to-white/10" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.3),transparent_50%)] dark:bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.1),transparent_50%)]" />
      
      {/* Shimmer effect */}
      <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out">
        <div className="w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      </div>
      
      {/* Content */}
      <div className="relative z-10 p-8 md:p-10">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="flex items-center gap-3"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
                <div className="relative p-3 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20">
                  <MessageSquare className="h-6 w-6 md:h-7 md:w-7 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight flex items-center gap-2">
                  SMS Bot Admin
                  <Sparkles className="h-5 w-5 text-white/80 animate-pulse" />
                </h1>
                <p className="text-white/90 text-sm md:text-base font-medium mt-1">
                  Oakton Community College
                </p>
              </div>
            </motion.div>
          </div>
          
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="flex items-center gap-3"
          >
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                onToggleTheme()
                setIsDark(prev => !prev)
              }}
              className="h-10 w-10 bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 text-white hover:text-white transition-all duration-200 hover:scale-110"
              title="Toggle dark mode"
            >
              {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>
            <Button
              variant="ghost"
              onClick={onLogout}
              className="h-10 px-4 bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 text-white hover:text-white transition-all duration-200 hover:scale-105 font-medium"
            >
              <LogOut className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </motion.div>
        </div>
      </div>
    </motion.header>
  )
}
