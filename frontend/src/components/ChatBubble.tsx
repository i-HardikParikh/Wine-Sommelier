import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { ChevronDown, ChevronUp, Zap } from 'lucide-react'
import { useState } from 'react'
import type { Message } from '../hooks/useChat'

interface Props {
  message: Message
}

const pipelineColors: Record<string, string> = {
  analyze_query:    'text-blue-600 font-semibold',
  vector_search:    'text-purple-600 font-semibold',
  vision_analysis:  'text-pink-600 font-semibold',
  ocr_analysis:     'text-orange-600 font-semibold',
  answer_synthesis: 'text-green-600 font-semibold',
  fallback:         'text-yellow-600 font-semibold',
}

export default function ChatBubble({ message }: Props) {
  const [showMeta, setShowMeta] = useState(false)
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-5`}
    >
      <div className={`max-w-[78%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        {/* Avatar label */}
        <span className="text-xs font-sans text-wine-300 px-1">
          {isUser ? 'You' : '🍷 Sommelier'}
        </span>

        {/* Bubble */}
        <div
          className={`rounded-sm px-5 py-4 ${
            isUser
              ? 'bg-burgundy text-white border border-burgundy/20 shadow-sm'
              : 'bg-white border border-wine-800/80 text-cream shadow-sm'
          }`}
        >
          {isUser ? (
            <p className="font-sans text-sm leading-relaxed">{message.content}</p>
          ) : (
            <div className="font-body text-base leading-relaxed prose prose-sm max-w-none
                            prose-p:my-1.5 prose-headings:font-display prose-headings:text-wine-50
                            prose-strong:text-burgundy prose-em:text-wine-600">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Meta (assistant only) */}
        {!isUser && (message.sources?.length || message.pipelinePath?.length) && (
          <div className="px-1 w-full">
            <button
              onClick={() => setShowMeta(!showMeta)}
              className="flex items-center gap-1 text-wine-200 hover:text-wine-100 text-xs font-sans transition-colors"
            >
              <Zap size={11} />
              {showMeta ? 'Hide' : 'Show'} pipeline
              {showMeta ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
              {message.latencyMs && (
                <span className="ml-2 text-wine-300">{message.latencyMs.toFixed(0)}ms</span>
              )}
            </button>

            {showMeta && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-2 space-y-2"
              >
                {/* Pipeline path */}
                {message.pipelinePath?.length ? (
                  <div className="flex flex-wrap gap-1.5">
                    {message.pipelinePath.map((node, i) => (
                      <span key={i} className={`text-xs font-mono px-2 py-0.5 bg-wine-950 border border-wine-800/40 rounded-sm ${pipelineColors[node] || 'text-cream/50'}`}>
                        {node}
                      </span>
                    ))}
                  </div>
                ) : null}

                {/* Sources */}
                {message.sources?.length ? (
                  <div>
                    <p className="text-wine-200 text-xs font-sans mb-1">Sources:</p>
                    <div className="flex flex-wrap gap-1">
                      {message.sources.map((s, i) => (
                        <span key={i} className="text-xs font-sans px-2 py-0.5 bg-wine-900/40 border border-wine-800/30 text-wine-100 rounded-sm">
                          📄 {s}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
              </motion.div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-wine-300 text-xs px-1 font-sans">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </motion.div>
  )
}
