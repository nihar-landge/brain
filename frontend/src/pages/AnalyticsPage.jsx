import { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Brain, Loader2, Download, Sparkles } from 'lucide-react'
import { predictMood, getEnergyForecast, getPatterns, getPredictionStatus, getInsights, getDashboardData } from '../api'

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

export default function AnalyticsPage() {
    const [mlStatus, setMlStatus] = useState(null)
    const [moodPrediction, setMoodPrediction] = useState(null)
    const [energyForecast, setEnergyForecast] = useState(null)
    const [patterns, setPatterns] = useState(null)
    const [dashData, setDashData] = useState(null)
    const [insights, setInsights] = useState([])
    const [predDate, setPredDate] = useState(new Date(Date.now() + 86400000).toISOString().slice(0, 10))
    const [loading, setLoading] = useState({ status: true, mood: false, energy: true, patterns: true })
    const [timeRange, setTimeRange] = useState('90')

    useEffect(() => {
        const load = async () => {
            try {
                const [statusRes, energyRes, patternRes, dashRes, insightsRes] = await Promise.allSettled([
                    getPredictionStatus(),
                    getEnergyForecast(7),
                    getPatterns('mood', parseInt(timeRange)),
                    getDashboardData(),
                    getInsights(),
                ])
                if (statusRes.status === 'fulfilled') setMlStatus(statusRes.value.data)
                if (energyRes.status === 'fulfilled') setEnergyForecast(energyRes.value.data)
                if (patternRes.status === 'fulfilled') setPatterns(patternRes.value.data)
                if (dashRes.status === 'fulfilled') setDashData(dashRes.value.data)
                if (insightsRes.status === 'fulfilled') {
                    const ins = insightsRes.value.data
                    setInsights(Array.isArray(ins) ? ins : [])
                }
            } catch (err) { console.error(err) }
            finally { setLoading(prev => ({ ...prev, status: false, energy: false, patterns: false })) }
        }
        load()
    }, [timeRange])

    const handlePredict = async () => {
        setLoading(prev => ({ ...prev, mood: true }))
        try {
            const res = await predictMood(predDate)
            setMoodPrediction(res.data)
        } catch (err) { console.error(err) }
        finally { setLoading(prev => ({ ...prev, mood: false })) }
    }

    const moodTrend = dashData?.mood_trend || []
    const dayAbbrevs = patterns?.day_of_week_averages
        ? Object.entries(patterns.day_of_week_averages).map(([day, avg]) => ({ day, avg }))
        : []
    const habitStats = dashData?.habit_stats || []
    const avgMood = dashData?.average_mood

    return (
        <div className="space-y-8 max-w-5xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Analytics & Insights</h1>
                    <p className="text-sm text-gray-500 mt-1">Patterns, predictions, and correlations</p>
                </div>
            </div>

            {/* Time Range Tabs */}
            <div className="flex gap-2">
                {[
                    { label: 'This Week', value: '7' },
                    { label: 'This Month', value: '30' },
                    { label: 'Last 90 Days', value: '90' },
                    { label: 'All Time', value: '365' },
                ].map(({ label, value }) => (
                    <button key={value}
                        onClick={() => setTimeRange(value)}
                        className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                            timeRange === value
                                ? 'bg-black text-white'
                                : 'text-gray-500 hover:bg-gray-100'
                        }`}>
                        {label}
                    </button>
                ))}
            </div>

            {/* Mood Trends */}
            <div className="card p-6">
                <h3 className="font-semibold text-gray-900 mb-1">Mood Trends</h3>
                {avgMood && (
                    <p className="text-sm text-gray-500 mb-4">
                        Average: <span className="font-semibold text-gray-900">{avgMood.toFixed(1)}/10</span>
                    </p>
                )}
                {moodTrend.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                        <LineChart data={moodTrend}>
                            <XAxis dataKey="date" tick={{ fill: '#808080', fontSize: 12 }} tickFormatter={d => d.slice(5)} axisLine={false} tickLine={false} />
                            <YAxis domain={[1, 10]} tick={{ fill: '#808080', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <Tooltip content={<ChartTooltip />} />
                            <Line type="monotone" dataKey="mood" stroke="#000000" strokeWidth={2} name="Mood"
                                dot={{ r: 3, fill: '#000000' }}
                                activeDot={{ r: 5, fill: '#000000', stroke: '#ffffff', strokeWidth: 2 }} />
                        </LineChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-[250px] flex items-center justify-center">
                        <p className="text-sm text-gray-400">Not enough data yet. Keep journaling to see trends.</p>
                    </div>
                )}
            </div>

            {/* Energy Patterns + Mood by Day */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Energy Forecast */}
                <div className="card p-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Energy Patterns (7 Day)</h3>
                    {energyForecast?.forecast?.length > 0 ? (
                        <>
                            <ResponsiveContainer width="100%" height={200}>
                                <AreaChart data={energyForecast.forecast}>
                                    <defs>
                                        <linearGradient id="energyGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#000000" stopOpacity={0.1} />
                                            <stop offset="100%" stopColor="#000000" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="day" tick={{ fill: '#808080', fontSize: 11 }} axisLine={false} tickLine={false} />
                                    <YAxis domain={[0, 10]} tick={{ fill: '#808080', fontSize: 11 }} axisLine={false} tickLine={false} />
                                    <Tooltip content={<ChartTooltip />} />
                                    <Area type="monotone" dataKey="energy" stroke="#000000" fill="url(#energyGrad)" strokeWidth={2} name="Energy"
                                        dot={{ r: 3, fill: '#000000' }} />
                                </AreaChart>
                            </ResponsiveContainer>
                            <div className="flex justify-between mt-3 text-xs text-gray-500">
                                <span>Peak: {energyForecast.peak_days?.join(', ') || '--'}</span>
                                <span>Low: {energyForecast.low_days?.join(', ') || '--'}</span>
                            </div>
                        </>
                    ) : (
                        <div className="h-[200px] flex items-center justify-center">
                            <p className="text-sm text-gray-400">More data needed</p>
                        </div>
                    )}
                </div>

                {/* Mood by Day of Week */}
                <div className="card p-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Mood by Day of Week</h3>
                    {dayAbbrevs.length > 0 ? (
                        <>
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={dayAbbrevs}>
                                    <XAxis dataKey="day" tick={{ fill: '#808080', fontSize: 11 }} axisLine={false} tickLine={false} />
                                    <YAxis domain={[0, 10]} tick={{ fill: '#808080', fontSize: 11 }} axisLine={false} tickLine={false} />
                                    <Tooltip content={<ChartTooltip />} />
                                    <Bar dataKey="avg" fill="#1a1a1a" radius={[4, 4, 0, 0]} name="Avg Mood" />
                                </BarChart>
                            </ResponsiveContainer>
                            {patterns && (
                                <div className="flex justify-between mt-3 text-xs text-gray-500">
                                    <span>Best: <span className="font-semibold text-gray-700">{patterns.best_day}</span></span>
                                    <span>{patterns.data_points} data points</span>
                                    <span>Worst: <span className="font-semibold text-gray-700">{patterns.worst_day}</span></span>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="h-[200px] flex items-center justify-center">
                            <p className="text-sm text-gray-400">More entries needed</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Correlations / Insights */}
            <div className="card p-6">
                <h3 className="font-semibold text-gray-900 mb-4">
                    <Sparkles className="w-4 h-4 inline mr-2" />
                    Correlations Discovered
                </h3>
                {insights.length > 0 ? (
                    <div className="space-y-4">
                        {insights.map((insight, i) => (
                            <div key={i} className={`insight-card ${
                                insight.type === 'warning' ? 'insight-card-warning' :
                                insight.type === 'success' ? 'insight-card-success' : ''
                            }`}>
                                <div className="flex items-start gap-3">
                                    <span className="text-xl">
                                        {insight.type === 'pattern' ? '💡' :
                                         insight.type === 'warning' ? '⚠️' : '💡'}
                                    </span>
                                    <div>
                                        <p className="font-medium text-gray-900">{insight.title || 'Pattern'}</p>
                                        <p className="text-sm text-gray-600 mt-0.5">
                                            {insight.description || insight.content || JSON.stringify(insight)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-sm text-gray-400">
                        Add more journal entries and track habits to discover correlations.
                    </p>
                )}
            </div>

            {/* Habit Success Analysis */}
            {habitStats.length > 0 && (
                <div className="card p-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Habit Success Analysis</h3>
                    <div className="space-y-3">
                        {habitStats.map((h, i) => (
                            <div key={i}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-700">{h.name}</span>
                                    <span className="font-semibold text-gray-900">{Math.round((h.rate || 0) * 100)}%</span>
                                </div>
                                <div className="progress-bar-bg">
                                    <div className="progress-bar-fill" style={{ width: `${(h.rate || 0) * 100}%` }} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Mood Prediction Tool */}
            <div className="card p-6">
                <h3 className="font-semibold text-gray-900 mb-4">
                    <Brain className="w-4 h-4 inline mr-2" />
                    Mood Prediction
                </h3>
                <div className="flex gap-3 mb-4">
                    <input type="date" className="input-field flex-1" value={predDate}
                        onChange={e => setPredDate(e.target.value)} />
                    <button onClick={handlePredict} disabled={loading.mood} className="btn-primary">
                        {loading.mood ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Predict'}
                    </button>
                </div>

                {moodPrediction && (
                    <div className="animate-in p-4 bg-gray-100 rounded-lg">
                        <div className="text-center py-2">
                            <p className="text-4xl font-bold font-mono text-gray-900">{moodPrediction.prediction?.toFixed(1)}</p>
                            <p className="text-sm text-gray-500 mt-1">out of 10</p>
                            {moodPrediction.confidence && (
                                <div className="flex items-center justify-center gap-2 mt-3">
                                    <div className="h-2 w-24 rounded-full overflow-hidden bg-gray-300">
                                        <div className="h-full rounded-full bg-black"
                                            style={{ width: `${(moodPrediction.confidence || 0) * 100}%` }}></div>
                                    </div>
                                    <span className="text-sm font-mono text-gray-600">
                                        {((moodPrediction.confidence || 0) * 100).toFixed(0)}% confidence
                                    </span>
                                </div>
                            )}
                        </div>
                        {moodPrediction.factors?.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200 text-sm text-gray-600 space-y-1">
                                <p className="text-xs text-gray-500">{moodPrediction.method}</p>
                                {moodPrediction.factors.map((f, i) => <p key={i}>· {f}</p>)}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* ML Status */}
            {mlStatus && (
                <div className="text-center text-xs text-gray-400 py-2">
                    ML Engine: {mlStatus.strategy?.replace(/_/g, ' ')} · {mlStatus.journal_entries || 0} entries · {mlStatus.mood_entries || 0} moods · {mlStatus.confidence_level}
                </div>
            )}
        </div>
    )
}
