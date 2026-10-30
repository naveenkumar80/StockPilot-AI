"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import {
  Bookmark,
  Search,
  Plus,
  Trash2,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  RefreshCw,
  ExternalLink,
  Briefcase,
} from "lucide-react"
import { api, StockItem, LiveQuote } from "@/lib/api"
import { SignalBadge } from "@/components/common/SignalBadge"
import { formatINR, formatPercent } from "@/lib/utils"

const DEFAULT_WATCHLIST = [
  "RELIANCE",
  "TCS",
  "INFY",
  "HDFCBANK",
  "ICICIBANK",
  "SBIN",
  "TATAMOTORS",
  "BEL",
]

export default function WatchlistPage() {
  const [symbols, setSymbols] = useState<string[]>([])
  const [stocks, setStocks] = useState<StockItem[]>([])
  const [quotes, setQuotes] = useState<Record<string, LiveQuote>>({})
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [isAdding, setIsAdding] = useState(false)

  // Load from LocalStorage or default
  useEffect(() => {
    try {
      const saved = localStorage.getItem("stockpilot_watchlist")
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length > 0) {
          setSymbols(parsed)
          return
        }
      }
    } catch (e) {
      console.warn("Failed to read watchlist from localStorage", e)
    }
    setSymbols(DEFAULT_WATCHLIST)
  }, [])

  // Sync back to LocalStorage
  const updateSymbols = (newSyms: string[]) => {
    setSymbols(newSyms)
    try {
      localStorage.setItem("stockpilot_watchlist", JSON.stringify(newSyms))
    } catch (e) {
      console.warn("Failed to save watchlist to localStorage", e)
    }
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const [screenerRes, quotesRes] = await Promise.allSettled([
        api.getStocks({ page: 1, page_size: 50 }),
        api.getLiveQuotes(symbols),
      ])

      if (screenerRes.status === "fulfilled") {
        setStocks(screenerRes.value.items)
      }
      if (quotesRes.status === "fulfilled") {
        setQuotes(quotesRes.value)
      }
    } catch (err) {
      console.error("Error loading watchlist data:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (symbols.length > 0) {
      loadData()
      const timer = setInterval(loadData, 10000)
      return () => clearInterval(timer)
    }
  }, [symbols])

  const handleAddStock = (sym: string) => {
    const clean = sym.trim().toUpperCase()
    if (clean && !symbols.includes(clean)) {
      updateSymbols([...symbols, clean])
    }
    setSearchQuery("")
    setIsAdding(false)
  }

  const handleRemoveStock = (sym: string) => {
    updateSymbols(symbols.filter((s) => s !== sym))
  }

  // Filter available stocks to add
  const availableToAdd = stocks.filter(
    (s) =>
      !symbols.includes(s.symbol) &&
      (s.symbol.includes(searchQuery.toUpperCase()) ||
        s.company_name.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#172231] pb-5">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Bookmark className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Personal Watchlist</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Track live Indian equities, streaming quotes, and algorithmic AI trade signals
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsAdding(!isAdding)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-semibold transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Symbol
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#121B27] hover:bg-[#1A2636] border border-[#1E2D42] text-xs font-medium text-slate-200 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Add Stock Dialog / Search Drawer */}
      {isAdding && (
        <div className="p-4 rounded-xl bg-[#0E1520] border border-emerald-500/30 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white">Add Stock to Watchlist</span>
            <button
              onClick={() => setIsAdding(false)}
              className="text-xs text-slate-400 hover:text-white"
            >
              Cancel
            </button>
          </div>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search ticker symbol (e.g. RELIANCE, TCS, INFY)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-[#090E17] border border-[#1E2D42] rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              autoFocus
            />
          </div>

          {searchQuery && (
            <div className="max-h-48 overflow-y-auto space-y-1 pt-1">
              {availableToAdd.length > 0 ? (
                availableToAdd.slice(0, 6).map((item) => (
                  <button
                    key={item.symbol}
                    onClick={() => handleAddStock(item.symbol)}
                    className="w-full flex items-center justify-between p-2 rounded-lg bg-[#090E17] hover:bg-[#121B27] border border-transparent hover:border-[#1E2D42] text-left text-xs transition-colors"
                  >
                    <div>
                      <span className="font-bold text-white">{item.symbol}</span>
                      <span className="text-slate-400 ml-2">{item.company_name}</span>
                    </div>
                    <span className="text-emerald-400 font-semibold flex items-center gap-1">
                      <Plus className="w-3.5 h-3.5" /> Add
                    </span>
                  </button>
                ))
              ) : (
                <div className="text-xs text-slate-500 py-2 text-center">
                  No matching unadded symbols found. Press enter to add custom symbol:{" "}
                  <button
                    onClick={() => handleAddStock(searchQuery)}
                    className="text-emerald-400 font-bold underline"
                  >
                    {searchQuery.toUpperCase()}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Watchlist Table */}
      <div className="rounded-2xl bg-[#0E1520] border border-[#172231] overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#090E17] border-b border-[#172231] text-slate-400 font-semibold select-none">
              <tr>
                <th className="py-3 px-4">Symbol / Company</th>
                <th className="py-3 px-4 text-right">Last Price</th>
                <th className="py-3 px-4 text-right">24h Change</th>
                <th className="py-3 px-4 text-center">AI Signal</th>
                <th className="py-3 px-4 text-center">Confidence</th>
                <th className="py-3 px-4 text-right">Volume</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#172231]/60">
              {symbols.length > 0 ? (
                symbols.map((sym) => {
                  const stockInfo = stocks.find((s) => s.symbol === sym)
                  const live = quotes[sym]
                  const price = live?.last_price ?? stockInfo?.last_price ?? 0
                  const changePct = live?.day_change_perc ?? stockInfo?.change_24h ?? 0
                  const isPositive = changePct >= 0
                  const signal = stockInfo?.signal ?? "HOLD"
                  const prob = stockInfo?.probability_up ?? 0.5

                  return (
                    <tr
                      key={sym}
                      className="hover:bg-[#121B27]/50 transition-colors group"
                    >
                      <td className="py-3 px-4">
                        <Link href={`/stocks/${sym}`} className="flex items-center gap-2">
                          <span className="font-bold text-white group-hover:text-emerald-400 transition-colors">
                            {sym}
                          </span>
                          <span className="text-[10px] text-slate-500 truncate max-w-[140px]">
                            {stockInfo?.company_name || "NSE Equity"}
                          </span>
                        </Link>
                      </td>

                      <td className="py-3 px-4 text-right font-mono font-bold text-white">
                        {price > 0 ? formatINR(price) : "—"}
                      </td>

                      <td className="py-3 px-4 text-right font-mono font-semibold">
                        <span
                          className={`inline-flex items-center gap-0.5 ${
                            isPositive ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {isPositive ? (
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          ) : (
                            <TrendingDown className="w-3.5 h-3.5" />
                          )}
                          {formatPercent(changePct)}
                        </span>
                      </td>

                      <td className="py-3 px-4 text-center">
                        <SignalBadge signal={signal} />
                      </td>

                      <td className="py-3 px-4 text-center font-mono text-[11px] text-slate-300">
                        {Math.round(prob * 100)}%
                      </td>

                      <td className="py-3 px-4 text-right font-mono text-slate-400 text-[11px]">
                        {(live?.volume || stockInfo?.volume_24h || 0).toLocaleString("en-IN")}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/stocks/${sym}`}
                            title="Deep Dive Stock Analysis"
                            className="p-1.5 rounded-lg bg-[#121B27] hover:bg-[#1A2636] border border-[#1E2D42] text-slate-300 hover:text-white transition-colors"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </Link>
                          <Link
                            href="/paper-trading"
                            title="Paper Trade Symbol"
                            className="p-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 transition-colors"
                          >
                            <Briefcase className="w-3.5 h-3.5" />
                          </Link>
                          <button
                            onClick={() => handleRemoveStock(sym)}
                            title="Remove from Watchlist"
                            className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-500 text-xs">
                    Your watchlist is empty. Click "+ Add Symbol" above to begin tracking stocks.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

