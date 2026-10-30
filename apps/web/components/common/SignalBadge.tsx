import React from "react"
import { cn } from "@/lib/utils"

interface SignalBadgeProps {
  signal: "BUY" | "HOLD" | "SELL" | "NO_TRADE" | string
  className?: string
}

export function SignalBadge({ signal, className }: SignalBadgeProps) {
  const s = signal?.toUpperCase() || "NO_TRADE"

  let colorClass = "bg-[#161F2E] text-slate-300 border-[#223044]"
  let label = s

  if (s === "BUY") {
    colorClass = "bg-[#092D21] text-[#00E58F] border-[#10563C] font-bold"
    label = "BUY"
  } else if (s === "SELL") {
    colorClass = "bg-[#2D1214] text-[#FF4D4D] border-[#571B20] font-bold"
    label = "SELL"
  } else if (s === "HOLD") {
    colorClass = "bg-[#2D2411] text-[#FFB020] border-[#553E17] font-bold"
    label = "HOLD"
  } else if (s === "NO_TRADE") {
    colorClass = "bg-[#141C28] text-slate-400 border-[#1F2C3E]"
    label = "NO TRADE"
  }

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono tracking-wider border uppercase transition-colors select-none",
        colorClass,
        className
      )}
    >
      {label}
    </span>
  )
}
