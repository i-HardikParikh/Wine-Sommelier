import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

type Mode = 'login' | 'register'

export default function LoginPage() {
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      if (mode === 'login') {
        await login(email, password)
        toast.success('Welcome back, connoisseur.')
      } else {
        await register(email, password, fullName)
        toast.success('Your cellar awaits.')
      }
      navigate('/chat')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Authentication failed.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-wine-800/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-burgundy/10 rounded-full blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="relative w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="text-5xl mb-4">🍷</div>
          <h1 className="font-display text-3xl text-cream tracking-wide">Wine Sommelier</h1>
          <p className="font-body italic text-wine-400 mt-1 text-lg">Your personal cellar companion</p>
        </div>

        {/* Card */}
        <div className="card p-8">
          {/* Mode toggle */}
          <div className="flex rounded-sm border border-wine-700/40 mb-8 overflow-hidden">
            {(['login', 'register'] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 py-2.5 text-sm font-sans font-medium capitalize transition-all duration-200 ${
                  mode === m
                    ? 'bg-wine-700/60 text-gold'
                    : 'text-cream/50 hover:text-cream/80'
                }`}
              >
                {m === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <AnimatePresence mode="wait">
              {mode === 'register' && (
                <motion.div
                  key="fullname"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <label className="block text-xs font-sans text-wine-400 uppercase tracking-widest mb-1.5">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Jean-Pierre Dupont"
                    className="input-field"
                    required
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <div>
              <label className="block text-xs font-sans text-wine-400 uppercase tracking-widest mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="sommelier@domain.com"
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-sans text-wine-400 uppercase tracking-widest mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="input-field"
                required
                minLength={8}
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full mt-6"
            >
              {isSubmitting
                ? 'Please wait…'
                : mode === 'login'
                ? 'Enter the Cellar'
                : 'Begin Your Journey'}
            </button>
          </form>
        </div>

        <p className="text-center text-wine-600 text-xs mt-6 font-sans">
          Powered by OpenAI · LangGraph · Pinecone
        </p>
      </motion.div>
    </div>
  )
}
