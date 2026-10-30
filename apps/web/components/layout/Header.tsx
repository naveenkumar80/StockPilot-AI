"use client"

import React, { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Search, Bell, Sun, Moon, Command } from "lucide-react"
import { api, LiveQuote } from "@/lib/api"
import { CommandPaletteModal } from "@/components/layout/CommandPaletteModal"

export function Header() {
  const router = useRouter()
  const [searchVal, setSearchVal] = useState("")
  const [isDark, setIsDark] = useState(true)
  const [isPaletteOpen, setIsPaletteOpen] = useState(false)

  // Real-time indices state aligned with Groww live market
  const [indices, setIndices] = useState({
    nifty: { price: 22933.10, change_pct: 1.03, flash: "" },
    sensex: { price: 74072.29, change_pct: 1.13, flash: "" },
    bankNifty: { price: 54913.85, change_pct: 1.19, flash: "" },
  })

  const prevPrices = useRef({
    nifty: 22933.10,
    sensex: 74072.29,
    bankNifty: 54913.85,
  })

  useEffect(() => {
    let isMounted = true

    const pollIndices = async () => {
      try {
        const quotes = await api.getLiveQuotes(["NIFTY50", "SENSEX", "NIFTYBANK"])
        if (!isMounted) return

        const n = quotes["NIFTY50"]
        const s = quotes["SENSEX"]
        const b = quotes["NIFTYBANK"]

        setIndices((prev) => {
          const nPrice = n ? n.last_price : prev.nifty.price
          const sPrice = s ? s.last_price : prev.sensex.price
          const bPrice = b ? b.last_price : prev.bankNifty.price

          const nFlash = nPrice > prevPrices.current.nifty ? "up" : nPrice < prevPrices.current.nifty ? "down" : ""
          const sFlash = sPrice > prevPrices.current.sensex ? "up" : sPrice < prevPrices.current.sensex ? "down" : ""
          const bFlash = bPrice > prevPrices.current.bankNifty ? "up" : bPrice < prevPrices.current.bankNifty ? "down" : ""

          prevPrices.current = { nifty: nPrice, sensex: sPrice, bankNifty: bPrice }

          return {
            nifty: { price: nPrice, change_pct: n ? n.day_change_perc : prev.nifty.change_pct, flash: nFlash },
            sensex: { price: sPrice, change_pct: s ? s.day_change_perc : prev.sensex.change_pct, flash: sFlash },
            bankNifty: { price: bPrice, change_pct: b ? b.day_change_perc : prev.bankNifty.change_pct, flash: bFlash },
          }
        })

        // Clear flashes after 800ms
        setTimeout(() => {
          if (isMounted) {
            setIndices((prev) => ({
              nifty: { ...prev.nifty, flash: "" },
              sensex: { ...prev.sensex, flash: "" },
              bankNifty: { ...prev.bankNifty, flash: "" },
            }))
          }
        }, 800)
      } catch (err) {
        // Silently retain last known price
      }
    }

    const interval = setInterval(pollIndices, 2500)
    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [])

  // Global Ctrl+K / Cmd+K Command Palette listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setIsPaletteOpen((prev) => !prev)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchVal.trim()) {
      router.push(`/stocks/${searchVal.trim().toUpperCase()}`)
    } else {
      setIsPaletteOpen(true)
    }
  }

  const formatPrice = (p: number) =>
    p.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })

  return (
    <>
      <header className="h-16 bg-[#0B0F17] border-b border-[#172231] px-6 flex items-center justify-between sticky top-0 z-30 select-none">
        {/* Search Bar / Quick Command Launcher */}
        <div
          onClick={() => setIsPaletteOpen(true)}
          className="relative w-80 cursor-pointer group"
        >
          <Search className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 absolute left-3 top-1/2 -translate-y-1/2 transition-colors" />
          <input
            type="text"
            readOnly
            placeholder="Search stocks, pages, commands..."
            value={searchVal}
            onClick={() => setIsPaletteOpen(true)}
            className="w-full bg-[#121B27] group-hover:bg-[#162130] border border-[#1E2B3D] group-hover:border-emerald-500/40 rounded-full pl-9 pr-14 py-1.5 text-xs font-sans text-slate-200 placeholder-slate-500 focus:outline-none cursor-pointer transition-all shadow-inner"
          />
          <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 text-[10px] font-mono text-slate-400">
            <span className="text-[9px]">⌘</span>K
          </div>
        </div>

      {/* Indices Badges & Sparklines */}
      <div className="hidden xl:flex items-center gap-3 font-mono">
        {/* NIFTY 50 */}
        <div
          className={`flex items-center gap-2.5 px-3 py-1.5 rounded-lg border transition-all duration-300 ${
            indices.nifty.flash === "up"
              ? "bg-emerald-950/60 border-emerald-500/50"
              : indices.nifty.flash === "down"
              ? "bg-rose-950/60 border-rose-500/50"
              : "bg-[#101724] border-[#1A2636]"
          }`}
        >
          <div className="text-left">
            <span className="text-[10px] text-slate-400 block font-sans font-bold">NIFTY 50</span>
            <div className="flex items-center gap-1.5 text-xs">
              <span className="font-semibold text-white">{formatPrice(indices.nifty.price)}</span>
              <span
                className={`font-bold text-[11px] ${
                  indices.nifty.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {indices.nifty.change_pct >= 0 ? "+" : ""}
                {indices.nifty.change_pct.toFixed(2)}%
              </span>
            </div>
          </div>
          {/* Mini Sparkline Green */}
          <svg className="w-12 h-5 text-emerald-400 shrink-0" viewBox="0 0 50 20" fill="none">
            <path
              d="M2 15 L10 13 L18 16 L26 8 L34 11 L42 4 L48 6"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {/* SENSEX */}
        <div
          className={`flex items-center gap-2.5 px-3 py-1.5 rounded-lg border transition-all duration-300 ${
            indices.sensex.flash === "up"
              ? "bg-emerald-950/60 border-emerald-500/50"
              : indices.sensex.flash === "down"
              ? "bg-rose-950/60 border-rose-500/50"
              : "bg-[#101724] border-[#1A2636]"
          }`}
        >
          <div className="text-left">
            <span className="text-[10px] text-slate-400 block font-sans font-bold">SENSEX</span>
            <div className="flex items-center gap-1.5 text-xs">
              <span className="font-semibold text-white">{formatPrice(indices.sensex.price)}</span>
              <span
                className={`font-bold text-[11px] ${
                  indices.sensex.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {indices.sensex.change_pct >= 0 ? "+" : ""}
                {indices.sensex.change_pct.toFixed(2)}%
              </span>
            </div>
          </div>
          <svg className="w-12 h-5 text-emerald-400 shrink-0" viewBox="0 0 50 20" fill="none">
            <path
              d="M2 16 L10 14 L18 11 L26 13 L34 7 L42 9 L48 3"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {/* NIFTY BANK */}
        <div
          className={`flex items-center gap-2.5 px-3 py-1.5 rounded-lg border transition-all duration-300 ${
            indices.bankNifty.flash === "up"
              ? "bg-emerald-950/60 border-emerald-500/50"
              : indices.bankNifty.flash === "down"
              ? "bg-rose-950/60 border-rose-500/50"
              : "bg-[#101724] border-[#1A2636]"
          }`}
        >
          <div className="text-left">
            <span className="text-[10px] text-slate-400 block font-sans font-bold">NIFTY BANK</span>
            <div className="flex items-center gap-1.5 text-xs">
              <span className="font-semibold text-white">{formatPrice(indices.bankNifty.price)}</span>
              <span
                className={`font-bold text-[11px] ${
                  indices.bankNifty.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {indices.bankNifty.change_pct >= 0 ? "+" : ""}
                {indices.bankNifty.change_pct.toFixed(2)}%
              </span>
            </div>
          </div>
          <svg className="w-12 h-5 text-rose-400 shrink-0" viewBox="0 0 50 20" fill="none">
            <path
              d="M2 5 L10 7 L18 6 L26 12 L34 10 L42 16 L48 14"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>


      {/* Right Controls: Theme Toggle, Notifications, Profile Avatar */}
      <div className="flex items-center gap-3">
        {/* Sun / Moon Toggle */}
        <button
          onClick={() => setIsDark(!isDark)}
          className="w-12 h-6 rounded-full bg-[#162130] border border-[#202E42] flex items-center px-1 transition-colors relative"
          title="Toggle Light/Dark Theme"
        >
          <div
            className={`w-4 h-4 rounded-full bg-slate-300 flex items-center justify-center text-slate-900 transition-transform ${
              isDark ? "translate-x-6" : "translate-x-0"
            }`}
          >
            {isDark ? <Moon className="w-2.5 h-2.5" /> : <Sun className="w-2.5 h-2.5" />}
          </div>
        </button>

        {/* Bell Notification */}
        <div className="relative cursor-pointer p-2 rounded-full hover:bg-[#141E2C] transition-colors text-slate-400 hover:text-slate-200">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-3.5 h-3.5 rounded-full bg-rose-500 text-white font-bold text-[9px] flex items-center justify-center">
            1
          </span>
        </div>

        {/* User Profile Avatar N */}
        <div className="w-8 h-8 rounded-full bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center justify-center cursor-pointer shadow-md transition-all">
          N
        </div>
      </div>
    </header>

    <CommandPaletteModal
      isOpen={isPaletteOpen}
      onClose={() => setIsPaletteOpen(false)}
    />
  </>
  )
}
