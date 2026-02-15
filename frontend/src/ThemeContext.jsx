import { createContext, useContext, useState, useEffect, useMemo } from 'react'

const ThemeContext = createContext()

const THEMES = ['monochrome', 'dark', 'light']

export function ThemeProvider({ children }) {
    const [theme, setTheme] = useState(() => {
        const saved = localStorage.getItem('brain-theme')
        return THEMES.includes(saved) ? saved : 'monochrome'
    })

    useEffect(() => {
        localStorage.setItem('brain-theme', theme)
        document.documentElement.setAttribute('data-theme', theme)
    }, [theme])

    return (
        <ThemeContext.Provider value={{ theme, setTheme, THEMES }}>
            {children}
        </ThemeContext.Provider>
    )
}

export function useTheme() {
    const ctx = useContext(ThemeContext)
    if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
    return ctx
}

/**
 * Returns resolved hex color values for Recharts components.
 * Re-computes when the theme changes.
 */
export function useChartColors() {
    const { theme } = useTheme()

    return useMemo(() => {
        const s = getComputedStyle(document.documentElement)
        const get = (name) => s.getPropertyValue(name).trim()

        return {
            // Primary line/bar/dot color
            line: get('--color-black') || '#000000',
            // Background (for active dot stroke, etc.)
            bg: get('--color-white') || '#ffffff',
            // Axis tick labels
            tick: get('--color-gray-500') || '#808080',
            // Bar fill (slightly lighter than line)
            bar: get('--color-gray-900') || '#1a1a1a',
            // Gradient fill color
            gradient: get('--color-gray-700') || '#4d4d4d',
            // Active dot fill
            activeDotFill: get('--color-gray-300') || '#cccccc',
            // Muted stroke
            mutedStroke: get('--color-gray-600') || '#666666',
        }
    }, [theme])
}
