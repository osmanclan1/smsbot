import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Input } from '../ui/input'
import { Button } from '../ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Send, Upload, Phone, Settings, MessageSquare, PhoneCall } from 'lucide-react'
import { toast } from 'sonner'

import { API_BASE } from '../../config/api'

const triggerOptions = [
  { group: 'Account Issues', options: [
    { value: 'overdue_balance', label: 'Overdue Balance' },
    { value: 'hold_on_account', label: 'Hold on Account' }
  ]},
  { group: 'Payment Reminders', options: [
    { value: 'payment_deadline_7days', label: 'Payment Deadline (7 days)' },
    { value: 'payment_deadline_3days', label: 'Payment Deadline (3 days)' },
    { value: 'payment_deadline_1day', label: 'Payment Deadline (1 day)' }
  ]},
  { group: 'Registration & Classes', options: [
    { value: 'not_registered', label: 'Not Registered' },
    { value: 'registration_opens', label: 'Registration Opens' },
    { value: 'class_starts_soon', label: 'Class Starts Soon' },
    { value: 'drop_deadline_warning', label: 'Drop Deadline Warning' }
  ]},
  { group: 'Financial Aid', options: [
    { value: 'financial_aid_deadline', label: 'Financial Aid Deadline' }
  ]},
  { group: 'Academic Support', options: [
    { value: 'advising_reminder', label: 'Advising Reminder' },
    { value: 'graduation_checklist', label: 'Graduation Checklist' }
  ]},
  { group: 'General', options: [
    { value: 'upcoming_deadline', label: 'Upcoming Deadline (Generic)' }
  ]}
]

