import { useState, useRef, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { Brain, LayoutDashboard, BookOpen, MessageCircle, Target, BarChart3, Settings, Users, Clock, FlaskConical, MoreHorizontal, Candy, ListChecks } from 'lucide-react'
import { getActiveContext } from './api'
import Dashboard from './pages/Dashboard'
import JournalPage from './pages/JournalPage'
import ChatPage from './pages/ChatPage'
import GoalsPage from './pages/GoalsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SocialGraphPage from './pages/SocialGraphPage'
import TimeTrackerPage from './pages/TimeTrackerPage'
import CausalPage from './pages/CausalPage'
import SettingsPage from './pages/SettingsPage'
import DopamineMenuPage from './pages/DopamineMenuPage'
import TasksPage from './pages/TasksPage'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/journal', icon: BookOpen, label: 'Journal' },
  { to: '/chat', icon: MessageCircle, label: 'Chat' },
  { to: '/goals', icon: Target, label: 'Goals' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/social', icon: Users, label: 'Social' },
  { to: '/timer', icon: Clock, label: 'Timer' },
  { to: '/dopamine', icon: Candy, label: 'Dopamine' },
  { to: '/tasks', icon: ListChecks, label: 'Tasks' },
  { to: '/causal', icon: FlaskConical, label: 'Causal' },
]

// First 4 items shown on mobile bottom bar + "More" for the rest
const mobileNavItems = navItems.slice(0, 4)
const mobileOverflowItems = navItems.slice(4)

function getElapsedSeconds(activeContext) {
  if (!activeContext?.started_at) return 0

  const startedAt = activeContext.started_at
  const normalized = startedAt.includes('T') ? startedAt : `${startedAt.replace(' ', 'T')}Z`
  const parsed = new Date(normalized)

  if (Number.isNaN(parsed.getTime())) {
    return (activeContext.elapsed_minutes || 0) * 60
  }

  return Math.max(0, Math.floor((Date.now() - parsed.getTime()) / 1000))
}

function formatBeaconTime(seconds) {
  const mins = String(Math.floor(seconds / 60)).padStart(2, '0')
  const secs = String(seconds % 60).padStart(2, '0')
  return `${mins}:${secs}`
}

export default function App() {
  const location = useLocation()
  const [showMore, setShowMore] = useState(false)
  const [activeTimer, setActiveTimer] = useState(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const moreRef = useRef(null)

  // Close "More" menu on outside click or route change
  useEffect(() => {
    setShowMore(false)
  }, [location.pathname])

  useEffect(() => {
    const handleClick = (e) => {
      if (moreRef.current && !moreRef.current.contains(e.target)) {
        setShowMore(false)
      }
    }
    if (showMore) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [showMore])

  const isOverflowActive = mobileOverflowItems.some(item => 
    item.to === '/' ? location.pathname === '/' : location.pathname.startsWith(item.to)
  )

  useEffect(() => {
    let mounted = true

    const refreshActiveTimer = async () => {
      try {
        const { data } = await getActiveContext()
        if (!mounted) return

        if (data?.active) {
          setActiveTimer(data)
          setElapsedSeconds(getElapsedSeconds(data))
        } else {
          setActiveTimer(null)
          setElapsedSeconds(0)
        }
      } catch {
        // keep previous beacon state on transient errors
      }
    }

    refreshActiveTimer()
    const poll = setInterval(refreshActiveTimer, 10000)

    return () => {
      mounted = false
      clearInterval(poll)
    }
  }, [])

  useEffect(() => {
    if (!activeTimer) return

    const tick = setInterval(() => {
      setElapsedSeconds(getElapsedSeconds(activeTimer))
    }, 1000)

    return () => clearInterval(tick)
  }, [activeTimer])

  return (
    <div className="min-h-screen bg-white">
      {/* Top Navigation Bar — hidden on mobile */}
      <header className="sticky top-0 z-20 bg-white border-b border-gray-200 hidden sm:block">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-14">
          {/* Logo */}
          <NavLink to="/" className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-gray-900" />
            <span className="text-base font-semibold text-gray-900">brain</span>
          </NavLink>

          {/* Center Nav */}
          <nav className="flex items-center gap-1">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `nav-link flex items-center gap-2 ${isActive ? 'nav-link-active' : ''}`
                }
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            {activeTimer?.active && (
              <NavLink
                to="/timer"
                className="focus-beacon-chip flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-gray-200 bg-gray-100/80 hover:bg-gray-100 transition-colors"
              >
                <span className="relative flex items-center justify-center w-2.5 h-2.5">
                  <span className="focus-beacon-ring absolute inset-0 rounded-full" />
                  <span className="focus-beacon-dot w-2 h-2 rounded-full bg-accent" />
                </span>
                <span className="text-[11px] font-mono text-gray-700">{formatBeaconTime(elapsedSeconds)}</span>
                <span className="text-xs text-gray-600 max-w-[120px] truncate">{activeTimer.context_name}</span>
              </NavLink>
            )}

            {/* Settings */}
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link-active' : ''}`
              }
            >
              <Settings className="w-4 h-4" />
            </NavLink>
          </div>
        </div>
      </header>

      {/* Mobile Top Bar — shown only on mobile */}
      <header className="sticky top-0 z-20 bg-white border-b border-gray-200 sm:hidden">
        <div className="px-4 flex items-center justify-between h-12 gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <NavLink to="/" className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-gray-900" />
              <span className="text-base font-semibold text-gray-900">brain</span>
            </NavLink>

            {activeTimer?.active && (
              <NavLink
                to="/timer"
                className="focus-beacon-chip flex items-center gap-1.5 px-2 py-1 rounded-md border border-gray-200 bg-gray-100/90"
              >
                <span className="relative flex items-center justify-center w-2 h-2">
                  <span className="focus-beacon-ring absolute inset-0 rounded-full" />
                  <span className="focus-beacon-dot w-1.5 h-1.5 rounded-full bg-accent" />
                </span>
                <span className="text-[10px] font-mono text-gray-700">{formatBeaconTime(elapsedSeconds)}</span>
              </NavLink>
            )}
          </div>

          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `p-2 rounded-lg transition-colors ${isActive ? 'bg-gray-100 text-black' : 'text-gray-500'}`
            }
          >
            <Settings className="w-5 h-5" />
          </NavLink>
        </div>
      </header>

      {/* Main Content — add bottom padding on mobile for tab bar */}
      <main className="max-w-6xl mx-auto px-4 py-6 sm:px-6 sm:py-8 pb-24 sm:pb-8 animate-in" key={location.pathname}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/journal" element={<JournalPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/goals" element={<GoalsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/social" element={<SocialGraphPage />} />
          <Route path="/timer" element={<TimeTrackerPage />} />
          <Route path="/dopamine" element={<DopamineMenuPage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/causal" element={<CausalPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>

      {/* Mobile Bottom Tab Bar — shown only on mobile */}
      <nav className="fixed bottom-0 left-0 right-0 z-20 bg-white border-t border-gray-200 sm:hidden safe-bottom">
        <div className="flex items-center justify-around h-16">
          {mobileNavItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 py-2 px-3 min-w-[56px] transition-colors ${
                  isActive ? 'text-black' : 'text-gray-400'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{label}</span>
            </NavLink>
          ))}
          {/* More menu */}
          <div className="relative" ref={moreRef}>
            <button
              onClick={() => setShowMore(!showMore)}
              className={`flex flex-col items-center justify-center gap-0.5 py-2 px-3 min-w-[56px] transition-colors ${
                isOverflowActive || showMore ? 'text-black' : 'text-gray-400'
              }`}
            >
              <MoreHorizontal className="w-5 h-5" />
              <span className="text-[10px] font-medium">More</span>
            </button>
            {showMore && (
              <div className="absolute bottom-full right-0 mb-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1">
                {mobileOverflowItems.map(({ to, icon: Icon, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
                        isActive ? 'bg-gray-100 text-black font-medium' : 'text-gray-600'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4" />
                    <span>{label}</span>
                  </NavLink>
                ))}
                <NavLink
                  to="/settings"
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 text-sm transition-colors border-t border-gray-100 ${
                      isActive ? 'bg-gray-100 text-black font-medium' : 'text-gray-600'
                    }`
                  }
                >
                  <Settings className="w-4 h-4" />
                  <span>Settings</span>
                </NavLink>
              </div>
            )}
          </div>
        </div>
      </nav>
    </div>
  )
}
