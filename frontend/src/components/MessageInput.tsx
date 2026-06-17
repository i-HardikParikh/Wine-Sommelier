import { useState, useRef, KeyboardEvent } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2 } from 'lucide-react'

interface Props {
  onSend: (message: string) => void
  isLoading: boolean
  disabled?: boolean
}

const SUGGESTIONS = [
  'What wine pairs with a truffle risotto?',
  'Recommend a bold red under $30.',
  'What is the difference between Barolo and Barbaresco?',
  'Best Champagnes for a celebration?',
]

export default function MessageInput({ onSend, isLoading, disabled }: Props) {
  const [value, setValue] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    if (!value.trim() || isLoading) return
    onSend(value.trim())
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }

  const useSuggestion = (s: string) => {
    setValue(s)
    setShowSuggestions(false)
    textareaRef.current?.focus()
  }

  return (
    <div className="border-t border-wine-800/30 bg-wine-950/60 backdrop-blur-sm px-4 py-4">
      {/* Suggestions */}
      <AnimatePresence>
        {showSuggestions && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="flex flex-wrap gap-2 mb-3"
          >
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                onClick={() => useSuggestion(s)}
                className="text-xs font-sans px-3 py-1.5 rounded-sm border border-wine-700/40
                           text-wine-400 hover:text-gold hover:border-gold/40 transition-all duration-150"
              >
                {s}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input row */}
      <div className="flex items-end gap-3">
        <button
          onClick={() => setShowSuggestions(!showSuggestions)}
          className="text-wine-600 hover:text-wine-400 text-xs font-sans pb-3 transition-colors whitespace-nowrap"
        >
          💡 Ideas
        </button>

        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="Ask your sommelier anything about wine…"
            rows={1}
            disabled={disabled || isLoading}
            className="input-field resize-none pr-12 font-body text-base leading-relaxed"
            style={{ minHeight: '48px' }}
          />
          <button
            onClick={handleSend}
            disabled={!value.trim() || isLoading}
            className="absolute right-3 bottom-3 text-wine-500 hover:text-gold disabled:opacity-30
                       transition-colors duration-150"
          >
            {isLoading
              ? <Loader2 size={18} className="animate-spin" />
              : <Send size={18} />}
          </button>
        </div>
      </div>

      <p className="text-wine-700 text-xs font-sans text-center mt-2">
        Press Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}
