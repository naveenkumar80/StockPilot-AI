"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Filter,
  LineChart,
  BrainCircuit,
  History,
  Briefcase,
  FileText,
  Bookmark,
  BarChart3,
  Settings,
  ArrowRight,
  TrendingUp,
} from "lucide-react"
import { cn } from "@/lib/utils"

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Stock Screener", href: "/screener", icon: Filter },
  { name: "Market Insights", href: "/insights", icon: TrendingUp },
  { name: "Stock Analysis", href: "/stocks/RELIANCE", icon: LineChart },
  { name: "AI Predictions", href: "/models", icon: BrainCircuit },
  { name: "Backtesting", href: "/backtesting", icon: History },
  { name: "Paper Trading", href: "/paper-trading", icon: Briefcase },
  { name: "News & Research", href: "/research", icon: FileText },
  { name: "Watchlist", href: "/watchlist", icon: Bookmark },
  { name: "Analytics", href: "/models", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const [timeStr, setTimeStr] = React.useState("")

  React.useEffect(() => {
    const update = () => {
      setTimeStr(new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour12: false }))
    }
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [])


  return (
    <aside className="w-60 bg-[#0B0F17] border-r border-[#172231] flex flex-col justify-between shrink-0 h-screen sticky top-0 select-none overflow-y-auto">
      <div>
        {/* Brand Logo & Title */}
        <div className="h-16 flex items-center px-5 gap-3 border-b border-[#172231]">
          {/* Origami Logo Icon */}
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <svg
              className="w-5 h-5 fill-current"
              viewBox="0 0 24 24"
            >
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </div>
          <div>
            <div className="text-sm font-extrabold tracking-tight text-white flex items-center gap-1.5 font-sans">
              StockPilot AI
            </div>
            <div className="text-[10px] text-slate-400 font-medium tracking-tight">AI-Powered Stock Analysis</div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {navigation.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || (item.href.startsWith("/stocks") && pathname.startsWith("/stocks"))
            const Icon = item.icon

            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all",
                  isActive
                    ? "bg-[#0E352B] text-emerald-300 font-semibold shadow-inner border border-emerald-800/40"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#121B27]"
                )}
              >
                <Icon className={cn("w-4 h-4", isActive ? "text-emerald-400" : "text-slate-500")} />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Bottom Promo & Market Status */}
      <div className="p-3 space-y-3">
        {/* Promotional Card */}
        <div className="relative overflow-hidden p-3.5 rounded-xl bg-gradient-to-br from-[#101F38] via-[#0E1B30] to-[#0A1322] border border-[#1E3354] shadow-md">
          <div className="text-[11px] font-bold text-white leading-snug">
            Make Smarter Investment Decisions
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">with AI + Market Data</div>
          <Link
            href="/research"
            className="mt-2.5 w-6 h-6 rounded-full bg-blue-600/80 hover:bg-blue-500 flex items-center justify-center text-white transition-colors"
          >
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Live Market Badge */}
        <div className="p-2.5 rounded-lg bg-[#0E1520] border border-[#172231] flex items-center justify-between text-[11px] font-mono">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <div>
              <span className="text-slate-200 font-bold block text-[10px]">Live Market</span>
              <span className="text-slate-400 text-[10px]">NSE • <span className="text-emerald-400">Open</span></span>
            </div>
          </div>
          <span className="text-[10px] text-slate-400 font-mono font-medium">{timeStr ? `${timeStr} IST` : "09:15 – 15:30 IST"}</span>
        </div>

      </div>
    </aside>
  )
}
