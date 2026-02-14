import { useState, useEffect } from 'react'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Brain, Loader2 } from 'lucide-react'
import { predictMood, getEnergyForecast, getPatterns, getPredictionStatus } from '../api'

const ChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
        <div className="card px-3 py-2 text-[11px]">
            <p className="text-text-muted">{label}</p>
            {payload.map((p, i) => (
                <p key={i} className="text-text font-medium mt-0.5">
                    {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
                </p>
            ))}
        </div>
    )
}

export default function PredictionsPage() {
    const [mlStatus, setMlStatus] = useState(null)
    const [moodPrediction, setMoodPrediction] = useState(null)
    const [energyForecast, setEnergyForecast] = useState(null)
    const [patterns, setPatterns] = useState(null)
    const [predDate, setPredDate] = useState(new Date(Date.now() + 86400000).toISOString().slice(0, 10))
    const [loading, setLoading] = useState({ status: true, mood: false, energy: true, patterns: true })

    useEffect(() => {
        const load = async () => {
            try {
                const [statusRes, energyRes, patternRes] = await Promise.allSettled([
                    getPredictionStatus(),
                    getEnergyForecast(7),
                    getPatterns('mood', 90),
                ])
                if (statusRes.status === 'fulfilled') setMlStatus(statusRes.value.data)
                if (energyRes.status === 'fulfilled') setEnergyForecast(energyRes.value.data)
                if (patternRes.status === 'fulfilled') setPatterns(patternRes.value.data)
            } catch (err) { console.error(err) }
            finally { setLoading(prev => ({ ...prev, status: false, energy: false, patterns: false })) }
        }
        load()
    }, [])

    const handlePredict = async () => {
        setLoading(prev => ({ ...prev, mood: true }))
        try {
            const res = await predictMood(predDate)
            setMoodPrediction(res.data)
        } catch (err) { console.error(err) }
        finally { setLoading(prev => ({ ...prev, mood: false })) }
    }

    const dayAbbrevs = patterns?.day_of_week_averages ? Object.entries(patterns.day_of_week_averages).map(([day, avg]) => ({ day, avg })) : []

    return (
        <div className="space-y-6 max-w-3xl">
            {/* Header */}
            <div>
                <h1 className="text-lg font-medium text-text">Predictions</h1>
                <p className="text-[13px] text-text-muted mt-1">AI-powered pattern insights</p>
            </div>

            {/* ML Status */}
            <div className="card p-5">
                <div className="flex items-center gap-2 mb-4">
                    <Brain className="w-4 h-4 text-text-muted" />
                    <span className="text-[13px] text-text-muted">
                        ML Engine &middot; <span className="text-text capitalize">{mlStatus?.strategy?.replace(/_/g, ' ') || '...'}</span>
                    </span>
                </div>
                <div className="grid grid-cols-4 gap-3">
                    {[
                        { label: 'Entries', value: mlStatus?.journal_entries || 0 },
                        { label: 'Moods', value: mlStatus?.mood_entries || 0 },
                        { label: 'Habits', value: mlStatus?.habit_logs || 0 },
                        { label: 'Confidence', value: mlStatus?.confidence_level || 'None' },
                    ].map(({ label, value }) => (
                        <div key={label} className="text-center py-2 border border-border rounded-md">
                            <p className="text-[14px] font-mono font-medium text-text capitalize">{value}</p>
                            <p className="text-[10px] text-text-faint mt-0.5">{label}</p>
                        </div>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                {/* Mood Prediction */}
                <div className="card p-5">
                    <h3 className="text-[13px] text-text-muted mb-4">Mood Prediction</h3>
                    <div className="flex gap-2 mb-4">
                        <input type="date" className="input-field flex-1" value={predDate}
                            onChange={e => setPredDate(e.target.value)} />
                        <button onClick={handlePredict} disabled={loading.mood} className="btn-primary text-[13px]">
                            {loading.mood ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Predict'}
                        </button>
                    </div>

                    {moodPrediction && (
                        <div className="space-y-3 animate-in">
                            <div className="text-center py-4 border border-border rounded-md">
                                <p className="text-3xl font-mono font-medium text-text">{moodPrediction.prediction?.toFixed(1)}</p>
                                <p className="text-[11px] text-text-faint mt-1">out of 10</p>
                                <div className="flex items-center justify-center gap-2 mt-3">
                                    <div className="h-1 w-16 rounded-full overflow-hidden bg-border">
                                        <div className="h-full rounded-full bg-primary" style={{ width: `${(moodPrediction.confidence || 0) * 100}%` }}></div>
                                    </div>
                                    <span className="text-[11px] font-mono text-text-muted">{((moodPrediction.confidence || 0) * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                            <div className="text-[12px] text-text-muted space-y-1">
                                <p className="text-[11px] text-text-faint">{moodPrediction.method}</p>
                                {moodPrediction.factors?.map((f, i) => <p key={i}>&middot; {f}</p>)}
                            </div>
                        </div>
                    )}
                </div>

                {/* Energy Forecast */}
                <div className="card p-5">
                    <h3 className="text-[13px] text-text-muted mb-4">7-Day Energy</h3>
                    {energyForecast?.forecast?.length > 0 ? (
                        <>
                            <ResponsiveContainer width="100%" height={160}>
                                <AreaChart data={energyForecast.forecast}>
                                    <defs>
                                        <linearGradient id="energyGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#525252" stopOpacity={0.15} />
                                            <stop offset="100%" stopColor="#525252" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="day" tick={{ fill: '#404040', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <YAxis domain={[0, 10]} tick={{ fill: '#404040', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <Tooltip content={<ChartTooltip />} />
                                    <Area type="monotone" dataKey="energy" stroke="#737373" fill="url(#energyGrad)" strokeWidth={1.5} name="Energy"
                                        dot={false} activeDot={{ r: 3, fill: '#d4d4d4', stroke: '#0a0a0a', strokeWidth: 2 }} />
                                </AreaChart>
                            </ResponsiveContainer>
                            <div className="flex justify-between mt-3 text-[11px] text-text-faint">
                                <span>Peak: {energyForecast.peak_days?.join(', ')}</span>
                                <span>Low: {energyForecast.low_days?.join(', ')}</span>
                            </div>
                        </>
                    ) : (
                        <div className="h-[160px] flex items-center justify-center">
                            <p className="text-[13px] text-text-faint">More data needed</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Day of Week */}
            <div className="card p-5">
                <h3 className="text-[13px] text-text-muted mb-4">Mood by Day of Week</h3>
                {dayAbbrevs.length > 0 ? (
                    <>
                        <ResponsiveContainer width="100%" height={180}>
                            <BarChart data={dayAbbrevs}>
                                <XAxis dataKey="day" tick={{ fill: '#404040', fontSize: 10 }} axisLine={false} tickLine={false} />
                                <YAxis domain={[0, 10]} tick={{ fill: '#404040', fontSize: 10 }} axisLine={false} tickLine={false} />
                                <Tooltip content={<ChartTooltip />} />
                                <Bar dataKey="avg" fill="#222222" radius={[3, 3, 0, 0]} name="Avg Mood" />
                            </BarChart>
                        </ResponsiveContainer>
                        {patterns && (
                            <div className="flex justify-between mt-3 text-[11px] text-text-faint">
                                <span>Best: {patterns.best_day}</span>
                                <span>{patterns.data_points} data points</span>
                                <span>Worst: {patterns.worst_day}</span>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="h-[180px] flex items-center justify-center">
                        <p className="text-[13px] text-text-faint">More entries needed</p>
                    </div>
                )}
            </div>
        </div>
    )
}
