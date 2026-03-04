import { createContext, useContext, useState, useCallback, useRef } from 'react'
import { CheckCircle, X, Info } from 'lucide-react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
    const [toast, setToast] = useState(null)
    const timerRef = useRef(null)

    const showToast = useCallback((msg, type = 'info') => {
        if (timerRef.current) clearTimeout(timerRef.current)
        setToast({ msg, type })
        timerRef.current = setTimeout(() => setToast(null), 3000)
    }, [])

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}
            {toast && (
                <div className={`toast ${toast.type === 'success' ? 'toast-success' :
                        toast.type === 'error' ? 'toast-error' : 'toast-info'
                    }`}>
                    <div className="flex items-center gap-2">
                        {toast.type === 'success' && <CheckCircle className="w-4 h-4" />}
                        {toast.type === 'error' && <X className="w-4 h-4" />}
                        {toast.type === 'info' && <Info className="w-4 h-4" />}
                        {toast.msg}
                    </div>
                </div>
            )}
        </ToastContext.Provider>
    )
}

export function useToast() {
    const ctx = useContext(ToastContext)
    if (!ctx) return { showToast: () => { } }
    return ctx
}
