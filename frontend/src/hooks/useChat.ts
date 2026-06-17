import { useState, useCallback, useRef } from 'react'
import { chatApi } from '../api/client'
import toast from 'react-hot-toast'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  pipelinePath?: string[]
  latencyMs?: number
  queryType?: string
  timestamp: Date
}

export interface Session {
  session_id: string
  title: string
  updated_at: string
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [sessionId, setSessionId] = useState<string | undefined>()
  const [isLoading, setIsLoading] = useState(false)
  const [sessions, setSessions] = useState<Session[]>([])
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || isLoading) return

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)

    try {
      const { data } = await chatApi.query(question, sessionId)
      if (!sessionId) setSessionId(data.session_id)

      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        pipelinePath: data.pipeline_path,
        latencyMs: data.latency_ms,
        queryType: data.query_type,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to get a response. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, sessionId])

  const loadSessions = useCallback(async () => {
    try {
      const { data } = await chatApi.getSessions()
      setSessions(
        data.map((s: any) => ({
          session_id: s.session_id,
          title: s.messages[0]?.content?.slice(0, 40) || 'New Conversation',
          updated_at: s.updated_at,
        }))
      )
    } catch { /* ignore */ }
  }, [])

  const switchSession = useCallback((id: string) => {
    setSessionId(id)
    setMessages([])
  }, [])

  const newSession = useCallback(() => {
    setSessionId(undefined)
    setMessages([])
  }, [])

  const deleteSession = useCallback(async (id: string) => {
    await chatApi.deleteSession(id)
    setSessions((prev) => prev.filter((s) => s.session_id !== id))
    if (id === sessionId) newSession()
  }, [sessionId, newSession])

  return {
    messages, sessionId, isLoading, sessions,
    sendMessage, loadSessions, switchSession, newSession, deleteSession,
  }
}
