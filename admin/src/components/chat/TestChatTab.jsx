import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Input } from '../ui/input'
import { Button } from '../ui/button'
import { MessageCircle, Send, Bot, User, Sparkles, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { API_BASE } from '../../config/api'
const TEST_PHONE = '+15555551234'

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
]

export default function TestChatTab() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi! I'm here to help with any questions about Oakton Community College. How can I assist you today?" }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef(null)

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE}/api/admin/test-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: TEST_PHONE, message: userMessage }),
        signal: AbortSignal.timeout(30000)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      if (data.response) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
      } else {
        toast.error('Sorry, I encountered an error.')
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        toast.error('Request timed out. Please check your connection and try again.')
      } else if (error.message.includes('Failed to fetch') || error.message.includes('ERR_CONNECTION_REFUSED')) {
        toast.error('Unable to connect to server. Please ensure the backend is running.')
      } else {
        toast.error(`Error: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const sendMessageWithQuestion = async (question) => {
    if (!question.trim() || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: question.trim() }])
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE}/api/admin/test-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: TEST_PHONE, message: question.trim() }),
        signal: AbortSignal.timeout(30000)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      if (data.response) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
      } else {
        toast.error('Sorry, I encountered an error.')
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        toast.error('Request timed out. Please check your connection and try again.')
      } else if (error.message.includes('Failed to fetch') || error.message.includes('ERR_CONNECTION_REFUSED')) {
        toast.error('Unable to connect to server. Please ensure the backend is running.')
      } else {
        toast.error(`Error: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([
      { role: 'assistant', content: "Hi! I'm here to help with any questions about Oakton Community College. How can I assist you today?" }
    ])
    toast.success('Chat cleared')
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="border-2">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <MessageCircle className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold">Test Chat Interface</CardTitle>
                <CardDescription className="mt-1">
                  Test the bot's responses without sending SMS messages
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
        <CardContent className="space-y-6">
          {/* Chat Messages */}
          <div className="border-2 rounded-xl p-6 max-h-[600px] overflow-y-auto bg-gradient-to-b from-muted/30 to-background backdrop-blur-sm">
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
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border-2 border-primary/20">
                        <Bot className="h-5 w-5 text-primary" />
                      </div>
                    )}
                    <motion.div
                      initial={{ scale: 0.9 }}
                      animate={{ scale: 1 }}
                      className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-br from-primary to-primary/90 text-primary-foreground'
                          : 'bg-card border-2 text-card-foreground'
                      }`}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </motion.div>
                    {msg.role === 'user' && (
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border-2 border-primary/20">
                        <User className="h-5 w-5 text-primary" />
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
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border-2 border-primary/20">
                    <Bot className="h-5 w-5 text-primary animate-pulse" />
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
              placeholder="Ask a question..."
              disabled={loading}
              className="flex-1 h-11 text-base border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
            <Button 
              onClick={sendMessage} 
              disabled={loading || !input.trim()}
              className="h-11 px-6 bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 shadow-lg hover:shadow-xl transition-all duration-200"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>

          {/* Sample Questions */}
          <div className="space-y-3 pt-2 border-t">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <label className="text-sm font-semibold">Sample Questions</label>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {sampleQuestions.map((q, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  size="sm"
                  onClick={() => sendMessageWithQuestion(q)}
                  className="justify-start text-left h-auto py-2.5 px-3 text-xs border-2 hover:border-primary/50 hover:bg-primary/5 transition-all duration-200"
                  disabled={loading}
                >
                  {q}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
