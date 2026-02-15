import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CalendarDays, ChevronLeft, ChevronRight, Play, Plus, Zap } from 'lucide-react'
import { createTask, getCalendarEvents, getGoals, getHabits, getTasks, startContext } from '../api'

function startOfWeek(date) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

function addDays(date, n) {
  const d = new Date(date)
  d.setDate(d.getDate() + n)
  return d
}

function dateKey(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function formatInputDateTime(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d}T${h}:${min}`
}

function hourLabel(hour) {
  const suffix = hour >= 12 ? 'PM' : 'AM'
  const value = hour % 12 || 12
  return `${value}:00 ${suffix}`
}

function parseSafeDate(value) {
  if (!value) return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

function eventRange(event) {
  const start = parseSafeDate(event.start)
  if (!start) return null

  const endFromEvent = parseSafeDate(event.end)
  if (endFromEvent && endFromEvent > start) return { start, end: endFromEvent }

  if (typeof event.duration_minutes === 'number' && event.duration_minutes > 0) {
    return { start, end: new Date(start.getTime() + event.duration_minutes * 60 * 1000) }
  }

  return { start, end: new Date(start.getTime() + 30 * 60 * 1000) }
}

function eventClockLabel(event) {
  const range = eventRange(event)
  if (!range) return ''
  const start = range.start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const end = range.end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return `${start} - ${end}`
}

function splitDateTimeParts(date) {
  return {
    date: formatInputDateTime(date).slice(0, 10),
    time: formatInputDateTime(date).slice(11, 16),
  }
}

function buildDateTime(datePart, timePart) {
  if (!datePart) return null
  const safeTime = timePart || '00:00'
  return parseSafeDate(`${datePart}T${safeTime}`)
}

export default function CalendarPage() {
  const navigate = useNavigate()
  const [weekStart, setWeekStart] = useState(startOfWeek(new Date()))
  const [events, setEvents] = useState([])
  const [goals, setGoals] = useState([])
  const [habits, setHabits] = useState([])
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [visibleHourStart, setVisibleHourStart] = useState(0)
  const [visibleHourEnd, setVisibleHourEnd] = useState(24)
  const [mobileDayIndex, setMobileDayIndex] = useState(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1)
  const [composer, setComposer] = useState({ dayIndex: 0, hour: 9, open: false })
  const [draft, setDraft] = useState({
    title: '',
    priority: 'medium',
    goal_id: '',
    habit_id: '',
    task_id: '',
    start_date: '',
    start_time: '',
    end_date: '',
    end_time: '',
    context_type: 'deep_work',
  })
  const [submitting, setSubmitting] = useState(false)
  const [mobileSheetMounted, setMobileSheetMounted] = useState(false)
  const [mobileSheetOpen, setMobileSheetOpen] = useState(false)
  const desktopGridRef = useRef(null)
  const mobileListRef = useRef(null)
  const DESKTOP_HOUR_HEIGHT = 72
  const MOBILE_HOUR_HEIGHT = 64

  const hours = useMemo(() => {
    const start = Math.max(0, Math.min(23, visibleHourStart))
    const end = Math.max(start + 1, Math.min(24, visibleHourEnd))
    return [...Array(end - start)].map((_, i) => i + start)
  }, [visibleHourEnd, visibleHourStart])

  const weekDays = useMemo(() => [...Array(7)].map((_, i) => addDays(weekStart, i)), [weekStart])

  const loadEvents = async () => {
    setLoading(true)
    try {
      const start = weekStart.toISOString()
      const end = addDays(weekStart, 7).toISOString()
      const { data } = await getCalendarEvents({ start, end })
      setEvents(data.events || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadEvents()
  }, [weekStart])

  useEffect(() => {
    const loadLinks = async () => {
      try {
        const [{ data: goalData }, { data: habitData }, { data: taskData }] = await Promise.all([
          getGoals('all'),
          getHabits('all'),
          getTasks({ status: 'all' }),
        ])
        setGoals(goalData || [])
        setHabits(habitData || [])
        setTasks((taskData || []).filter((t) => t.status !== 'done'))
      } catch (e) {
        console.error(e)
      }
    }
    loadLinks()
  }, [])

  useEffect(() => {
    if (loading || hours.length === 0) return
    const currentHour = new Date().getHours()
    const clamped = Math.max(hours[0], Math.min(hours[hours.length - 1], currentHour))
    const hourIndex = Math.max(0, clamped - hours[0])

    if (desktopGridRef.current) {
      desktopGridRef.current.scrollTop = Math.max(0, hourIndex * DESKTOP_HOUR_HEIGHT - 120)
    }
    if (mobileListRef.current) {
      mobileListRef.current.scrollTop = Math.max(0, hourIndex * MOBILE_HOUR_HEIGHT - 90)
    }
  }, [DESKTOP_HOUR_HEIGHT, MOBILE_HOUR_HEIGHT, loading, hours, weekStart, mobileDayIndex])

  useEffect(() => {
    if (composer.open) {
      setMobileSheetMounted(true)
      const id = window.requestAnimationFrame(() => setMobileSheetOpen(true))
      return () => window.cancelAnimationFrame(id)
    }

    setMobileSheetOpen(false)
    if (mobileSheetMounted) {
      const id = window.setTimeout(() => setMobileSheetMounted(false), 240)
      return () => window.clearTimeout(id)
    }
  }, [composer.open, mobileSheetMounted])

  const groupedByDay = useMemo(() => {
    const map = {}
    for (const d of weekDays) {
      map[dateKey(d)] = []
    }
    for (const e of events) {
      if (!e.start) continue
      const key = dateKey(new Date(e.start))
      if (!map[key]) map[key] = []
      map[key].push(e)
    }
    for (const key of Object.keys(map)) {
      map[key].sort((a, b) => (a.start || '').localeCompare(b.start || ''))
    }
    return map
  }, [events, weekDays])

  const totalLoggedMinutes = useMemo(
    () => events.filter((e) => e.type === 'session_logged').reduce((sum, e) => sum + (e.duration_minutes || 0), 0),
    [events]
  )

  const timedEventsByDay = useMemo(() => {
    const map = {}
    const windowStartMin = visibleHourStart * 60
    const windowEndMin = visibleHourEnd * 60

    for (const e of events) {
      if (e.all_day || !e.start) continue

      const range = eventRange(e)
      if (!range) continue

      const day = dateKey(range.start)
      const key = day
      if (!map[key]) map[key] = []

      const startMin = range.start.getHours() * 60 + range.start.getMinutes()
      const endMin = range.end.getHours() * 60 + range.end.getMinutes()
      const clippedStartMin = Math.max(windowStartMin, startMin)
      const clippedEndMin = Math.min(windowEndMin, endMin)

      if (clippedEndMin <= clippedStartMin) continue

      map[key].push({
        ...e,
        _startMin: clippedStartMin,
        _endMin: clippedEndMin,
        _rawStartHour: range.start.getHours(),
      })
    }

    for (const key of Object.keys(map)) {
      map[key].sort((a, b) => a._startMin - b._startMin)
    }

    return map
  }, [events, visibleHourEnd, visibleHourStart])

  const allDayByDate = useMemo(() => {
    const map = {}
    for (const e of events) {
      if (!e.all_day || !e.start) continue
      const key = dateKey(new Date(e.start))
      if (!map[key]) map[key] = []
      map[key].push(e)
    }
    return map
  }, [events])

  const openComposer = (dayIndex, hour) => {
    const day = weekDays[dayIndex]
    const start = new Date(day)
    start.setHours(hour, 0, 0, 0)
    const end = new Date(start.getTime() + 45 * 60 * 1000)
    const startParts = splitDateTimeParts(start)
    const endParts = splitDateTimeParts(end)

    setComposer({ dayIndex, hour, open: true })
    setDraft((prev) => ({
      ...prev,
      start_date: startParts.date,
      start_time: startParts.time,
      end_date: endParts.date,
      end_time: endParts.time,
    }))
    if (window.innerWidth < 768) setMobileDayIndex(dayIndex)
  }

  const createScheduledTask = async () => {
    if (!draft.title.trim()) return
    setSubmitting(true)
    try {
      const start = buildDateTime(draft.start_date, draft.start_time)
      const endInput = buildDateTime(draft.end_date, draft.end_time)
      if (!start) return
      const end = endInput && endInput > start ? endInput : new Date(start.getTime() + 30 * 60 * 1000)
      const duration = Math.max(1, Math.round((end.getTime() - start.getTime()) / 60000))

      await createTask({
        title: draft.title.trim(),
        priority: draft.priority,
        status: 'todo',
        scheduled_at: formatInputDateTime(start),
        scheduled_end: formatInputDateTime(end),
        is_all_day: false,
        estimated_minutes: duration,
        goal_id: draft.goal_id ? Number(draft.goal_id) : null,
        habit_id: draft.habit_id ? Number(draft.habit_id) : null,
      })

      await loadEvents()
      setComposer((prev) => ({ ...prev, open: false }))
    } catch (e) {
      console.error(e)
    } finally {
      setSubmitting(false)
    }
  }

  const startTimerNow = async () => {
    setSubmitting(true)
    try {
      const fallback = `Focus block ${hourLabel(composer.hour)}`
      await startContext({
        context_name: draft.title.trim() || fallback,
        context_type: draft.context_type,
        task_complexity: 5,
        habit_id: draft.habit_id ? Number(draft.habit_id) : undefined,
        task_id: draft.task_id ? Number(draft.task_id) : undefined,
      })
      navigate('/timer')
    } catch (e) {
      console.error(e)
    } finally {
      setSubmitting(false)
    }
  }

  const selectedStart = buildDateTime(draft.start_date, draft.start_time)
  const selectedEnd = buildDateTime(draft.end_date, draft.end_time)
  const selectedSlotText = selectedStart
    ? `${selectedStart.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })} · ${selectedStart.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}${selectedEnd ? ` - ${selectedEnd.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : ''}`
    : `${weekDays[composer.dayIndex]?.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })} at ${hourLabel(composer.hour)}`

  const renderComposerForm = (isMobile = false) => (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500">Selected slot</p>
          <p className="text-sm font-semibold text-gray-900 mt-0.5">{selectedSlotText}</p>
        </div>
        <button className="btn-ghost !min-h-0 !py-1.5 !px-2.5" onClick={() => setComposer((prev) => ({ ...prev, open: false }))}>Close</button>
      </div>

      <input
        className="input-field !min-h-[40px]"
        placeholder="Task or session title"
        value={draft.title}
        onChange={(e) => setDraft((prev) => ({ ...prev, title: e.target.value }))}
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <div className="rounded-lg border border-gray-200 bg-gray-100/50 p-2">
          <p className="text-[11px] uppercase tracking-wide text-gray-500">Start</p>
          <div className="grid grid-cols-1 gap-2 mt-1.5">
            <input
              type="date"
              className="input-field !min-h-[38px] !py-1.5"
              value={draft.start_date}
              onChange={(e) => setDraft((prev) => ({ ...prev, start_date: e.target.value }))}
            />
            <input
              type="time"
              step="60"
              className="input-field !min-h-[38px] !py-1.5"
              value={draft.start_time}
              onChange={(e) => setDraft((prev) => ({ ...prev, start_time: e.target.value }))}
            />
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-gray-100/50 p-2">
          <p className="text-[11px] uppercase tracking-wide text-gray-500">End</p>
          <div className="grid grid-cols-1 gap-2 mt-1.5">
            <input
              type="date"
              className="input-field !min-h-[38px] !py-1.5"
              value={draft.end_date}
              onChange={(e) => setDraft((prev) => ({ ...prev, end_date: e.target.value }))}
            />
            <input
              type="time"
              step="60"
              className="input-field !min-h-[38px] !py-1.5"
              value={draft.end_time}
              onChange={(e) => setDraft((prev) => ({ ...prev, end_time: e.target.value }))}
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <select
          className="input-field"
          value={draft.goal_id}
          onChange={(e) => setDraft((prev) => ({ ...prev, goal_id: e.target.value }))}
        >
          <option value="">No goal link</option>
          {goals.map((g) => (
            <option key={g.id} value={g.id}>{g.goal_title || g.title || `Goal ${g.id}`}</option>
          ))}
        </select>
        <select
          className="input-field"
          value={draft.habit_id}
          onChange={(e) => setDraft((prev) => ({ ...prev, habit_id: e.target.value }))}
        >
          <option value="">No habit link</option>
          {habits.map((h) => (
            <option key={h.id} value={h.id}>{h.habit_name || h.name || `Habit ${h.id}`}</option>
          ))}
        </select>
      </div>

      <select
        className="input-field"
        value={draft.task_id}
        onChange={(e) => setDraft((prev) => ({ ...prev, task_id: e.target.value }))}
      >
        <option value="">No task link (for timer)</option>
        {tasks.map((t) => (
          <option key={t.id} value={t.id}>{t.title}</option>
        ))}
      </select>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <select
          className="input-field"
          value={draft.priority}
          onChange={(e) => setDraft((prev) => ({ ...prev, priority: e.target.value }))}
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select
          className="input-field"
          value={draft.context_type}
          onChange={(e) => setDraft((prev) => ({ ...prev, context_type: e.target.value }))}
        >
          <option value="deep_work">Deep work</option>
          <option value="coding">Coding</option>
          <option value="writing">Writing</option>
          <option value="studying">Studying</option>
          <option value="communication">Communication</option>
          <option value="admin">Admin</option>
          <option value="personal">Personal</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          disabled={submitting || !draft.title.trim()}
          onClick={createScheduledTask}
          className="btn-primary !min-h-[40px] !py-2 flex items-center justify-center gap-2 disabled:opacity-30"
        >
          <Plus className="w-4 h-4" /> Create task
        </button>
        <button
          type="button"
          disabled={submitting}
          onClick={startTimerNow}
          className="btn-secondary !min-h-[40px] !py-2 flex items-center justify-center gap-2"
        >
          <Play className="w-4 h-4" /> Start timer
        </button>
      </div>

      <p className="text-xs text-gray-500">
        Start/end are fully editable. Overlapping events appear in every occupied hour block for consistency.
      </p>
      {isMobile && <div className="h-2" />}
    </div>
  )

  return (
    <div className="space-y-6 w-full">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Calendar</h1>
          <p className="text-sm text-gray-500 mt-1">Track planned tasks and actual logged focus time in one view.</p>
        </div>
        <div className="hidden sm:flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border border-gray-200 bg-gray-100 text-gray-600">
          <Zap className="w-3.5 h-3.5 text-accent" />
          {totalLoggedMinutes} min logged this week
        </div>
      </div>

      <div className="card p-4 sm:p-5">
        <div className="flex items-center justify-between gap-3">
          <button className="btn-secondary" onClick={() => setWeekStart(addDays(weekStart, -7))}>
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="text-center">
            <p className="text-sm text-gray-500">Week of</p>
            <p className="font-semibold text-gray-900">{weekStart.toLocaleDateString()}</p>
          </div>
          <button className="btn-secondary" onClick={() => setWeekStart(addDays(weekStart, 7))}>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
        <div className="mt-3 flex items-center justify-end">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>Hours</span>
            <select
              className="input-field !py-1.5 !px-2.5 !text-xs !min-h-0"
              value={visibleHourStart}
              onChange={(e) => {
                const next = Number(e.target.value)
                setVisibleHourStart(next)
                if (next >= visibleHourEnd) setVisibleHourEnd(Math.min(24, next + 1))
              }}
            >
              {[...Array(24)].map((_, h) => (
                <option key={`start-${h}`} value={h}>{hourLabel(h)}</option>
              ))}
            </select>
            <span>to</span>
            <select
              className="input-field !py-1.5 !px-2.5 !text-xs !min-h-0"
              value={visibleHourEnd}
              onChange={(e) => {
                const next = Number(e.target.value)
                setVisibleHourEnd(next)
                if (next <= visibleHourStart) setVisibleHourStart(Math.max(0, next - 1))
              }}
            >
              {[...Array(24)].map((_, i) => i + 1).map((h) => (
                <option key={`end-${h}`} value={h}>{h === 24 ? '12:00 AM' : hourLabel(h)}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          <div className="h-20 skeleton" />
          <div className="h-96 skeleton" />
        </div>
      ) : (
        <>
          <div className={`grid grid-cols-1 gap-4 items-start transition-all duration-300 ${composer.open ? 'md:grid-cols-[minmax(0,1fr)_430px]' : ''}`}>
            <div className="space-y-4 min-w-0">
              <div className="card p-4">
                <div className="flex flex-wrap gap-2 items-center justify-between">
                  <p className="text-xs text-gray-500">All-day tasks</p>
                  <div className="flex flex-wrap gap-2">
                    {weekDays.map((day) => {
                      const key = dateKey(day)
                      const items = allDayByDate[key] || []
                      return (
                        <div key={key} className="text-[11px] px-2.5 py-1.5 rounded-lg border border-gray-200 bg-gray-100/70 text-gray-700">
                          {day.toLocaleDateString(undefined, { weekday: 'short' })}: {items.length}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>

              <div className="hidden md:block card overflow-hidden">
                <div ref={desktopGridRef} className="max-h-[68vh] overflow-auto overscroll-contain">
                  <div className="grid min-w-[940px]" style={{ gridTemplateColumns: '90px repeat(7, minmax(0, 1fr))' }}>
                    <div className="border-b border-r border-gray-200 bg-gray-100/80 p-2" />
                    {weekDays.map((day) => {
                      const key = dateKey(day)
                      const dayEvents = groupedByDay[key] || []
                      const logged = dayEvents.filter((e) => e.type === 'session_logged').reduce((sum, e) => sum + (e.duration_minutes || 0), 0)
                      return (
                        <div key={key} className="border-b border-r last:border-r-0 border-gray-200 bg-gray-100/80 p-2.5">
                          <p className="text-[11px] text-gray-500 uppercase tracking-wide">{day.toLocaleDateString(undefined, { weekday: 'short' })}</p>
                          <p className="text-sm font-semibold text-gray-900">{day.toLocaleDateString()}</p>
                          <p className="text-[11px] text-gray-500 mt-0.5">{logged}m logged</p>
                        </div>
                      )
                    })}

                    <div className="border-r border-gray-200 bg-white">
                      {hours.map((hour) => (
                        <div key={`label-${hour}`} className="h-[72px] border-b border-gray-200 px-2 pt-2 text-xs text-gray-500">
                          {hourLabel(hour)}
                        </div>
                      ))}
                    </div>

                    {weekDays.map((day, idx) => {
                      const key = dateKey(day)
                      const dayEvents = timedEventsByDay[key] || []
                      const dayHeight = hours.length * DESKTOP_HOUR_HEIGHT

                      return (
                        <div key={`col-${key}`} className="relative border-r last:border-r-0 border-gray-200" style={{ height: dayHeight }}>
                          {hours.map((hour) => (
                            <button
                              key={`${key}-slot-${hour}`}
                              type="button"
                              onClick={() => openComposer(idx, hour)}
                              className="absolute left-0 right-0 border-b border-gray-200 hover:bg-gray-100/60 transition-colors"
                              style={{ top: (hour - hours[0]) * DESKTOP_HOUR_HEIGHT, height: DESKTOP_HOUR_HEIGHT }}
                            />
                          ))}

                          {dayEvents.map((e) => {
                            const top = ((e._startMin - visibleHourStart * 60) / 60) * DESKTOP_HOUR_HEIGHT
                            const height = Math.max(24, ((e._endMin - e._startMin) / 60) * DESKTOP_HOUR_HEIGHT)
                            return (
                              <button
                                key={`evt-${e.id}-${e._startMin}`}
                                type="button"
                                onClick={() => openComposer(idx, e._rawStartHour)}
                                className={`calendar-event absolute left-1 right-1 z-10 px-2 py-1 text-left ${e.type === 'session_logged' ? 'calendar-event-session' : ''}`}
                                style={{ top, height }}
                                title={`${e.title} (${eventClockLabel(e)})`}
                              >
                                <p className="text-[11px] font-medium truncate">{e.title}</p>
                                <p className="text-[10px] opacity-90 truncate">{eventClockLabel(e)}</p>
                              </button>
                            )
                          })}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>

              <div ref={mobileListRef} className={`md:hidden card p-3 space-y-3 overflow-y-auto overscroll-contain transition-all duration-300 ${composer.open ? 'max-h-[46vh]' : 'max-h-[68vh]'}`}>
                <div className="flex items-center justify-between sticky top-0 bg-white py-1 z-10">
                  <button className="btn-secondary" onClick={() => setMobileDayIndex((v) => Math.max(0, v - 1))} disabled={mobileDayIndex === 0}>
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <p className="text-sm font-semibold text-gray-900">
                    {weekDays[mobileDayIndex]?.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
                  </p>
                  <button className="btn-secondary" onClick={() => setMobileDayIndex((v) => Math.min(6, v + 1))} disabled={mobileDayIndex === 6}>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>

                <div className="grid" style={{ gridTemplateColumns: '72px 1fr' }}>
                  <div>
                    {hours.map((hour) => (
                      <div key={`m-label-${hour}`} className="h-[64px] border-b border-gray-200 text-xs text-gray-500 pt-1.5 pr-2 text-right">
                        {hourLabel(hour)}
                      </div>
                    ))}
                  </div>

                  <div className="relative border-l border-r border-gray-200" style={{ height: hours.length * MOBILE_HOUR_HEIGHT }}>
                    {hours.map((hour) => (
                      <button
                        key={`m-slot-${hour}`}
                        type="button"
                        onClick={() => openComposer(mobileDayIndex, hour)}
                        className="absolute left-0 right-0 border-b border-gray-200"
                        style={{ top: (hour - hours[0]) * MOBILE_HOUR_HEIGHT, height: MOBILE_HOUR_HEIGHT }}
                      />
                    ))}

                    {(timedEventsByDay[dateKey(weekDays[mobileDayIndex])] || []).map((e) => {
                      const top = ((e._startMin - visibleHourStart * 60) / 60) * MOBILE_HOUR_HEIGHT
                      const height = Math.max(22, ((e._endMin - e._startMin) / 60) * MOBILE_HOUR_HEIGHT)
                      return (
                        <button
                          key={`m-evt-${e.id}-${e._startMin}`}
                          type="button"
                          onClick={() => openComposer(mobileDayIndex, e._rawStartHour)}
                          className={`calendar-event absolute left-1 right-1 z-10 px-2 py-1 text-left ${e.type === 'session_logged' ? 'calendar-event-session' : ''}`}
                          style={{ top, height }}
                        >
                          <p className="text-[11px] font-medium truncate">{e.title}</p>
                          <p className="text-[10px] opacity-90 truncate">{eventClockLabel(e)}</p>
                        </button>
                      )
                    })}
                  </div>
                </div>
              </div>
            </div>

            {composer.open && (
              <div className="hidden md:block sticky top-20 animate-in">
                <div className="card p-4 border-l-4 border-l-accent max-h-[78vh] overflow-y-auto">
                  {renderComposerForm(false)}
                </div>
              </div>
            )}
          </div>

          {mobileSheetMounted && (
            <>
              <button
                type="button"
                aria-label="Close editor"
                className={`md:hidden fixed inset-0 z-40 transition-opacity duration-200 ${mobileSheetOpen ? 'bg-black/35 opacity-100' : 'bg-black/0 opacity-0'}`}
                onClick={() => setComposer((prev) => ({ ...prev, open: false }))}
              />
              <div
                className={`md:hidden fixed inset-x-0 bottom-0 z-50 rounded-t-2xl border border-gray-200 bg-white shadow-2xl p-4 safe-bottom max-h-[82vh] overflow-y-auto transition-all duration-250 ease-out ${mobileSheetOpen ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'}`}
              >
                {renderComposerForm(true)}
              </div>
            </>
          )}
        </>
      )}

      <div className="card p-4">
        <div className="flex flex-wrap gap-3 text-xs text-gray-600">
          <span className="inline-flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-accent/70" /> Logged session</span>
          <span className="inline-flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-gray-400" /> Planned task</span>
          <span className="inline-flex items-center gap-1"><CalendarDays className="w-3.5 h-3.5" /> All-day due tasks included</span>
        </div>
      </div>
    </div>
  )
}
