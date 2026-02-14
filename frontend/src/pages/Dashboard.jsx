import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Plus, MessageCircle, TrendingUp, Sparkles, Calendar } from 'lucide-react'
import { getDashboardData, getStats, getPredictionStatus, getInsights, getHabits, getHabitStats, predictMood } from '../api'

const moodEmoji = (v) => {
    if (v >= 9) return '😄'
    if (v >= 7) return '😊'
    if (v >= 5) return '😐'
    if (v >= 3) return '😔'
    return '😢'
}

const ChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
        <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs shadow-lg">
            <p className="text-gray-500">{label}</p>
            {payload.map((p, i) => (
                <p key={i} className="text-gray-900 font-medium mt-0.5">
                    {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
                </p>
            ))}
        </div>
    )
}

export default function Dashboard() {
    const navigate = useNavigate()
    const [data, setData] = useState(null)
    const [stats, setStats] = useState(null)
    const [mlStatus, setMlStatus] = useState(null)
    const [habits, setHabits] = useState([])
    const [habitStats, setHabitStats] = useState({})
    const [moodPrediction, setMoodPrediction] = useState(null)
    const [insights, setInsights] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchAll = async () => {
            try {
                const [dashRes, statsRes, mlRes, habitsRes, insightsRes] = await Promise.allSettled([
                    getDashboardData(),
                    getStats(),
                    getPredictionStatus(),
                    getHabits(),
                    getInsights(),
                ])
                if (dashRes.status === 'fulfilled') setData(dashRes.value.data)
                if (statsRes.status === 'fulfilled') setStats(statsRes.value.data)
                if (mlRes.status === 'fulfilled') setMlStatus(mlRes.value.data)
                if (insightsRes.status === 'fulfilled') {
                    const ins = insightsRes.value.data
                    setInsights(Array.isArray(ins) ? ins.slice(0, 3) : [])
                }

                // Fetch habit stats
                if (habitsRes.status === 'fulfilled') {
                    const habitsData = habitsRes.value.data
                    setHabits(habitsData)
                    const sMap = {}
                    for (const h of habitsData) {
                        try {
                            const { data: s } = await getHabitStats(h.id)
                            sMap[h.id] = s
                        } catch { sMap[h.id] = null }
                    }
                    setHabitStats(sMap)
                }

                // Predict tomorrow's mood
                try {
                    const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10)
                    const predRes = await predictMood(tomorrow)
                    setMoodPrediction(predRes.data)
                } catch { /* prediction not available yet */ }
            } catch (err) { console.error(err) }
            finally { setLoading(false) }
        }
        fetchAll()
    }, [])

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="h-6 skeleton w-48"></div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                    <div className="h-48 skeleton"></div>
                    <div className="h-48 skeleton"></div>
                </div>
                <div className="h-64 skeleton"></div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                    <div className="h-40 skeleton"></div>
                    <div className="h-40 skeleton"></div>
                </div>
            </div>
        )
    }

    const moodTrend = data?.mood_trend || []
    const todayMood = moodTrend.length > 0 ? moodTrend[moodTrend.length - 1]?.mood : null
    const todayEnergy = data?.average_energy || null
    const today = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })

    return (
        <div className="space-y-8">
            {/* Top Row: Snapshot + Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Today's Snapshot */}
                <div className="card p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">Today's Snapshot</h2>

                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <span className="text-4xl">{moodEmoji(todayMood || 7)}</span>
                            <div>
                                <p className="text-sm text-gray-500">Current Mood</p>
                                <p className="text-xl font-semibold text-gray-900">{todayMood ? `${todayMood}/10` : '--'}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <span className="text-4xl">⚡</span>
                            <div>
                                <p className="text-sm text-gray-500">Energy Level</p>
                                <p className="text-xl font-semibold text-gray-900">{todayEnergy ? `${Math.round(todayEnergy)}/10` : '--'}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-2 text-sm text-gray-500">
                            <Calendar className="w-4 h-4" />
                            <span>{today}</span>
                        </div>
                    </div>

                    {/* Tomorrow's prediction */}
                    {moodPrediction?.prediction && (
                        <div className="mt-4 p-3 bg-gray-100 rounded-lg">
                            <p className="text-sm text-gray-600">Tomorrow's prediction</p>
                            <p className="text-lg font-semibold text-gray-900">
                                Mood: {moodPrediction.prediction.toFixed(1)}/10{' '}
                                {moodPrediction.prediction > (todayMood || 7) ? '↗️' : '↘️'}
                            </p>
                            {moodPrediction.confidence && (
                                <p className="text-xs text-gray-500">{(moodPrediction.confidence * 100).toFixed(0)}% confidence</p>
                            )}
                        </div>
                    )}
                </div>

                {/* Quick Actions */}
                <div className="card p-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Quick Actions</h3>

                    <div className="space-y-2">
                        <button
                            className="btn-primary w-full flex items-center justify-start gap-3 py-3"
                            onClick={() => navigate('/journal')}
                        >
                            <Plus className="w-4 h-4" />
                            New Entry
                        </button>

                        <button
                            className="btn-secondary w-full flex items-center justify-start gap-3 py-3"
                            onClick={() => navigate('/chat')}
                        >
                            <MessageCircle className="w-4 h-4" />
                            Chat with AI
                        </button>

                        <button
                            className="btn-ghost w-full flex items-center justify-start gap-3 py-3"
                            onClick={() => navigate('/analytics')}
                        >
                            <TrendingUp className="w-4 h-4" />
                            See Insights
                        </button>
                    </div>
                </div>
            </div>

            {/* Mood Trend Chart */}
            <div className="card p-6">
                <h3 className="font-semibold text-gray-900 mb-4">This Week's Mood</h3>
                {moodTrend.length > 0 ? (
                    <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={moodTrend}>
                            <XAxis
                                dataKey="date"
                                tick={{ fill: '#808080', fontSize: 12 }}
                                tickFormatter={d => d.slice(5)}
                                axisLine={false}
                                tickLine={false}
                            />
                            <YAxis
                                domain={[1, 10]}
                                tick={{ fill: '#808080', fontSize: 12 }}
                                axisLine={false}
                                tickLine={false}
                            />
                            <Tooltip content={<ChartTooltip />} />
                            <Line
                                type="monotone"
                                dataKey="mood"
                                stroke="#000000"
                                strokeWidth={2}
                                dot={{ r: 4, fill: '#000000' }}
                                activeDot={{ r: 6, fill: '#000000', stroke: '#ffffff', strokeWidth: 2 }}
                                name="Mood"
                            />
                        </LineChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-[200px] flex items-center justify-center">
                        <p className="text-sm text-gray-400">No mood data yet. Start journaling to see trends.</p>
                    </div>
                )}
            </div>

            {/* Goals Progress + Habits Streak */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Goals Progress */}
                <div className="card p-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Goals Progress</h3>
                    {data?.goal_progress?.length > 0 ? (
                        <div className="space-y-4">
                            {data.goal_progress.slice(0, 3).map((goal, i) => (
                                <div key={i}>
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="text-gray-700">{goal.title}</span>
                                        <span className="font-semibold text-gray-900">{goal.progress}%</span>
                                    </div>
                                    <div className="progress-bar-bg">
                                        <div className="progress-bar-fill" style={{ width: `${goal.progress}%` }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-gray-400">No active goals. Create one to start tracking.</p>
                    )}
                </div>

                {/* Habits Streak */}
                <div className="card p-6">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="font-semibold text-gray-900">Habits Streak</h3>
                        <button
                            onClick={() => navigate('/goals')}
                            className="btn-link text-sm"
                        >
                            View All Habits →
                        </button>
                    </div>
                    {habits.length > 0 ? (
                        <div className="space-y-3">
                            {habits.slice(0, 4).map(habit => {
                                const s = habitStats[habit.id]
                                return (
                                    <div key={habit.id} className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <span className="text-lg">{
                                                habit.category === 'fitness' ? '🏃' :
                                                habit.category === 'mindfulness' ? '🧘' :
                                                habit.category === 'learning' ? '📚' :
                                                habit.category === 'health' ? '💪' : '✨'
                                            }</span>
                                            <span className="text-sm text-gray-700">{habit.name}</span>
                                        </div>
                                        <span className="text-sm font-semibold text-gray-900">
                                            {s?.current_streak || 0} days {s?.current_streak > 3 ? '🔥' : ''}
                                        </span>
                                    </div>
                                )
                            })}
                        </div>
                    ) : (
                        <p className="text-sm text-gray-400">No habits yet. Add some to start building streaks.</p>
                    )}
                </div>
            </div>

            {/* AI Insights */}
            <div className="card p-6">
                <h3 className="font-semibold text-gray-900 mb-4">
                    <Sparkles className="w-4 h-4 inline mr-2" />
                    AI Insights
                </h3>
                {insights.length > 0 ? (
                    <div className="space-y-4">
                        {insights.map((insight, i) => (
                            <div key={i} className="insight-card">
                                <div className="flex items-start gap-3">
                                    <span className="text-2xl">
                                        {insight.type === 'pattern' ? '💡' :
                                         insight.type === 'warning' ? '⚠️' :
                                         insight.type === 'prediction' ? '📊' : '💡'}
                                    </span>
                                    <div className="flex-1">
                                        <p className="font-medium text-gray-900">{insight.title || 'Insight'}</p>
                                        <p className="text-sm text-gray-600 mt-1">{insight.description || insight.content || JSON.stringify(insight)}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="insight-card">
                        <div className="flex items-start gap-3">
                            <span className="text-2xl">💡</span>
                            <div>
                                <p className="font-medium text-gray-900">Getting started</p>
                                <p className="text-sm text-gray-600 mt-1">
                                    Add more journal entries and track habits to unlock AI-powered insights and patterns.
                                </p>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* ML Status */}
            {mlStatus && (
                <div className="text-center text-xs text-gray-400 py-2">
                    ML Engine: {mlStatus.strategy?.replace(/_/g, ' ')} · {mlStatus.journal_entries || 0} entries · {mlStatus.confidence_level}
                </div>
            )}
        </div>
    )
}
