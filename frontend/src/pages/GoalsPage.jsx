import { useState, useEffect, useCallback } from 'react'
import { ChevronDown, ChevronRight, CheckCircle, Flag, Trash2, Check, Calendar, Clock, Plus, X } from 'lucide-react'
import { getGoals, createGoal, updateGoal, deleteGoal, getGoal, createHabit, logHabit, getHabitStats, deleteHabit } from '../api'

const priorityLabel = { 1: 'Low', 2: 'Normal', 3: 'Mid', 4: 'High', 5: 'Critical' }
const habitIcons = {
    fitness: '🏃', health: '💪', mindfulness: '🧘',
    learning: '📚', productivity: '⚡', social: '👥',
}
const categories = ['health', 'fitness', 'learning', 'mindfulness', 'productivity', 'social']

export default function GoalsPage() {
    // Goals state
    const [goals, setGoals] = useState([])
    const [goalsLoading, setGoalsLoading] = useState(true)
    const [showGoalForm, setShowGoalForm] = useState(false)
    const [goalFilter, setGoalFilter] = useState('active')
    const [goalForm, setGoalForm] = useState({
        goal_title: '', goal_description: '', goal_category: 'personal',
        start_date: new Date().toISOString().slice(0, 10), target_date: '', priority: 3,
    })

    // Expanded goal details (Goal → Habits → Sessions)
    const [expandedGoalId, setExpandedGoalId] = useState(null)
    const [goalDetail, setGoalDetail] = useState(null)
    const [detailLoading, setDetailLoading] = useState(false)
    const [habitStatsMap, setHabitStatsMap] = useState({})

    // Habit form (inline, per-goal)
    const [showHabitFormForGoal, setShowHabitFormForGoal] = useState(null)
    const [habitForm, setHabitForm] = useState({
        habit_name: '', habit_description: '', habit_category: '', target_frequency: 'daily'
    })

    // Load goals list
    const loadGoals = useCallback(async () => {
        try { const res = await getGoals(goalFilter); setGoals(res.data) }
        catch (err) { console.error(err) }
        finally { setGoalsLoading(false) }
    }, [goalFilter])

    useEffect(() => { loadGoals() }, [loadGoals])

    // Load goal detail when expanded
    const toggleGoal = async (goalId) => {
        if (expandedGoalId === goalId) {
            setExpandedGoalId(null)
            setGoalDetail(null)
            return
        }
        setExpandedGoalId(goalId)
        setDetailLoading(true)
        try {
            const { data } = await getGoal(goalId)
            setGoalDetail(data)
            // Load stats for each habit
            const sMap = {}
            for (const h of data.habits || []) {
                try { const { data: s } = await getHabitStats(h.id); sMap[h.id] = s }
                catch { sMap[h.id] = null }
            }
            setHabitStatsMap(sMap)
        } catch (err) { console.error(err) }
        finally { setDetailLoading(false) }
    }

    // Reload the currently expanded goal detail
    const reloadDetail = async () => {
        if (!expandedGoalId) return
        try {
            const { data } = await getGoal(expandedGoalId)
            setGoalDetail(data)
            const sMap = {}
            for (const h of data.habits || []) {
                try { const { data: s } = await getHabitStats(h.id); sMap[h.id] = s }
                catch { sMap[h.id] = null }
            }
            setHabitStatsMap(sMap)
        } catch (err) { console.error(err) }
    }

    // Goal handlers
    const handleGoalSubmit = async (e) => {
        e.preventDefault()
        try {
            await createGoal(goalForm)
            setShowGoalForm(false)
            setGoalForm({ goal_title: '', goal_description: '', goal_category: 'personal', start_date: new Date().toISOString().slice(0, 10), target_date: '', priority: 3 })
            loadGoals()
        } catch (err) { console.error(err) }
    }

    const updateProgress = async (id, delta) => {
        const goal = goals.find(g => g.id === id)
        if (!goal) return
        const np = Math.max(0, Math.min(100, goal.progress + delta))
        try { await updateGoal(id, { progress: np }); loadGoals() }
        catch (err) { console.error(err) }
    }

    const handleMarkComplete = async (id) => {
        try {
            await updateGoal(id, { progress: 100, status: 'completed' })
            loadGoals()
        } catch (err) { console.error(err) }
    }

    const handleDeleteGoal = async (id) => {
        if (!confirm('Delete this goal and all its habits?')) return
        try {
            await deleteGoal(id)
            if (expandedGoalId === id) { setExpandedGoalId(null); setGoalDetail(null) }
            loadGoals()
        } catch (err) { console.error(err) }
    }

    // Habit handlers
    const handleHabitSubmit = async (e, goalId) => {
        e.preventDefault()
        if (!habitForm.habit_name.trim()) return
        try {
            await createHabit({ ...habitForm, goal_id: goalId })
            setHabitForm({ habit_name: '', habit_description: '', habit_category: '', target_frequency: 'daily' })
            setShowHabitFormForGoal(null)
            reloadDetail()
            loadGoals() // refresh habit_count
        } catch (err) { console.error(err) }
    }

    const handleLog = async (habitId) => {
        try {
            await logHabit(habitId, { completed: true })
            reloadDetail()
        } catch (err) { console.error(err) }
    }

    const handleDeleteHabit = async (id) => {
        if (!confirm('Delete this habit and unlink its sessions?')) return
        try {
            await deleteHabit(id)
            reloadDetail()
            loadGoals()
        } catch (err) { console.error(err) }
    }

    const daysLeft = (targetDate) => {
        if (!targetDate) return null
        const diff = Math.ceil((new Date(targetDate) - new Date()) / (1000 * 60 * 60 * 24))
        return diff > 0 ? diff : 0
    }

    const formatMins = (mins) => {
        if (!mins) return '0m'
        const h = Math.floor(mins / 60)
        const m = mins % 60
        return h > 0 ? `${h}h ${m}m` : `${m}m`
    }

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Goals</h1>
                    <p className="text-sm text-gray-500 mt-0.5">Goal &rarr; Habit &rarr; Session hierarchy</p>
                </div>
                <div className="flex gap-2">
                    <div className="flex border border-gray-200 rounded-lg overflow-hidden">
                        {['active', 'completed', 'all'].map(f => (
                            <button key={f} onClick={() => setGoalFilter(f)}
                                className={`px-3 py-2 text-sm font-medium capitalize transition-colors ${
                                    goalFilter === f
                                        ? 'bg-black text-white'
                                        : 'text-gray-500 hover:bg-gray-100'
                                }`}>
                                {f}
                            </button>
                        ))}
                    </div>
                    <button onClick={() => setShowGoalForm(!showGoalForm)}
                        className={showGoalForm ? 'btn-secondary' : 'btn-primary'}>
                        {showGoalForm ? 'Cancel' : '+ New Goal'}
                    </button>
                </div>
            </div>

            {/* Goal Form */}
            {showGoalForm && (
                <form onSubmit={handleGoalSubmit} className="card p-6 space-y-4 animate-in">
                    <input className="input-field" placeholder="Goal title — the big 'Why'" required
                        value={goalForm.goal_title}
                        onChange={e => setGoalForm({ ...goalForm, goal_title: e.target.value })} />
                    <textarea className="input-field min-h-[60px] resize-none" placeholder="Description..."
                        value={goalForm.goal_description}
                        onChange={e => setGoalForm({ ...goalForm, goal_description: e.target.value })} />
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                        <select className="input-field" value={goalForm.goal_category}
                            onChange={e => setGoalForm({ ...goalForm, goal_category: e.target.value })}>
                            {['personal', 'health', 'career', 'education', 'finance', 'creative'].map(c => (
                                <option key={c} value={c}>{c}</option>
                            ))}
                        </select>
                        <input type="date" className="input-field" value={goalForm.start_date}
                            onChange={e => setGoalForm({ ...goalForm, start_date: e.target.value })} />
                        <input type="date" className="input-field" value={goalForm.target_date}
                            onChange={e => setGoalForm({ ...goalForm, target_date: e.target.value })} required />
                        <select className="input-field" value={goalForm.priority}
                            onChange={e => setGoalForm({ ...goalForm, priority: parseInt(e.target.value) })}>
                            {[1, 2, 3, 4, 5].map(p => <option key={p} value={p}>{priorityLabel[p]}</option>)}
                        </select>
                    </div>
                    <button type="submit" className="btn-primary w-full">Create Goal</button>
                </form>
            )}

            {/* Goal Cards */}
            <div className="space-y-4">
                {goalsLoading ? (
                    [...Array(2)].map((_, i) => <div key={i} className="h-40 skeleton"></div>)
                ) : goals.length > 0 ? (
                    goals.map(goal => {
                        const isExpanded = expandedGoalId === goal.id
                        return (
                            <div key={goal.id} className="card overflow-hidden">
                                {/* Goal Header — clickable to expand */}
                                <div className="p-5 sm:p-6 cursor-pointer" onClick={() => toggleGoal(goal.id)}>
                                    <div className="flex justify-between items-start">
                                        <div className="flex items-start gap-3 flex-1">
                                            <div className="mt-0.5">
                                                {isExpanded
                                                    ? <ChevronDown className="w-5 h-5 text-gray-400" />
                                                    : <ChevronRight className="w-5 h-5 text-gray-400" />}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h3 className="text-lg font-semibold text-gray-900">{goal.title}</h3>
                                                {goal.description && (
                                                    <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">{goal.description}</p>
                                                )}
                                                <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-gray-500">
                                                    <span className="capitalize">{goal.category}</span>
                                                    <span className="flex items-center gap-1">
                                                        <Flag className="w-3 h-3" /> {priorityLabel[goal.priority]}
                                                    </span>
                                                    <span>{goal.habit_count} habit{goal.habit_count !== 1 ? 's' : ''}</span>
                                                    {goal.target_date && (
                                                        <span className="flex items-center gap-1">
                                                            <Calendar className="w-3 h-3" /> {daysLeft(goal.target_date)}d left
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 ml-3" onClick={e => e.stopPropagation()}>
                                            <span className="text-sm font-semibold text-gray-700">{goal.progress}%</span>
                                            <button onClick={() => handleDeleteGoal(goal.id)}
                                                className="text-gray-400 hover:text-gray-600 transition-colors p-1">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>

                                    {/* Progress Bar */}
                                    <div className="mt-3 ml-8">
                                        <div className="progress-bar-bg">
                                            <div className="progress-bar-fill" style={{ width: `${goal.progress}%` }} />
                                        </div>
                                    </div>
                                </div>

                                {/* Expanded: Habits + Sessions */}
                                {isExpanded && (
                                    <div className="border-t border-gray-200 bg-gray-100/30 animate-in">
                                        {/* Progress actions */}
                                        <div className="px-5 sm:px-6 py-3 flex flex-wrap gap-2 border-b border-gray-200">
                                            {[5, 10, 25].map(v => (
                                                <button key={v} onClick={() => updateProgress(goal.id, v)}
                                                    className="btn-secondary text-xs py-1.5 px-2.5" style={{ minHeight: 'auto' }}>
                                                    +{v}%
                                                </button>
                                            ))}
                                            <button onClick={() => updateProgress(goal.id, -10)}
                                                className="btn-secondary text-xs py-1.5 px-2.5" style={{ minHeight: 'auto' }}>-10%</button>
                                            {goal.progress < 100 && (
                                                <button onClick={() => handleMarkComplete(goal.id)}
                                                    className="btn-primary text-xs py-1.5 px-2.5 sm:ml-auto flex items-center gap-1" style={{ minHeight: 'auto' }}>
                                                    <CheckCircle className="w-3 h-3" /> Complete
                                                </button>
                                            )}
                                        </div>

                                        {/* Habits List */}
                                        <div className="px-5 sm:px-6 py-4">
                                            <div className="flex items-center justify-between mb-3">
                                                <h4 className="text-sm font-semibold text-gray-700">Habits (The "How")</h4>
                                                <button
                                                    onClick={() => setShowHabitFormForGoal(showHabitFormForGoal === goal.id ? null : goal.id)}
                                                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900 transition-colors">
                                                    {showHabitFormForGoal === goal.id
                                                        ? <><X className="w-3 h-3" /> Cancel</>
                                                        : <><Plus className="w-3 h-3" /> Add Habit</>}
                                                </button>
                                            </div>

                                            {/* Inline habit form */}
                                            {showHabitFormForGoal === goal.id && (
                                                <form onSubmit={(e) => handleHabitSubmit(e, goal.id)}
                                                    className="card p-4 space-y-3 mb-4 animate-in bg-white">
                                                    <input placeholder="Habit name — the recurring 'How'"
                                                        value={habitForm.habit_name}
                                                        onChange={e => setHabitForm({ ...habitForm, habit_name: e.target.value })}
                                                        className="input-field" required />
                                                    <input placeholder="Description (optional)"
                                                        value={habitForm.habit_description}
                                                        onChange={e => setHabitForm({ ...habitForm, habit_description: e.target.value })}
                                                        className="input-field" />
                                                    <div className="flex gap-2 flex-wrap">
                                                        {categories.map(cat => (
                                                            <button key={cat} type="button"
                                                                onClick={() => setHabitForm({ ...habitForm, habit_category: cat })}
                                                                className={`px-2 py-1 rounded-lg text-xs capitalize transition-colors ${
                                                                    habitForm.habit_category === cat
                                                                        ? 'bg-black text-white'
                                                                        : 'text-gray-600 border border-gray-200 hover:bg-gray-100'
                                                                }`}>
                                                                {habitIcons[cat] || '✨'} {cat}
                                                            </button>
                                                        ))}
                                                    </div>
                                                    <div className="flex gap-2 flex-wrap">
                                                        {['daily', '3x_per_week', 'weekly'].map(f => (
                                                            <button key={f} type="button"
                                                                onClick={() => setHabitForm({ ...habitForm, target_frequency: f })}
                                                                className={`px-2 py-1 rounded-lg text-xs transition-colors ${
                                                                    habitForm.target_frequency === f
                                                                        ? 'bg-black text-white'
                                                                        : 'text-gray-600 border border-gray-200 hover:bg-gray-100'
                                                                }`}>
                                                                {f.replace(/_/g, ' ')}
                                                            </button>
                                                        ))}
                                                    </div>
                                                    <button type="submit" className="btn-primary w-full text-sm">Create Habit</button>
                                                </form>
                                            )}

                                            {detailLoading ? (
                                                <div className="space-y-3">
                                                    {[...Array(2)].map((_, i) => <div key={i} className="h-28 skeleton" />)}
                                                </div>
                                            ) : goalDetail?.habits?.length > 0 ? (
                                                <div className="space-y-3">
                                                    {goalDetail.habits.map(habit => {
                                                        const s = habitStatsMap[habit.id]
                                                        const icon = habitIcons[habit.category] || '✨'
                                                        return (
                                                            <HabitCard
                                                                key={habit.id}
                                                                habit={habit}
                                                                stats={s}
                                                                icon={icon}
                                                                onLog={() => handleLog(habit.id)}
                                                                onDelete={() => handleDeleteHabit(habit.id)}
                                                                formatMins={formatMins}
                                                            />
                                                        )
                                                    })}
                                                </div>
                                            ) : (
                                                <p className="text-sm text-gray-400 text-center py-4">
                                                    No habits yet. Add one to start tracking how you'll achieve this goal.
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )
                    })
                ) : (
                    <div className="card p-8 text-center">
                        <p className="text-gray-400">No {goalFilter} goals. Create one to start tracking.</p>
                    </div>
                )}
            </div>
        </div>
    )
}

/** Habit card with weekly calendar and session history */
function HabitCard({ habit, stats, icon, onLog, onDelete, formatMins }) {
    const [showSessions, setShowSessions] = useState(false)
    const s = stats

    return (
        <div className="card p-4 bg-white">
            <div className="flex justify-between items-start">
                <div className="flex items-start gap-2">
                    <span className="text-xl">{icon}</span>
                    <div>
                        <h5 className="text-sm font-semibold text-gray-900">{habit.name}</h5>
                        <p className="text-xs text-gray-500">
                            {habit.frequency?.replace(/_/g, ' ')}
                            {habit.total_sessions > 0 && (
                                <> &middot; {habit.total_sessions} session{habit.total_sessions !== 1 ? 's' : ''} &middot; {formatMins(habit.total_minutes)}</>
                            )}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-1">
                    <button onClick={onDelete}
                        className="text-gray-400 hover:text-gray-600 transition-colors p-1">
                        <Trash2 className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>

            {/* Streak + Stats Row */}
            <div className="flex items-center gap-4 mt-3 text-xs">
                <div>
                    <span className="text-lg font-bold text-gray-900">{s?.current_streak || 0}</span>
                    <span className="text-gray-500 ml-1">day streak {(s?.current_streak || 0) > 3 ? '🔥' : ''}</span>
                </div>
                <div className="h-4 w-px bg-gray-200" />
                <span className="text-gray-500">Best: {s?.longest_streak || 0}d</span>
                <span className="text-gray-500">{s ? Math.round(s.completion_rate * 100) : 0}%</span>
            </div>

            {/* Weekly Calendar */}
            <div className="mt-3">
                <div className="grid grid-cols-7 gap-1">
                    {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, i) => {
                        const now = new Date()
                        const todayDow = now.getDay()
                        const dayIdx = todayDow === 0 ? 6 : todayDow - 1
                        const isToday = i === dayIdx
                        const isFuture = i > dayIdx

                        const cellDate = new Date(now)
                        cellDate.setDate(now.getDate() - (dayIdx - i))
                        const cellDateStr = cellDate.toLocaleDateString('en-CA')

                        const weekLogs = s?.week_logs || []
                        const isCompleted = weekLogs.includes(cellDateStr)

                        return (
                            <div key={i} className="text-center">
                                <p className="text-[9px] text-gray-400 mb-0.5">{day}</p>
                                <div className={`
                                    w-7 h-7 rounded-full flex items-center justify-center mx-auto text-[10px]
                                    ${isCompleted ? 'bg-success' :
                                      isToday ? 'border-2 border-black' :
                                      isFuture ? 'bg-gray-100' :
                                      'bg-gray-200'}
                                `}>
                                    {isCompleted && <Check className="w-3 h-3 text-white" />}
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 mt-3">
                <button onClick={onLog} className="btn-primary text-xs py-1.5 px-3" style={{ minHeight: 'auto' }}>
                    Log Today
                </button>
                {habit.sessions?.length > 0 && (
                    <button onClick={() => setShowSessions(!showSessions)}
                        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors">
                        <Clock className="w-3 h-3" />
                        {showSessions ? 'Hide' : 'Sessions'}
                    </button>
                )}
            </div>

            {/* Session History (The "Proof") */}
            {showSessions && habit.sessions?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200 space-y-1.5 animate-in">
                    <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Recent Sessions (Proof)</p>
                    {habit.sessions.map(session => (
                        <div key={session.id} className="flex items-center justify-between text-xs text-gray-600">
                            <div className="flex items-center gap-2">
                                <span className="text-gray-400 font-mono text-[10px]">
                                    {session.started_at?.slice(5, 10)} {session.started_at?.slice(11, 16)}
                                </span>
                                <span>{session.context_name}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="font-mono">{formatMins(session.duration_minutes)}</span>
                                {session.productivity_rating && (
                                    <span className="text-gray-400">{session.productivity_rating}/10</span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
