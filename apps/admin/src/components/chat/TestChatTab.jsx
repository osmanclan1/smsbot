import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Input } from '../ui/input'
import { Button } from '../ui/button'
import { MessageCircle, Send, Bot, User, Sparkles, Trash2, Phone, AlertTriangle } from 'lucide-react'
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
  const [sendAsSMS, setSendAsSMS] = useState(false)
  const [phoneNumber, setPhoneNumber] = useState('')
  const chatEndRef = useRef(null)

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    // Validate phone number if sending as SMS
    if (sendAsSMS) {
      const phone = phoneNumber.trim() || TEST_PHONE
      if (!phone || (!phone.startsWith('+') && phone.length < 10)) {
        toast.error('Please enter a valid phone number (E.164 format: +1234567890)')
        return
      }
    }

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    
    if (sendAsSMS) {
      setMessages(prev => [...prev, { 
        role: 'system', 
        content: `📤 Sending SMS to ${phoneNumber.trim() || TEST_PHONE}...`,
        isSystem: true 
      }])
    }
    
    setLoading(true)

    try {
      let response, data
      
      if (sendAsSMS) {
        // Send real SMS
        const phone = phoneNumber.trim() || TEST_PHONE
        response = await fetch(`${API_BASE}/api/admin/send-sms`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            phone_number: phone, 
            message: userMessage,
            process_response: true  // Get AI response and send it back
          }),
          signal: AbortSignal.timeout(30000)
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        data = await response.json()

        if (data.success) {
          setMessages(prev => {
            const updated = prev.slice(0, -1) // Remove "Sending..." message
            updated.push({ 
              role: 'system', 
              content: `✅ SMS sent! Message ID: ${data.message_id?.substring(0, 8) || 'N/A'}`,
              isSystem: true 
            })
            if (data.response_text) {
              updated.push({ role: 'assistant', content: data.response_text })
            }
            return updated
          })
          toast.success('SMS sent successfully!')
        } else {
          setMessages(prev => {
            const updated = prev.slice(0, -1)
            updated.push({ 
              role: 'system', 
              content: `❌ Failed to send SMS: ${data.error || 'Unknown error'}`,
              isSystem: true 
            })
            return updated
          })
          toast.error(`SMS failed: ${data.error || 'Unknown error'}`)
        }
      } else {
        // Simulate conversation (existing behavior)
        response = await fetch(`${API_BASE}/api/admin/test-chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone_number: TEST_PHONE, message: userMessage }),
          signal: AbortSignal.timeout(30000)
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        data = await response.json()

        if (data.response) {
          setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
        } else {
          toast.error('Sorry, I encountered an error.')
        }
      }
    } catch (error) {
      if (sendAsSMS) {
        setMessages(prev => {
          const updated = prev.slice(0, -1)
          updated.push({ 
            role: 'system', 
            content: `❌ Error: ${error.message}`,
            isSystem: true 
          })
          return updated
        })
      }
      
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

    // Validate phone number if sending as SMS
    if (sendAsSMS) {
      const phone = phoneNumber.trim() || TEST_PHONE
      if (!phone || (!phone.startsWith('+') && phone.length < 10)) {
        toast.error('Please enter a valid phone number (E.164 format: +1234567890)')
        return
      }
    }

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: question.trim() }])
    
    if (sendAsSMS) {
      setMessages(prev => [...prev, { 
        role: 'system', 
        content: `📤 Sending SMS to ${phoneNumber.trim() || TEST_PHONE}...`,
        isSystem: true 
      }])
    }
    
    setLoading(true)

    try {
      let response, data
      
      if (sendAsSMS) {
        const phone = phoneNumber.trim() || TEST_PHONE
        response = await fetch(`${API_BASE}/api/admin/send-sms`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            phone_number: phone, 
            message: question.trim(),
            process_response: true
          }),
          signal: AbortSignal.timeout(30000)
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        data = await response.json()

        if (data.success) {
          setMessages(prev => {
            const updated = prev.slice(0, -1)
            updated.push({ 
              role: 'system', 
              content: `✅ SMS sent! Message ID: ${data.message_id?.substring(0, 8) || 'N/A'}`,
              isSystem: true 
            })
            if (data.response_text) {
              updated.push({ role: 'assistant', content: data.response_text })
            }
            return updated
          })
          toast.success('SMS sent successfully!')
        } else {
          setMessages(prev => {
            const updated = prev.slice(0, -1)
            updated.push({ 
              role: 'system', 
              content: `❌ Failed to send SMS: ${data.error || 'Unknown error'}`,
              isSystem: true 
            })
            return updated
          })
          toast.error(`SMS failed: ${data.error || 'Unknown error'}`)
        }
      } else {
        response = await fetch(`${API_BASE}/api/admin/test-chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone_number: TEST_PHONE, message: question.trim() }),
          signal: AbortSignal.timeout(30000)
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        data = await response.json()

        if (data.response) {
          setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
        } else {
          toast.error('Sorry, I encountered an error.')
        }
      }
    } catch (error) {
      if (sendAsSMS) {
        setMessages(prev => {
          const updated = prev.slice(0, -1)
          updated.push({ 
            role: 'system', 
            content: `❌ Error: ${error.message}`,
            isSystem: true 
          })
          return updated
        })
      }
      
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
                  {sendAsSMS 
                    ? '⚠️ Real SMS mode - messages will be sent to actual phone numbers'
                    : 'Test the bot\'s responses without sending SMS messages'}
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
                          : msg.isSystem
                          ? 'bg-muted/50 border-2 border-muted text-muted-foreground'
                          : 'bg-card border-2 text-card-foreground'
                      }`}
                    >
                      <p className={`text-sm leading-relaxed whitespace-pre-wrap ${msg.isSystem ? 'font-mono' : ''}`}>
                        {msg.content}
                      </p>
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

          {/* SMS Settings */}
          <div className="space-y-3 p-4 bg-muted/30 rounded-lg border-2">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="send-as-sms"
                checked={sendAsSMS}
                onChange={(e) => {
                  setSendAsSMS(e.target.checked)
                  if (e.target.checked) {
                    toast.warning('Real SMS mode enabled - messages will be sent to actual phone numbers!', {
                      duration: 5000
                    })
                  }
                }}
                className="w-4 h-4 rounded border-2 border-primary text-primary focus:ring-2 focus:ring-primary/20"
              />
              <label htmlFor="send-as-sms" className="text-sm font-semibold cursor-pointer flex items-center gap-2">
                <Phone className="h-4 w-4" />
                Send as real SMS
              </label>
            </div>
            {sendAsSMS && (
              <div className="space-y-2 pl-7">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <AlertTriangle className="h-3 w-3" />
                  <span>Messages will be sent to the phone number below</span>
                </div>
                <Input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="Phone number (E.164: +1234567890)"
                  className="h-9 text-sm border-2"
                />
                {!phoneNumber.trim() && (
                  <p className="text-xs text-muted-foreground pl-1">
                    Will use test number: {TEST_PHONE}
                  </p>
                )}
              </div>
            )}
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
