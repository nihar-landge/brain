export function StatCard({ label, value, sub, icon: Icon, onClick }) {
    return (
        <button
            onClick={onClick}
            className="bg-[var(--color-white)] border border-[var(--color-gray-200)] rounded-xl transition-[box-shadow] duration-300 hover:shadow-[0_8px_16px_var(--card-shadow-hover)] p-3 sm:p-4 text-left hover:bg-[var(--bg-secondary)] w-full"
        >
            <div className="flex items-start justify-between">
                <div className="min-w-0">
                    <p className="text-[10px] sm:text-xs text-[var(--text-muted)] uppercase tracking-wide truncate">{label}</p>
                    <p className="text-xl sm:text-2xl font-bold text-[var(--text-primary)] mt-0.5 sm:mt-1">{value}</p>
                    {sub && <p className="text-[10px] sm:text-xs text-[var(--text-muted)] mt-0.5 sm:mt-1 truncate">{sub}</p>}
                </div>
                {Icon && <Icon className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[var(--text-muted)] flex-shrink-0" />}
            </div>
        </button>
    )
}
