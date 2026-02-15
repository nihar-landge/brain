import { useState, useEffect, useCallback, useRef } from 'react'
import {
    Search, X, Calendar, Plus, ChevronDown, ChevronUp,
    Pencil, Trash2, Tag, Flame, BookOpen, Clock, Hash
} from 'lucide-react'
import {
    getJournalEntries, createJournalEntry, updateJournalEntry,
    deleteJournalEntry, searchJournalEntries
} from '../api'

const moodConfig = [
    { value: 1, emoji: '😢', label: 'Awful' },
    { value: 2, emoji: '😣', label: 'Bad' },
    { value: 3, emoji: '😔', label: 'Down' },
    { value: 4, emoji: '😕', label: 'Meh' },
    { value: 5, emoji: '😐', label: 'Okay' },
    { value: 6, emoji: '🙂', label: 'Fine' },
    { value: 7, emoji: '😊', label: 'Good' },
    { value: 8, emoji: '😁', label: 'Great' },
    { value: 9, emoji: '😄', label: 'Amazing' },
    { value: 10, emoji: '🤩', label: 'On Top' },
]

const moodEmoji = (v) => moodConfig.find(m => m.value === v)?.emoji || '😐'

const moodAccent = (v) => {
    if (v >= 8) return 'border-l-emerald-400'
    if (v >= 6) return 'border-l-sky-400'
    if (v >= 4) return 'border-l-amber-400'
    if (v >= 2) return 'border-l-orange-400'
    return 'border-l-red-400'
}

const categories = ['daily', 'reflection', 'gratitude', 'goals', 'ideas']

const prompts = [
    "What's on your mind right now?",
    "What made you smile today?",
    "What are you grateful for?",
    "What challenge did you face today?",
    "What would you tell your future self?",
    "What small win happened today?",
    "How did you grow today?",
    "What's something you learned recently?",
]

function getRandomPrompt() {
    return prompts[Math.floor(Math.random() * prompts.length)]
}

function wordCount(text) {
    return text.trim() ? text.trim().split(/\s+/).length : 0
}

