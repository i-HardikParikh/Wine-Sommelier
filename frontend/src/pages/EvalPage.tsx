import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts'
import { FlaskConical, Play, ChevronDown, ChevronUp } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { evalApi } from '../api/client'
import toast from 'react-hot-toast'

interface EvalRun {
  run_id: string
  status: string
  num_samples: number
  aggregate_scores: Record<string, number>
  started_at: string
  completed_at?: string
}

interface EvalResult {
  sample_id: string
  question: string
  answer: string
  scores: { metric: string; score: number; reasoning: string }[]
  overall_score: number
}

export default function EvalPage() {
  const [numSamples, setNumSamples] = useState(5)
  const [isRunning, setIsRunning] = useState(false)
  const [runs, setRuns] = useState<EvalRun[]>([])
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const [results, setResults] = useState<EvalResult[]>([])
  const [expandedSample, setExpandedSample] = useState<string | null>(null)

  useEffect(() => { loadRuns() }, [])

  const loadRuns = async () => {
    try {
      const { data } = await evalApi.listResults()
      setRuns(data)
    } catch { /* ignore */ }
  }

  const startEval = async () => {
    setIsRunning(true)
    const toastId = toast.loading(`Running eval on ${numSamples} samples…`)
    try {
      const { data } = await evalApi.runEval(numSamples)
      toast.success('Evaluation complete!', { id: toastId })
      await loadRuns()
      viewResults(data.run_id)
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Eval failed.', { id: toastId })
    } finally {
      setIsRunning(false)
    }
  }

  const viewResults = async (runId: string) => {
    setSelectedRun(runId)
    try {
      const { data } = await evalApi.getResult(runId)
      setResults(data.results || [])
    } catch { /* ignore */ }
  }

  const selectedRunData = runs.find((r) => r.run_id === selectedRun)
  const radarData = selectedRunData
    ? Object.entries(selectedRunData.aggregate_scores).map(([k, v]) => ({
        metric: k.replace('_', ' '),
        score: Math.round(v * 100),
      }))
    : []

  const scoreColor = (s: number) =>
    s >= 0.8 ? 'text-green-400' : s >= 0.6 ? 'text-yellow-400' : 'text-red-400'

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-6 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-1">
              <FlaskConical className="text-gold" size={22} />
              <h1 className="font-display text-2xl text-cream">Evaluation Suite</h1>
            </div>
            <p className="font-body italic text-wine-200">
              LLM-as-judge: automatically score your sommelier on Relevance, Faithfulness, Completeness & Tone.
            </p>
          </div>

          {/* Run controls */}
          <div className="card p-5 mb-6 flex items-center gap-6">
            <div>
              <label className="text-xs font-sans text-wine-200 uppercase tracking-widest block mb-1.5">
                Samples
              </label>
              <input
                type="number"
                min={1} max={20}
                value={numSamples}
                onChange={(e) => setNumSamples(Number(e.target.value))}
                className="input-field w-24 text-center"
              />
            </div>
            <button
              onClick={startEval}
              disabled={isRunning}
              className="btn-primary flex items-center gap-2 mt-4"
            >
              <Play size={15} />
              {isRunning ? 'Running…' : 'Run Evaluation'}
            </button>
            <p className="text-wine-200 text-xs font-sans mt-4">
              Each sample runs the full RAG pipeline + 4 judge calls.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Run list */}
            <div className="space-y-2">
              <p className="text-xs font-sans text-wine-300 uppercase tracking-widest mb-3">Past Runs</p>
              {runs.length === 0 && (
                <p className="text-wine-200 text-sm font-sans italic">No runs yet.</p>
              )}
              {runs.map((run) => {
                const avg = Object.values(run.aggregate_scores).reduce((a, b) => a + b, 0) /
                  Math.max(Object.values(run.aggregate_scores).length, 1)
                return (
                  <button
                    key={run.run_id}
                    onClick={() => viewResults(run.run_id)}
                    className={`w-full text-left card px-4 py-3 hover:border-wine-600/50 transition-all ${
                      selectedRun === run.run_id ? 'border-gold/40 bg-wine-800/20' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-cream text-sm font-sans">{run.num_samples} samples</p>
                        <p className="text-wine-300 text-xs font-sans">
                          {new Date(run.started_at).toLocaleDateString()}
                        </p>
                      </div>
                      <span className={`text-lg font-display font-bold ${scoreColor(avg)}`}>
                        {(avg * 100).toFixed(0)}
                      </span>
                    </div>
                  </button>
                )
              })}
            </div>

            {/* Results panel */}
            <div className="lg:col-span-2 space-y-5">
              {selectedRunData && radarData.length > 0 && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card p-5">
                  <p className="text-xs font-sans text-wine-300 uppercase tracking-widest mb-4">Aggregate Scores</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="rgba(114,47,55,0.4)" />
                      <PolarAngleAxis dataKey="metric" tick={{ fill: '#9b4a55', fontSize: 11, fontFamily: 'DM Sans' }} />
                      <Radar
                        dataKey="score"
                        stroke="#C9A84C"
                        fill="#C9A84C"
                        fillOpacity={0.2}
                        strokeWidth={2}
                      />
                      <Tooltip
                        contentStyle={{ background: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '2px', fontSize: 12, color: '#111827' }}
                        itemStyle={{ color: '#111827' }}
                        formatter={(v: number) => [`${v}/100`, 'Score']}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </motion.div>
              )}

              {/* Per-sample results */}
              {results.map((r, i) => (
                <motion.div
                  key={r.sample_id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="card"
                >
                  <button
                    onClick={() => setExpandedSample(expandedSample === r.sample_id ? null : r.sample_id)}
                    className="w-full px-5 py-4 flex items-center justify-between"
                  >
                    <div className="text-left flex-1">
                      <p className="text-cream text-sm font-sans truncate">{r.question}</p>
                      <div className="flex gap-3 mt-1">
                        {r.scores.map((s) => (
                          <span key={s.metric} className="text-xs font-sans text-wine-300">
                            {s.metric.split('_')[0]}: <span className={scoreColor(s.score)}>{(s.score * 100).toFixed(0)}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-3 ml-4">
                      <span className={`font-display text-xl font-bold ${scoreColor(r.overall_score)}`}>
                        {(r.overall_score * 100).toFixed(0)}
                      </span>
                      {expandedSample === r.sample_id ? <ChevronUp size={15} className="text-wine-500" /> : <ChevronDown size={15} className="text-wine-500" />}
                    </div>
                  </button>

                  {expandedSample === r.sample_id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      className="border-t border-wine-800/30 px-5 py-4 space-y-4"
                    >
                      <div>
                        <p className="text-xs font-sans text-wine-300 uppercase tracking-widest mb-1.5">Answer</p>
                        <p className="font-body text-cream text-sm leading-relaxed">{r.answer}</p>
                      </div>
                      <div>
                        <p className="text-xs font-sans text-wine-300 uppercase tracking-widest mb-2">Judge Reasoning</p>
                        <div className="space-y-2">
                          {r.scores.map((s) => (
                            <div key={s.metric} className="flex gap-3">
                              <span className={`text-xs font-mono w-28 shrink-0 ${scoreColor(s.score)}`}>
                                {s.metric} {(s.score * 100).toFixed(0)}
                              </span>
                              <p className="text-wine-200 text-xs font-sans leading-relaxed">{s.reasoning}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
