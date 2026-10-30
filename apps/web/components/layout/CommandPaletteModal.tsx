"use client"

import React, { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import {
  Search,
  LayoutDashboard,
  Filter,
  TrendingUp,
  LineChart,
  BrainCircuit,
  History,
  Briefcase,
  FileText,
  Bookmark,
  Settings,
  ArrowRight,
  ExternalLink,
} from "lucide-react"

interface CommandItem {
  id: string
  title: string
  category: "PAGES" | "STOCKS" | "ACTIONS"
  href: string
  icon: any
  badge?: string
}

const ALL_COMMANDS: CommandItem[] = [
  // Pages
  { id: "dash", title: "Dashboard", category: "PAGES", href: "/", icon: LayoutDashboard },
  { id: "screener", title: "Stock Screener", category: "PAGES", href: "/screener", icon: Filter },
  { id: "insights", title: "Market Insights & Macro", category: "PAGES", href: "/insights", icon: TrendingUp },
  { id: "backtest", title: "Backtesting Strategy Studio", category: "PAGES", href: "/backtesting", icon: History },
  { id: "paper", title: "Paper Trading Simulator", category: "PAGES", href: "/paper-trading", icon: Briefcase },
  { id: "research", title: "AI Research Assistant", category: "PAGES", href: "/research", icon: FileText },
  { id: "models", title: "AI Predictions & Models", category: "PAGES", href: "/models", icon: BrainCircuit },
  { id: "watchlist", title: "Personal Watchlist", category: "PAGES", href: "/watchlist", icon: Bookmark },
  { id: "settings", title: "Platform Settings", category: "PAGES", href: "/settings", icon: Settings },

  // Stocks
  { id: "rel", title: "RELIANCE — Reliance Industries Ltd", category: "STOCKS", href: "/stocks/RELIANCE", icon: LineChart, badge: "NSE" },
  { id: "tcs", title: "TCS — Tata Consultancy Services", category: "STOCKS", href: "/stocks/TCS", icon: LineChart, badge: "NSE" },
  { id: "infy", title: "INFY — Infosys Ltd", category: "STOCKS", href: "/stocks/INFY", icon: LineChart, badge: "NSE" },
  { id: "hdfc", title: "HDFCBANK — HDFC Bank Ltd", category: "STOCKS", href: "/stocks/HDFCBANK", icon: LineChart, badge: "NSE" },
  { id: "icici", title: "ICICIBANK — ICICI Bank Ltd", category: "STOCKS", href: "/stocks/ICICIBANK", icon: LineChart, badge: "NSE" },
  { id: "sbin", title: "SBIN — State Bank of India", category: "STOCKS", href: "/stocks/SBIN", icon: LineChart, badge: "NSE" },
  { id: "tatamot", title: "TATAMOTORS — Tata Motors Ltd", category: "STOCKS", href: "/stocks/TATAMOTORS", icon: LineChart, badge: "NSE" },
  { id: "bel", title: "BEL — Bharat Electronics Ltd", category: "STOCKS", href: "/stocks/BEL", icon: LineChart, badge: "NSE" },
  { id: "ntpc", title: "NTPC — NTPC Ltd", category: "STOCKS", href: "/stocks/NTPC", icon: LineChart, badge: "NSE" },
  { id: "adani", title: "ADANIPORTS — Adani Ports & SEZ", category: "STOCKS", href: "/stocks/ADANIPORTS", icon: LineChart, badge: "NSE" },
  { id: "powergrid", title: "POWERGRID — Power Grid Corp", category: "STOCKS", href: "/stocks/POWERGRID", icon: LineChart, badge: "NSE" },
  { id: "titan", title: "TITAN — Titan Company Ltd", category: "STOCKS", href: "/stocks/TITAN", icon: LineChart, badge: "NSE" },
]

interface CommandPaletteModalProps {
  isOpen: boolean
  onClose: () => void
}

export function CommandPaletteModal({ isOpen, onClose }: CommandPaletteModalProps) {
  const router = useRouter()
  const [query, setQuery] = useState("")
  const [selectedIdx, setSelectedIdx] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen) {
      setQuery("")
      setSelectedIdx(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

  const filtered = ALL_COMMANDS.filter(
    (item) =>
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      item.category.toLowerCase().includes(query.toLowerCase())
  )

  useEffect(() => {
    setSelectedIdx(0)
  }, [query])

  const handleSelect = (item: CommandItem) => {
    onClose()
    router.push(item.href)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setSelectedIdx((prev) => (prev + 1) % Math.max(filtered.length, 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setSelectedIdx((prev) => (prev - 1 + filtered.length) % Math.max(filtered.length, 1))
    } else if (e.key === "Enter" && filtered[selectedIdx]) {
      e.preventDefault()
      handleSelect(filtered[selectedIdx])
    } else if (e.key === "Escape") {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-black/75 backdrop-blur-md select-none animate-in fade-in duration-100"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl bg-[#0E1520] border border-[#1E2E42] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[520px]"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-[#172436] bg-[#090E17]">
          <Search className="w-5 h-5 text-emerald-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a stock symbol, page name, or action (e.g. RELIANCE, screener, paper)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm font-sans text-white placeholder-slate-500 focus:outline-none"
          />
          <kbd className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono text-slate-400 bg-slate-800 border border-slate-700">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="overflow-y-auto p-2 space-y-1">
          {filtered.length > 0 ? (
            filtered.map((item, idx) => {
              const Icon = item.icon
              const isSelected = idx === selectedIdx

              return (
                <div
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIdx(idx)}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl cursor-pointer transition-all ${
                    isSelected
                      ? "bg-emerald-500/10 border border-emerald-500/30 text-white"
                      : "text-slate-300 hover:bg-[#121B27]"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-1.5 rounded-lg ${
                        isSelected ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-800/80 text-slate-400"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold">{item.title}</div>
                      <div className="text-[10px] text-slate-500 uppercase font-mono">{item.category}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {item.badge && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-800 text-slate-400 border border-slate-700 font-mono">
                        {item.badge}
                      </span>
                    )}
                    {isSelected && <ArrowRight className="w-3.5 h-3.5 text-emerald-400" />}
                  </div>
                </div>
              )
            })
          ) : (
            <div className="p-8 text-center text-xs text-slate-500 font-mono">
              No matching pages or ticker symbols found for "{query}".
            </div>
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2.5 bg-[#090E17] border-t border-[#172436] flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <div className="flex items-center gap-3">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>ESC Close</span>
          </div>
          <span className="text-emerald-400 font-medium font-sans">StockPilot Quick Jump</span>
        </div>
      </div>
    </div>
  )
}

