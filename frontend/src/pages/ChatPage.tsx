import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Wine } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import ChatBubble from '../components/ChatBubble'
import MessageInput from '../components/MessageInput'
import { useChat } from '../hooks/useChat'

export default function ChatPage() {
  const { messages, isLoading, sendMessage } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="border-b border-wine-800/30 px-6 py-4 flex items-center justify-between bg-wine-950/40 backdrop-blur-sm">
          <div>
            <h1 className="font-display text-xl text-cream">Your Personal Sommelier</h1>
            <p className="font-body italic text-wine-400 text-sm">Ask anything about wine</p>
          </div>
          <div className="flex items-center gap-2 text-wine-600 text-xs font-sans">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            Connected
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="h-full flex flex-col items-center justify-center text-center"
            >
              <div className="text-6xl mb-4 opacity-30">🍷</div>
              <h2 className="font-display text-2xl text-cream/40 mb-2">Welcome to your cellar</h2>
              <p className="font-body italic text-wine-600 max-w-sm">
                Ask me about wine pairings, recommendations, regions, varietals, or anything else
                in the wonderful world of wine.
              </p>
            </motion.div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <ChatBubble key={msg.id} message={msg} />
            ))}
          </AnimatePresence>

          {/* Typing indicator */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 text-wine-500 text-sm font-sans mb-4"
            >
              <div className="flex gap-1">
                {[0, 0.15, 0.3].map((delay, i) => (
                  <motion.div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-gold/50"
                    animate={{ y: [0, -4, 0] }}
                    transition={{ repeat: Infinity, duration: 0.8, delay }}
                  />
                ))}
              </div>
              Your sommelier is thinking…
            </motion.div>
          )}

          <div ref={bottomRef} />
        </div>

        <MessageInput onSend={sendMessage} isLoading={isLoading} />
      </div>
    </div>
  )
}
