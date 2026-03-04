import { useState, useEffect } from 'react'
import { FileText, RefreshCw, Calendar, TrendingUp, Sparkles } from 'lucide-react'
import { getWeeklyReport, getMonthlyReport, generateReport } from '../api'
import { useToast } from '../hooks/useToast'

export default function ReportsPage() {
    const [tab, setTab] = useState('weekly')
    const [report, setReport] = useState(null)
    const [loading, setLoading] = useState(true)
    const [generating, setGenerating] = useState(false)
    const { showToast } = useToast()

    const fetchReport = async (type) => {
        setLoading(true)
        try {
            const { data } = type === 'weekly' ? await getWeeklyReport() : await getMonthlyReport()
            setReport(data)
        } catch (err) {
            setReport(null)
        }
        setLoading(false)
    }

    useEffect(() => { fetchReport(tab) }, [tab])

    const handleGenerate = async () => {
        setGenerating(true)
        try {
            await generateReport(tab)
            await fetchReport(tab)
            showToast(`${tab === 'weekly' ? 'Weekly' : 'Monthly'} report generated!`, 'success')
        } catch (err) {
            console.error(err)
            showToast('Failed to generate report', 'error')
        }
        setGenerating(false)
    }

    return (
        <div className="space-y-6 max-w-3xl">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-lg font-medium text-[var(--text-primary)]">Reports</h1>
                    <p className="text-[13px] text-[var(--text-muted)] mt-1">AI-generated life summaries</p>
                </div>
                <button
                    onClick={handleGenerate}
                    disabled={generating}
                    className="btn-primary text-[13px] flex items-center gap-1.5"
                >
                    <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
                    {generating ? 'Generating...' : 'Generate Report'}
                </button>
            </div>

            {/* Tab Toggle */}
            <div className="flex gap-1 p-1 bg-[var(--bg-secondary)] rounded-lg w-fit">
                <button
                    onClick={() => setTab('weekly')}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'weekly'
                        ? 'bg-[var(--color-white)] text-[var(--text-primary)] shadow-sm'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
                        }`}
                >
                    <span className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5" />
                        Weekly
                    </span>
                </button>
                <button
                    onClick={() => setTab('monthly')}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'monthly'
                        ? 'bg-[var(--color-white)] text-[var(--text-primary)] shadow-sm'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
                        }`}
                >
                    <span className="flex items-center gap-1.5">
                        <TrendingUp className="w-3.5 h-3.5" />
                        Monthly
                    </span>
                </button>
            </div>

            {/* Report Content */}
            {loading ? (
                <div className="card p-5 sm:p-8 space-y-6 animate-in">
                    <div className="flex items-start justify-between">
                        <div>
                            <div className="h-5 w-40 skeleton rounded"></div>
                            <div className="h-3 w-28 skeleton rounded mt-2"></div>
                        </div>
                        <div className="w-5 h-5 skeleton rounded"></div>
                    </div>
                    <div className="space-y-3">
                        <div className="h-4 skeleton rounded w-full"></div>
                        <div className="h-4 skeleton rounded w-5/6"></div>
                        <div className="h-4 skeleton rounded w-3/4"></div>
                        <div className="h-4 skeleton rounded w-4/5"></div>
                    </div>
                    <div className="pt-4 border-t border-[var(--border-primary)]">
                        <div className="h-4 w-24 skeleton rounded mb-3"></div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            <div className="p-3 bg-[var(--bg-secondary)] rounded-lg"><div className="h-6 w-10 skeleton rounded mx-auto"></div><div className="h-2 w-16 skeleton rounded mx-auto mt-2"></div></div>
                            <div className="p-3 bg-[var(--bg-secondary)] rounded-lg"><div className="h-6 w-10 skeleton rounded mx-auto"></div><div className="h-2 w-16 skeleton rounded mx-auto mt-2"></div></div>
                            <div className="p-3 bg-[var(--bg-secondary)] rounded-lg"><div className="h-6 w-10 skeleton rounded mx-auto"></div><div className="h-2 w-16 skeleton rounded mx-auto mt-2"></div></div>
                            <div className="p-3 bg-[var(--bg-secondary)] rounded-lg"><div className="h-6 w-10 skeleton rounded mx-auto"></div><div className="h-2 w-16 skeleton rounded mx-auto mt-2"></div></div>
                        </div>
                    </div>
                </div>
            ) : report ? (
                <div className="card p-5 sm:p-8 animate-in">
                    {/* Report Header */}
                    <div className="flex items-start justify-between mb-6">
                        <div>
                            <h2 className="text-base font-semibold text-[var(--text-primary)]">
                                {report.title || `${tab === 'weekly' ? 'Weekly' : 'Monthly'} Report`}
                            </h2>
                            {report.period && (
                                <p className="text-xs text-[var(--text-muted)] mt-1">{report.period}</p>
                            )}
                            {report.generated_at && (
                                <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                                    Generated {new Date(report.generated_at).toLocaleDateString()}
                                </p>
                            )}
                        </div>
                        <FileText className="w-5 h-5 text-[var(--text-muted)]" />
                    </div>

                    {/* Report Sections */}
                    {report.sections ? (
                        <div className="space-y-5">
                            {(Array.isArray(report.sections) ? report.sections : Object.entries(report.sections).map(([k, v]) => ({ title: k, content: v }))).map((section, i) => (
                                <div key={i}>
                                    <h3 className="text-sm font-medium text-[var(--text-primary)] mb-2 capitalize">
                                        {(section.title || '').replace(/_/g, ' ')}
                                    </h3>
                                    <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
                                        {typeof section.content === 'string' ? section.content : JSON.stringify(section.content, null, 2)}
                                    </p>
                                </div>
                            ))}
                        </div>
                    ) : report.content ? (
                        <div className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
                            {report.content}
                        </div>
                    ) : report.summary ? (
                        <div className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
                            {report.summary}
                        </div>
                    ) : (
                        <div className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
                            {JSON.stringify(report, null, 2)}
                        </div>
                    )}

                    {/* Key Metrics */}
                    {report.metrics && (
                        <div className="mt-6 pt-4 border-t border-[var(--border-primary)]">
                            <h3 className="text-sm font-medium text-[var(--text-primary)] mb-3">Key Metrics</h3>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                {Object.entries(report.metrics).map(([key, value]) => (
                                    <div key={key} className="p-3 bg-[var(--bg-secondary)] rounded-lg text-center">
                                        <p className="text-lg font-bold text-[var(--text-primary)]">
                                            {typeof value === 'number' ? value.toFixed(1) : value}
                                        </p>
                                        <p className="text-[11px] text-[var(--text-muted)] capitalize mt-0.5">
                                            {key.replace(/_/g, ' ')}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            ) : (
                <div className="card p-10 text-center animate-in">
                    <div className="w-14 h-14 rounded-2xl bg-[var(--bg-secondary)] flex items-center justify-center mx-auto mb-4">
                        <FileText className="w-7 h-7 text-[var(--text-muted)]" />
                    </div>
                    <p className="text-sm font-medium text-[var(--text-primary)]">
                        No {tab} report yet
                    </p>
                    <p className="text-xs text-[var(--text-muted)] mt-1 max-w-xs mx-auto">
                        Generate an AI-powered summary of your {tab === 'weekly' ? 'week' : 'month'} — including mood trends, habits, and productivity insights.
                    </p>
                    <button
                        onClick={handleGenerate}
                        disabled={generating}
                        className="btn-primary text-xs mt-4 mx-auto"
                    >
                        <span className="flex items-center gap-1.5">
                            <Sparkles className="w-3.5 h-3.5" />
                            Generate Report
                        </span>
                    </button>
                </div>
            )}
        </div>
    )
}
