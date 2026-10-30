import React from "react"
import { cn } from "@/lib/utils"

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  change?: number
  isPercent?: boolean
  badge?: string
  className?: string
  icon?: React.ReactNode
}

export function MetricCard({
  title,
  value,
  subtitle,
  change,
  badge,
  className,
  icon,
}: MetricCardProps) {
  const isPositive = change !== undefined && change > 0
  const isNegative = change !== undefined && change < 0

  return (
    <div
      className={cn(
        "bg-[#12161F] border border-[#252E3E] rounded-lg p-4 flex flex-col justify-between shadow-sm hover:border-[#354257] transition-all",
        className
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</span>
        {icon && <div className="text-slate-400">{icon}</div>}
        {badge && (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            {badge}
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold font-mono tracking-tight text-slate-100">{value}</span>
        {change !== undefined && (
          <span
            className={cn(
              "text-xs font-mono font-medium",
              isPositive && "text-emerald-400",
              isNegative && "text-rose-400",
              !isPositive && !isNegative && "text-slate-400"
            )}
          >
            {isPositive ? "+" : ""}
            {change.toFixed(2)}%
          </span>
        )}
      </div>

      {subtitle && <p className="text-xs text-slate-400 mt-2">{subtitle}</p>}
    </div>
  )
}
