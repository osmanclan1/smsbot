import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog'
import { RefreshCw, MessageCircle, Bot, User, Phone, Clock, FileText } from 'lucide-react'
import { toast } from 'sonner'

import { API_BASE } from '../../config/api'

export default function ConversationsTab() {
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/admin/conversations?limit=50`, {
        signal: AbortSignal.timeout(10000)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()

      if (data.conversations) {
        setConversations(data.conversations)
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        toast.error('Request timed out. Please check your connection.')
      } else if (error.message.includes('Failed to fetch') || error.message.includes('ERR_CONNECTION_REFUSED')) {
        toast.error('Unable to connect to server. Please ensure the backend is running.')
      } else {
        toast.error(`Error loading conversations: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const viewConversation = async (conversationId) => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/conversations/${conversationId}`, {
        signal: AbortSignal.timeout(10000)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const conv = await response.json()
      setSelectedConversation(conv)
      setDialogOpen(true)
    } catch (error) {
      if (error.name === 'AbortError') {
        toast.error('Request timed out. Please check your connection.')
      } else if (error.message.includes('Failed to fetch') || error.message.includes('ERR_CONNECTION_REFUSED')) {
        toast.error('Unable to connect to server. Please ensure the backend is running.')
      } else {
        toast.error(`Error loading conversation: ${error.message}`)
      }
    }
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
                <CardTitle className="text-xl font-bold">Recent Conversations</CardTitle>
                <CardDescription className="mt-1">
                  View and manage conversation history
                </CardDescription>
              </div>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadConversations} 
              disabled={loading}
              className="h-9 border-2"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading && conversations.length === 0 ? (
            <div className="text-center py-16 space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent mx-auto" />
              <p className="text-muted-foreground">Loading conversations...</p>
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-16 space-y-4">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto">
                <MessageCircle className="h-8 w-8 text-muted-foreground" />
              </div>
              <div>
                <p className="font-semibold text-lg">No conversations yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Conversations will appear here once they're created
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {conversations.map((conv, idx) => {
                const lastMessage = conv.messages[conv.messages.length - 1]
                const lastMessageText = lastMessage
                  ? (lastMessage.content.substring(0, 80) + (lastMessage.content.length > 80 ? '...' : ''))
                  : 'No messages'

                return (
                  <motion.div
                    key={conv.conversation_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    onClick={() => viewConversation(conv.conversation_id)}
                    className="group p-5 rounded-xl border-2 bg-card hover:bg-accent/50 cursor-pointer transition-all duration-200 border-l-4 border-l-primary hover:shadow-md hover:scale-[1.01]"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="flex-shrink-0 p-2 rounded-lg bg-primary/10">
                            <Phone className="h-4 w-4 text-primary" />
                          </div>
                          <h3 className="font-bold text-base truncate">{conv.phone_number}</h3>
                        </div>
                        <p className="text-sm text-muted-foreground mb-4 line-clamp-2 leading-relaxed">
                          {lastMessageText}
                        </p>
                        <div className="flex flex-wrap items-center gap-3 text-xs">
                          <Badge variant={conv.status === 'active' ? 'default' : 'secondary'} className="text-xs">
                            {conv.status}
                          </Badge>
                          <div className="flex items-center gap-1.5 text-muted-foreground">
                            <FileText className="h-3.5 w-3.5" />
                            <span>{conv.messages.length} messages</span>
                          </div>
                          {conv.trigger_type && (
                            <div className="px-2 py-1 rounded-md bg-muted text-muted-foreground">
                              {conv.trigger_type.replace(/_/g, ' ')}
                            </div>
                          )}
                          <div className="flex items-center gap-1.5 text-muted-foreground ml-auto">
                            <Clock className="h-3.5 w-3.5" />
                            <span>{new Date(conv.updated_at).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader className="pb-4 border-b">
            <DialogTitle className="text-xl font-bold flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Conversation Transcript
            </DialogTitle>
            {selectedConversation && (
              <DialogDescription className="pt-2 space-y-2">
                <div className="flex flex-wrap gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    <span className="font-medium">{selectedConversation.phone_number}</span>
                  </div>
                  <Badge variant={selectedConversation.status === 'active' ? 'default' : 'secondary'}>
                    {selectedConversation.status}
                  </Badge>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    <span>{new Date(selectedConversation.created_at).toLocaleString()}</span>
                  </div>
                  {selectedConversation.trigger_type && (
                    <div className="px-2 py-1 rounded-md bg-muted text-muted-foreground text-xs">
                      Trigger: {selectedConversation.trigger_type}
                    </div>
                  )}
                </div>
              </DialogDescription>
            )}
          </DialogHeader>
          <div className="flex-1 overflow-y-auto p-6 space-y-4 mt-4">
            {selectedConversation?.messages.map((msg, idx) => {
              const isUser = msg.role === 'user'
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: isUser ? 20 : -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {!isUser && (
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border-2 border-primary/20">
                      <Bot className="h-5 w-5 text-primary" />
                    </div>
                  )}
                  <div className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm ${
                    isUser
                      ? 'bg-gradient-to-br from-primary to-primary/90 text-primary-foreground'
                      : 'bg-card border-2 text-card-foreground'
                  }`}>
                    <div className="text-xs font-semibold mb-1.5 opacity-70 flex items-center gap-1.5">
                      {isUser ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
                      {isUser ? 'Student' : 'Assistant'}
                    </div>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    <p className="text-xs opacity-60 mt-2">
                      {new Date(msg.timestamp).toLocaleString()}
                    </p>
                  </div>
                  {isUser && (
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border-2 border-primary/20">
                      <User className="h-5 w-5 text-primary" />
                    </div>
                  )}
                </motion.div>
              )
            })}
          </div>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}
