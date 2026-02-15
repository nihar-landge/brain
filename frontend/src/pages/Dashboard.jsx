import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import {
    Plus, MessageCircle, TrendingUp, Sparkles, Calendar, Clock, Users,
    AlertTriangle, Zap, Brain, ArrowUpRight, ArrowDownRight, Timer, FlaskConical,
    Activity, Battery
} from 'lucide-react'
import {
    getDashboardData, getPredictionStatus, getInsights, getHabits, getHabitStats, predictMood,
    getContextSummary, getActiveContext, getDeepWorkBlocks,
    getPeople, getSocialBatteryHistory, getToxicPatterns,
    getCorrelations, getCounterfactuals,
} from '../api'
import { useChartColors } from '../ThemeContext'

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
        <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg px-3 py-2 text-xs shadow-lg">
            <p className="text-[var(--text-muted)]">{label}</p>
            {payload.map((p, i) => (
                <p key={i} className="text-[var(--text-primary)] font-medium mt-0.5">
                    {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
                </p>
            ))}
        </div>
    )
}

function StatCard({ label, value, sub, icon: Icon, onClick }) {
    return (
        <button
            onClick={onClick}
            className="card p-3 sm:p-4 text-left hover:bg-[var(--bg-secondary)] transition-colors w-full"
        >
            <div className="flex items-start justify-between">
                <div className="min-w-0">
                    <p className="text-[10px] sm:text-xs text-[var(--text-muted)] uppercase tracking-wide truncate">{label}</p>
                    <p className="text-xl sm:text-2xl font-bold text-[var(--text-primary)] mt-0.5 sm:mt-1">{value}</p>
                    {sub && <p className="text-[10px] sm:text-xs text-[var(--text-muted)] mt-0.5 sm:mt-1 truncate">{sub}</p>}
                </div>
                {Icon && <Icon className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[var(--text-muted)] flex-shrink-0" />}
            </div>
        </button>
    )
}

export default function Dashboard() {
    const navigate = useNavigate()
    const colors = useChartColors()
    const [data, setData] = useState(null)
    const [mlStatus, setMlStatus] = useState(null)
    const [habits, setHabits] = useState([])
    const [habitStats, setHabitStats] = useState({})
    const [moodPrediction, setMoodPrediction] = useState(null)
    const [insights, setInsights] = useState([])
    const [loading, setLoading] = useState(true)

    // New feature state
    const [contextSummary, setContextSummary] = useState(null)
    const [activeContext, setActiveContext] = useState(null)
    const [deepWork, setDeepWork] = useState([])
    const [people, setPeople] = useState([])
    const [socialBattery, setSocialBattery] = useState([])
    const [toxicPatterns, setToxicPatterns] = useState([])
    const [correlations, setCorrelations] = useState([])
    const [counterfactuals, setCounterfactuals] = useState([])

    useEffect(() => {
        const fetchAll = async () => {
            try {
                const [
                    dashRes, mlRes, habitsRes, insightsRes,
                    ctxRes, activeRes, deepRes,
                    peopleRes, batteryRes, toxicRes,
                    corrRes, cfRes,
                ] = await Promise.allSettled([
                    getDashboardData(),
                    getPredictionStatus(),
                    getHabits(),
                    getInsights(),
                    getContextSummary(),
                    getActiveContext(),
                    getDeepWorkBlocks(7),
                    getPeople(),
                    getSocialBatteryHistory(7),
                    getToxicPatterns(),
                    getCorrelations(30),
                    getCounterfactuals(),
                ])

                if (dashRes.status === 'fulfilled') setData(dashRes.value.data)
                if (mlRes.status === 'fulfilled') setMlStatus(mlRes.value.data)
                if (insightsRes.status === 'fulfilled') {
                    const ins = insightsRes.value.data
                    setInsights(Array.isArray(ins) ? ins.slice(0, 3) : [])
                }
                if (ctxRes.status === 'fulfilled') setContextSummary(ctxRes.value.data)
                if (activeRes.status === 'fulfilled') setActiveContext(activeRes.value.data)
                if (deepRes.status === 'fulfilled') setDeepWork(deepRes.value.data || [])
                if (peopleRes.status === 'fulfilled') setPeople(peopleRes.value.data || [])
                if (batteryRes.status === 'fulfilled') setSocialBattery(batteryRes.value.data || [])
                if (toxicRes.status === 'fulfilled') setToxicPatterns(toxicRes.value.data || [])
                if (corrRes.status === 'fulfilled') setCorrelations(corrRes.value.data?.correlations || [])
                if (cfRes.status === 'fulfilled') setCounterfactuals(cfRes.value.data || [])

                // Fetch habit stats in parallel
                if (habitsRes.status === 'fulfilled') {
                    const habitsData = habitsRes.value.data
                    setHabits(habitsData)
                    const statsResults = await Promise.allSettled(
                        habitsData.map(h => getHabitStats(h.id))
                    )
                    const sMap = {}
                    habitsData.forEach((h, i) => {
                        sMap[h.id] = statsResults[i].status === 'fulfilled' ? statsResults[i].value.data : null
                    })
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
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[...Array(4)].map((_, i) => <div key={i} className="h-24 skeleton"></div>)}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="h-56 skeleton"></div>
                    <div className="h-56 skeleton"></div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {[...Array(3)].map((_, i) => <div key={i} className="h-40 skeleton"></div>)}
                </div>
            </div>
        )
    }

    const moodTrend = data?.mood_trend || []
    const todayMood = moodTrend.length > 0 ? moodTrend[moodTrend.length - 1]?.mood : null
    const todayEnergy = moodTrend.length > 0 ? moodTrend[moodTrend.length - 1]?.energy : null
    const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })

    const totalDeepMins = contextSummary?.deep_work_minutes || 0
    const totalFocusMins = contextSummary?.total_minutes || 0
    const latestBattery = socialBattery.length > 0 ? socialBattery[socialBattery.length - 1]?.battery_level : null

    // Top correlations (significant only, sorted by absolute strength)
    const topCorrelations = correlations
        .filter(c => c.significant)
        .sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
        .slice(0, 4)

    // Top counterfactuals sorted by biggest positive change
    const topCounterfactuals = [...counterfactuals]
        .sort((a, b) => b.change - a.change)
        .slice(0, 2)

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-[var(--text-primary)]">Dashboard</h1>
                    <p className="text-sm text-[var(--text-muted)] mt-0.5 flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5" />
                        {today}
                    </p>
                </div>
                <div className="flex gap-2">
                    <button onClick={() => navigate('/journal')} className="btn-primary flex items-center gap-2 text-sm">
                        <Plus className="w-4 h-4" />
                        <span className="hidden sm:inline">New Entry</span>
                    </button>
                    <button onClick={() => navigate('/chat')} className="btn-secondary flex items-center gap-2 text-sm">
                        <MessageCircle className="w-4 h-4" />
                        <span className="hidden sm:inline">Chat</span>
                    </button>
                </div>
            </div>

            {/* Toxic Pattern Alert Banner */}
            {toxicPatterns.length > 0 && (
                <button
                    onClick={() => navigate('/social')}
                    className="w-full card border-l-4 border-l-red-400 p-4 flex items-start gap-3 text-left hover:bg-[var(--bg-secondary)] transition-colors"
                >
                    <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-[var(--text-primary)]">
                            {toxicPatterns.length} toxic pattern{toxicPatterns.length > 1 ? 's' : ''} detected
                        </p>
                        <p className="text-xs text-[var(--text-muted)] mt-0.5 truncate">
                            {toxicPatterns[0].person_name}: {toxicPatterns[0].suggestion}
                        </p>
                    </div>
                    <ArrowUpRight className="w-4 h-4 text-[var(--text-muted)] flex-shrink-0" />
                </button>
            )}

            {/* Active Timer Banner */}
            {activeContext?.active && (
                <button
                    onClick={() => navigate('/timer')}
                    className="w-full card border-l-4 border-l-emerald-400 p-4 flex items-center gap-3 text-left hover:bg-[var(--bg-secondary)] transition-colors"
                >
                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                    <Timer className="w-4 h-4 text-emerald-600" />
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-[var(--text-primary)]">
                            {activeContext.context_name}
                        </p>
                        <p className="text-xs text-[var(--text-muted)]">
                            {activeContext.context_type} &middot; {activeContext.elapsed_minutes} min elapsed
                        </p>
                    </div>
                    <ArrowUpRight className="w-4 h-4 text-[var(--text-muted)]" />
                </button>
            )}

            {/* Stat Cards Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
                <StatCard
                    label="Mood"
                    value={todayMood ? `${todayMood}/10` : '--'}
                    sub={todayMood ? moodEmoji(todayMood) : 'No data yet'}
                    icon={Activity}
                    onClick={() => navigate('/analytics')}
                />
                <StatCard
                    label="Deep Work"
                    value={totalDeepMins ? `${totalDeepMins}m` : '0m'}
                    sub={`${contextSummary?.total_contexts || 0} sessions`}
                    icon={Zap}
                    onClick={() => navigate('/timer')}
                />
                <StatCard
                    label="Social"
                    value={latestBattery != null ? `${latestBattery}/10` : '--'}
                    sub={`${people.length} tracked`}
                    icon={Battery}
                    onClick={() => navigate('/social')}
                />
                <StatCard
                    label="Energy"
                    value={todayEnergy ? `${Math.round(todayEnergy)}/10` : '--'}
                    sub={moodPrediction?.prediction
                        ? `Tmrw: ${moodPrediction.prediction.toFixed(1)}`
                        : 'No prediction'}
                    icon={TrendingUp}
                    onClick={() => navigate('/analytics')}
                />
            </div>

            {/* Mood Trend + Focus Summary Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
                {/* Mood Trend — takes 2 cols */}
                <div className="card p-4 sm:p-6 md:col-span-2">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-[var(--text-primary)]">Mood This Week</h3>
                        <button onClick={() => navigate('/analytics')} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                            View All &rarr;
                        </button>
                    </div>
                    {moodTrend.length > 0 ? (
                        <ResponsiveContainer width="100%" height={180}>
                            <LineChart data={moodTrend}>
                                <XAxis
                                    dataKey="date"
                                    tick={{ fill: colors.tick, fontSize: 11 }}
                                    tickFormatter={d => d.slice(5)}
                                    axisLine={false}
                                    tickLine={false}
                                />
                                <YAxis domain={[1, 10]} tick={{ fill: colors.tick, fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
                                <Tooltip content={<ChartTooltip />} />
                                <Line type="monotone" dataKey="mood" stroke={colors.line} strokeWidth={2} dot={{ r: 3, fill: colors.line }} activeDot={{ r: 5, fill: colors.line, stroke: colors.bg, strokeWidth: 2 }} name="Mood" />
                                {moodTrend[0]?.energy !== undefined && (
                                    <Line type="monotone" dataKey="energy" stroke={colors.mutedStroke} strokeWidth={1.5} strokeDasharray="4 3" dot={false} name="Energy" />
                                )}
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[180px] flex items-center justify-center">
                            <p className="text-sm text-[var(--text-muted)]">Start journaling to see mood trends.</p>
                        </div>
                    )}
                </div>

                {/* Today's Focus Breakdown */}
                <div className="card p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-[var(--text-primary)]">Today's Focus</h3>
                        <Clock className="w-4 h-4 text-[var(--text-muted)]" />
                    </div>
                    {totalFocusMins > 0 ? (
                        <div className="space-y-3">
                            <div className="text-center">
                                <p className="text-3xl font-bold text-[var(--text-primary)]">{totalFocusMins}m</p>
                                <p className="text-xs text-[var(--text-muted)]">total tracked</p>
                            </div>
                            {/* Type breakdown as horizontal bars */}
                            <div className="space-y-2 mt-4">
                                {Object.entries(contextSummary?.type_breakdown || {})
                                    .sort((a, b) => b[1] - a[1])
                                    .slice(0, 4)
                                    .map(([type, mins]) => (
                                        <div key={type}>
                                            <div className="flex justify-between text-xs mb-1">
                                                <span className="text-[var(--text-secondary)] capitalize">{type.replace(/_/g, ' ')}</span>
                                                <span className="text-[var(--text-muted)]">{mins}m</span>
                                            </div>
                                            <div className="h-1.5 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-[var(--text-primary)] rounded-full transition-all"
                                                    style={{ width: `${Math.min(100, (mins / totalFocusMins) * 100)}%`, opacity: 0.7 }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                            </div>
                            {(contextSummary?.interruptions || 0) > 0 && (
                                <p className="text-xs text-[var(--text-muted)] text-center mt-2">
                                    {contextSummary.interruptions} interruption{contextSummary.interruptions > 1 ? 's' : ''}
                                </p>
                            )}
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center gap-2 py-6">
                            <p className="text-sm text-[var(--text-muted)]">No focus sessions today</p>
                            <button onClick={() => navigate('/timer')} className="text-xs text-accent hover:underline">
                                Start a timer &rarr;
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Goals + Habits + Social Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
                {/* Goals Progress */}
                <div className="card p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-[var(--text-primary)]">Goals</h3>
                        <button onClick={() => navigate('/goals')} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                            View All &rarr;
                        </button>
                    </div>
                    {data?.goal_progress?.length > 0 ? (
                        <div className="space-y-4">
                            {data.goal_progress.slice(0, 3).map((goal, i) => (
                                <div key={i}>
                                    <div className="flex justify-between text-sm mb-1.5">
                                        <span className="text-[var(--text-secondary)] truncate mr-2">{goal.title}</span>
                                        <span className="font-semibold text-[var(--text-primary)] flex-shrink-0">{goal.progress}%</span>
                                    </div>
                                    <div className="progress-bar-bg">
                                        <div className="progress-bar-fill" style={{ width: `${goal.progress}%` }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-[var(--text-muted)]">No active goals.</p>
                    )}
                </div>

                {/* Habits Streak */}
                <div className="card p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-[var(--text-primary)]">Habits</h3>
                        <button onClick={() => navigate('/goals')} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                            View All &rarr;
                        </button>
                    </div>
                    {habits.length > 0 ? (
                        <div className="space-y-3">
                            {habits.slice(0, 4).map(habit => {
                                const s = habitStats[habit.id]
                                return (
                                    <div key={habit.id} className="flex items-center justify-between">
                                        <span className="text-sm text-[var(--text-secondary)] truncate mr-2">{habit.name}</span>
                                        <span className="text-sm font-semibold text-[var(--text-primary)] flex-shrink-0">
                                            {s?.current_streak || 0}d {s?.current_streak > 3 ? '🔥' : ''}
                                        </span>
                                    </div>
                                )
                            })}
                        </div>
                    ) : (
                        <p className="text-sm text-[var(--text-muted)]">No habits yet.</p>
                    )}
                </div>

                {/* Social Pulse */}
                <div className="card p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-[var(--text-primary)]">Social Pulse</h3>
                        <button onClick={() => navigate('/social')} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                            View All &rarr;
                        </button>
                    </div>
                    {people.length > 0 ? (
                        <div className="space-y-3">
                            {people
                                .sort((a, b) => b.total_mentions - a.total_mentions)
                                .slice(0, 4)
                                .map(p => (
                                    <div key={p.id} className="flex items-center justify-between">
                                        <div className="flex items-center gap-2 min-w-0">
                                            <div className="w-6 h-6 rounded-full bg-[var(--bg-secondary)] flex items-center justify-center flex-shrink-0">
                                                <span className="text-xs font-medium text-[var(--text-secondary)]">
                                                    {p.name.charAt(0).toUpperCase()}
                                                </span>
                                            </div>
                                            <span className="text-sm text-[var(--text-secondary)] truncate">{p.name}</span>
                                        </div>
                                        <div className="flex items-center gap-1 flex-shrink-0">
                                            {p.avg_mood_impact != null && (
                                                p.avg_mood_impact >= 0
                                                    ? <ArrowUpRight className="w-3 h-3 text-emerald-500" />
                                                    : <ArrowDownRight className="w-3 h-3 text-red-400" />
                                            )}
                                            <span className="text-xs text-[var(--text-muted)]">
                                                {p.total_mentions} mention{p.total_mentions !== 1 ? 's' : ''}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            {/* Social Battery mini sparkline */}
                            {socialBattery.length > 1 && (
                                <div className="pt-2 border-t border-[var(--border-primary)]">
                                    <p className="text-xs text-[var(--text-muted)] mb-1">Battery this week</p>
                                    <ResponsiveContainer width="100%" height={32}>
                                        <LineChart data={socialBattery}>
                                            <Line type="monotone" dataKey="battery_level" stroke={colors.line} strokeWidth={1.5} dot={false} />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            )}
                        </div>
                    ) : (
                        <p className="text-sm text-[var(--text-muted)]">No people tracked yet. Journal about interactions to start.</p>
                    )}
                </div>
            </div>

            {/* Causal Insights + What-If Row */}
            {(topCorrelations.length > 0 || topCounterfactuals.length > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
                    {/* Top Correlations */}
                    {topCorrelations.length > 0 && (
                        <div className="card p-4 sm:p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-semibold text-[var(--text-primary)] flex items-center gap-2">
                                    <FlaskConical className="w-4 h-4" />
                                    What Drives Your Mood
                                </h3>
                                <button onClick={() => navigate('/causal')} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                                    Explore &rarr;
                                </button>
                            </div>
                            <div className="space-y-3">
                                {topCorrelations.map((c, i) => {
                                    const pct = Math.abs(c.correlation) * 100
                                    const isPositive = c.direction === 'positive'
                                    return (
                                        <div key={i}>
                                            <div className="flex items-center justify-between text-sm mb-1">
                                                <span className="text-[var(--text-secondary)] capitalize">{c.feature.replace(/_/g, ' ')}</span>
                                                <span className={`text-xs font-medium ${isPositive ? 'text-emerald-600' : 'text-red-500'}`}>
                                                    {isPositive ? '+' : '-'}{pct.toFixed(0)}%
                                                </span>
                                            </div>
                                            <div className="h-1.5 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full ${isPositive ? 'bg-emerald-500' : 'bg-red-400'}`}
                                                    style={{ width: `${pct}%`, opacity: 0.7 }}
                                                />
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {/* What-If Counterfactuals */}
                    {topCounterfactuals.length > 0 && (
                        <div className="card p-4 sm:p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-semibold text-[var(--text-primary)] flex items-center gap-2">
                                    <Sparkles className="w-4 h-4" />
                                    What If...
                                </h3>
                                <button onClick={() => navigate('/causal')} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                                    Explore &rarr;
                                </button>
                            </div>
                            <div className="space-y-3">
                                {topCounterfactuals.map((cf, i) => (
                                    <div key={i} className="p-3 bg-[var(--bg-secondary)] rounded-lg">
                                        <p className="text-sm text-[var(--text-secondary)]">{cf.scenario}</p>
                                        <div className="flex items-center gap-2 mt-2">
                                            <span className="text-xs text-[var(--text-muted)]">Mood impact:</span>
                                            <span className={`text-sm font-semibold ${cf.change > 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                                                {cf.change > 0 ? '+' : ''}{cf.change.toFixed(1)}
                                            </span>
                                            <span className="text-xs text-[var(--text-muted)]">({cf.confidence})</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Deep Work This Week */}
            {deepWork.length > 0 && (
                <div className="card p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-[var(--text-primary)] flex items-center gap-2">
                            <Zap className="w-4 h-4" />
                            Deep Work This Week
                        </h3>
                        <button onClick={() => navigate('/timer')} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                            View All &rarr;
                        </button>
                    </div>
                    <ResponsiveContainer width="100%" height={120}>
                        <BarChart data={deepWork.slice(-7)}>
                            <XAxis
                                dataKey="date"
                                tick={{ fill: colors.tick, fontSize: 10 }}
                                tickFormatter={d => d.slice(5)}
                                axisLine={false}
                                tickLine={false}
                            />
                            <YAxis hide />
                            <Tooltip content={<ChartTooltip />} />
                            <Bar dataKey="duration_minutes" name="Minutes" radius={[3, 3, 0, 0]}>
                                {deepWork.slice(-7).map((entry, idx) => (
                                    <Cell
                                        key={idx}
                                        fill={entry.flow_state ? colors.line : colors.mutedStroke}
                                        opacity={entry.flow_state ? 1 : 0.5}
                                    />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                    <div className="flex items-center justify-center gap-4 flex-wrap mt-2 text-xs text-[var(--text-muted)]">
                        <span className="flex items-center gap-1">
                            <span className="inline-block w-2 h-2 rounded-sm" style={{ backgroundColor: colors.line }} /> Flow state
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="inline-block w-2 h-2 rounded-sm" style={{ backgroundColor: colors.mutedStroke, opacity: 0.5 }} /> Deep work
                        </span>
                    </div>
                </div>
            )}

            {/* AI Insights */}
            <div className="card p-4 sm:p-6">
                <h3 className="font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                    <Brain className="w-4 h-4" />
                    AI Insights
                </h3>
                {insights.length > 0 ? (
                    <div className="space-y-3">
                        {insights.map((insight, i) => (
                            <div key={i} className="p-3 bg-[var(--bg-secondary)] rounded-lg">
                                <p className="text-sm font-medium text-[var(--text-primary)]">{insight.title || 'Insight'}</p>
                                <p className="text-xs text-[var(--text-secondary)] mt-1">{insight.description || insight.content || JSON.stringify(insight)}</p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="p-3 bg-[var(--bg-secondary)] rounded-lg">
                        <p className="text-sm text-[var(--text-secondary)]">
                            Add journal entries, track habits, and log focus time to unlock AI insights.
                        </p>
                    </div>
                )}
            </div>

            {/* ML Status Footer */}
            {mlStatus && (
                <div className="text-center text-xs text-[var(--text-muted)] py-2">
                    ML: {mlStatus.strategy?.replace(/_/g, ' ')} &middot; {mlStatus.journal_entries || 0} entries &middot; {mlStatus.confidence_level}
                </div>
            )}
        </div>
    )
}
