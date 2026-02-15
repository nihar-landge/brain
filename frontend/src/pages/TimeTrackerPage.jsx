import { useState, useEffect, useCallback, useRef } from 'react'
import { Play, Square, Pause, Clock, Brain, Zap, AlertCircle, BarChart3 } from 'lucide-react'
import { startContext, stopContext, getActiveContext, logInterruption, getContextSummary, getDeepWorkBlocks, getOptimalWorkTimes, getAttentionResidue } from '../api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

const CONTEXT_TYPES = ['deep_work', 'coding', 'writing', 'studying', 'communication', 'admin', 'personal']

function useChartColors() {
  return { primary: '#4A90E2', secondary: '#666666', muted: '#cccccc', success: '#2ecc71', error: '#e74c3c' }
}

export default function TimeTrackerPage() {
  const [tab, setTab] = useState('timer')
  const [active, setActive] = useState(null)
  const [contextName, setContextName] = useState('')
  const [contextType, setContextType] = useState('deep_work')
  const [complexity, setComplexity] = useState(5)
  const [elapsed, setElapsed] = useState(0)
  const [summary, setSummary] = useState(null)
  const [deepWork, setDeepWork] = useState([])
  const [optimalTimes, setOptimalTimes] = useState(null)
  const [residue, setResidue] = useState(null)
  const [loading, setLoading] = useState(true)
  const [stopForm, setStopForm] = useState({ mood: 5, energy: 5, productivity: 5 })
  const timerRef = useRef(null)
  const colors = useChartColors()

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [aRes, sRes, dRes, oRes, rRes] = await Promise.allSettled([
        getActiveContext(), getContextSummary(), getDeepWorkBlocks(), getOptimalWorkTimes(), getAttentionResidue()
      ])
      if (aRes.status === 'fulfilled') {
        const data = aRes.value.data
        if (data.active) { setActive(data); setElapsed(data.elapsed_minutes || 0) }
        else { setActive(null); setElapsed(0) }
      }
      if (sRes.status === 'fulfilled') setSummary(sRes.value.data)
      if (dRes.status === 'fulfilled') setDeepWork(dRes.value.data)
      if (oRes.status === 'fulfilled') setOptimalTimes(oRes.value.data)
      if (rRes.status === 'fulfilled') setResidue(rRes.value.data)
    } catch { } finally { setLoading(false) }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  // Timer tick
  useEffect(() => {
    if (active) {
      timerRef.current = setInterval(() => setElapsed(prev => prev + 1), 60000)
      return () => clearInterval(timerRef.current)
    } else {
      clearInterval(timerRef.current)
    }
  }, [active])

  const handleStart = async () => {
    if (!contextName.trim()) return
    try {
      const res = await startContext({ context_name: contextName, context_type: contextType, task_complexity: complexity })
      setActive(res.data)
      setElapsed(0)
      setContextName('')
    } catch { }
  }

  const handleStop = async () => {
    try {
      await stopContext({ mood_after: stopForm.mood, energy_after: stopForm.energy, productivity_rating: stopForm.productivity })
      setActive(null)
      setElapsed(0)
      loadData()
    } catch { }
  }

  const handleInterrupt = async () => {
    try {
      await logInterruption('manual')
      loadData()
    } catch { }
  }

  const formatTime = (mins) => {
    const h = Math.floor(mins / 60)
    const m = mins % 60
    return h > 0 ? `${h}h ${m}m` : `${m}m`
  }

  const tabs = [
    { id: 'timer', label: 'Timer', icon: Clock },
    { id: 'summary', label: 'Today', icon: BarChart3 },
    { id: 'deepwork', label: 'Deep Work', icon: Brain },
    { id: 'insights', label: 'Insights', icon: Zap },
  ]

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-5 h-5 border-2 border-gray-300 border-t-black rounded-full animate-spin" /></div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Time Tracker</h1>
        <p className="text-sm text-gray-500 mt-1">Track context switches, deep work, and cognitive load</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === t.id ? 'border-black text-black' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Timer Tab */}
      {tab === 'timer' && (
        <div className="space-y-4">
          {active ? (
            /* Active Timer */
            <div className="card p-6 border-2 border-accent">
              <div className="text-center">
                <p className="text-xs text-accent font-medium uppercase tracking-wide mb-1">Currently Working On</p>
                <h2 className="text-xl font-bold text-gray-900">{active.context_name}</h2>
                <span className="text-xs text-gray-500">{active.context_type?.replace('_', ' ')}</span>
                <div className="text-4xl font-mono font-bold text-gray-900 mt-4">{formatTime(elapsed)}</div>
              </div>
              <div className="mt-6 space-y-3">
                <div>
                  <label className="text-xs text-gray-500">Mood After ({stopForm.mood})</label>
                  <input type="range" min="1" max="10" value={stopForm.mood} onChange={e => setStopForm({ ...stopForm, mood: Number(e.target.value) })} className="w-full" />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Energy After ({stopForm.energy})</label>
                  <input type="range" min="1" max="10" value={stopForm.energy} onChange={e => setStopForm({ ...stopForm, energy: Number(e.target.value) })} className="w-full" />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Productivity ({stopForm.productivity})</label>
                  <input type="range" min="1" max="10" value={stopForm.productivity} onChange={e => setStopForm({ ...stopForm, productivity: Number(e.target.value) })} className="w-full" />
                </div>
              </div>
              <div className="flex gap-3 mt-4">
                <button onClick={handleStop} className="btn-primary flex-1 flex items-center justify-center gap-2">
                  <Square className="w-4 h-4" /> Stop
                </button>
                <button onClick={handleInterrupt} className="btn-ghost flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" /> Interrupted
                </button>
              </div>
            </div>
          ) : (
            /* Start New Context */
            <div className="card p-6">
              <h3 className="text-sm font-medium text-gray-900 mb-4">Start New Context</h3>
              <div className="space-y-3">
                <input value={contextName} onChange={e => setContextName(e.target.value)} placeholder="What are you working on?" className="input-field w-full" onKeyDown={e => e.key === 'Enter' && handleStart()} />
                <div className="grid grid-cols-2 gap-3">
                  <select value={contextType} onChange={e => setContextType(e.target.value)} className="input-field">
                    {CONTEXT_TYPES.map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                  </select>
                  <div>
                    <label className="text-xs text-gray-500">Complexity: {complexity}/10</label>
                    <input type="range" min="1" max="10" value={complexity} onChange={e => setComplexity(Number(e.target.value))} className="w-full" />
                  </div>
                </div>
                <button onClick={handleStart} disabled={!contextName.trim()} className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-30">
                  <Play className="w-4 h-4" /> Start Timer
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Today Summary Tab */}
      {tab === 'summary' && summary && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="card p-4 text-center"><p className="text-2xl font-bold">{summary.total_contexts}</p><p className="text-xs text-gray-500 mt-1">Contexts</p></div>
            <div className="card p-4 text-center"><p className="text-2xl font-bold">{formatTime(summary.total_minutes)}</p><p className="text-xs text-gray-500 mt-1">Total Time</p></div>
            <div className="card p-4 text-center"><p className="text-2xl font-bold">{formatTime(summary.deep_work_minutes)}</p><p className="text-xs text-gray-500 mt-1">Deep Work</p></div>
            <div className="card p-4 text-center"><p className="text-2xl font-bold">{summary.interruptions}</p><p className="text-xs text-gray-500 mt-1">Interruptions</p></div>
          </div>

          {summary.avg_cognitive_load && (
            <div className="card p-4"><span className="text-sm text-gray-500">Avg Cognitive Load:</span> <span className="font-bold">{summary.avg_cognitive_load}/10</span></div>
          )}

          {/* Type Breakdown */}
          {Object.keys(summary.type_breakdown).length > 0 && (
            <div className="card p-6">
              <h3 className="text-sm font-medium text-gray-900 mb-4">Time by Type</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={Object.entries(summary.type_breakdown).map(([type, mins]) => ({ type: type.replace('_', ' '), minutes: mins }))}>
                  <XAxis dataKey="type" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="minutes" fill={colors.primary} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Context Timeline */}
          {summary.contexts?.length > 0 && (
            <div className="card p-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Timeline</h3>
              <div className="space-y-2">
                {summary.contexts.map((c, i) => (
                  <div key={c.id || i} className="flex items-center gap-3 text-sm">
                    <span className="text-xs text-gray-400 font-mono w-14">{c.started_at?.slice(11, 16)}</span>
                    <div className={`w-2 h-2 rounded-full flex-shrink-0 ${c.is_interruption ? 'bg-error' : 'bg-accent'}`} />
                    <span className="text-gray-900 flex-1">{c.name}</span>
                    <span className="text-gray-400 text-xs">{c.duration_minutes ? formatTime(c.duration_minutes) : '...'}</span>
                    {c.productivity && <span className="text-xs font-mono text-gray-500">{c.productivity}/10</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Deep Work Tab */}
      {tab === 'deepwork' && (
        <div className="space-y-4">
          {deepWork.length === 0 ? (
            <div className="card p-8 text-center text-gray-500">
              <Brain className="w-8 h-8 mx-auto mb-3 text-gray-300" />
              <p>No deep work blocks recorded yet. Start a 45+ minute uninterrupted session to qualify.</p>
            </div>
          ) : (
            <>
              <div className="card p-6">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Deep Work Blocks (Last 30 Days)</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={deepWork}>
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => d.slice(5)} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="duration_minutes" fill={colors.primary} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="grid gap-2">
                {deepWork.slice(-10).reverse().map((b, i) => (
                  <div key={b.id || i} className="card p-3 flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      {b.flow_state && <Brain className="w-4 h-4 text-accent" />}
                      <span className="text-gray-900">{b.date}</span>
                      <span className="text-gray-400">{b.start_time?.slice(0, 5)} — {b.end_time?.slice(0, 5)}</span>
                    </div>
                    <span className="font-mono text-gray-600">{formatTime(b.duration_minutes)}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Insights Tab */}
      {tab === 'insights' && (
        <div className="space-y-4">
          {/* Optimal Times */}
          {optimalTimes && optimalTimes.hours && Object.keys(optimalTimes.hours).length > 0 && (
            <div className="card p-6">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Optimal Work Times</h3>
              {optimalTimes.best_time && <p className="text-sm text-gray-600 mb-4">Best: <span className="font-bold text-success">{optimalTimes.best_time}</span> | Worst: <span className="font-bold text-error">{optimalTimes.worst_time}</span></p>}
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={Object.entries(optimalTimes.hours).map(([h, score]) => ({ hour: `${h}:00`, score }))}>
                  <XAxis dataKey="hour" tick={{ fontSize: 10 }} />
                  <YAxis domain={[0, 10]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="score" fill={colors.primary} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Attention Residue */}
          {residue && (
            <div className="card p-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Attention Residue Analysis</h3>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div><span className="text-xs text-gray-500">Total Switches:</span><p className="text-xl font-bold">{residue.total_switches}</p></div>
                <div><span className="text-xs text-gray-500">Avg Switch Cost:</span><p className="text-xl font-bold">{residue.avg_switch_cost_minutes} min</p></div>
              </div>
              {residue.recommendation && (
                <div className="bg-accent/10 rounded-lg p-3 text-sm text-gray-800">{residue.recommendation}</div>
              )}
              {residue.switch_penalties && Object.keys(residue.switch_penalties).length > 0 && (
                <div className="mt-4 space-y-1">
                  <p className="text-xs text-gray-500 mb-2">Switch Costs by Transition:</p>
                  {Object.entries(residue.switch_penalties).sort((a, b) => b[1].avg_switch_cost - a[1].avg_switch_cost).slice(0, 5).map(([key, val]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <span className="text-gray-600">{key}</span>
                      <span className="font-mono">{val.avg_switch_cost} min ({val.count}x)</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {(!optimalTimes || !Object.keys(optimalTimes.hours || {}).length) && !residue?.recommendation && (
            <div className="card p-8 text-center text-gray-500">
              <Zap className="w-8 h-8 mx-auto mb-3 text-gray-300" />
              <p>Track more context sessions to unlock productivity insights.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
