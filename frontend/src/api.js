import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''
const API_KEY = import.meta.env.VITE_API_KEY || ''

const api = axios.create({
    baseURL: `${API_BASE}/api`,
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
    },
})

// ======================== JOURNAL ========================

export const createJournalEntry = (data) => api.post('/journal', data)
export const getJournalEntries = (params) => api.get('/journal', { params })
export const getJournalEntry = (id) => api.get(`/journal/${id}`)
export const updateJournalEntry = (id, data) => api.put(`/journal/${id}`, data)
export const deleteJournalEntry = (id) => api.delete(`/journal/${id}`)
export const searchJournalEntries = (query) => api.post('/journal/search', null, { params: { query } })

// ======================== CHAT ========================

export const sendChatMessage = (message) => api.post('/chat', { message })
export const getChatHistory = (limit = 20) => api.get('/chat/history', { params: { limit } })
export const clearChatHistory = () => api.delete('/chat/clear')

// ======================== PREDICTIONS ========================

export const predictMood = (date) => api.post('/predict/mood', { date })
export const predictHabit = (habit, date) => api.post('/predict/habit', { habit, date })
export const getEnergyForecast = (days = 7) => api.get('/predict/energy', { params: { days_ahead: days } })
export const getPredictionStatus = () => api.get('/predict/status')
export const retrainModels = (model = 'all') => api.post('/predict/retrain', null, { params: { model_name: model } })
export const getModelPerformance = () => api.get('/predict/performance')

// ======================== ANALYTICS ========================

export const getDashboardData = () => api.get('/analytics/dashboard')
export const getPatterns = (category = 'mood', days = 90) =>
    api.get('/analytics/patterns', { params: { category, lookback_days: days } })
export const getInsights = () => api.get('/analytics/insights')
export const generateInsights = () => api.post('/analytics/generate-insights')

// ======================== GOALS ========================

export const createGoal = (data) => api.post('/goals', data)
export const getGoals = (status = 'active') => api.get('/goals', { params: { status } })
export const getGoal = (id) => api.get(`/goals/${id}`)
export const updateGoal = (id, data) => api.put(`/goals/${id}`, data)
export const deleteGoal = (id) => api.delete(`/goals/${id}`)

// ======================== HABITS ========================

export const createHabit = (data) => api.post('/habits', data)
export const getHabits = (status = 'active') => api.get('/habits', { params: { status } })
export const getHabit = (id) => api.get(`/habits/${id}`)
export const updateHabit = (id, data) => api.put(`/habits/${id}`, data)
export const deleteHabit = (id) => api.delete(`/habits/${id}`)
export const logHabit = (id, data) => api.post(`/habits/${id}/log`, data)
export const getHabitStats = (id) => api.get(`/habits/${id}/stats`)

// ======================== SEARCH ========================

export const semanticSearch = (query, limit = 10) => api.post('/search', { query, limit })
export const findSimilar = (entryId, limit = 5) => api.post('/search/similar', { entry_id: entryId, limit })

// ======================== DATA MANAGEMENT ========================

export const exportData = () => api.get('/data/export')
export const importData = (data) => api.post('/data/import', data)
export const createBackup = () => api.post('/data/backup')
export const listBackups = () => api.get('/data/backup/list')

// ======================== SYSTEM ========================

export const getHealthCheck = () => api.get('/health')
export const getStats = () => api.get('/stats')

export default api
