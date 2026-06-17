import { useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Trash2, Upload, FlaskConical, LogOut, Wine } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useChat } from '../hooks/useChat'
import { ingestApi } from '../api/client'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'

export default function Sidebar() {
  const { user, logout } = useAuth()
  const { sessions, sessionId, loadSessions, switchSession, newSession, deleteSession } = useChat()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => { loadSessions() }, [loadSessions])

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0]
    if (!file) return
    const toastId = toast.loading(`Indexing ${file.name}…`)
    try {
      const { data } = await ingestApi.uploadDocument(file)
      toast.success(`✓ ${data.chunks_indexed} chunks indexed from ${file.name}`, { id: toastId })
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Upload failed.', { id: toastId })
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'] },
    maxFiles: 1,
  })

  return (
    <aside className="w-64 flex flex-col h-full bg-wine-950/80 border-r border-wine-800/40 backdrop-blur-md">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-wine-800/30">
        <div className="flex items-center gap-2.5">
          <Wine className="text-gold" size={20} />
          <span className="font-display text-lg text-cream">Sommelier</span>
        </div>
        <p className="text-wine-300 text-xs mt-0.5 font-sans">{user?.full_name}</p>
      </div>

      {/* New Chat */}
      <div className="px-3 pt-4">
        <button
          onClick={() => { newSession(); navigate('/chat') }}
          className="flex items-center gap-2 w-full px-3 py-2.5 rounded-sm border border-wine-700/40
                     text-wine-100 hover:text-gold hover:border-gold/40 text-sm font-sans
                     transition-all duration-200"
        >
          <Plus size={15} />
          New Conversation
        </button>
      </div>

      {/* Sessions */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
        <p className="text-wine-600 text-xs uppercase tracking-widest px-2 mb-2 font-sans">History</p>
        <AnimatePresence>
          {sessions.map((s) => (
            <motion.div
              key={s.session_id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              className={`group flex items-center justify-between px-3 py-2 rounded-sm cursor-pointer
                         text-sm font-sans transition-all duration-150
                         ${s.session_id === sessionId
                           ? 'bg-wine-800/50 text-gold'
                           : 'text-wine-200 hover:bg-wine-900/60 hover:text-wine-50'}`}
              onClick={() => { switchSession(s.session_id); navigate('/chat') }}
            >
              <span className="truncate flex-1">{s.title}</span>
              <button
                onClick={(e) => { e.stopPropagation(); deleteSession(s.session_id) }}
                className="opacity-0 group-hover:opacity-100 text-wine-300 hover:text-wine-100 ml-1 transition-opacity"
              >
                <Trash2 size={13} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <div className="px-3 pb-2">
        <hr className="gold-divider mb-3" />

        {/* Upload */}
        <div
          {...getRootProps()}
          className={`border border-dashed rounded-sm px-3 py-3 text-center cursor-pointer mb-2
                     transition-all duration-200 text-xs font-sans
                     ${isDragActive
                       ? 'border-gold/60 bg-gold/5 text-gold'
                       : 'border-wine-700/40 text-wine-300 hover:border-wine-600 hover:text-wine-200'}`}
        >
          <input {...getInputProps()} />
          <Upload size={13} className="inline mr-1.5" />
          {isDragActive ? 'Drop wine doc…' : 'Upload PDF / PPTX'}
        </div>

        {/* Eval */}
        <button
          onClick={() => navigate('/eval')}
          className={`flex items-center gap-2 w-full px-3 py-2 rounded-sm text-xs font-sans
                     transition-all duration-150
                     ${location.pathname === '/eval'
                       ? 'text-gold bg-wine-800/40'
                       : 'text-wine-300 hover:text-wine-100'}`}
        >
          <FlaskConical size={13} />
          Evaluation Suite
        </button>

        {/* Logout */}
        <button
          onClick={() => { logout(); navigate('/login') }}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-sm text-xs font-sans
                     text-wine-200 hover:text-wine-50 transition-all duration-150"
        >
          <LogOut size={13} />
          Sign Out
        </button>
      </div>
    </aside>
  )
}
