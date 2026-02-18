import { Tabs, TabsList, TabsTrigger } from '../ui/tabs'
import { MessageSquare, Send, MessageCircle, BarChart3 } from 'lucide-react'
import { motion } from 'framer-motion'

const tabIcons = {
  test: MessageSquare,
  trigger: Send,
  conversations: MessageCircle,
  results: BarChart3
}

export default function Navigation({ activeTab, onTabChange }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
      className="mb-8"
    >
      <Tabs value={activeTab} onValueChange={onTabChange} className="w-full">
        <TabsList className="inline-flex h-12 items-center justify-start rounded-xl bg-muted/50 p-1.5 w-full border border-border/50 shadow-sm">
          {[
            { value: 'test', label: 'Test Chat', icon: MessageSquare },
            { value: 'trigger', label: 'Trigger', icon: Send },
            { value: 'conversations', label: 'Conversations', icon: MessageCircle },
            { value: 'results', label: 'Results', icon: BarChart3 }
          ].map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.value
            
            return (
              <TabsTrigger
                key={tab.value}
                value={tab.value}
                className={`
                  relative flex-1 h-full px-4 md:px-6 rounded-lg font-medium text-sm transition-all duration-200
                  data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-md
                  data-[state=inactive]:text-muted-foreground hover:text-foreground
                  hover:data-[state=inactive]:bg-background/50
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
                  ${isActive ? 'scale-[1.02]' : ''}
                `}
              >
                <div className="flex items-center justify-center gap-2">
                  <Icon className={`h-4 w-4 transition-transform duration-200 ${isActive ? 'scale-110' : ''}`} />
                  <span className="hidden sm:inline">{tab.label}</span>
                </div>
              </TabsTrigger>
            )
          })}
        </TabsList>
      </Tabs>
    </motion.div>
  )
}