function formatDate(dateStr) {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

function formatDateFull(dateStr) {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

function timeAgo(dateStr) {
    if (!dateStr) return ''
    const now = new Date()
    const d = new Date(dateStr)
    const diffMs = now - d
    const diffDays = Math.floor(diffMs / 86400000)
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
    return formatDate(dateStr)
}

// ─── Mood Picker ─────────────────────────────────────────
function MoodPicker({ value, onChange }) {
    return (
        <div>
            <p className="text-sm font-medium text-[var(--color-gray-700)] mb-3">How are you feeling?</p>
            <div className="flex flex-wrap gap-1.5 sm:gap-2">
                {moodConfig.map(m => (
                    <button
                        key={m.value}
                        type="button"
                        onClick={() => onChange(m.value)}
                        className={`flex flex-col items-center gap-0.5 p-1.5 sm:p-2 rounded-xl transition-all ${
                            value === m.value
                                ? 'bg-[var(--color-gray-100)] ring-2 ring-[var(--color-black)] scale-110'
                                : 'hover:bg-[var(--color-gray-100)] opacity-60 hover:opacity-100'
                        }`}
                    >
                        <span className="text-lg sm:text-xl">{m.emoji}</span>
                        <span className="text-[9px] sm:text-[10px] text-[var(--color-gray-600)] font-medium">{m.label}</span>
                    </button>
                ))}
            </div>
        </div>
    )
}

// ─── Metric Slider ───────────────────────────────────────
function MetricSlider({ icon, label, value, onChange, lowLabel, highLabel }) {
    return (
        <div>
            <label className="text-sm font-medium flex items-center gap-2 mb-2 text-[var(--color-gray-700)]">
                <span>{icon}</span> {label}: <span className="font-bold text-[var(--color-gray-900)]">{value}/10</span>
            </label>
            <input
                type="range" min="1" max="10" value={value}
                onChange={e => onChange(parseInt(e.target.value))}
            />
            <div className="flex justify-between text-[10px] text-[var(--color-gray-400)] mt-1">
                <span>{lowLabel}</span>
                <span>{highLabel}</span>
            </div>
        </div>
    )
}

// ─── Journal Entry Card ──────────────────────────────────
function EntryCard({ entry, expanded, onToggle, onEdit, onDelete }) {
    const tags = (() => {
        try {
            return typeof entry.tags === 'string' ? JSON.parse(entry.tags) : (entry.tags || [])
        } catch { return [] }
    })()

    return (
        <div
            className={`card border-l-4 ${entry.mood ? moodAccent(entry.mood) : 'border-l-[var(--color-gray-300)]'} transition-all`}
        >
            {/* Header — always visible */}
            <button
                onClick={onToggle}
                className="w-full text-left p-4 sm:p-5 flex items-start gap-3"
            >
                {/* Mood emoji */}
                <div className="flex-shrink-0 mt-0.5">
                    <span className="text-2xl">{entry.mood ? moodEmoji(entry.mood) : '📝'}</span>
                </div>

                {/* Content preview */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                        {entry.title && (
                            <h4 className="font-semibold text-[var(--color-gray-900)] text-sm sm:text-base">{entry.title}</h4>
                        )}
                        {entry.category && entry.category !== 'daily' && (
                            <span className="badge text-[10px]">{entry.category}</span>
                        )}
                    </div>
                    <p className={`text-sm text-[var(--color-gray-600)] mt-1 ${expanded ? '' : 'line-clamp-2'}`}>
                        {entry.content}
                    </p>
                    <div className="flex items-center gap-3 mt-2 text-[11px] text-[var(--color-gray-400)]">
                        <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {timeAgo(entry.entry_date || entry.created_at)}
                        </span>
                        {entry.mood && (
                            <span>{entry.mood}/10</span>
                        )}
                        {entry.energy_level && (
                            <span className="flex items-center gap-0.5">
                                <span>⚡</span>{entry.energy_level}
                            </span>
                        )}
                        {tags.length > 0 && (
                            <span className="flex items-center gap-0.5">
                                <Tag className="w-3 h-3" />
                                {tags.length}
                            </span>
                        )}
                    </div>
                </div>

                {/* Expand icon */}
                <div className="flex-shrink-0 mt-1">
                    {expanded
                        ? <ChevronUp className="w-4 h-4 text-[var(--color-gray-400)]" />
                        : <ChevronDown className="w-4 h-4 text-[var(--color-gray-400)]" />
                    }
                </div>
            </button>

            {/* Expanded detail */}
            {expanded && (
                <div className="px-4 sm:px-5 pb-4 sm:pb-5 border-t border-[var(--color-gray-200)] animate-in">
                    {/* Full content */}
                    <div className="pt-4 text-sm text-[var(--color-gray-700)] whitespace-pre-wrap leading-relaxed">
                        {entry.content}
                    </div>

                    {/* Metadata grid */}
                    <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs text-[var(--color-gray-500)]">
                        <span className="flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5" />
                            {formatDateFull(entry.entry_date || entry.created_at)}
                        </span>
                        {entry.mood && (
                            <span>Mood: {moodEmoji(entry.mood)} {entry.mood}/10</span>
                        )}
                        {entry.energy_level && (
                            <span>Energy: ⚡ {entry.energy_level}/10</span>
                        )}
                        {entry.stress_level && (
                            <span>Stress: {entry.stress_level}/10</span>
                        )}
                        {entry.category && (
                            <span className="capitalize">{entry.category}</span>
                        )}
                    </div>

                    {/* Tags */}
                    {tags.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-3">
                            {tags.map((tag, i) => (
                                <span key={i} className="badge text-[11px]">
                                    <Hash className="w-2.5 h-2.5 mr-0.5" />{tag}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2 mt-4 pt-3 border-t border-[var(--color-gray-200)]">
                        <button onClick={() => onEdit(entry)} className="btn-ghost text-xs flex items-center gap-1.5 !px-3 !py-1.5 !min-h-0">
                            <Pencil className="w-3.5 h-3.5" /> Edit
                        </button>
                        <button onClick={() => onDelete(entry.id)} className="btn-ghost text-xs flex items-center gap-1.5 !px-3 !py-1.5 !min-h-0 text-[var(--danger-text)] hover:bg-[var(--danger-hover-bg)]">
                            <Trash2 className="w-3.5 h-3.5" /> Delete
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}

// ─── Main Page ───────────────────────────────────────────
export default function JournalPage() {
    const [entries, setEntries] = useState([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [editingEntry, setEditingEntry] = useState(null)
    const [expandedId, setExpandedId] = useState(null)
    const [searchQuery, setSearchQuery] = useState('')
    const [searchResults, setSearchResults] = useState(null)
    const [activeCategory, setActiveCategory] = useState(null)
    const [saving, setSaving] = useState(false)
    const [deleting, setDeleting] = useState(null)
    const [placeholder] = useState(getRandomPrompt)
    const textareaRef = useRef(null)
    const [form, setForm] = useState({
        content: '', title: '', mood: 7, energy_level: 7, stress_level: 3,
        tags: '', category: 'daily',
        entry_date: new Date().toLocaleDateString('en-CA'),
        entry_time: new Date().toTimeString().slice(0, 5)
    })

    const resetForm = () => {
        setForm({
            content: '', title: '', mood: 7, energy_level: 7, stress_level: 3,
            tags: '', category: 'daily',
            entry_date: new Date().toLocaleDateString('en-CA'),
            entry_time: new Date().toTimeString().slice(0, 5)
        })
        setEditingEntry(null)
    }

    const loadEntries = useCallback(async () => {
        try {
            const res = await getJournalEntries()
            setEntries(res.data)
        } catch (err) { console.error(err) }
        finally { setLoading(false) }
    }, [])

    useEffect(() => { loadEntries() }, [loadEntries])

    // Focus textarea when form opens
    useEffect(() => {
        if (showForm && textareaRef.current) {
            setTimeout(() => textareaRef.current.focus(), 100)
        }
    }, [showForm])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setSaving(true)
        try {
            const payload = {
                ...form,
                tags: form.tags.split(',').map(t => t.trim()).filter(Boolean)
            }
            if (editingEntry) {
                await updateJournalEntry(editingEntry.id, payload)
            } else {
                await createJournalEntry(payload)
            }
            setShowForm(false)
            resetForm()
            loadEntries()
        } catch (err) { console.error(err) }
        finally { setSaving(false) }
    }

    const handleEdit = (entry) => {
        const tags = (() => {
            try {
                const t = typeof entry.tags === 'string' ? JSON.parse(entry.tags) : (entry.tags || [])
                return t.join(', ')
            } catch { return '' }
        })()
        setForm({
            content: entry.content || '',
            title: entry.title || '',
            mood: entry.mood || 7,
            energy_level: entry.energy_level || 7,
            stress_level: entry.stress_level || 3,
            tags,
            category: entry.category || 'daily',
            entry_date: entry.entry_date || new Date().toLocaleDateString('en-CA'),
            entry_time: new Date().toTimeString().slice(0, 5),
        })
        setEditingEntry(entry)
        setShowForm(true)
        setExpandedId(null)
    }

    const handleDelete = async (id) => {
        if (!confirm('Delete this entry? This cannot be undone.')) return
        setDeleting(id)
        try {
            await deleteJournalEntry(id)
            setExpandedId(null)
            loadEntries()
        } catch (err) { console.error(err) }
        finally { setDeleting(null) }
    }

    const handleSearch = async () => {
        if (!searchQuery.trim()) { setSearchResults(null); return }
        try {
            const res = await searchJournalEntries(searchQuery)
            setSearchResults(res.data)
        } catch (err) { console.error(err) }
    }

    const clearSearch = () => {
        setSearchResults(null)
        setSearchQuery('')
    }

    // Filter by category
    const displayEntries = (searchResults || entries).filter(e =>
        !activeCategory || e.category === activeCategory
    )

    // Stats
    const totalEntries = entries.length
    const thisWeek = entries.filter(e => {
        const d = new Date(e.entry_date || e.created_at)
        const now = new Date()
        return (now - d) < 7 * 86400000
    }).length

    // Calculate writing streak
    const streak = (() => {
        if (entries.length === 0) return 0
        const dates = [...new Set(
            entries.map(e => (e.entry_date || e.created_at || '').slice(0, 10))
        )].sort().reverse()
        let count = 0
        const today = new Date().toLocaleDateString('en-CA')
        const yesterday = new Date(Date.now() - 86400000).toLocaleDateString('en-CA')
        // Streak must start from today or yesterday
        if (dates[0] !== today && dates[0] !== yesterday) return 0
        let expected = new Date(dates[0])
        for (const d of dates) {
            const current = new Date(d)
            const diff = Math.round((expected - current) / 86400000)
            if (diff > 1) break
            count++
            expected = new Date(current.getTime() - 86400000)
        }
        return count
    })()

    return (
        <div className="space-y-5 sm:space-y-6 max-w-3xl mx-auto">
            {/* ─── Header + Stats ─── */}
            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-[var(--color-gray-900)]">Journal</h1>
                    <p className="text-sm text-[var(--color-gray-500)] mt-0.5">
                        Your private space to reflect
                    </p>
                </div>
                <div className="flex items-center gap-4 text-xs text-[var(--color-gray-500)]">
                    {streak > 0 && (
                        <span className="flex items-center gap-1 font-medium">
                            <Flame className="w-3.5 h-3.5 text-orange-500" />
                            {streak}d streak
                        </span>
                    )}
                    <span className="flex items-center gap-1">
                        <BookOpen className="w-3.5 h-3.5" />
                        {totalEntries} entries
                    </span>
                    <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {thisWeek} this week
                    </span>
                </div>
            </div>

            {/* ─── New / Edit Entry Form ─── */}
            {showForm ? (
                <div className="card p-4 sm:p-6 animate-in">
                    <div className="flex justify-between items-center mb-5">
                        <h2 className="text-lg font-bold text-[var(--color-gray-900)]">
                            {editingEntry ? 'Edit Entry' : 'New Entry'}
                        </h2>
                        <button
                            type="button"
                            onClick={() => { setShowForm(false); resetForm() }}
                            className="btn-ghost !p-2 !min-h-0"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Content first — the main thing */}
                        <div>
                            <input
                                className="input-field mb-2 text-base font-medium"
                                placeholder="Title (optional)"
                                value={form.title}
                                onChange={e => setForm({ ...form, title: e.target.value })}
                            />
                            <textarea
                                ref={textareaRef}
                                value={form.content}
                                onChange={e => setForm({ ...form, content: e.target.value })}
                                placeholder={placeholder}
                                className="input-field min-h-[180px] sm:min-h-[220px] resize-none text-sm leading-relaxed"
                                required
                            />
                            <div className="flex justify-between items-center mt-1.5 text-[11px] text-[var(--color-gray-400)]">
                                <span>{wordCount(form.content)} words</span>
                                <span>{form.content.length} characters</span>
                            </div>
                        </div>

                        {/* Mood Picker */}
                        <MoodPicker
                            value={form.mood}
                            onChange={mood => setForm({ ...form, mood })}
                        />

                        {/* Energy + Stress sliders */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                            <MetricSlider
                                icon="⚡" label="Energy" value={form.energy_level}
                                onChange={v => setForm({ ...form, energy_level: v })}
                                lowLabel="Exhausted" highLabel="Energized"
                            />
                            <MetricSlider
                                icon="😰" label="Stress" value={form.stress_level}
                                onChange={v => setForm({ ...form, stress_level: v })}
                                lowLabel="Calm" highLabel="Overwhelmed"
                            />
                        </div>

                        {/* Date, Category, Tags row */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            <div>
                                <label className="text-[11px] text-[var(--color-gray-500)] uppercase tracking-wider mb-1 block">Date</label>
                                <input
                                    type="date"
                                    value={form.entry_date}
                                    onChange={e => setForm({ ...form, entry_date: e.target.value })}
                                    className="input-field text-xs"
                                />
                            </div>
                            <div>
                                <label className="text-[11px] text-[var(--color-gray-500)] uppercase tracking-wider mb-1 block">Time</label>
                                <input
                                    type="time"
                                    value={form.entry_time}
                                    onChange={e => setForm({ ...form, entry_time: e.target.value })}
                                    className="input-field text-xs"
                                />
                            </div>
                            <div>
                                <label className="text-[11px] text-[var(--color-gray-500)] uppercase tracking-wider mb-1 block">Category</label>
                                <select
                                    className="input-field text-xs"
                                    value={form.category}
                                    onChange={e => setForm({ ...form, category: e.target.value })}
                                >
                                    {categories.map(c => (
                                        <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="text-[11px] text-[var(--color-gray-500)] uppercase tracking-wider mb-1 block">Tags</label>
                                <input
                                    className="input-field text-xs"
                                    placeholder="comma separated"
                                    value={form.tags}
                                    onChange={e => setForm({ ...form, tags: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* Submit */}
                        <div className="flex justify-end gap-2 pt-2">
                            <button
                                type="button"
                                onClick={() => { setShowForm(false); resetForm() }}
                                className="btn-ghost text-sm"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={saving || !form.content.trim()}
                                className="btn-primary text-sm"
                            >
                                {saving ? 'Saving...' : editingEntry ? 'Update' : 'Save Entry'}
                            </button>
                        </div>
                    </form>
                </div>
            ) : (
                /* Collapsed new entry prompt */
                <button
                    onClick={() => { resetForm(); setShowForm(true) }}
                    className="card w-full p-4 sm:p-5 text-left hover:bg-[var(--color-gray-100)] transition-colors group"
                >
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-[var(--color-gray-100)] group-hover:bg-[var(--color-gray-200)] flex items-center justify-center transition-colors">
                            <Plus className="w-4 h-4 text-[var(--color-gray-500)]" />
                        </div>
                        <span className="text-sm text-[var(--color-gray-400)] group-hover:text-[var(--color-gray-600)] transition-colors">
                            {placeholder}
                        </span>
                    </div>
                </button>
            )}

            {/* ─── Search + Category Filters ─── */}
            <div className="space-y-3">
                {/* Search bar */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-gray-400)]" />
                    <input
                        className="input-field pl-10 pr-10 text-sm"
                        placeholder="Search entries..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleSearch()}
                    />
                    {searchQuery && (
                        <button
                            onClick={clearSearch}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-gray-400)] hover:text-[var(--color-gray-600)]"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    )}
                </div>

                {/* Category filter pills */}
                <div className="flex gap-2 overflow-x-auto pb-1 -mb-1">
                    <button
                        onClick={() => setActiveCategory(null)}
                        className={`badge whitespace-nowrap transition-all ${
                            !activeCategory ? 'bg-[var(--color-black)] text-[var(--color-white)]' : ''
                        }`}
                    >
                        All
                    </button>
                    {categories.map(c => (
                        <button
                            key={c}
                            onClick={() => setActiveCategory(activeCategory === c ? null : c)}
                            className={`badge whitespace-nowrap capitalize transition-all ${
                                activeCategory === c ? 'bg-[var(--color-black)] text-[var(--color-white)]' : ''
                            }`}
                        >
                            {c}
                        </button>
                    ))}
                </div>

                {searchResults && (
                    <p className="text-xs text-[var(--color-gray-400)]">
                        {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"
                    </p>
                )}
            </div>

            {/* ─── Entries List ─── */}
            <div className="space-y-3">
                {loading ? (
                    [...Array(4)].map((_, i) => (
                        <div key={i} className="skeleton h-20 rounded-xl" />
                    ))
                ) : displayEntries.length > 0 ? (
                    displayEntries.map(entry => (
                        <EntryCard
                            key={entry.id}
                            entry={entry}
                            expanded={expandedId === entry.id}
                            onToggle={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
                            onEdit={handleEdit}
                            onDelete={handleDelete}
                        />
                    ))
                ) : (
                    <div className="text-center py-16">
                        <div className="text-4xl mb-3">📝</div>
                        <p className="text-[var(--color-gray-500)] text-sm font-medium">
                            {searchResults
                                ? 'No entries match your search.'
                                : activeCategory
                                    ? `No ${activeCategory} entries yet.`
                                    : 'Your journal is empty.'}
                        </p>
                        <p className="text-[var(--color-gray-400)] text-xs mt-1">
                            {!searchResults && !activeCategory && 'Start writing to capture your thoughts and track your mood.'}
                        </p>
                        {!searchResults && !activeCategory && (
                            <button
                                onClick={() => { resetForm(); setShowForm(true) }}
                                className="btn-primary text-sm mt-4"
                            >
                                Write your first entry
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
