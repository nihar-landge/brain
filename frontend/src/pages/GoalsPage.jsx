import { useState, useEffect, useCallback } from 'react'
import { CheckCircle, Circle, Clock, Flag, MoreVertical, Plus, Flame, Trash2, Check, Sparkles, Calendar } from 'lucide-react'
import { getGoals, createGoal, updateGoal, getHabits, createHabit, logHabit, getHabitStats, deleteHabit } from '../api'

const priorityLabel = { 1: 'Low', 2: 'Normal', 3: 'Mid', 4: 'High', 5: 'Critical' }
const habitIcons = {
    fitness: '🏃', health: '💪', mindfulness: '🧘',
    learning: '📚', productivity: '⚡', social: '👥',
}

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

    // Habits state
    const [habits, setHabits] = useState([])
    const [habitStatsMap, setHabitStatsMap] = useState({})
    const [habitsLoading, setHabitsLoading] = useState(true)
    const [showHabitForm, setShowHabitForm] = useState(false)
    const [habitForm, setHabitForm] = useState({
        habit_name: '', habit_description: '', habit_category: '', target_frequency: 'daily'
    })

    const categories = ['health', 'fitness', 'learning', 'mindfulness', 'productivity', 'social']

    // Load goals
    const loadGoals = useCallback(async () => {
        try { const res = await getGoals(goalFilter); setGoals(res.data) }
        catch (err) { console.error(err) }
        finally { setGoalsLoading(false) }
    }, [goalFilter])

    // Load habits
    const loadHabits = async () => {
        try {
            const { data } = await getHabits()
            setHabits(data)
            const sMap = {}
            for (const h of data) {
                try { const { data: s } = await getHabitStats(h.id); sMap[h.id] = s }
                catch { sMap[h.id] = null }
            }
            setHabitStatsMap(sMap)
        } catch (e) { console.error(e) }
        setHabitsLoading(false)
    }

    useEffect(() => { loadGoals() }, [loadGoals])
    useEffect(() => { loadHabits() }, [])

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

    // Habit handlers
    const handleHabitSubmit = async (e) => {
        e.preventDefault()
        if (!habitForm.habit_name.trim()) return
        await createHabit(habitForm)
        setHabitForm({ habit_name: '', habit_description: '', habit_category: '', target_frequency: 'daily' })
        setShowHabitForm(false)
        loadHabits()
    }

    const handleLog = async (habitId) => {
        await logHabit(habitId, { completed: true })
        loadHabits()
    }

    const handleDeleteHabit = async (id) => {
        if (!confirm('Delete this habit?')) return
        await deleteHabit(id)
        loadHabits()
    }

    const daysLeft = (targetDate) => {
        if (!targetDate) return null
        const diff = Math.ceil((new Date(targetDate) - new Date()) / (1000 * 60 * 60 * 24))
        return diff > 0 ? diff : 0
    }

    return (
        <div className="space-y-10 max-w-4xl mx-auto">
            {/* ============ GOALS SECTION ============ */}
            <section>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">Goals</h2>
                    <div className="flex gap-2">
                        <div className="flex border border-gray-200 rounded-lg overflow-hidden">
                            {['active', 'completed', 'all'].map(f => (
                                <button key={f} onClick={() => setGoalFilter(f)}
                                    className={`px-3 py-2 text-sm font-medium capitalize transition-colors ${
                                        goalFilter === f
                                            ? 'bg-black text-white'
                                            : 'text-gray-500 hover:bg-gray-50'
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
                    <form onSubmit={handleGoalSubmit} className="card p-6 space-y-4 mb-6 animate-in">
                        <input className="input-field" placeholder="Goal title" required
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
                        goals.map(goal => (
                            <div key={goal.id} className="card p-6">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-start gap-3">
                                        <span className="text-3xl">🎯</span>
                                        <div>
                                            <h3 className="text-xl font-semibold text-gray-900">{goal.title}</h3>
                                            {goal.description && (
                                                <p className="text-sm text-gray-500 mt-0.5">{goal.description}</p>
                                            )}
                                            <p className="text-sm text-gray-500 capitalize">{goal.category}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Progress Bar */}
                                <div className="mb-4">
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="text-gray-600">Progress</span>
                                        <span className="font-semibold text-gray-900">{goal.progress}%</span>
                                    </div>
                                    <div className="progress-bar-bg">
                                        <div className="progress-bar-fill" style={{ width: `${goal.progress}%` }} />
                                    </div>
                                </div>

                                {/* Metadata */}
                                <div className="flex flex-wrap gap-3 text-sm text-gray-600 mb-4">
                                    {goal.target_date && (
                                        <>
                                            <span className="flex items-center gap-1">
                                                <Calendar className="w-4 h-4" />
                                                Target: {goal.target_date}
                                            </span>
                                            <span>{daysLeft(goal.target_date)} days left</span>
                                        </>
                                    )}
                                    <span className="flex items-center gap-1">
                                        <Flag className="w-4 h-4" />
                                        {priorityLabel[goal.priority]}
                                    </span>
                                </div>

                                {/* Actions */}
                                <div className="flex flex-wrap gap-2">
                                    {[5, 10, 25].map(v => (
                                        <button key={v} onClick={() => updateProgress(goal.id, v)}
                                            className="btn-secondary text-sm py-2 px-3">
                                            +{v}%
                                        </button>
                                    ))}
                                    <button onClick={() => updateProgress(goal.id, -10)}
                                        className="btn-secondary text-sm py-2 px-3">-10%</button>
                                    {goal.progress < 100 && (
                                        <button onClick={() => updateProgress(goal.id, 100 - goal.progress)}
                                            className="btn-primary text-sm py-2 px-3 sm:ml-auto flex items-center gap-1">
                                            <CheckCircle className="w-4 h-4" />
                                            <span className="hidden sm:inline">Mark</span> Complete
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="card p-8 text-center">
                            <p className="text-gray-400">No {goalFilter} goals. Create one to start tracking.</p>
                        </div>
                    )}
                </div>
            </section>

            {/* ============ HABITS SECTION ============ */}
            <section>
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">Habits</h2>
                    <button onClick={() => setShowHabitForm(!showHabitForm)}
                        className={showHabitForm ? 'btn-secondary' : 'btn-primary'}>
                        {showHabitForm ? 'Cancel' : '+ New Habit'}
                    </button>
                </div>

                {/* Habit Form */}
                {showHabitForm && (
                    <form onSubmit={handleHabitSubmit} className="card p-6 space-y-4 mb-6 animate-in">
                        <input placeholder="Habit name" value={habitForm.habit_name}
                            onChange={e => setHabitForm({ ...habitForm, habit_name: e.target.value })}
                            className="input-field" required />
                        <input placeholder="Description (optional)" value={habitForm.habit_description}
                            onChange={e => setHabitForm({ ...habitForm, habit_description: e.target.value })}
                            className="input-field" />
                        <div>
                            <p className="text-sm text-gray-600 mb-2">Category</p>
                            <div className="flex gap-2 flex-wrap">
                                {categories.map(cat => (
                                    <button key={cat} type="button"
                                        onClick={() => setHabitForm({ ...habitForm, habit_category: cat })}
                                        className={`px-3 py-2 rounded-lg text-sm capitalize transition-colors ${
                                            habitForm.habit_category === cat
                                                ? 'bg-black text-white'
                                                : 'text-gray-600 border border-gray-200 hover:bg-gray-50'
                                        }`}>
                                        {habitIcons[cat] || '✨'} {cat}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div>
                            <p className="text-sm text-gray-600 mb-2">Frequency</p>
                            <div className="flex gap-2 flex-wrap">
                                {['daily', '3x_per_week', 'weekly'].map(f => (
                                    <button key={f} type="button"
                                        onClick={() => setHabitForm({ ...habitForm, target_frequency: f })}
                                        className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                                            habitForm.target_frequency === f
                                                ? 'bg-black text-white'
                                                : 'text-gray-600 border border-gray-200 hover:bg-gray-50'
                                        }`}>
                                        {f.replace(/_/g, ' ')}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <button type="submit" className="btn-primary w-full">Create Habit</button>
                    </form>
                )}

                {/* Habit Cards */}
                <div className="space-y-4">
                    {habitsLoading ? (
                        [...Array(2)].map((_, i) => <div key={i} className="h-48 skeleton"></div>)
                    ) : habits.length > 0 ? (
                        habits.map(habit => {
                            const s = habitStatsMap[habit.id]
                            const icon = habitIcons[habit.category] || '✨'
                            return (
                                <div key={habit.id} className="card p-6">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="flex items-start gap-3">
                                            <span className="text-3xl">{icon}</span>
                                            <div>
                                                <h3 className="text-lg font-semibold text-gray-900">{habit.name}</h3>
                                                <p className="text-sm text-gray-500">{habit.frequency?.replace(/_/g, ' ')}</p>
                                            </div>
                                        </div>
                                        <button onClick={() => handleDeleteHabit(habit.id)}
                                            className="text-gray-400 hover:text-gray-600 transition-colors">
                                            <Trash2 className="w-5 h-5" />
                                        </button>
                                    </div>

                                    {/* Streak Info */}
                                    <div className="flex items-center gap-6 mb-4">
                                        <div>
                                            <p className="text-2xl font-bold text-gray-900">{s?.current_streak || 0}</p>
                                            <p className="text-xs text-gray-500">day streak {(s?.current_streak || 0) > 3 ? '🔥' : ''}</p>
                                        </div>
                                        <div className="h-8 w-px bg-gray-200" />
                                        <div className="space-y-0.5">
                                            <p className="text-sm text-gray-600">Longest: {s?.longest_streak || 0} days</p>
                                            <p className="text-sm text-gray-600">Success: {s ? Math.round(s.completion_rate * 100) : 0}%</p>
                                        </div>
                                    </div>

                                    {/* Weekly Calendar */}
                                    <div className="mb-4">
                                        <p className="text-sm text-gray-600 mb-2">This week</p>
                                        <div className="grid grid-cols-7 gap-1 sm:gap-2">
                                            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, i) => {
                                                const today = new Date().getDay()
                                                const dayIdx = today === 0 ? 6 : today - 1 // Mon=0
                                                const isPast = i < dayIdx
                                                const isToday = i === dayIdx
                                                return (
                                                    <div key={day} className="text-center">
                                                        <p className="text-[10px] sm:text-xs text-gray-500 mb-1">{day}</p>
                                                        <div className={`
                                                            w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center mx-auto
                                                            ${isPast && s?.current_streak > 0 ? 'bg-green-500' :
                                                              isToday ? 'border-2 border-black' :
                                                              'bg-gray-200'}
                                                        `}>
                                                            {isPast && s?.current_streak > 0 && (
                                                                <Check className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                                                            )}
                                                        </div>
                                                    </div>
                                                )
                                            })}
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2">
                                        <button onClick={() => handleLog(habit.id)} className="btn-primary text-sm">
                                            Log Today
                                        </button>
                                        <button className="btn-ghost text-sm">View Stats</button>
                                    </div>
                                </div>
                            )
                        })
                    ) : (
                        <div className="card p-8 text-center">
                            <p className="text-gray-400">No habits yet. Add some to start building streaks.</p>
                        </div>
                    )}
                </div>
            </section>
        </div>
    )
}
