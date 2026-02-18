import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { RefreshCw, CheckCircle2, AlertCircle, Clock, TrendingUp, Info } from 'lucide-react'
import { toast } from 'sonner'

import { API_BASE } from '../../config/api'

const resultTypeConfig = {
  paid: { variant: 'default', icon: CheckCircle2, label: 'Paid', color: 'text-green-600 dark:text-green-400' },
  registered: { variant: 'default', icon: CheckCircle2, label: 'Registered', color: 'text-blue-600 dark:text-blue-400' },
  resolved: { variant: 'default', icon: CheckCircle2, label: 'Resolved', color: 'text-blue-600 dark:text-blue-400' },
  escalated: { variant: 'destructive', icon: AlertCircle, label: 'Escalated', color: 'text-orange-600 dark:text-orange-400' },
  reminder_sent: { variant: 'secondary', icon: Clock, label: 'Reminder Sent', color: 'text-purple-600 dark:text-purple-400' },
  no_response: { variant: 'outline', icon: Clock, label: 'No Response', color: 'text-muted-foreground' },
  abandoned: { variant: 'outline', icon: AlertCircle, label: 'Abandoned', color: 'text-muted-foreground' }
}

export default function ResultsTab() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResults()
  }, [])

  const loadResults = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/admin/results?limit=50`, {
        signal: AbortSignal.timeout(10000)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()

      if (data.results) {
        setResults(data.results)
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        toast.error('Request timed out. Please check your connection.')
      } else if (error.message.includes('Failed to fetch') || error.message.includes('ERR_CONNECTION_REFUSED')) {
        toast.error('Unable to connect to server. Please ensure the backend is running.')
      } else {
        toast.error(`Error loading results: ${error.message}`)
      }
    } finally {
      setLoading(false)
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
              <div className="p-2 rounded-lg bg-secondary/10">
                <TrendingUp className="h-5 w-5 text-secondary" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold">Conversation Results</CardTitle>
                <CardDescription className="mt-1">
                  View outcomes and resolutions from conversations
                </CardDescription>
              </div>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadResults} 
              disabled={loading}
              className="h-9 border-2"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading && results.length === 0 ? (
            <div className="text-center py-16 space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent mx-auto" />
              <p className="text-muted-foreground">Loading results...</p>
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-16 space-y-4">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto">
                <TrendingUp className="h-8 w-8 text-muted-foreground" />
              </div>
              <div>
                <p className="font-semibold text-lg">No results yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Results will appear here once conversations are completed
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((result, idx) => {
                const config = resultTypeConfig[result.result_type] || { 
                  variant: 'outline', 
                  icon: Info, 
                  label: result.result_type,
                  color: 'text-muted-foreground'
                }
                const Icon = config.icon

                return (
                  <motion.div
                    key={result.result_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    className="group p-5 rounded-xl border-2 bg-card hover:bg-accent/50 transition-all duration-200 border-l-4 border-l-primary hover:shadow-md"
                  >
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-bold text-base">
                            Conversation: {result.conversation_id.substring(0, 12)}...
                          </h3>
                        </div>
                        {result.phone_number && (
                          <p className="text-sm text-muted-foreground mb-3 flex items-center gap-2">
                            <span className="font-medium">Phone:</span> {result.phone_number}
                          </p>
                        )}
                      </div>
                      <Badge variant={config.variant} className="flex items-center gap-1.5 text-xs h-7 px-3">
                        <Icon className={`h-3.5 w-3.5 ${config.color}`} />
                        {config.label}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                      <Clock className="h-3.5 w-3.5" />
                      <span>{new Date(result.created_at).toLocaleString()}</span>
                    </div>
                    {result.metadata && Object.keys(result.metadata).length > 0 && (
                      <details className="mt-3 group/details">
                        <summary className="text-sm font-medium cursor-pointer text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2 list-none">
                          <Info className="h-4 w-4 group-open/details:rotate-90 transition-transform" />
                          View Details
                        </summary>
                        <div className="mt-3 p-4 rounded-lg bg-muted/50 border border-border">
                          <pre className="text-xs overflow-x-auto">
                            {JSON.stringify(result.metadata, null, 2)}
                          </pre>
                        </div>
                      </details>
                    )}
                  </motion.div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}
