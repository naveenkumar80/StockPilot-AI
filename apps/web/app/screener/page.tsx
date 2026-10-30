"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { Search, ArrowUpDown, Filter, ChevronRight, AlertCircle, RefreshCw, Briefcase } from "lucide-react"
import { api, StockItem } from "@/lib/api"
import { SignalBadge } from "@/components/common/SignalBadge"
import { QuickTradeModal } from "@/components/common/QuickTradeModal"
import { formatINR, formatPercent } from "@/lib/utils"

export default function ScreenerPage() {
  const [stocks, setStocks] = useState<StockItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tradeStock, setTradeStock] = useState<StockItem | null>(null)

  // Filters & Sorting state
  const [query, setQuery] = useState("")
  const [signalFilter, setSignalFilter] = useState<string>("ALL")
  const [sortBy, setSortBy] = useState<string>("probability_up")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")

  const loadData = () => {
    setLoading(true)
    setError(null)
    api.getStocks({
      query: query || undefined,
      signal: signalFilter !== "ALL" ? signalFilter : undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
      page: 1,
      page_size: 50,
    })
      .then((res) => {
        setStocks(res.items)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      loadData()
    }, 200)
    return () => clearTimeout(timer)
  }, [query, signalFilter, sortBy, sortOrder])

  const toggleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(col)
      setSortOrder("desc")
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#202736] pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">Equities Screener</h1>
          <p className="text-xs text-slate-400 mt-1">
            Filter Indian stocks by ML prediction probability, expected return, technical momentum, and news sentiment
          </p>
        </div>

        <button
          onClick={loadData}
          className="px-3 py-1.5 bg-[#1A2230] hover:bg-[#252E3E] text-xs font-mono text-slate-200 rounded border border-[#252E3E] flex items-center gap-1.5 self-start md:self-auto transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Control Bar: Search + Filters */}
      <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-4 flex flex-col md:flex-row gap-4 justify-between items-stretch md:items-center">
        {/* Search input */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by symbol or company name..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-[#181E29] border border-[#252E3E] rounded-md pl-9 pr-4 py-2 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Signal Filter Buttons */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
          <span className="text-xs font-mono text-slate-400 mr-1 flex items-center gap-1">
            <Filter className="w-3 h-3" /> Signal:
          </span>
          {["ALL", "BUY", "HOLD", "SELL", "NO_TRADE"].map((sig) => (
            <button
              key={sig}
              onClick={() => setSignalFilter(sig)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                signalFilter === sig
                  ? "bg-blue-600 text-white font-semibold"
                  : "bg-[#181E29] text-slate-400 hover:text-slate-200 hover:bg-[#202736]"
              }`}
            >
              {sig === "NO_TRADE" ? "NO TRADE" : sig}
            </button>
          ))}
        </div>
      </div>

      {/* Screener Table */}
      <div className="bg-[#12161F] border border-[#252E3E] rounded-lg overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-xs font-mono text-slate-400 animate-pulse">
            Loading screener universe from backend...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs font-mono text-rose-400 space-y-2">
            <AlertCircle className="w-6 h-6 mx-auto text-rose-400" />
            <div>Failed to load screener data: {error}</div>
          </div>
        ) : stocks.length === 0 ? (
          <div className="p-12 text-center text-xs font-mono text-slate-500">
            No stocks matched your active query and filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-[#252E3E] bg-[#0E121A] text-slate-400 select-none">
                  <th
                    onClick={() => toggleSort("symbol")}
                    className="p-3 cursor-pointer hover:text-slate-200 transition-colors"
                  >
                    <div className="flex items-center gap-1">
                      TICKER <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="p-3">COMPANY</th>
                  <th
                    onClick={() => toggleSort("price")}
                    className="p-3 text-right cursor-pointer hover:text-slate-200 transition-colors"
                  >
                    <div className="flex items-center justify-end gap-1">
                      PRICE <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="p-3 text-right">24H CHG</th>
                  <th className="p-3 text-center">SIGNAL</th>
                  <th
                    onClick={() => toggleSort("probability_up")}
                    className="p-3 text-right cursor-pointer hover:text-slate-200 transition-colors"
                  >
                    <div className="flex items-center justify-end gap-1">
                      P(UP 5D) <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    onClick={() => toggleSort("expected_return")}
                    className="p-3 text-right cursor-pointer hover:text-slate-200 transition-colors"
                  >
                    <div className="flex items-center justify-end gap-1">
                      EXP. RET <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="p-3 text-center">RISK</th>
                  <th className="p-3 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1C2432]">
                {stocks.map((stock) => (
                  <tr key={stock.id} className="hover:bg-[#181E29] transition-colors">
                    <td className="p-3 font-bold text-slate-100">
                      <Link href={`/stocks/${stock.symbol}`} className="hover:text-blue-400">
                        {stock.symbol}
                      </Link>
                    </td>
                    <td className="p-3 text-slate-400 truncate max-w-[200px]">{stock.company_name}</td>
                    <td className="p-3 text-right font-medium text-slate-200">{formatINR(stock.last_price)}</td>
                    <td className="p-3 text-right">
                      <span className={stock.change_24h >= 0 ? "text-emerald-400" : "text-rose-400"}>
                        {formatPercent(stock.change_24h)}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <SignalBadge signal={stock.signal} />
                    </td>
                    <td className="p-3 text-right font-bold text-slate-100">
                      {stock.probability_up ? `${(stock.probability_up * 100).toFixed(0)}%` : "N/A"}
                    </td>
                    <td className="p-3 text-right">
                      {stock.expected_return !== null && stock.expected_return !== undefined ? (
                        <span className={stock.expected_return > 0 ? "text-emerald-400 font-semibold" : "text-rose-400"}>
                          {formatPercent(stock.expected_return * 100)}
                        </span>
                      ) : (
                        "N/A"
                      )}
                    </td>
                    <td className="p-3 text-center">
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded border ${
                          stock.risk_level === "LOW"
                            ? "bg-emerald-950/40 text-emerald-300 border-emerald-800/40"
                            : stock.risk_level === "MEDIUM"
                            ? "bg-amber-950/40 text-amber-300 border-amber-800/40"
                            : "bg-rose-950/40 text-rose-300 border-rose-800/40"
                        }`}
                      >
                        {stock.risk_level}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => setTradeStock(stock)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded transition-colors text-[11px] font-semibold"
                        >
                          <Briefcase className="w-3 h-3" /> Trade
                        </button>
                        <Link
                          href={`/stocks/${stock.symbol}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#1A2230] hover:bg-blue-600 hover:text-white text-blue-400 rounded transition-colors text-[11px]"
                        >
                          Analysis <ChevronRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {tradeStock && (
        <QuickTradeModal
          isOpen={!!tradeStock}
          onClose={() => setTradeStock(null)}
          symbol={tradeStock.symbol}
          currentPrice={tradeStock.last_price}
        />
      )}
    </div>
  )
}
