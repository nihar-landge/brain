import { useEffect, useMemo, useState } from 'react'
import { Plus, Trash2, Sparkles, Coffee, Trophy } from 'lucide-react'
import { getDopamineItems, createDopamineItem, updateDopamineItem, deleteDopamineItem } from '../api'

const CATEGORY_ORDER = ['starter', 'main', 'sides', 'dessert', 'specials']
const CATEGORY_LABEL = {
  starter: 'Starter (Quick Reset)',
  main: 'Main (Productive Break)',
  sides: 'Sides (Light Fun)',
  dessert: 'Dessert (Big Reward)',
  specials: 'Specials (Celebration Mode)',
}

const EMPTY_FORM = {
  category: 'starter',
  title: '',
  description: '',
  duration_min: 5,
  energy_type: 'relax',
  is_active: true,
}

export default function DopamineMenuPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)

  const loadItems = async () => {
    setLoading(true)
    try {
      const { data } = await getDopamineItems(false)
      setItems(data || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadItems()
  }, [])

  const grouped = useMemo(() => {
    const result = { starter: [], main: [], sides: [], dessert: [], specials: [] }
    for (const item of items) {
      if (result[item.category]) result[item.category].push(item)
    }
    return result
  }, [items])

  const startEdit = (item) => {
    setEditingId(item.id)
    setForm({
      category: item.category,
      title: item.title,
      description: item.description || '',
      duration_min: item.duration_min || 5,
      energy_type: item.energy_type || 'relax',
      is_active: item.is_active,
    })
  }

  const resetForm = () => {
    setEditingId(null)
    setForm(EMPTY_FORM)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return

    try {
      const payload = {
        ...form,
        duration_min: Number(form.duration_min) || 5,
      }
      if (editingId) {
        await updateDopamineItem(editingId, payload)
      } else {
        await createDopamineItem(payload)
      }
      resetForm()
      loadItems()
    } catch (e) {
      console.error(e)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this dopamine item?')) return
    try {
      await deleteDopamineItem(id)
      loadItems()
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Dopamine Menu</h1>
          <p className="text-sm text-gray-500 mt-1">Curated breaks so you avoid doom-scrolling and return to focus faster.</p>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-full border border-gray-200 bg-gray-100 text-gray-600">
          <Sparkles className="w-3.5 h-3.5 text-accent" /> Custom rewards
        </div>
      </div>

      <form onSubmit={handleSubmit} className="card p-4 sm:p-6 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="input-field">
            {CATEGORY_ORDER.map((cat) => (
              <option key={cat} value={cat}>{CATEGORY_LABEL[cat]}</option>
            ))}
          </select>
          <input
            className="input-field"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="Break title"
            required
          />
          <input
            type="number"
            min="1"
            max="120"
            className="input-field"
            value={form.duration_min}
            onChange={(e) => setForm({ ...form, duration_min: e.target.value })}
            placeholder="Minutes"
          />
          <select value={form.energy_type} onChange={(e) => setForm({ ...form, energy_type: e.target.value })} className="input-field">
            <option value="relax">Relax</option>
            <option value="physical">Physical</option>
            <option value="mental">Mental</option>
          </select>
        </div>

        <textarea
          className="input-field min-h-[72px] resize-none"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          placeholder="Optional instructions..."
        />

        <div className="flex items-center justify-between gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
            />
            Active item
          </label>

          <div className="flex gap-2">
            {editingId && (
              <button type="button" className="btn-secondary" onClick={resetForm}>Cancel</button>
            )}
            <button type="submit" className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> {editingId ? 'Update Item' : 'Add Item'}
            </button>
          </div>
        </div>
      </form>

      {loading ? (
        <div className="space-y-3">
          <div className="h-24 skeleton" />
          <div className="h-24 skeleton" />
        </div>
      ) : (
        <div className="space-y-4">
          {CATEGORY_ORDER.map((cat) => (
            <section key={cat} className="card p-4 sm:p-5">
              <div className="flex items-center gap-2 mb-3">
                {cat === 'starter' && <Coffee className="w-4 h-4 text-gray-500" />}
                {cat === 'specials' && <Trophy className="w-4 h-4 text-gray-500" />}
                <h3 className="text-sm sm:text-base font-semibold text-gray-900">{CATEGORY_LABEL[cat]}</h3>
              </div>

              {grouped[cat].length === 0 ? (
                <p className="text-sm text-gray-400">No items in this category yet.</p>
              ) : (
                <div className="space-y-2">
                  {grouped[cat].map((item) => (
                    <div key={item.id} className="border border-gray-200 rounded-lg p-3 bg-white">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-medium text-gray-900 text-sm">{item.title}</p>
                          {item.description && <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>}
                          <p className="text-[11px] text-gray-500 mt-1">
                            {item.duration_min ? `${item.duration_min} min` : 'Flexible'} · {item.energy_type || 'relax'} · {item.is_active ? 'active' : 'inactive'}
                          </p>
                        </div>
                        <div className="flex gap-1">
                          <button onClick={() => startEdit(item)} className="btn-secondary text-xs py-1 px-2" style={{ minHeight: 'auto' }}>Edit</button>
                          <button onClick={() => handleDelete(item.id)} className="btn-ghost text-xs py-1 px-2" style={{ minHeight: 'auto' }}>
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
