import { useState, useEffect } from 'react'
import { CheckCircle2, Circle, Plus, Flame, Trash2, X } from 'lucide-react'
import { getHabits, createHabit, logHabit, getHabitStats, deleteHabit } from '../api'

export default function HabitsPage() {
    const [habits, setHabits] = useState([])
    const [stats, setStats] = useState({})
    const [showForm, setShowForm] = useState(false)
    const [form, setForm] = useState({ habit_name: '', habit_description: '', habit_category: '', target_frequency: 'daily' })
    const [loading, setLoading] = useState(true)

    const fetchHabits = async () => {
        try {
            const { data } = await getHabits()
            setHabits(data)
            const statsMap = {}
            for (const h of data) {
                try {
                    const { data: s } = await getHabitStats(h.id)
                    statsMap[h.id] = s
                } catch { statsMap[h.id] = null }
            }
            setStats(statsMap)
        } catch (e) { console.error(e) }
        setLoading(false)
    }

    useEffect(() => { fetchHabits() }, [])

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!form.habit_name.trim()) return
        await createHabit(form)
        setForm({ habit_name: '', habit_description: '', habit_category: '', target_frequency: 'daily' })
        setShowForm(false)
        fetchHabits()
    }

    const handleLog = async (habitId, completed) => {
        await logHabit(habitId, { completed })
        fetchHabits()
    }

    const handleDelete = async (id) => {
        if (!confirm('Delete this habit?')) return
        await deleteHabit(id)
        fetchHabits()
    }

    const categories = ['health', 'fitness', 'learning', 'mindfulness', 'productivity', 'social']

    return (
        <div className="space-y-6 max-w-3xl">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-lg font-medium text-text">Habits</h1>
                    <p className="text-[13px] text-text-muted mt-1">Daily tracker</p>
                </div>
                <button onClick={() => setShowForm(!showForm)}
                    className={showForm ? 'btn-secondary text-[13px]' : 'btn-primary text-[13px]'}>
                    {showForm ? 'Cancel' : 'New Habit'}
                </button>
            </div>

            {/* Create Form */}
            {showForm && (
                <form onSubmit={handleSubmit} className="card p-5 space-y-4 animate-in">
                    <input placeholder="Habit name" value={form.habit_name}
                        onChange={e => setForm({ ...form, habit_name: e.target.value })}
                        className="input-field" />
                    <input placeholder="Description (optional)" value={form.habit_description}
                        onChange={e => setForm({ ...form, habit_description: e.target.value })}
                        className="input-field" />
                    <div className="flex gap-2 flex-wrap">
                        {categories.map(cat => (
                            <button key={cat} type="button" onClick={() => setForm({ ...form, habit_category: cat })}
                                className={`px-3 py-1.5 rounded-md text-[12px] capitalize transition-colors ${
                                    form.habit_category === cat
                                        ? 'bg-[#e5e5e5] text-black'
                                        : 'text-text-muted border border-border hover:border-border-light'
                                }`}>
                                {cat}
                            </button>
                        ))}
                    </div>
                    <div className="flex gap-2">
                        {['daily', '3x_per_week', 'weekly'].map(f => (
                            <button key={f} type="button" onClick={() => setForm({ ...form, target_frequency: f })}
                                className={`px-3 py-1.5 rounded-md text-[12px] transition-colors ${
                                    form.target_frequency === f
                                        ? 'bg-[#e5e5e5] text-black'
                                        : 'text-text-muted border border-border hover:border-border-light'
                                }`}>
                                {f.replace(/_/g, ' ')}
                            </button>
                        ))}
                    </div>
                    <button type="submit" className="btn-primary w-full">Create Habit</button>
                </form>
            )}

            {/* Today's Checklist */}
            <div>
                <h3 className="text-[12px] text-text-muted mb-3">Today</h3>
                {loading ? (
                    <div className="card p-6 text-center text-[13px] text-text-faint">Loading...</div>
                ) : habits.length === 0 ? (
                    <div className="card p-6 text-center">
                        <p className="text-[13px] text-text-faint">No habits yet</p>
                    </div>
                ) : (
                    <div className="space-y-1">
                        {habits.map((habit) => {
                            const s = stats[habit.id]
                            const todayLogged = s?.current_streak > 0
                            return (
                                <div key={habit.id} className="card px-4 py-3 flex items-center gap-3 group">
                                    <button onClick={() => handleLog(habit.id, true)}
                                        className="flex-shrink-0 transition-colors">
                                        {todayLogged
                                            ? <CheckCircle2 className="w-4 h-4 text-text" />
                                            : <Circle className="w-4 h-4 text-text-faint" />
                                        }
                                    </button>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-[13px] font-medium text-text truncate">{habit.name}</p>
                                        <p className="text-[11px] text-text-faint truncate">
                                            {habit.category && <span className="capitalize">{habit.category}</span>}
                                            {habit.frequency && <span> &middot; {habit.frequency.replace(/_/g, ' ')}</span>}
                                        </p>
                                    </div>
                                    {s && s.current_streak > 0 && (
                                        <div className="flex items-center gap-1 text-[11px] text-text-muted">
                                            <Flame className="w-3 h-3" />
                                            <span className="font-mono">{s.current_streak}</span>
                                        </div>
                                    )}
                                    {s && (
                                        <span className="text-[11px] font-mono text-text-faint">{Math.round(s.completion_rate * 100)}%</span>
                                    )}
                                    <button onClick={() => handleDelete(habit.id)}
                                        className="opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Trash2 className="w-3.5 h-3.5 text-text-faint hover:text-text-muted" />
                                    </button>
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>

            {/* Stats */}
            {habits.length > 0 && (
                <div>
                    <h3 className="text-[12px] text-text-muted mb-3">Stats</h3>
                    <div className="grid grid-cols-3 gap-3">
                        {habits.map(habit => {
                            const s = stats[habit.id]
                            if (!s) return null
                            return (
                                <div key={habit.id} className="card p-4">
                                    <p className="text-[12px] text-text-muted truncate mb-3">{habit.name}</p>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span className="text-[11px] text-text-faint">Streak</span>
                                            <span className="text-[13px] font-mono text-text">{s.current_streak}d</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-[11px] text-text-faint">Rate</span>
                                            <span className="text-[13px] font-mono text-text">{Math.round(s.completion_rate * 100)}%</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-[11px] text-text-faint">Total</span>
                                            <span className="text-[13px] font-mono text-text">{s.total_completed}/{s.total_logs}</span>
                                        </div>
                                        <div className="progress-bar-bg mt-1">
                                            <div className="progress-bar-fill" style={{ width: `${s.completion_rate * 100}%` }} />
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}
        </div>
    )
}
