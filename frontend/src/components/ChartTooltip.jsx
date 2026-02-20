export function ChartTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null
    return (
        <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg px-3 py-2 text-xs shadow-lg">
            <p className="text-[var(--text-muted)]">{label}</p>
            {payload.map((p, i) => (
                <p key={i} className="text-[var(--text-primary)] font-medium mt-0.5">
                    {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
                </p>
            ))}
        </div>
    )
}
