import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Play,
  Square,
  Clock,
  Brain,
  Zap,
  AlertCircle,
  BarChart3,
  Target,
  Sparkles,
  Activity,
} from 'lucide-react'
import {
  startContext,
  stopContext,
  getActiveContext,
  logInterruption,
  getContextSummary,
  getDeepWorkBlocks,
  getOptimalWorkTimes,
  getAttentionResidue,
  getHabits,
  getTasks,
  suggestDopamine,
  updateDopamineEvent,
} from '../api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const CONTEXT_TYPES = [
  'deep_work',
  'coding',
  'writing',
  'studying',
  'communication',
  'admin',
  'personal',
]

function useChartColors() {
  return {
    primary: '#4A90E2',
    secondary: '#666666',
    muted: '#cccccc',
    success: '#2ecc71',
    error: '#e74c3c',
  }
}

function getElapsedSeconds(activeContext) {
  if (!activeContext) return 0

  const startedAt = activeContext.started_at
  if (!startedAt) return (activeContext.elapsed_minutes || 0) * 60

  const normalized = startedAt.includes('T')
    ? startedAt
    : `${startedAt.replace(' ', 'T')}Z`

  const parsed = new Date(normalized)
  if (Number.isNaN(parsed.getTime())) {
    return (activeContext.elapsed_minutes || 0) * 60
  }

  return Math.max(0, Math.floor((Date.now() - parsed.getTime()) / 1000))
}

