import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Circle, Trash2, CalendarClock, Plus } from 'lucide-react'
import { createTask, deleteTask, getGoals, getHabits, getTasks, updateTask } from '../api'

const EMPTY_FORM = {
  title: '',
  description: '',
  priority: 'medium',
  status: 'todo',
  schedule_type: 'none',
  due_date: '',
  scheduled_at: '',
  scheduled_end: '',
  estimated_minutes: '',
  goal_id: '',
  habit_id: '',
  tags: '',
}

export default function TasksPage() {
  const [tasks, setTasks] = useState([])
  const [goals, setGoals] = useState([])
  const [habits, setHabits] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [statusFilter, setStatusFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')

  const loadAll = async () => {
    setLoading(true)
    try {
      const [{ data: taskData }, { data: goalData }, { data: habitData }] = await Promise.all([
        getTasks({ status: statusFilter, priority: priorityFilter }),
        getGoals('all'),
        getHabits('all'),
      ])
      setTasks(taskData || [])
      setGoals(goalData || [])
      setHabits(habitData || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [statusFilter, priorityFilter])

  const todoCount = useMemo(() => tasks.filter((t) => t.status !== 'done').length, [tasks])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return
    try {
      const isAllDay = form.schedule_type === 'all_day'
      const isTimed = form.schedule_type === 'timed'

      await createTask({
        title: form.title,
        description: form.description || null,
        priority: form.priority,
        status: form.status,
        due_date: isAllDay ? (form.due_date || null) : null,
        scheduled_at: isTimed ? (form.scheduled_at || null) : null,
        scheduled_end: isTimed ? (form.scheduled_end || null) : null,
        is_all_day: isAllDay,
        estimated_minutes: form.estimated_minutes ? Number(form.estimated_minutes) : null,
        goal_id: form.goal_id ? Number(form.goal_id) : null,
        habit_id: form.habit_id ? Number(form.habit_id) : null,
        tags: form.tags
          ? form.tags
              .split(',')
              .map((t) => t.trim())
              .filter(Boolean)
          : [],
      })
      setForm(EMPTY_FORM)
      setShowForm(false)
      loadAll()
    } catch (e) {
      console.error(e)
    }
  }

  const toggleDone = async (task) => {
    try {
      await updateTask(task.id, { status: task.status === 'done' ? 'todo' : 'done' })
      loadAll()
    } catch (e) {
      console.error(e)
    }
  }

  const removeTask = async (id) => {
    if (!confirm('Delete this task?')) return
    try {
      await deleteTask(id)
      loadAll()
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Tasks</h1>
          <p className="text-sm text-gray-500 mt-1">Plan future work, schedule actions, and tag by goals/habits.</p>
        </div>
        <button className={showForm ? 'btn-secondary' : 'btn-primary'} onClick={() => setShowForm((s) => !s)}>
          {showForm ? 'Cancel' : '+ New Task'}
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="card p-3 sm:p-4"><p className="text-xs text-gray-500">Open Tasks</p><p className="text-xl font-semibold mt-1">{todoCount}</p></div>
        <div className="card p-3 sm:p-4"><p className="text-xs text-gray-500">Completed</p><p className="text-xl font-semibold mt-1">{tasks.filter((t) => t.status === 'done').length}</p></div>
        <div className="card p-3 sm:p-4"><p className="text-xs text-gray-500">High Priority</p><p className="text-xl font-semibold mt-1">{tasks.filter((t) => ['high', 'critical'].includes(t.priority)).length}</p></div>
        <div className="card p-3 sm:p-4"><p className="text-xs text-gray-500">Scheduled</p><p className="text-xl font-semibold mt-1">{tasks.filter((t) => t.scheduled_at).length}</p></div>
      </div>

      <div className="flex flex-wrap gap-2">
        {['all', 'todo', 'in_progress', 'done'].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${statusFilter === s ? 'bg-black text-white border-black' : 'border-gray-200 text-gray-600 hover:bg-gray-100'}`}
          >
            {s.replace('_', ' ')}
          </button>
        ))}
        {['all', 'low', 'medium', 'high', 'critical'].map((p) => (
          <button
            key={p}
            onClick={() => setPriorityFilter(p)}
            className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${priorityFilter === p ? 'bg-black text-white border-black' : 'border-gray-200 text-gray-600 hover:bg-gray-100'}`}
          >
            {p}
          </button>
        ))}
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card p-4 sm:p-6 space-y-3 animate-in">
          <input className="input-field" placeholder="Task title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <textarea className="input-field min-h-[72px] resize-none" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <select className="input-field" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
            <select className="input-field" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="todo">To do</option>
              <option value="in_progress">In progress</option>
              <option value="done">Done</option>
            </select>
            <select className="input-field" value={form.schedule_type} onChange={(e) => setForm({ ...form, schedule_type: e.target.value })}>
              <option value="none">No schedule</option>
              <option value="all_day">All-day (date only)</option>
              <option value="timed">Specific time</option>
            </select>
            <input
              type="number"
              min="1"
              max="1440"
              className="input-field"
              placeholder="Estimated minutes"
              value={form.estimated_minutes}
              onChange={(e) => setForm({ ...form, estimated_minutes: e.target.value })}
            />
          </div>

          {form.schedule_type === 'all_day' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Due on</label>
                <input
                  type="date"
                  className="input-field"
                  value={form.due_date}
                  onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                />
              </div>
            </div>
          )}

          {form.schedule_type === 'timed' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Start at</label>
                <input
                  type="datetime-local"
                  className="input-field"
                  value={form.scheduled_at}
                  onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">End at</label>
                <input
                  type="datetime-local"
                  className="input-field"
                  value={form.scheduled_end}
                  onChange={(e) => setForm({ ...form, scheduled_end: e.target.value })}
                />
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <select className="input-field" value={form.goal_id} onChange={(e) => setForm({ ...form, goal_id: e.target.value })}>
              <option value="">Tag Goal (optional)</option>
              {goals.map((g) => (
                <option key={g.id} value={g.id}>{g.title}</option>
              ))}
            </select>
            <select className="input-field" value={form.habit_id} onChange={(e) => setForm({ ...form, habit_id: e.target.value })}>
              <option value="">Tag Habit (optional)</option>
              {habits.map((h) => (
                <option key={h.id} value={h.id}>{h.name}</option>
              ))}
            </select>
          </div>

          <input
            className="input-field"
            placeholder="Tags (comma separated): resume, outreach"
            value={form.tags}
            onChange={(e) => setForm({ ...form, tags: e.target.value })}
          />

          <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2">
            <Plus className="w-4 h-4" /> Create Task
          </button>
        </form>
      )}

      {loading ? (
        <div className="space-y-2">
          <div className="h-20 skeleton" />
          <div className="h-20 skeleton" />
        </div>
      ) : tasks.length === 0 ? (
        <div className="card p-8 text-center text-gray-400">No tasks found for selected filters.</div>
      ) : (
        <div className="space-y-2">
          {tasks.map((task) => (
            <div key={task.id} className="card p-3 sm:p-4">
              <div className="flex items-start gap-3">
                <button onClick={() => toggleDone(task)} className="mt-0.5 text-gray-500 hover:text-gray-800">
                  {task.status === 'done' ? <CheckCircle2 className="w-5 h-5 text-success" /> : <Circle className="w-5 h-5" />}
                </button>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className={`font-medium ${task.status === 'done' ? 'line-through text-gray-400' : 'text-gray-900'}`}>{task.title}</p>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">{task.priority}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">{task.status.replace('_', ' ')}</span>
                  </div>

                  {task.description && <p className="text-sm text-gray-500 mt-1">{task.description}</p>}

                  <div className="flex flex-wrap gap-2 mt-2 text-xs text-gray-500">
                    {task.goal_title && <span className="badge">Goal: {task.goal_title}</span>}
                    {task.habit_name && <span className="badge">Habit: {task.habit_name}</span>}
                    {task.due_date && <span className="badge">Due: {task.due_date}</span>}
                    {task.scheduled_at && (
                      <span className="badge flex items-center gap-1">
                        <CalendarClock className="w-3 h-3" /> {task.scheduled_at.slice(0, 16).replace('T', ' ')}
                      </span>
                    )}
                    {(task.spent_minutes || 0) > 0 && <span className="badge">Spent: {task.spent_minutes}m</span>}
                    {task.estimated_minutes && <span className="badge">Est: {task.estimated_minutes}m</span>}
                    {(task.tags || []).map((tag) => <span key={tag} className="badge">#{tag}</span>)}
                  </div>
                </div>

                <button onClick={() => removeTask(task.id)} className="btn-ghost text-gray-500" style={{ minHeight: 'auto', padding: '6px' }}>
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
