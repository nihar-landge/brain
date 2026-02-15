import { useState, useEffect, useCallback } from 'react'
import { Search, X, Calendar, Filter, Plus } from 'lucide-react'
import { getJournalEntries, createJournalEntry, searchJournalEntries } from '../api'

const moodEmoji = (v) => {
    if (v >= 9) return '😄'
    if (v >= 7) return '😊'
    if (v >= 5) return '😐'
    if (v >= 3) return '😔'
    return '😢'
}

const categories = ['daily', 'reflection', 'gratitude', 'goals', 'ideas']

export default function JournalPage() {
    const [entries, setEntries] = useState([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [searchResults, setSearchResults] = useState(null)
    const [saving, setSaving] = useState(false)
    const [form, setForm] = useState({
        content: '', title: '', mood: 7, energy_level: 7, stress_level: 3,
        tags: '', category: 'daily',
        entry_date: new Date().toLocaleDateString('en-CA'),
        entry_time: new Date().toTimeString().slice(0, 5)
    })

    const loadEntries = useCallback(async () => {
        try {
            const res = await getJournalEntries()
            setEntries(res.data)
        } catch (err) { console.error(err) }
        finally { setLoading(false) }
    }, [])

    useEffect(() => { loadEntries() }, [loadEntries])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setSaving(true)
        try {
            await createJournalEntry({
                ...form,
                tags: form.tags.split(',').map(t => t.trim()).filter(Boolean)
            })
            setShowForm(false)
            setForm({ content: '', title: '', mood: 7, energy_level: 7, stress_level: 3, tags: '', category: 'daily', entry_date: new Date().toLocaleDateString('en-CA'), entry_time: new Date().toTimeString().slice(0, 5) })
            loadEntries()
        } catch (err) { console.error(err) }
        finally { setSaving(false) }
    }

    const handleSearch = async () => {
        if (!searchQuery.trim()) { setSearchResults(null); return }
        try {
            const res = await searchJournalEntries(searchQuery)
            setSearchResults(res.data)
        } catch (err) { console.error(err) }
    }

    const displayEntries = searchResults || entries

    const formatDate = (dateStr) => {
        if (!dateStr) return ''
        const d = new Date(dateStr)
        return d.toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })
    }

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            {/* Entry Form */}
            {showForm ? (
                <div className="card p-6 animate-in">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-2xl font-bold text-gray-900">Journal Entry</h2>
                        <button type="button" onClick={() => setShowForm(false)} className="btn-ghost">
                            Cancel
                        </button>
                    </div>

                    <form onSubmit={handleSubmit}>
                        {/* Date & Time */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                            <div>
                                <label className="text-sm text-gray-600 block mb-1">Date</label>
                                <input
                                    type="date"
                                    value={form.entry_date}
                                    onChange={e => setForm({ ...form, entry_date: e.target.value })}
                                    className="input-field"
                                />
                            </div>
                            <div>
                                <label className="text-sm text-gray-600 block mb-1">Time</label>
                                <input
                                    type="time"
                                    value={form.entry_time}
                                    onChange={e => setForm({ ...form, entry_time: e.target.value })}
                                    className="input-field"
                                />
                            </div>
                        </div>

                        {/* Mood Sliders */}
                        <div className="space-y-5 mb-6">
                            <h3 className="text-sm font-medium text-gray-700">How are you feeling?</h3>

                            <div>
                                <label className="text-sm font-medium flex items-center gap-2 mb-2">
                                    <span>{moodEmoji(form.mood)}</span> Mood: <span className="font-semibold">{form.mood}/10</span>
                                </label>
                                <input
                                    type="range" min="1" max="10" value={form.mood}
                                    onChange={e => setForm({ ...form, mood: parseInt(e.target.value) })}
                                />
                            </div>

                            <div>
                                <label className="text-sm font-medium flex items-center gap-2 mb-2">
                                    <span>⚡</span> Energy: <span className="font-semibold">{form.energy_level}/10</span>
                                </label>
                                <input
                                    type="range" min="1" max="10" value={form.energy_level}
                                    onChange={e => setForm({ ...form, energy_level: parseInt(e.target.value) })}
                                />
                            </div>

                            <div>
                                <label className="text-sm font-medium flex items-center gap-2 mb-2">
                                    <span>😰</span> Stress: <span className="font-semibold">{form.stress_level}/10</span>
                                </label>
                                <input
                                    type="range" min="1" max="10" value={form.stress_level}
                                    onChange={e => setForm({ ...form, stress_level: parseInt(e.target.value) })}
                                />
                            </div>
                        </div>

                        {/* Content */}
                        <div className="mb-6">
                            <label className="text-sm font-medium mb-2 block text-gray-700">What's on your mind?</label>
                            <input
                                className="input-field mb-3"
                                placeholder="Title (optional)"
                                value={form.title}
                                onChange={e => setForm({ ...form, title: e.target.value })}
                            />
                            <textarea
                                value={form.content}
                                onChange={e => setForm({ ...form, content: e.target.value })}
                                placeholder="Write your thoughts..."
                                className="input-field min-h-[200px] resize-none"
                                required
                            />
                        </div>

                        {/* Tags & Category */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                            <div>
                                <label className="text-sm font-medium mb-2 block text-gray-700">Tags</label>
                                <input
                                    className="input-field"
                                    placeholder="productive, grateful, ..."
                                    value={form.tags}
                                    onChange={e => setForm({ ...form, tags: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block text-gray-700">Category</label>
                                <select
                                    className="input-field"
                                    value={form.category}
                                    onChange={e => setForm({ ...form, category: e.target.value })}
                                >
                                    {categories.map(c => (
                                        <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex justify-between">
                            <button type="button" onClick={() => setShowForm(false)} className="btn-ghost">
                                Cancel
                            </button>
                            <button type="submit" disabled={saving || !form.content.trim()} className="btn-primary">
                                {saving ? 'Saving...' : 'Save ✓'}
                            </button>
                        </div>
                    </form>
                </div>
            ) : (
                /* New Entry Button when form is hidden */
                <div className="flex justify-end">
                    <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
                        <Plus className="w-4 h-4" />
                        New Entry
                    </button>
                </div>
            )}

            {/* Recent Entries */}
            <div className="card p-6">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-4">
                    <h3 className="text-xl font-semibold text-gray-900">Recent Entries</h3>
                    <div className="flex gap-2">
                        <div className="relative flex-1 sm:flex-initial">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <input
                                className="input-field pl-10 w-full sm:w-48"
                                placeholder="Search..."
                                value={searchQuery}
                                onChange={e => setSearchQuery(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleSearch()}
                            />
                        </div>
                        <button onClick={handleSearch} className="btn-secondary">
                            <Filter className="w-4 h-4" />
                        </button>
                        {searchResults && (
                            <button onClick={() => { setSearchResults(null); setSearchQuery('') }} className="btn-ghost px-2">
                                <X className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                </div>

                {searchResults && (
                    <p className="text-xs text-gray-500 mb-4">
                        {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"
                    </p>
                )}

                <div className="space-y-4">
                    {loading ? (
                        [...Array(3)].map((_, i) => <div key={i} className="h-24 skeleton"></div>)
                    ) : displayEntries.length > 0 ? (
                        displayEntries.map((entry) => (
                            <div
                                key={entry.id}
                                className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition cursor-pointer"
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex items-center gap-2">
                                        <Calendar className="w-4 h-4 text-gray-500" />
                                        <span className="text-sm font-medium text-gray-900">
                                            {formatDate(entry.entry_date || entry.created_at)}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {entry.mood && (
                                            <span className="text-sm text-gray-600">
                                                {moodEmoji(entry.mood)} {entry.mood}/10
                                            </span>
                                        )}
                                        {entry.energy_level && (
                                            <span className="text-sm text-gray-600">
                                                ⚡{entry.energy_level}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {entry.title && (
                                    <h4 className="font-medium text-gray-900 mb-1">{entry.title}</h4>
                                )}

                                <p className="text-gray-700 text-sm line-clamp-2">{entry.content}</p>

                                {entry.tags?.length > 0 && (
                                    <div className="flex flex-wrap gap-2 mt-3">
                                        {(() => {
                                            try {
                                                const tags = typeof entry.tags === 'string' ? JSON.parse(entry.tags) : entry.tags
                                                return tags.map((tag, i) => (
                                                    <span key={i} className="badge text-xs">{tag}</span>
                                                ))
                                            } catch { return null }
                                        })()}
                                    </div>
                                )}
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-12">
                            <p className="text-gray-400">No entries yet. Start writing to capture your thoughts.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