export default function TimeTrackerPage() {
  const [tab, setTab] = useState('timer')
  const [active, setActive] = useState(null)
  const [contextName, setContextName] = useState('')
  const [contextType, setContextType] = useState('deep_work')
  const [complexity, setComplexity] = useState(5)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [summary, setSummary] = useState(null)
  const [deepWork, setDeepWork] = useState([])
  const [optimalTimes, setOptimalTimes] = useState(null)
  const [residue, setResidue] = useState(null)
  const [loading, setLoading] = useState(true)
  const [stopForm, setStopForm] = useState({ mood: 5, energy: 5, productivity: 5 })
  const [habits, setHabits] = useState([])
  const [selectedHabitId, setSelectedHabitId] = useState('')
  const [tasks, setTasks] = useState([])
  const [selectedTaskId, setSelectedTaskId] = useState('')
  const [dopamineSuggestion, setDopamineSuggestion] = useState(null)
  const [breakSecondsLeft, setBreakSecondsLeft] = useState(0)
  const [shownLongSessionMilestones, setShownLongSessionMilestones] = useState({
    sixty: false,
    ninety: false,
  })
  const timerRef = useRef(null)
  const breakTimerRef = useRef(null)
  const colors = useChartColors()

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [aRes, sRes, dRes, oRes, rRes, hRes, tRes] = await Promise.allSettled([
        getActiveContext(),
        getContextSummary(),
        getDeepWorkBlocks(),
        getOptimalWorkTimes(),
        getAttentionResidue(),
        getHabits(),
        getTasks({ status: 'all' }),
      ])

      if (aRes.status === 'fulfilled') {
        const data = aRes.value.data
        if (data.active) {
          setActive(data)
          setElapsedSeconds(getElapsedSeconds(data))
        } else {
          setActive(null)
          setElapsedSeconds(0)
        }
      }
      if (sRes.status === 'fulfilled') setSummary(sRes.value.data)
      if (dRes.status === 'fulfilled') setDeepWork(dRes.value.data)
      if (oRes.status === 'fulfilled') setOptimalTimes(oRes.value.data)
      if (rRes.status === 'fulfilled') setResidue(rRes.value.data)
      if (hRes.status === 'fulfilled') setHabits(hRes.value.data || [])
      if (tRes.status === 'fulfilled') {
        const openTasks = (tRes.value.data || []).filter((t) => t.status !== 'done')
        setTasks(openTasks)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    if (!active) {
      setShownLongSessionMilestones({ sixty: false, ninety: false })
    }
  }, [active])

  useEffect(() => {
    if (active) {
      timerRef.current = setInterval(() => {
        const fromStart = getElapsedSeconds(active)
        if (fromStart > 0) {
          setElapsedSeconds(fromStart)
        } else {
          setElapsedSeconds((prev) => prev + 1)
        }
      }, 1000)
      return () => clearInterval(timerRef.current)
    }
    clearInterval(timerRef.current)
  }, [active])

  useEffect(() => {
    if (breakSecondsLeft > 0) {
      breakTimerRef.current = setInterval(() => {
        setBreakSecondsLeft((prev) => Math.max(0, prev - 1))
      }, 1000)
      return () => clearInterval(breakTimerRef.current)
    }
    clearInterval(breakTimerRef.current)
  }, [breakSecondsLeft])

  const requestDopamineSuggestion = useCallback(async (payload) => {
    try {
      const { data } = await suggestDopamine(payload)
      if (data?.options?.length) {
        setDopamineSuggestion(data)
      }
    } catch (e) {
      console.error(e)
    }
  }, [])

  const dismissSuggestion = async () => {
    if (dopamineSuggestion?.event_id) {
      try {
        await updateDopamineEvent(dopamineSuggestion.event_id, { accepted: false, completed: false })
      } catch (e) {
        console.error(e)
      }
    }
    setDopamineSuggestion(null)
  }

  const acceptSuggestion = async (item) => {
    const mins = item.duration_min || 5
    setBreakSecondsLeft(mins * 60)
    if (dopamineSuggestion?.event_id) {
      try {
        await updateDopamineEvent(dopamineSuggestion.event_id, { accepted: true })
      } catch (e) {
        console.error(e)
      }
    }
  }

  const completeSuggestion = async () => {
    if (dopamineSuggestion?.event_id) {
      try {
        await updateDopamineEvent(dopamineSuggestion.event_id, {
          accepted: true,
          completed: true,
        })
      } catch (e) {
        console.error(e)
      }
    }
    setBreakSecondsLeft(0)
    setDopamineSuggestion(null)
  }

  const handleStart = async () => {
    if (!contextName.trim()) return
    try {
      const payload = {
        context_name: contextName,
        context_type: contextType,
        task_complexity: complexity,
      }
      if (selectedHabitId) payload.habit_id = Number(selectedHabitId)
      if (selectedTaskId) payload.task_id = Number(selectedTaskId)
      const res = await startContext(payload)
      setActive(res.data)
      setElapsedSeconds(0)
      setContextName('')
      setSelectedHabitId('')
      setSelectedTaskId('')
    } catch {}
  }

  const handleStop = async () => {
    try {
      const { data } = await stopContext({
        mood_after: stopForm.mood,
        energy_after: stopForm.energy,
        productivity_rating: stopForm.productivity,
      })

      const sessionMinutes = data?.duration_minutes || elapsedMinutes

      setActive(null)
      setElapsedSeconds(0)

      if (stopForm.energy <= 4 || sessionMinutes >= 90) {
        requestDopamineSuggestion({
          trigger_type: 'exhausted',
          session_minutes: sessionMinutes,
          energy_after: stopForm.energy,
          productivity_rating: stopForm.productivity,
          context_log_id: data?.id,
        })
      } else if (stopForm.productivity >= 8 && sessionMinutes >= 60) {
        requestDopamineSuggestion({
          trigger_type: 'manual',
          session_minutes: sessionMinutes,
          productivity_rating: stopForm.productivity,
          context_log_id: data?.id,
        })
      }

      loadData()
    } catch {}
  }

  const handleInterrupt = async () => {
    try {
      await logInterruption('manual')
      loadData()
    } catch {}
  }

  const formatTime = (mins) => {
    const h = Math.floor(mins / 60)
    const m = mins % 60
    return h > 0 ? `${h}h ${m}m` : `${m}m`
  }

  const formatClock = (mins) => {
    const h = String(Math.floor(mins / 3600)).padStart(2, '0')
    const m = String(Math.floor((mins % 3600) / 60)).padStart(2, '0')
    const s = String(mins % 60).padStart(2, '0')
    return `${h}:${m}:${s}`
  }

  const formatCountdown = (seconds) => {
    const m = String(Math.floor(seconds / 60)).padStart(2, '0')
    const s = String(seconds % 60).padStart(2, '0')
    return `${m}:${s}`
  }

  const tabs = [
    { id: 'timer', label: 'Timer', icon: Clock },
    { id: 'summary', label: 'Today', icon: BarChart3 },
    { id: 'deepwork', label: 'Deep Work', icon: Brain },
    { id: 'insights', label: 'Insights', icon: Zap },
  ]

  const elapsedMinutes = Math.floor(elapsedSeconds / 60)
  const focusProgress = Math.min(100, Math.round((elapsedMinutes / 90) * 100))

  useEffect(() => {
    if (tab === 'timer' && !active && !dopamineSuggestion) {
      requestDopamineSuggestion({ trigger_type: 'pre_start', session_minutes: 0 })
    }
  }, [tab, active, dopamineSuggestion, requestDopamineSuggestion])

  useEffect(() => {
    if (!active) return

    if (elapsedMinutes >= 60 && !shownLongSessionMilestones.sixty) {
      requestDopamineSuggestion({
        trigger_type: 'long_session',
        session_minutes: elapsedMinutes,
        context_log_id: active.id,
      })
      setShownLongSessionMilestones((prev) => ({ ...prev, sixty: true }))
    }

    if (elapsedMinutes >= 90 && !shownLongSessionMilestones.ninety) {
      requestDopamineSuggestion({
        trigger_type: 'long_session',
        session_minutes: elapsedMinutes,
        context_log_id: active.id,
      })
      setShownLongSessionMilestones((prev) => ({ ...prev, ninety: true }))
    }
  }, [elapsedMinutes, active, shownLongSessionMilestones, requestDopamineSuggestion])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-5 h-5 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Time Tracker</h1>
          <p className="text-sm text-gray-500 mt-1">Track context switches, deep work, and cognitive load</p>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-full border border-gray-200 bg-gray-100 text-gray-600">
          <Sparkles className="w-3.5 h-3.5 text-accent" />
          Focus mode
        </div>
      </div>

      <div className="flex gap-1 p-1 rounded-xl border border-gray-200 bg-gray-100/70 w-full sm:w-fit overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${
              tab === t.id ? 'bg-white text-black shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'timer' && (
        <div className="space-y-4 animate-in">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="card p-3 sm:p-4">
              <p className="text-[11px] text-gray-500 uppercase tracking-wide">Today Focus</p>
              <p className="text-lg sm:text-xl font-semibold text-gray-900 mt-1">{formatTime(summary?.deep_work_minutes || 0)}</p>
            </div>
            <div className="card p-3 sm:p-4">
              <p className="text-[11px] text-gray-500 uppercase tracking-wide">Sessions</p>
              <p className="text-lg sm:text-xl font-semibold text-gray-900 mt-1">{summary?.total_contexts || 0}</p>
            </div>
            <div className="card p-3 sm:p-4">
              <p className="text-[11px] text-gray-500 uppercase tracking-wide">Interruptions</p>
              <p className="text-lg sm:text-xl font-semibold text-gray-900 mt-1">{summary?.interruptions || 0}</p>
            </div>
            <div className="card p-3 sm:p-4">
              <p className="text-[11px] text-gray-500 uppercase tracking-wide">Avg Load</p>
              <p className="text-lg sm:text-xl font-semibold text-gray-900 mt-1">
                {summary?.avg_cognitive_load ? `${summary.avg_cognitive_load}/10` : '--'}
              </p>
            </div>
          </div>

          {dopamineSuggestion && dopamineSuggestion.options?.length > 0 && (
            <div className="card p-4 border-l-4 border-l-accent">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-wide text-accent font-medium">Dopamine Menu Suggestion</p>
                  <p className="text-sm text-gray-700 mt-1">
                    Feeling exhausted or deep in a long session? Take a healthy break instead of scrolling.
                  </p>
                  {dopamineSuggestion.reason && (
                    <p className="text-xs text-gray-500 mt-1">
                      {dopamineSuggestion.selection_mode === 'ai' ? 'AI-ranked' : 'Rule-ranked'}: {dopamineSuggestion.reason}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button className="btn-secondary text-xs" onClick={dismissSuggestion}>Dismiss</button>
                </div>
              </div>

              {breakSecondsLeft > 0 ? (
                <div className="mt-3 rounded-lg border border-gray-200 bg-gray-100/70 p-3">
                  <p className="text-xs text-gray-500">Break timer running</p>
                  <p className="text-2xl font-mono font-semibold text-gray-900 mt-1">{formatCountdown(breakSecondsLeft)}</p>
                  <button className="btn-primary mt-3 text-xs" onClick={completeSuggestion}>Done, Back to Focus</button>
                </div>
              ) : (
                <div className="mt-3 grid sm:grid-cols-3 gap-2">
                  {dopamineSuggestion.options.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => acceptSuggestion(item)}
                      className="text-left border border-gray-200 rounded-lg p-3 hover:bg-gray-100 transition-colors"
                    >
                      <p className="text-xs text-gray-500 uppercase tracking-wide">{item.category}</p>
                      <p className="text-sm font-medium text-gray-900 mt-0.5">{item.title}</p>
                      {item.description && <p className="text-xs text-gray-500 mt-1 line-clamp-2">{item.description}</p>}
                      <p className="text-[11px] text-accent mt-1">{item.duration_min || 5} min</p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {active ? (
            <div className="card p-5 sm:p-6 border-2 border-accent overflow-hidden relative">
              <div
                className="absolute inset-0 opacity-60"
                style={{
                  background:
                    'radial-gradient(100% 120% at 100% 0%, rgba(74, 144, 226, 0.14) 0%, rgba(74, 144, 226, 0.03) 35%, transparent 70%)',
                }}
              />

              <div className="relative z-10 text-center">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium uppercase tracking-wide bg-accent/10 text-accent mb-2">
                  <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                  Live session
                </div>
                <h2 className="text-xl font-bold text-gray-900">{active.context_name}</h2>
                <span className="text-xs text-gray-500">{active.context_type?.replace('_', ' ')}</span>
                {active.habit_name && (
                  <div className="flex items-center justify-center gap-1.5 mt-1 text-xs text-gray-500">
                    <Target className="w-3 h-3" />
                    <span>{active.habit_name}</span>
                    {active.goal_title && <span className="text-gray-400">&middot; {active.goal_title}</span>}
                  </div>
                )}

                <div className="mt-5 flex justify-center">
                  <div
                    className="w-36 h-36 sm:w-44 sm:h-44 rounded-full p-2"
                    style={{
                      background: `conic-gradient(var(--color-accent) ${focusProgress}%, var(--color-gray-200) ${focusProgress}% 100%)`,
                    }}
                  >
                    <div className="w-full h-full rounded-full bg-white border border-gray-200 flex flex-col items-center justify-center">
                      <p className="text-[10px] uppercase tracking-wide text-gray-500">Flow Target 90m</p>
                      <div className="text-2xl sm:text-3xl font-mono font-bold text-gray-900 mt-1">{formatClock(elapsedSeconds)}</div>
                      <p className="text-xs text-gray-500 mt-1">{focusProgress}% milestone</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-3 relative z-10">
                <div>
                  <label className="text-xs text-gray-500">Mood After ({stopForm.mood})</label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={stopForm.mood}
                    onChange={(e) => setStopForm({ ...stopForm, mood: Number(e.target.value) })}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Energy After ({stopForm.energy})</label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={stopForm.energy}
                    onChange={(e) => setStopForm({ ...stopForm, energy: Number(e.target.value) })}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Productivity ({stopForm.productivity})</label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={stopForm.productivity}
                    onChange={(e) => setStopForm({ ...stopForm, productivity: Number(e.target.value) })}
                    className="w-full"
                  />
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 mt-4 relative z-10">
                <button onClick={handleStop} className="btn-primary flex-1 flex items-center justify-center gap-2">
                  <Square className="w-4 h-4" /> Stop
                </button>
                <button onClick={handleInterrupt} className="btn-ghost flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" /> Interrupted
                </button>
              </div>
            </div>
          ) : (
            <div className="grid lg:grid-cols-5 gap-4">
              <div className="card p-5 sm:p-6 lg:col-span-3">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-900">Start New Context</h3>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => requestDopamineSuggestion({ trigger_type: 'manual', session_minutes: 0 })}
                      className="text-[11px] text-gray-500 hover:text-gray-900 border border-gray-200 rounded-full px-2 py-1"
                    >
                      Need dopamine?
                    </button>
                    <span className="inline-flex items-center gap-1 text-[11px] text-gray-500">
                      <Sparkles className="w-3 h-3 text-accent" /> Focus sprint
                    </span>
                  </div>
                </div>

                <div className="space-y-3">
                  <input
                    value={contextName}
                    onChange={(e) => setContextName(e.target.value)}
                    placeholder="What are you working on?"
                    className="input-field w-full"
                    onKeyDown={(e) => e.key === 'Enter' && handleStart()}
                  />

                  <select
                    value={selectedHabitId}
                    onChange={(e) => setSelectedHabitId(e.target.value)}
                    className="input-field w-full"
                  >
                    <option value="">No habit (standalone session)</option>
                    {habits.map((h) => (
                      <option key={h.id} value={h.id}>
                        {h.name}
                        {h.goal_title ? ` — ${h.goal_title}` : ''}
                      </option>
                    ))}
                  </select>

                  <select
                    value={selectedTaskId}
                    onChange={(e) => setSelectedTaskId(e.target.value)}
                    className="input-field w-full"
                  >
                    <option value="">No task link</option>
                    {tasks.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.title}
                        {t.priority ? ` · ${t.priority}` : ''}
                      </option>
                    ))}
                  </select>

                  <div className="flex flex-wrap gap-2">
                    {CONTEXT_TYPES.map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setContextType(t)}
                        className={`px-2.5 py-1.5 rounded-full text-xs border transition-colors ${
                          contextType === t
                            ? 'bg-black text-white border-black'
                            : 'border-gray-200 text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        {t.replace('_', ' ')}
                      </button>
                    ))}
                  </div>

                  <div className="rounded-xl border border-gray-200 p-3 bg-gray-100/50">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Complexity</span>
                      <span className="font-mono">{complexity}/10</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={complexity}
                      onChange={(e) => setComplexity(Number(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                      <span>Light</span>
                      <span>Deep</span>
                    </div>
                  </div>

                  <button
                    onClick={handleStart}
                    disabled={!contextName.trim()}
                    className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-30"
                  >
                    <Play className="w-4 h-4" /> Start Timer
                  </button>
                </div>
              </div>

              <div className="card p-5 sm:p-6 lg:col-span-2">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Session Guide</h4>
                <div className="space-y-3 text-sm">
                  <div className="flex items-start gap-2.5">
                    <div className="w-7 h-7 rounded-full bg-accent/10 text-accent flex items-center justify-center">
                      <Activity className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-gray-900 font-medium">Pick one clear outcome</p>
                      <p className="text-gray-500 text-xs">Define one deliverable before you hit start.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <div className="w-7 h-7 rounded-full bg-gray-100 text-gray-700 flex items-center justify-center">
                      <Clock className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-gray-900 font-medium">Aim for 45-90 minutes</p>
                      <p className="text-gray-500 text-xs">Long uninterrupted blocks improve deep work scoring.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <div className="w-7 h-7 rounded-full bg-gray-100 text-gray-700 flex items-center justify-center">
                      <Brain className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-gray-900 font-medium">Rate mood and output</p>
                      <p className="text-gray-500 text-xs">Your post-session ratings train better insights.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

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
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
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

      {tab === 'insights' && (
        <div className="space-y-4">
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