export default function TriggerTab() {
  const [phoneNumber, setPhoneNumber] = useState('')
  const [triggerType, setTriggerType] = useState('')
  const [channel, setChannel] = useState('sms')
  const [csvTriggerType, setCsvTriggerType] = useState('')
  const [csvChannel, setCsvChannel] = useState('sms')
  const [loading, setLoading] = useState(false)

  const handleManualTrigger = async (e) => {
    e.preventDefault()
    if (!phoneNumber || !triggerType) {
      toast.error('Please fill in all fields')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/admin/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phoneNumber, trigger_type: triggerType, channel: channel })
      })

      const data = await response.json()

      if (response.ok) {
        if (data.message_sent) {
          if (data.channel === 'voice') {
            toast.success(`✅ Voice call initiated! Conversation ID: ${data.conversation_id}${data.call_id ? ` | Call ID: ${data.call_id.substring(0, 8)}` : ''}`)
          } else {
            toast.success(`✅ SMS sent! Conversation ID: ${data.conversation_id}${data.message_id ? ` | Message ID: ${data.message_id.substring(0, 8)}` : ''}`)
          }
        } else {
          const errorMsg = data.channel === 'voice' ? data.voice_error : data.sms_error
          toast.warning(`⚠️ Trigger created but ${data.channel === 'voice' ? 'voice call' : 'SMS'} failed: ${errorMsg || 'Unknown error'}`)
        }
        setPhoneNumber('')
        setTriggerType('')
        setChannel('sms')
      } else {
        toast.error(data.detail || 'Failed to send trigger')
      }
    } catch (error) {
      toast.error(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleCSVUpload = async (e) => {
    e.preventDefault()
    const fileInput = e.target.querySelector('input[type="file"]')
    const file = fileInput?.files[0]

    if (!file) {
      toast.error('Please select a CSV file')
      return
    }

    if (!csvTriggerType) {
      toast.error('Please select a trigger type')
      return
    }

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('trigger_type', csvTriggerType)
      formData.append('channel', csvChannel)

      const response = await fetch(`${API_BASE}/api/admin/trigger/csv`, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (response.ok) {
        const total = data.triggers_created || 0
        const successful = data.successful || 0
        const failed = data.failed || 0
        const channelLabel = csvChannel === 'voice' ? 'voice calls' : 'SMS'
        if (failed > 0) {
          toast.warning(`CSV processed: ${successful} ${channelLabel} sent, ${failed} failed out of ${total} total.`)
        } else {
          toast.success(`✅ CSV processed! ${successful} ${channelLabel} sent successfully out of ${total} total.`)
        }
        e.target.reset()
        setCsvTriggerType('')
      } else {
        toast.error(data.detail || 'Failed to process CSV')
      }
    } catch (error) {
      toast.error(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Manual Trigger */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="border-2">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Phone className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold">Manual Trigger</CardTitle>
                <CardDescription className="mt-1">
                  Send a trigger message to a single phone number
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleManualTrigger} className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="phone-number" className="text-sm font-semibold flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Phone Number
                  <span className="text-muted-foreground font-normal">(E.164 format)</span>
                </label>
                <Input
                  id="phone-number"
                  type="text"
                  placeholder="+1234567890"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  required
                  className="h-11 border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="trigger-type" className="text-sm font-semibold flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Trigger Type
                </label>
                <Select value={triggerType} onValueChange={setTriggerType} required>
                  <SelectTrigger id="trigger-type" className="h-11 border-2 focus:ring-2 focus:ring-primary/20">
                    <SelectValue placeholder="Select trigger type" />
                  </SelectTrigger>
                  <SelectContent>
                    {triggerOptions.map((group) => (
                      <div key={group.group}>
                        <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground bg-muted/50">
                          {group.group}
                        </div>
                        {group.options.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </div>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label htmlFor="channel" className="text-sm font-semibold flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Channel
                </label>
                <Select value={channel} onValueChange={setChannel}>
                  <SelectTrigger id="channel" className="h-11 border-2 focus:ring-2 focus:ring-primary/20">
                    <SelectValue placeholder="Select channel" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sms">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="h-4 w-4" />
                        SMS
                      </div>
                    </SelectItem>
                    <SelectItem value="voice">
                      <div className="flex items-center gap-2">
                        <PhoneCall className="h-4 w-4" />
                        Voice Call
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button 
                type="submit" 
                disabled={loading} 
                className="w-full h-11 bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 shadow-lg hover:shadow-xl transition-all duration-200"
              >
                {channel === 'voice' ? (
                  <PhoneCall className="h-4 w-4 mr-2" />
                ) : (
                  <Send className="h-4 w-4 mr-2" />
                )}
                {channel === 'voice' ? 'Initiate Call' : 'Send Trigger'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </motion.div>

      {/* CSV Upload */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <Card className="border-2">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-secondary/10">
                <Upload className="h-5 w-5 text-secondary" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold">CSV Upload</CardTitle>
                <CardDescription className="mt-1">
                  Upload a CSV file to trigger multiple conversations at once
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCSVUpload} className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="csv-file" className="text-sm font-semibold flex items-center gap-2">
                  <Upload className="h-4 w-4" />
                  CSV File
                </label>
                <Input
                  id="csv-file"
                  type="file"
                  accept=".csv"
                  required
                  className="h-11 border-2 cursor-pointer file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 transition-all"
                />
                <p className="text-xs text-muted-foreground mt-1.5">
                  Format: phone_number,metadata (JSON optional)
                </p>
              </div>
              <div className="space-y-2">
                <label htmlFor="csv-trigger-type" className="text-sm font-semibold flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Trigger Type
                </label>
                <Select value={csvTriggerType} onValueChange={setCsvTriggerType} required>
                  <SelectTrigger id="csv-trigger-type" className="h-11 border-2 focus:ring-2 focus:ring-primary/20">
                    <SelectValue placeholder="Select trigger type" />
                  </SelectTrigger>
                  <SelectContent>
                    {triggerOptions.map((group) => (
                      <div key={group.group}>
                        <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground bg-muted/50">
                          {group.group}
                        </div>
                        {group.options.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </div>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label htmlFor="csv-channel" className="text-sm font-semibold flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Channel
                </label>
                <Select value={csvChannel} onValueChange={setCsvChannel}>
                  <SelectTrigger id="csv-channel" className="h-11 border-2 focus:ring-2 focus:ring-primary/20">
                    <SelectValue placeholder="Select channel" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sms">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="h-4 w-4" />
                        SMS
                      </div>
                    </SelectItem>
                    <SelectItem value="voice">
                      <div className="flex items-center gap-2">
                        <PhoneCall className="h-4 w-4" />
                        Voice Call
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button 
                type="submit" 
                disabled={loading} 
                className="w-full h-11 bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 shadow-lg hover:shadow-xl transition-all duration-200"
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload & Send
              </Button>
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
