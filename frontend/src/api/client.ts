import axios from 'axios'

const api = axios.create({ baseURL: '/' })

// Inject JWT from localStorage on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('wine_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401 → clear token and redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('wine_token')
      localStorage.removeItem('wine_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// ─── Auth ───────────────────────────────────────────────────────────────────
export const authApi = {
  register: (email: string, password: string, fullName: string) =>
    api.post('/auth/register', { email, password, full_name: fullName }),
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
}

// ─── Chat ───────────────────────────────────────────────────────────────────
export const chatApi = {
  query: (question: string, sessionId?: string) =>
    api.post('/chat/query', { question, session_id: sessionId }),
  getSessions: () => api.get('/chat/sessions'),
  deleteSession: (sessionId: string) => api.delete(`/chat/sessions/${sessionId}`),
}

// ─── Ingestion ──────────────────────────────────────────────────────────────
export const ingestApi = {
  uploadDocument: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/ingest/document', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

// ─── Eval ───────────────────────────────────────────────────────────────────
export const evalApi = {
  runEval: (numSamples: number) =>
    api.post('/eval/run', { num_samples: numSamples }),
  getResult: (runId: string) => api.get(`/eval/results/${runId}`),
  listResults: () => api.get('/eval/results'),
}

// ─── Health ─────────────────────────────────────────────────────────────────
export const healthApi = {
  check: () => api.get('/health'),
}
