import { useState, useEffect, useCallback } from 'react'
import { TrendingUp, FlaskConical, Lightbulb, ArrowRight, AlertTriangle } from 'lucide-react'
import { getCorrelations, runCausalAnalysis, getCounterfactuals, suggestExperiments } from '../api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

function useChartColors() {
  return { primary: '#4A90E2', secondary: '#666666', muted: '#cccccc', success: '#2ecc71', error: '#e74c3c', warning: '#f39c12' }
}

export default function CausalPage() {
  const [tab, setTab] = useState('correlations')
  const [correlations, setCorrelations] = useState(null)
  const [causal, setCausal] = useState(null)
  const [counterfactuals, setCounterfactuals] = useState([])
  const [experiments, setExperiments] = useState([])
  const [loading, setLoading] = useState(true)
  const [causalLoading, setCausalLoading] = useState(false)
  const [treatment, setTreatment] = useState('sleep_hours')
  const [outcome, setOutcome] = useState('mood')
  const colors = useChartColors()

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [cRes, cfRes, eRes] = await Promise.allSettled([
        getCorrelations(), getCounterfactuals(), suggestExperiments()
      ])
      if (cRes.status === 'fulfilled') setCorrelations(cRes.value.data)
      if (cfRes.status === 'fulfilled') setCounterfactuals(cfRes.value.data)
      if (eRes.status === 'fulfilled') setExperiments(eRes.value.data)
    } catch { } finally { setLoading(false) }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  const handleRunCausal = async () => {
    setCausalLoading(true)
    try {
      const res = await runCausalAnalysis(treatment, outcome)
      setCausal(res.data)
    } catch { } finally { setCausalLoading(false) }
  }

  const features = ['sleep_hours', 'habits_completed', 'deep_work_minutes', 'social_interactions', 'context_switches', 'interruptions', 'energy', 'stress', 'avg_social_impact']

  const tabs = [
    { id: 'correlations', label: 'Correlations', icon: TrendingUp },
    { id: 'causal', label: 'Causal Analysis', icon: ArrowRight },
    { id: 'whatif', label: 'What If', icon: Lightbulb },
    { id: 'experiments', label: 'Experiments', icon: FlaskConical },
  ]

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-5 h-5 border-2 border-gray-300 border-t-black rounded-full animate-spin" /></div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Causal Analysis</h1>
        <p className="text-sm text-gray-500 mt-1">Move beyond correlation to understand what actually causes your mood changes</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${tab === t.id ? 'border-black text-black' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Correlations Tab */}
      {tab === 'correlations' && (
        <div className="space-y-4">
          {correlations && correlations.correlations?.length > 0 ? (
            <>
              <div className="card p-4 text-sm text-gray-500">
                Based on {correlations.sample_size} days of data ({correlations.period_days} day window)
              </div>

              {/* Chart */}
              <div className="card p-6">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Correlation with Mood</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={correlations.correlations} layout="vertical">
                    <XAxis type="number" domain={[-1, 1]} tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="feature" tick={{ fontSize: 11 }} width={120} tickFormatter={f => f.replace(/_/g, ' ')} />
                    <Tooltip formatter={(v) => [v, 'Correlation']} />
                    <Bar dataKey="correlation" radius={[0, 4, 4, 0]}>
                      {correlations.correlations.map((entry, idx) => (
                        <Cell key={idx} fill={entry.correlation >= 0 ? colors.success : colors.error} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Table */}
              <div className="card overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left px-4 py-2 font-medium text-gray-600">Feature</th>
                      <th className="text-right px-4 py-2 font-medium text-gray-600">r</th>
                      <th className="text-right px-4 py-2 font-medium text-gray-600">Strength</th>
                      <th className="text-center px-4 py-2 font-medium text-gray-600">Sig.</th>
                      <th className="text-right px-4 py-2 font-medium text-gray-600">n</th>
                    </tr>
                  </thead>
                  <tbody>
                    {correlations.correlations.map((c, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="px-4 py-2">{c.feature.replace(/_/g, ' ')}</td>
                        <td className={`px-4 py-2 text-right font-mono ${c.correlation >= 0 ? 'text-success' : 'text-error'}`}>{c.correlation > 0 ? '+' : ''}{c.correlation}</td>
                        <td className="px-4 py-2 text-right text-gray-500">{c.strength}</td>
                        <td className="px-4 py-2 text-center">{c.significant ? '***' : ''}</td>
                        <td className="px-4 py-2 text-right text-gray-400">{c.sample_size}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="card p-8 text-center text-gray-500">
              <TrendingUp className="w-8 h-8 mx-auto mb-3 text-gray-300" />
              <p>Need at least 10 days of mood data to calculate correlations.</p>
              <p className="text-xs text-gray-400 mt-1">Keep logging journal entries with mood ratings.</p>
            </div>
          )}
        </div>
      )}

      {/* Causal Analysis Tab */}
      {tab === 'causal' && (
        <div className="space-y-4">
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-900 mb-4">Test a Causal Relationship</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
              <div>
                <label className="text-xs text-gray-500">Treatment (cause)</label>
                <select value={treatment} onChange={e => setTreatment(e.target.value)} className="input-field w-full">
                  {features.map(f => <option key={f} value={f}>{f.replace(/_/g, ' ')}</option>)}
                </select>
              </div>
              <div className="flex items-center justify-center">
                <ArrowRight className="w-5 h-5 text-gray-400" />
              </div>
              <div>
                <label className="text-xs text-gray-500">Outcome (effect)</label>
                <select value={outcome} onChange={e => setOutcome(e.target.value)} className="input-field w-full">
                  <option value="mood">mood</option>
                  <option value="energy">energy</option>
                  <option value="stress">stress</option>
                </select>
              </div>
            </div>
            <button onClick={handleRunCausal} disabled={causalLoading} className="btn-primary mt-4 w-full disabled:opacity-30">
              {causalLoading ? 'Analyzing...' : 'Run Analysis'}
            </button>
          </div>

          {causal && !causal.error && (
            <div className="card p-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Results</h3>
              <div className="space-y-3">
                <div className="bg-gray-50 rounded-lg p-4 text-sm">{causal.interpretation}</div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-gray-500">Method:</span> <span className="font-mono">{causal.method?.replace(/_/g, ' ')}</span></div>
                  <div><span className="text-gray-500">Estimated Effect:</span> <span className={`font-bold ${causal.estimated_effect >= 0 ? 'text-success' : 'text-error'}`}>{causal.estimated_effect > 0 ? '+' : ''}{causal.estimated_effect}</span></div>
                  {causal.effect_size_cohens_d != null && <div><span className="text-gray-500">Effect Size (d):</span> <span className="font-mono">{causal.effect_size_cohens_d}</span></div>}
                  {causal.effect_magnitude && <div><span className="text-gray-500">Magnitude:</span> <span>{causal.effect_magnitude}</span></div>}
                </div>
                {causal.caution && (
                  <div className="flex items-start gap-2 text-xs text-gray-500 mt-2">
                    <AlertTriangle className="w-4 h-4 text-warning flex-shrink-0 mt-0.5" />
                    <span>{causal.caution}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {causal?.error && (
            <div className="card p-6 text-center text-gray-500">{causal.message || causal.error}</div>
          )}
        </div>
      )}

      {/* What If Tab */}
      {tab === 'whatif' && (
        <div className="space-y-4">
          {counterfactuals.length === 0 ? (
            <div className="card p-8 text-center text-gray-500">
              <Lightbulb className="w-8 h-8 mx-auto mb-3 text-gray-300" />
              <p>Not enough data for counterfactual analysis yet.</p>
              <p className="text-xs text-gray-400 mt-1">Need 10+ days of data with mood, sleep, and habit tracking.</p>
            </div>
          ) : (
            counterfactuals.map((cf, i) => (
              <div key={i} className="card p-6">
                <h3 className="text-sm font-medium text-gray-900 mb-2">{cf.scenario}</h3>
                <div className="flex items-center gap-4 mt-3">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-400">{cf.current_avg}</p>
                    <p className="text-xs text-gray-400">Current</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-300" />
                  <div className="text-center">
                    <p className={`text-2xl font-bold ${cf.change >= 0 ? 'text-success' : 'text-error'}`}>{cf.predicted_avg}</p>
                    <p className="text-xs text-gray-400">Predicted</p>
                  </div>
                  <div className="text-center ml-auto">
                    <p className={`text-xl font-bold ${cf.change >= 0 ? 'text-success' : 'text-error'}`}>{cf.change > 0 ? '+' : ''}{cf.change}</p>
                    <p className="text-xs text-gray-400">Change</p>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-2">Confidence: {cf.confidence}</p>
              </div>
            ))
          )}
        </div>
      )}

      {/* Experiments Tab */}
      {tab === 'experiments' && (
        <div className="space-y-4">
          {experiments.length === 0 ? (
            <div className="card p-8 text-center text-gray-500">
              <FlaskConical className="w-8 h-8 mx-auto mb-3 text-gray-300" />
              <p>No experiment suggestions yet. More data with significant correlations needed.</p>
            </div>
          ) : (
            experiments.map((exp, i) => (
              <div key={i} className="card p-6">
                <div className="flex items-start gap-3">
                  <FlaskConical className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-gray-900">{exp.hypothesis}</h3>
                    <p className="text-sm text-gray-600 mt-2">{exp.protocol}</p>
                    <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
                      <span>Duration: {exp.duration_days} days</span>
                      <span>Variable: {exp.variable.replace(/_/g, ' ')}</span>
                      <span>r = {exp.correlation_with_mood}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">{exp.measurement}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
