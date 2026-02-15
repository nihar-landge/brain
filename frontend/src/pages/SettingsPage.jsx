import { useState, useEffect, useRef } from 'react'
import { Download, Upload, HardDrive, RefreshCw, Trash2, CheckCircle, Info, X, Brain } from 'lucide-react'
import {
    getStats,
    exportData,
    importData,
    createBackup,
    listBackups,
    clearChatHistory,
    retrainModels,
    getModelPerformance,
    getCalendarTimezone,
    updateCalendarTimezone,
    getGoogleCalendarStatus,
    getGoogleCalendarAuthUrl,
    disconnectGoogleCalendar,
    syncGoogleCalendar,
} from '../api'
import { useTheme } from '../ThemeContext'

export default function SettingsPage() {
    const { theme, setTheme } = useTheme()
    const [sysStats, setSysStats] = useState(null)
    const [models, setModels] = useState(null)
    const [backups, setBackups] = useState([])
    const [loading, setLoading] = useState({ export: false, import: false, backup: false, retrain: false, clear: false })
    const [toast, setToast] = useState(null)
    const [timezone, setTimezone] = useState('UTC')
    const [calendarStatus, setCalendarStatus] = useState(null)
    const toastTimerRef = useRef(null)

    const timezoneOptions = [
        'UTC',
        'Asia/Kolkata',
        'Europe/London',
        'Europe/Berlin',
        'America/New_York',
        'America/Los_Angeles',
        'Asia/Singapore',
        'Australia/Sydney',
    ]

    const showToast = (msg, type = 'info') => {
        if (toastTimerRef.current) clearTimeout(toastTimerRef.current)
        setToast({ msg, type })
        toastTimerRef.current = setTimeout(() => setToast(null), 3000)
    }

    useEffect(() => {
        getStats().then(r => setSysStats(r.data)).catch(() => {})
        getModelPerformance().then(r => setModels(r.data)).catch(() => {})
        listBackups().then(r => setBackups(r.data.backups || [])).catch(() => {})
        getCalendarTimezone().then(r => setTimezone(r.data.timezone || 'UTC')).catch(() => {})
        getGoogleCalendarStatus().then(r => setCalendarStatus(r.data)).catch(() => {})
    }, [])

    const handleTimezoneSave = async () => {
        try {
            await updateCalendarTimezone(timezone)
            showToast('Timezone updated', 'success')
        } catch {
            showToast('Failed to update timezone', 'error')
        }
    }

    const handleGoogleConnect = async () => {
        try {
            const { data } = await getGoogleCalendarAuthUrl()
            if (!data?.auth_url) throw new Error('No auth URL')
            window.open(data.auth_url, '_blank', 'noopener,noreferrer')
            showToast('Complete Google auth, then click Sync now', 'info')
        } catch {
            showToast('Google Calendar not configured on server', 'error')
        }
    }

    const handleGoogleDisconnect = async () => {
        try {
            await disconnectGoogleCalendar()
            setCalendarStatus((prev) => prev ? { ...prev, connected: false, calendar_id: null } : prev)
            showToast('Google Calendar disconnected', 'success')
        } catch {
            showToast('Failed to disconnect Google Calendar', 'error')
        }
    }

    const handleGoogleSync = async () => {
        try {
            const { data } = await syncGoogleCalendar()
            showToast(`Synced ${data.synced_tasks} tasks, ${data.synced_sessions} sessions`, 'success')
            getGoogleCalendarStatus().then(r => setCalendarStatus(r.data)).catch(() => {})
        } catch {
            showToast('Google sync failed', 'error')
        }
    }

    const handleExport = async () => {
        setLoading(l => ({ ...l, export: true }))
        try {
            const { data } = await exportData()
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `brain_export_${new Date().toISOString().split('T')[0]}.json`
            a.click()
            URL.revokeObjectURL(url)
            showToast('Data exported successfully', 'success')
        } catch { showToast('Export failed', 'error') }
        setLoading(l => ({ ...l, export: false }))
    }

    const handleImport = () => {
        const input = document.createElement('input')
        input.type = 'file'
        input.accept = '.json'
        input.onchange = async (e) => {
            const file = e.target.files[0]
            if (!file) return
            setLoading(l => ({ ...l, import: true }))
            try {
                const text = await file.text()
                const data = JSON.parse(text)
                await importData(data)
                showToast('Data imported successfully', 'success')
                getStats().then(r => setSysStats(r.data)).catch(() => {})
            } catch { showToast('Import failed', 'error') }
            setLoading(l => ({ ...l, import: false }))
        }
        input.click()
    }

    const handleBackup = async () => {
        setLoading(l => ({ ...l, backup: true }))
        try {
            await createBackup()
            showToast('Backup created', 'success')
            listBackups().then(r => setBackups(r.data.backups || [])).catch(() => {})
        } catch { showToast('Backup failed', 'error') }
        setLoading(l => ({ ...l, backup: false }))
    }

    const handleRetrain = async () => {
        setLoading(l => ({ ...l, retrain: true }))
        try {
            await retrainModels()
            showToast('Models retrained successfully', 'success')
            getModelPerformance().then(r => setModels(r.data)).catch(() => {})
        } catch { showToast('Retrain failed', 'error') }
        setLoading(l => ({ ...l, retrain: false }))
    }

    const handleClearChat = async () => {
        if (!confirm('Clear all chat history? This cannot be undone.')) return
        setLoading(l => ({ ...l, clear: true }))
        try {
            await clearChatHistory()
            showToast('Chat history cleared', 'success')
        } catch { showToast('Failed to clear chat', 'error') }
        setLoading(l => ({ ...l, clear: false }))
    }

    return (
        <div className="space-y-8 max-w-3xl mx-auto">
            {/* Toast */}
            {toast && (
                <div className={`toast ${
                    toast.type === 'success' ? 'toast-success' :
                    toast.type === 'error' ? 'toast-error' : 'toast-info'
                }`}>
                    <div className="flex items-center gap-2">
                        {toast.type === 'success' && <CheckCircle className="w-4 h-4" />}
                        {toast.type === 'error' && <X className="w-4 h-4" />}
                        {toast.type === 'info' && <Info className="w-4 h-4" />}
                        {toast.msg}
                    </div>
                </div>
            )}

            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
                <p className="text-sm text-gray-500 mt-1">Configure your personal AI system</p>
            </div>

            {/* Profile Section */}
            <div className="card">
                <div className="section-card-header flex items-center justify-between">
                    <span>Profile</span>
                    <span className="text-xs font-normal text-gray-400">Coming Soon</span>
                </div>
                <div className="p-4 sm:p-6 space-y-4 opacity-50 pointer-events-none">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-1">Name</label>
                            <input className="input-field" placeholder="Your name" defaultValue="" />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-1">Email</label>
                            <input className="input-field" type="email" placeholder="you@example.com" defaultValue="" />
                        </div>
                    </div>
                    <div>
                        <label className="text-sm font-medium text-gray-700 block mb-1">Timezone</label>
                        <select className="input-field">
                            <option>UTC (Default)</option>
                            <option>UTC+5:30 (Mumbai)</option>
                            <option>UTC-5 (Eastern)</option>
                            <option>UTC-8 (Pacific)</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Preferences Section */}
            <div className="card">
                <div className="section-card-header">
                    <span>Preferences</span>
                </div>
                <div className="p-4 sm:p-6 space-y-5">
                    {/* Theme — functional */}
                    <div>
                        <label className="text-sm font-medium text-gray-700 block mb-2">Theme</label>
                        <div className="flex flex-wrap gap-3">
                            {[
                                { value: 'monochrome', label: 'Monochrome' },
                                { value: 'dark', label: 'Dark' },
                                { value: 'light', label: 'Light' },
                            ].map(({ value, label }) => (
                                <label key={value} className="flex items-center gap-2 cursor-pointer">
                                    <input type="radio" name="theme" checked={theme === value}
                                        onChange={() => setTheme(value)}
                                        className="accent-black" />
                                    <span className="text-sm text-gray-700">{label}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="text-sm font-medium text-gray-700 block mb-2">Timezone</label>
                        <div className="flex flex-col sm:flex-row gap-2">
                            <select className="input-field" value={timezone} onChange={e => setTimezone(e.target.value)}>
                                {timezoneOptions.map(tz => (
                                    <option key={tz} value={tz}>{tz}</option>
                                ))}
                            </select>
                            <button className="btn-secondary" onClick={handleTimezoneSave}>Save</button>
                        </div>
                    </div>

                    <div className="pt-1">
                        <label className="text-sm font-medium text-gray-700 block mb-2">Google Calendar (Brain Calendar)</label>
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                            <button className="btn-secondary" onClick={handleGoogleConnect}>Connect</button>
                            <button className="btn-secondary" onClick={handleGoogleSync}>Sync now</button>
                            <button className="btn-ghost" onClick={handleGoogleDisconnect}>Disconnect</button>
                        </div>
                        <p className="text-xs text-gray-500">
                            {calendarStatus?.connected
                                ? `Connected · ${calendarStatus.calendar_id || 'Brain Calendar'}`
                                : 'Not connected'}
                        </p>
                    </div>

                    {/* Remaining preferences — Coming Soon */}
                    <div className="opacity-50 pointer-events-none space-y-5">
                        <div className="flex items-center gap-2 text-xs text-gray-400">
                            <span>More preferences coming soon</span>
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">AI Personality</label>
                            <div className="flex flex-wrap gap-3">
                                {['Supportive', 'Analytical', 'Balanced'].map((p, i) => (
                                    <label key={p} className="flex items-center gap-2 cursor-pointer">
                                        <input type="radio" name="personality" defaultChecked={i === 0}
                                            className="accent-black" />
                                        <span className="text-sm text-gray-700">{p}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">Notifications</label>
                            <div className="space-y-2">
                                {[
                                    { label: 'Daily journal reminder (8:00 PM)', checked: true },
                                    { label: 'Habit reminders', checked: true },
                                    { label: 'AI insights', checked: true },
                                    { label: 'Weekly summary email', checked: false },
                                ].map(({ label, checked }) => (
                                    <label key={label} className="flex items-center gap-2 cursor-pointer">
                                        <input type="checkbox" defaultChecked={checked} className="accent-black" />
                                        <span className="text-sm text-gray-700">{label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* ML Models Section */}
            <div className="card">
                <div className="section-card-header flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <span className="flex items-center gap-2">
                        <Brain className="w-4 h-4" />
                        ML Models
                    </span>
                    <button onClick={handleRetrain} disabled={loading.retrain}
                        className="btn-secondary text-sm py-2 px-3 flex items-center gap-1.5 w-full sm:w-auto justify-center">
                        <RefreshCw className={`w-3.5 h-3.5 ${loading.retrain ? 'animate-spin' : ''}`} />
                        {loading.retrain ? 'Training...' : 'Retrain All Models'}
                    </button>
                </div>
                <div className="p-6">
                    {models && models.models?.length > 0 ? (
                        <div className="space-y-3">
                            {models.models.map(m => (
                                <div key={m.name} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                                    <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full" style={{ background: 'var(--status-dot)' }}></div>
                                        <div>
                                            <p className="text-sm font-medium text-gray-900">{m.name}</p>
                                            <p className="text-xs text-gray-500">{m.type} · v{m.version}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        {m.accuracy != null && (
                                            <p className="text-sm font-mono font-semibold text-gray-900">{(m.accuracy * 100).toFixed(1)}%</p>
                                        )}
                                        <p className="text-xs text-gray-500">{m.training_samples} samples</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-gray-400">No trained models yet. Add more data to enable ML predictions.</p>
                    )}
                </div>
            </div>

            {/* Data Management Section */}
            <div className="card">
                <div className="section-card-header">Data Management</div>
                <div className="p-4 sm:p-6">
                    {/* System Stats */}
                    {sysStats && (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                            {[
                                { label: 'Total entries', val: sysStats.total_journal_entries },
                                { label: 'Database size', val: `${sysStats.database_size_kb} KB` },
                                { label: 'Chat messages', val: sysStats.total_chat_messages },
                                { label: 'Version', val: sysStats.version },
                            ].map(({ label, val }) => (
                                <div key={label} className="text-center p-3 bg-gray-100 rounded-lg">
                                    <p className="text-lg font-semibold font-mono text-gray-900">{val ?? '--'}</p>
                                    <p className="text-xs text-gray-500">{label}</p>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
                        <button onClick={handleExport} disabled={loading.export}
                            className="btn-secondary flex items-center justify-center gap-2 py-3">
                            <Download className="w-4 h-4" />
                            {loading.export ? 'Exporting...' : 'Export All Data (JSON)'}
                        </button>
                        <button onClick={handleImport} disabled={loading.import}
                            className="btn-secondary flex items-center justify-center gap-2 py-3">
                            <Upload className="w-4 h-4" />
                            {loading.import ? 'Importing...' : 'Import Data'}
                        </button>
                        <button onClick={handleBackup} disabled={loading.backup}
                            className="btn-secondary flex items-center justify-center gap-2 py-3">
                            <HardDrive className="w-4 h-4" />
                            {loading.backup ? 'Backing up...' : 'Backup Now'}
                        </button>
                    </div>

                    {/* Recent Backups */}
                    {backups.length > 0 && (
                        <div className="border-t border-gray-200 pt-4">
                            <p className="text-xs text-gray-500 mb-2">Recent Backups</p>
                            {backups.slice(0, 3).map(b => (
                                <div key={b.filename} className="flex justify-between py-2">
                                    <span className="text-sm font-mono text-gray-600">{b.filename}</span>
                                    <span className="text-sm font-mono text-gray-400">{b.size_mb} MB</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Danger Zone */}
            <div className="card" style={{ borderColor: 'var(--danger-border)' }}>
                <div className="section-card-header" style={{ color: 'var(--danger-text)' }}>Danger Zone</div>
                <div className="p-4 sm:p-6">
                    <button onClick={handleClearChat} disabled={loading.clear}
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors"
                        style={{ color: 'var(--danger-text)', border: '1px solid var(--danger-border)' }}
                        onMouseEnter={e => e.currentTarget.style.background = 'var(--danger-hover-bg)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                        <Trash2 className="w-4 h-4" />
                        {loading.clear ? 'Clearing...' : 'Clear All Chat History'}
                    </button>
                </div>
            </div>

            {/* About */}
            <div className="card">
                <div className="section-card-header">About</div>
                <div className="p-6">
                    <p className="text-sm text-gray-600">Version: {sysStats?.version || '1.0.0'}</p>
                    <p className="text-sm text-gray-500 mt-1">Personal AI Memory System - Local & Private</p>
                </div>
            </div>
        </div>
    )
}
