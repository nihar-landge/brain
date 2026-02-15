import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { Brain, LayoutDashboard, BookOpen, MessageCircle, Target, BarChart3, Settings } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import JournalPage from './pages/JournalPage'
import ChatPage from './pages/ChatPage'
import GoalsPage from './pages/GoalsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SettingsPage from './pages/SettingsPage'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/journal', icon: BookOpen, label: 'Journal' },
  { to: '/chat', icon: MessageCircle, label: 'Chat' },
  { to: '/goals', icon: Target, label: 'Goals' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
]

export default function App() {
  const location = useLocation()

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
      </header>

      {/* Mobile Top Bar — shown only on mobile */}
      <header className="sticky top-0 z-20 bg-white border-b border-gray-200 sm:hidden">
        <div className="px-4 flex items-center justify-between h-12">
          <NavLink to="/" className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-gray-900" />
            <span className="text-base font-semibold text-gray-900">brain</span>
          </NavLink>
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
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>

      {/* Mobile Bottom Tab Bar — shown only on mobile */}
      <nav className="fixed bottom-0 left-0 right-0 z-20 bg-white border-t border-gray-200 sm:hidden safe-bottom">
        <div className="flex items-center justify-around h-16">
          {navItems.map(({ to, icon: Icon, label }) => (
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
        </div>
      </nav>
    </div>
  )
}
