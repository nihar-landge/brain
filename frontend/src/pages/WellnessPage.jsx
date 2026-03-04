import { useState, useEffect } from 'react'
import { Heart, Moon, Battery, TrendingUp, AlertTriangle, Plus, X } from 'lucide-react'
import { logSleep, getSleepCorrelations, getSleepQuality, getBurnoutRisk } from '../api'
import { useToast } from '../hooks/useToast'

export default function WellnessPage() {
    const [sleepQuality, setSleepQuality] = useState(null)
    const [correlations, setCorrelations] = useState(null)
    const [burnout, setBurnout] = useState(null)
    const [loading, setLoading] = useState(true)
    const [showSleepForm, setShowSleepForm] = useState(false)
    const [sleepForm, setSleepForm] = useState({
        bed_time: '', wake_time: '', quality: 7, awakenings: 0, notes: ''
    })
    const [submitting, setSubmitting] = useState(false)
    const { showToast } = useToast()

    useEffect(() => {
        const fetchAll = async () => {
            const [qualRes, corrRes, burnRes] = await Promise.allSettled([
                getSleepQuality(),
                getSleepCorrelations(),
                getBurnoutRisk(),
            ])
            if (qualRes.status === 'fulfilled') setSleepQuality(qualRes.value.data)
            if (corrRes.status === 'fulfilled') setCorrelations(corrRes.value.data)
            if (burnRes.status === 'fulfilled') setBurnout(burnRes.value.data)
            setLoading(false)
        }
        fetchAll()
    }, [])

    const handleSleepSubmit = async (e) => {
        e.preventDefault()
        if (!sleepForm.bed_time || !sleepForm.wake_time) return
        setSubmitting(true)
        try {
            await logSleep(sleepForm)
            setShowSleepForm(false)
            setSleepForm({ bed_time: '', wake_time: '', quality: 7, awakenings: 0, notes: '' })
            // Refresh data
            const [qualRes, corrRes] = await Promise.allSettled([
                getSleepQuality(), getSleepCorrelations(),
            ])
            if (qualRes.status === 'fulfilled') setSleepQuality(qualRes.value.data)
            if (corrRes.status === 'fulfilled') setCorrelations(corrRes.value.data)
            showToast('Sleep logged!', 'success')
        } catch (err) {
            console.error(err)
            showToast('Failed to log sleep', 'error')
        }
        setSubmitting(false)
    }

    const getRiskColor = (risk) => {
        if (risk >= 70) return 'text-red-500'
        if (risk >= 40) return 'text-yellow-500'
        return 'text-emerald-500'
    }

    const getRiskLabel = (risk) => {
        if (risk >= 70) return 'High Risk'
        if (risk >= 40) return 'Moderate'
        return 'Low Risk'
    }

    if (loading) {
        return (
            <div className="space-y-6 max-w-4xl animate-in">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="h-5 w-24 skeleton rounded"></div>
                        <div className="h-3 w-48 skeleton rounded mt-2"></div>
                    </div>
                    <div className="h-9 w-28 skeleton rounded-lg"></div>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="card p-4 text-center"><div className="w-4 h-4 skeleton rounded-full mx-auto mb-2"></div><div className="h-7 w-16 skeleton rounded mx-auto"></div><div className="h-3 w-20 skeleton rounded mx-auto mt-2"></div></div>
                    <div className="card p-4 text-center"><div className="w-4 h-4 skeleton rounded-full mx-auto mb-2"></div><div className="h-7 w-16 skeleton rounded mx-auto"></div><div className="h-3 w-20 skeleton rounded mx-auto mt-2"></div></div>
                    <div className="card p-4 text-center col-span-2 sm:col-span-1"><div className="w-4 h-4 skeleton rounded-full mx-auto mb-2"></div><div className="h-7 w-16 skeleton rounded mx-auto"></div><div className="h-3 w-20 skeleton rounded mx-auto mt-2"></div></div>
                </div>
                <div className="card p-6"><div className="h-4 w-40 skeleton rounded mb-4"></div><div className="space-y-3"><div className="h-8 skeleton rounded"></div><div className="h-8 skeleton rounded"></div><div className="h-8 skeleton rounded"></div></div></div>
            </div>
        )
    }

    return (
        <div className="space-y-6 max-w-4xl">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-lg font-medium text-[var(--text-primary)]">Wellness</h1>
                    <p className="text-[13px] text-[var(--text-muted)] mt-1">Sleep tracking &amp; burnout monitoring</p>
                </div>
                <button
                    onClick={() => setShowSleepForm(!showSleepForm)}
                    className={showSleepForm ? 'btn-secondary text-[13px]' : 'btn-primary text-[13px]'}
                >
                    {showSleepForm ? 'Cancel' : <>
                        <span className="flex items-center gap-1.5"><Plus className="w-4 h-4" /> Log Sleep</span>
                    </>}
                </button>
            </div>

            {/* Sleep Log Form */}
            {showSleepForm && (
                <form onSubmit={handleSleepSubmit} className="card p-5 space-y-4 animate-in">
                    <h3 className="text-sm font-medium text-[var(--text-primary)]">Log Last Night's Sleep</h3>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="text-[11px] text-[var(--text-muted)] mb-1 block">Bed Time</label>
                            <input type="datetime-local" value={sleepForm.bed_time}
                                onChange={e => setSleepForm({ ...sleepForm, bed_time: e.target.value })}
                                className="input-field" />
                        </div>
                        <div>
                            <label className="text-[11px] text-[var(--text-muted)] mb-1 block">Wake Time</label>
                            <input type="datetime-local" value={sleepForm.wake_time}
                                onChange={e => setSleepForm({ ...sleepForm, wake_time: e.target.value })}
                                className="input-field" />
                        </div>
                    </div>
                    <div>
                        <label className="text-[11px] text-[var(--text-muted)] mb-1 block">
                            Quality: {sleepForm.quality}/10
                        </label>
                        <input type="range" min="1" max="10" value={sleepForm.quality}
                            onChange={e => setSleepForm({ ...sleepForm, quality: parseInt(e.target.value) })} />
                    </div>
                    <div>
                        <label className="text-[11px] text-[var(--text-muted)] mb-1 block">Awakenings</label>
                        <input type="number" min="0" max="20" value={sleepForm.awakenings}
                            onChange={e => setSleepForm({ ...sleepForm, awakenings: parseInt(e.target.value) })}
                            className="input-field" placeholder="How many times did you wake up?" />
                    </div>
                    <input placeholder="Notes (optional)" value={sleepForm.notes}
                        onChange={e => setSleepForm({ ...sleepForm, notes: e.target.value })}
                        className="input-field" />
                    <button type="submit" className="btn-primary w-full" disabled={submitting}>
                        {submitting ? 'Saving...' : 'Save Sleep Log'}
                    </button>
                </form>
            )}

            {/* Top Stats Row */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {/* Sleep Quality */}
                <div className="card p-4 text-center">
                    <Moon className="w-4 h-4 text-[var(--text-muted)] mx-auto mb-2" />
                    <p className="text-2xl font-bold text-[var(--text-primary)]">
                        {sleepQuality?.score != null ? `${Math.round(sleepQuality.score)}/100` : '--'}
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)] mt-1">Sleep Quality</p>
                </div>

                {/* Avg Duration */}
                <div className="card p-4 text-center">
                    <Heart className="w-4 h-4 text-[var(--text-muted)] mx-auto mb-2" />
                    <p className="text-2xl font-bold text-[var(--text-primary)]">
                        {sleepQuality?.avg_duration != null ? `${sleepQuality.avg_duration.toFixed(1)}h` : '--'}
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)] mt-1">Avg Sleep</p>
                </div>

                {/* Burnout Risk */}
                <div className="card p-4 text-center col-span-2 sm:col-span-1">
                    <AlertTriangle className="w-4 h-4 text-[var(--text-muted)] mx-auto mb-2" />
                    <p className={`text-2xl font-bold ${burnout?.risk_score != null ? getRiskColor(burnout.risk_score) : 'text-[var(--text-primary)]'}`}>
                        {burnout?.risk_score != null ? `${Math.round(burnout.risk_score)}%` : '--'}
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)] mt-1">
                        Burnout {burnout?.risk_score != null ? `· ${getRiskLabel(burnout.risk_score)}` : ''}
                    </p>
                </div>
            </div>

            {/* Burnout Factors */}
            {burnout?.factors && (
                <div className="card p-4 sm:p-6">
                    <h3 className="font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                        <Battery className="w-4 h-4" />
                        Burnout Risk Factors
                    </h3>
                    <div className="space-y-3">
                        {Object.entries(burnout.factors).map(([factor, value]) => (
                            <div key={factor}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-[var(--text-secondary)] capitalize">{factor.replace(/_/g, ' ')}</span>
                                    <span className="text-[var(--text-muted)]">{typeof value === 'number' ? `${Math.round(value)}%` : value}</span>
                                </div>
                                {typeof value === 'number' && (
                                    <div className="h-1.5 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${value >= 70 ? 'bg-red-400' : value >= 40 ? 'bg-yellow-400' : 'bg-emerald-400'}`}
                                            style={{ width: `${Math.min(100, value)}%` }}
                                        />
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                    {burnout?.recommendations && (
                        <div className="mt-4 pt-4 border-t border-[var(--border-primary)]">
                            <p className="text-[11px] text-[var(--text-muted)] mb-2">Recommendations</p>
                            <ul className="space-y-1">
                                {(Array.isArray(burnout.recommendations) ? burnout.recommendations : [burnout.recommendations]).map((rec, i) => (
                                    <li key={i} className="text-sm text-[var(--text-secondary)] flex items-start gap-2">
                                        <span className="text-emerald-500 mt-0.5">•</span>
                                        {typeof rec === 'string' ? rec : rec.suggestion || JSON.stringify(rec)}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {/* Sleep-Mood Correlations */}
            <div className="card p-4 sm:p-6">
                <h3 className="font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Sleep ↔ Mood Correlations
                </h3>
                {correlations?.correlations ? (
                    <div className="space-y-3">
                        {Object.entries(correlations.correlations).map(([metric, data]) => (
                            <div key={metric} className="p-3 bg-[var(--bg-secondary)] rounded-lg">
                                <p className="text-sm font-medium text-[var(--text-primary)] capitalize">{metric.replace(/_/g, ' ')}</p>
                                <p className="text-xs text-[var(--text-secondary)] mt-1">
                                    {typeof data === 'object' ? (data.insight || data.description || JSON.stringify(data)) : data}
                                </p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="py-8 text-center">
                        <Moon className="w-10 h-10 text-[var(--text-muted)] mx-auto mb-3 opacity-40" />
                        <p className="text-sm font-medium text-[var(--text-secondary)]">
                            No correlation data yet
                        </p>
                        <p className="text-xs text-[var(--text-muted)] mt-1">
                            Log a few nights of sleep to see how it affects your mood and energy.
                        </p>
                        <button
                            onClick={() => setShowSleepForm(true)}
                            className="btn-primary text-xs mt-4"
                        >
                            <span className="flex items-center gap-1.5"><Plus className="w-3.5 h-3.5" /> Log Sleep</span>
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
