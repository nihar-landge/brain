import { useState, useEffect, useCallback } from 'react'
import { Users, Plus, AlertTriangle, Battery, Network, X, UserPlus, ChevronDown, ChevronUp } from 'lucide-react'
import { getPeople, createPerson, updatePerson, deletePerson, getSocialGraph, getNetworkAnalysis, getToxicPatterns, logSocialBattery, getSocialBatteryHistory, createInteraction } from '../api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

function useChartColors() {
  return { primary: '#4A90E2', secondary: '#666666', muted: '#cccccc', success: '#2ecc71', error: '#e74c3c' }
}

export default function SocialGraphPage() {
  const [tab, setTab] = useState('people')
  const [people, setPeople] = useState([])
  const [graph, setGraph] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [warnings, setWarnings] = useState([])
  const [batteryHistory, setBatteryHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddPerson, setShowAddPerson] = useState(false)
  const [showAddInteraction, setShowAddInteraction] = useState(false)
  const [newPerson, setNewPerson] = useState({ name: '', relationship_type: 'friend', tags: [] })
  const [newInteraction, setNewInteraction] = useState({ person_id: '', interaction_date: new Date().toISOString().split('T')[0], interaction_type: 'meeting', mood_before: 5, mood_after: 5, draining_vs_energizing: 0, notes: '' })
  const [batteryLevel, setBatteryLevel] = useState(5)
  const colors = useChartColors()

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [pRes, gRes, aRes, wRes, bRes] = await Promise.allSettled([
        getPeople(), getSocialGraph(), getNetworkAnalysis(), getToxicPatterns(), getSocialBatteryHistory()
      ])
      if (pRes.status === 'fulfilled') setPeople(pRes.value.data)
      if (gRes.status === 'fulfilled') setGraph(gRes.value.data)
      if (aRes.status === 'fulfilled') setAnalysis(aRes.value.data)
      if (wRes.status === 'fulfilled') setWarnings(wRes.value.data)
      if (bRes.status === 'fulfilled') setBatteryHistory(bRes.value.data)
    } catch { } finally { setLoading(false) }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  const handleAddPerson = async () => {
    if (!newPerson.name.trim()) return
    try {
      await createPerson(newPerson)
      setNewPerson({ name: '', relationship_type: 'friend', tags: [] })
      setShowAddPerson(false)
      loadData()
    } catch { }
  }

  const handleAddInteraction = async () => {
    if (!newInteraction.person_id) return
    try {
      await createInteraction({ ...newInteraction, person_id: Number(newInteraction.person_id) })
      setShowAddInteraction(false)
      setNewInteraction({ person_id: '', interaction_date: new Date().toISOString().split('T')[0], interaction_type: 'meeting', mood_before: 5, mood_after: 5, draining_vs_energizing: 0, notes: '' })
      loadData()
    } catch { }
  }

  const handleLogBattery = async () => {
    try {
      await logSocialBattery({ battery_level: batteryLevel, solo_time_minutes: 0, social_time_minutes: 0 })
      loadData()
    } catch { }
  }

  const handleDeletePerson = async (id) => {
    if (!confirm('Deactivate this person?')) return
    try { await deletePerson(id); loadData() } catch { }
  }

  const relationshipColors = { friend: 'bg-blue-100 text-blue-700', family: 'bg-green-100 text-green-700', colleague: 'bg-yellow-100 text-yellow-700', mentor: 'bg-purple-100 text-purple-700', partner: 'bg-pink-100 text-pink-700', acquaintance: 'bg-gray-100 text-gray-600', other: 'bg-gray-100 text-gray-600' }

  const tabs = [
    { id: 'people', label: 'People', icon: Users },
    { id: 'graph', label: 'Graph', icon: Network },
    { id: 'warnings', label: 'Warnings', icon: AlertTriangle },
    { id: 'battery', label: 'Battery', icon: Battery },
  ]

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-5 h-5 border-2 border-gray-300 border-t-black rounded-full animate-spin" /></div>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Social Graph</h1>
          <p className="text-sm text-gray-500 mt-1">Track relationships and their impact on your wellbeing</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowAddInteraction(true)} className="btn-ghost text-sm flex items-center gap-1">
            <Plus className="w-4 h-4" /> Log Interaction
          </button>
          <button onClick={() => setShowAddPerson(true)} className="btn-primary text-sm flex items-center gap-1">
            <UserPlus className="w-4 h-4" /> Add Person
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === t.id ? 'border-black text-black' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            <t.icon className="w-4 h-4" /> {t.label}
            {t.id === 'warnings' && warnings.length > 0 && <span className="w-5 h-5 bg-error text-white text-xs rounded-full flex items-center justify-center">{warnings.length}</span>}
          </button>
        ))}
      </div>

      {/* People Tab */}
      {tab === 'people' && (
        <div className="space-y-4">
          {/* Stats */}
          {graph?.stats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="card p-4 text-center"><p className="text-2xl font-bold">{graph.stats.total_people}</p><p className="text-xs text-gray-500 mt-1">People</p></div>
              <div className="card p-4 text-center"><p className="text-2xl font-bold">{graph.stats.total_interactions}</p><p className="text-xs text-gray-500 mt-1">Interactions</p></div>
              <div className="card p-4 text-center"><p className="text-2xl font-bold">{graph.stats.most_mentioned || '—'}</p><p className="text-xs text-gray-500 mt-1">Most Mentioned</p></div>
              <div className="card p-4 text-center"><p className="text-2xl font-bold">{Object.keys(graph.stats.relationship_breakdown || {}).length}</p><p className="text-xs text-gray-500 mt-1">Relationship Types</p></div>
            </div>
          )}

          {/* People List */}
          {people.length === 0 ? (
            <div className="card p-8 text-center text-gray-500">
              <Users className="w-8 h-8 mx-auto mb-3 text-gray-300" />
              <p>No people tracked yet. Add someone to start building your social graph.</p>
            </div>
          ) : (
            <div className="grid gap-3">
              {people.map(p => (
                <div key={p.id} className="card p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-sm font-bold text-gray-600">
                      {p.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{p.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${relationshipColors[p.relationship_type] || relationshipColors.other}`}>{p.relationship_type || 'other'}</span>
                        <span className="text-xs text-gray-400">{p.total_mentions} mentions</span>
                        {p.interaction_frequency && <span className="text-xs text-gray-400">{p.interaction_frequency}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {p.avg_mood_impact != null && (
                      <span className={`text-sm font-mono ${p.avg_mood_impact >= 0 ? 'text-success' : 'text-error'}`}>
                        {p.avg_mood_impact > 0 ? '+' : ''}{p.avg_mood_impact}
                      </span>
                    )}
                    <button onClick={() => handleDeletePerson(p.id)} className="text-gray-400 hover:text-error transition-colors"><X className="w-4 h-4" /></button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Graph Tab */}
      {tab === 'graph' && (
        <div className="space-y-4">
          {graph && graph.nodes.length > 0 ? (
            <>
              {/* Simple node visualization */}
              <div className="card p-6">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Relationship Network</h3>
                <div className="flex flex-wrap gap-3 justify-center">
                  {graph.nodes.map(node => (
                    <div key={node.id} className="flex flex-col items-center gap-1" style={{ opacity: Math.max(0.4, Math.min(1, (node.total_mentions || 1) / 10)) }}>
                      <div className={`rounded-full flex items-center justify-center text-xs font-bold text-white ${node.avg_mood_impact >= 0 ? 'bg-accent' : 'bg-error'}`}
                        style={{ width: Math.max(32, Math.min(64, 24 + (node.total_mentions || 0) * 4)), height: Math.max(32, Math.min(64, 24 + (node.total_mentions || 0) * 4)) }}>
                        {node.name.charAt(0)}
                      </div>
                      <span className="text-xs text-gray-600 max-w-[80px] text-center truncate">{node.name}</span>
                    </div>
                  ))}
                </div>
                {graph.edges.length > 0 && <p className="text-xs text-gray-400 text-center mt-4">{graph.edges.length} connection{graph.edges.length > 1 ? 's' : ''} between people</p>}
              </div>

              {/* Network Analysis */}
              {analysis && !analysis.error && (
                <div className="card p-6">
                  <h3 className="text-sm font-medium text-gray-900 mb-3">Network Analysis</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><span className="text-gray-500">Density:</span> <span className="font-mono">{analysis.density}</span></div>
                    <div><span className="text-gray-500">Components:</span> <span className="font-mono">{analysis.num_components}</span></div>
                  </div>
                  {analysis.centrality && Object.keys(analysis.centrality).length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs text-gray-500 mb-1">Centrality (most connected):</p>
                      <div className="space-y-1">
                        {Object.entries(analysis.centrality).slice(0, 5).map(([id, val]) => {
                          const node = graph.nodes.find(n => String(n.id) === id)
                          return <div key={id} className="flex justify-between text-xs"><span>{node?.name || id}</span><span className="font-mono text-gray-500">{val}</span></div>
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Impact Chart */}
              {people.length > 0 && (
                <div className="card p-6">
                  <h3 className="text-sm font-medium text-gray-900 mb-4">Mood Impact by Person</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={people.filter(p => p.avg_mood_impact != null).map(p => ({ name: p.name, impact: p.avg_mood_impact }))}>
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} domain={[-5, 5]} />
                      <Tooltip />
                      <Bar dataKey="impact" fill={colors.primary} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          ) : (
            <div className="card p-8 text-center text-gray-500">
              <Network className="w-8 h-8 mx-auto mb-3 text-gray-300" />
              <p>No graph data yet. Add people and log interactions to build your network.</p>
            </div>
          )}
        </div>
      )}

      {/* Warnings Tab */}
      {tab === 'warnings' && (
        <div className="space-y-4">
          {warnings.length === 0 ? (
            <div className="card p-8 text-center text-gray-500">
              <AlertTriangle className="w-8 h-8 mx-auto mb-3 text-gray-300" />
              <p>No toxic patterns detected. Keep tracking interactions for better analysis.</p>
            </div>
          ) : (
            warnings.map((w, i) => (
              <div key={i} className={`card p-4 border-l-4 ${w.severity === 'high' ? 'border-l-error' : 'border-l-warning'}`}>
                <div className="flex items-start gap-3">
                  <AlertTriangle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${w.severity === 'high' ? 'text-error' : 'text-warning'}`} />
                  <div>
                    <p className="font-medium text-gray-900">{w.person_name} — {w.pattern.replace(/_/g, ' ')}</p>
                    <p className="text-sm text-gray-600 mt-1">{w.suggestion}</p>
                    <p className="text-xs text-gray-400 mt-2">Based on {w.interaction_count} interactions</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Battery Tab */}
      {tab === 'battery' && (
        <div className="space-y-4">
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-900 mb-4">Log Social Battery</h3>
            <div className="flex items-center gap-4">
              <input type="range" min="1" max="10" value={batteryLevel} onChange={e => setBatteryLevel(Number(e.target.value))} className="flex-1" />
              <span className="text-2xl font-bold w-12 text-center">{batteryLevel}</span>
              <button onClick={handleLogBattery} className="btn-primary text-sm">Log</button>
            </div>
            <div className="flex justify-between text-xs text-gray-400 mt-1 px-1"><span>Drained</span><span>Fully Charged</span></div>
          </div>

          {batteryHistory.length > 0 && (
            <div className="card p-6">
              <h3 className="text-sm font-medium text-gray-900 mb-4">Battery History</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={batteryHistory}>
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => d.slice(5)} />
                  <YAxis domain={[1, 10]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="battery_level" stroke={colors.primary} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Add Person Modal */}
      {showAddPerson && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={() => setShowAddPerson(false)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-lg" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">Add Person</h2>
            <div className="space-y-3">
              <input value={newPerson.name} onChange={e => setNewPerson({ ...newPerson, name: e.target.value })} placeholder="Name" className="input-field w-full" />
              <select value={newPerson.relationship_type} onChange={e => setNewPerson({ ...newPerson, relationship_type: e.target.value })} className="input-field w-full">
                {['friend', 'family', 'colleague', 'mentor', 'partner', 'acquaintance', 'other'].map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
              </select>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setShowAddPerson(false)} className="btn-ghost text-sm">Cancel</button>
              <button onClick={handleAddPerson} className="btn-primary text-sm" disabled={!newPerson.name.trim()}>Add</button>
            </div>
          </div>
        </div>
      )}

      {/* Add Interaction Modal */}
      {showAddInteraction && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={() => setShowAddInteraction(false)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-lg max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">Log Interaction</h2>
            <div className="space-y-3">
              <select value={newInteraction.person_id} onChange={e => setNewInteraction({ ...newInteraction, person_id: e.target.value })} className="input-field w-full">
                <option value="">Select person...</option>
                {people.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              <input type="date" value={newInteraction.interaction_date} onChange={e => setNewInteraction({ ...newInteraction, interaction_date: e.target.value })} className="input-field w-full" />
              <select value={newInteraction.interaction_type} onChange={e => setNewInteraction({ ...newInteraction, interaction_type: e.target.value })} className="input-field w-full">
                {['meeting', 'call', 'text', 'social_event', 'other'].map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
              </select>
              <div>
                <label className="text-xs text-gray-500">Mood Before ({newInteraction.mood_before})</label>
                <input type="range" min="1" max="10" value={newInteraction.mood_before} onChange={e => setNewInteraction({ ...newInteraction, mood_before: Number(e.target.value) })} className="w-full" />
              </div>
              <div>
                <label className="text-xs text-gray-500">Mood After ({newInteraction.mood_after})</label>
                <input type="range" min="1" max="10" value={newInteraction.mood_after} onChange={e => setNewInteraction({ ...newInteraction, mood_after: Number(e.target.value) })} className="w-full" />
              </div>
              <div>
                <label className="text-xs text-gray-500">Draining ← → Energizing ({newInteraction.draining_vs_energizing})</label>
                <input type="range" min="-5" max="5" value={newInteraction.draining_vs_energizing} onChange={e => setNewInteraction({ ...newInteraction, draining_vs_energizing: Number(e.target.value) })} className="w-full" />
              </div>
              <textarea value={newInteraction.notes} onChange={e => setNewInteraction({ ...newInteraction, notes: e.target.value })} placeholder="Notes..." className="input-field w-full" rows={2} />
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setShowAddInteraction(false)} className="btn-ghost text-sm">Cancel</button>
              <button onClick={handleAddInteraction} className="btn-primary text-sm" disabled={!newInteraction.person_id}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
