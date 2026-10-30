"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { Briefcase, ArrowUpRight, TrendingUp, History, ShieldCheck, RefreshCw, PlusCircle } from "lucide-react"
import { api, PaperPortfolio } from "@/lib/api"
import { MetricCard } from "@/components/common/MetricCard"
import { formatINR, formatPercent, formatDate } from "@/lib/utils"

export default function PaperTradingPage() {
  const [portfolio, setPortfolio] = useState<PaperPortfolio | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadPortfolio = () => {
    setLoading(true)
    api.getPaperPortfolio()
      .then((data) => {
        setPortfolio(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }

  const handleReset = async () => {
    if (!confirm("Are you sure you want to reset the virtual sandbox fund to ₹10,00,000 cash and clear all simulated positions?")) {
      return
    }
    setLoading(true)
    try {
      const fresh = await api.resetPaperPortfolio()
      setPortfolio(fresh)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPortfolio()
  }, [])

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#202736] pb-4">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 mb-1">
            <Briefcase className="w-5 h-5" />
            <span className="text-xs font-mono uppercase tracking-wider font-semibold">Virtual Portfolio</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">Paper Trading Simulator</h1>
          <p className="text-xs text-slate-400 mt-1">
            Zero-risk simulation environment strictly disconnected from real brokerage execution
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="px-3 py-1.5 bg-rose-950/40 hover:bg-rose-900/60 text-xs font-mono text-rose-300 rounded border border-rose-800/80 flex items-center gap-1.5 transition-colors"
          >
            Reset Sandbox (₹10L)
          </button>
          <button
            onClick={loadPortfolio}
            className="px-3 py-1.5 bg-[#1A2230] hover:bg-[#252E3E] text-xs font-mono text-slate-200 rounded border border-[#252E3E] flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>
      </div>

      {/* Safety Guardrail Banner */}
      <div className="p-4 bg-emerald-950/20 border border-emerald-800/40 rounded-lg flex items-center gap-3 text-xs text-emerald-200">
        <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
        <div className="leading-relaxed">
          <strong className="font-bold">Paper Trading Guarantee:</strong> All orders, executions, and positions displayed
          here are simulated using virtual INR capital. No real broker orders are placed, and no actual capital is at risk.
        </div>
      </div>

      {/* Portfolio Stats */}
      {portfolio && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Total Equity"
            value={formatINR(portfolio.total_equity)}
            change={portfolio.unrealized_pnl_pct}
            subtitle={`Initial Capital: ${formatINR(portfolio.initial_capital)}`}
            badge="VIRTUAL INR"
          />
          <MetricCard
            title="Available Cash Balance"
            value={formatINR(portfolio.cash_balance)}
            subtitle={`${((portfolio.cash_balance / portfolio.total_equity) * 100).toFixed(1)}% of Portfolio`}
          />
          <MetricCard
            title="Unrealized P&L"
            value={formatINR(portfolio.unrealized_pnl)}
            change={portfolio.unrealized_pnl_pct}
            subtitle="Open Positions Gain/Loss"
          />
          <MetricCard
            title="Active Holdings"
            value={portfolio.positions.length}
            subtitle="Open Equities in Sandbox"
            badge="ACTIVE"
          />
        </div>
      )}

      {/* Open Positions Table */}
      <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            Open Holdings & Exposure
          </h2>
          <Link
            href="/screener"
            className="text-xs font-mono text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            <PlusCircle className="w-3.5 h-3.5" /> Find Equities to Trade
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs font-mono text-slate-500 animate-pulse">
            Loading paper positions...
          </div>
        ) : !portfolio || portfolio.positions.length === 0 ? (
          <div className="p-8 text-center text-xs font-mono text-slate-500">
            No active paper positions. Browse the screener or stock details page to place a simulated BUY order.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-[#252E3E] text-slate-400 bg-[#0E121A]">
                  <th className="p-3">SYMBOL</th>
                  <th className="p-3">COMPANY</th>
                  <th className="p-3 text-right">QTY</th>
                  <th className="p-3 text-right">AVG PRICE</th>
                  <th className="p-3 text-right">CURRENT PRICE</th>
                  <th className="p-3 text-right">MARKET VALUE</th>
                  <th className="p-3 text-right">UNREALIZED P&L</th>
                  <th className="p-3 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1C2432]">
                {portfolio.positions.map((pos) => (
                  <tr key={pos.symbol} className="hover:bg-[#181E29] transition-colors">
                    <td className="p-3 font-bold text-slate-100">
                      <Link href={`/stocks/${pos.symbol}`} className="hover:text-blue-400">
                        {pos.symbol}
                      </Link>
                    </td>
                    <td className="p-3 text-slate-400">{pos.company_name}</td>
                    <td className="p-3 text-right text-slate-200">{pos.quantity}</td>
                    <td className="p-3 text-right text-slate-300">{formatINR(pos.average_buy_price)}</td>
                    <td className="p-3 text-right font-medium text-slate-100">{formatINR(pos.current_price)}</td>
                    <td className="p-3 text-right text-slate-200">{formatINR(pos.market_value)}</td>
                    <td className="p-3 text-right">
                      <span className={pos.unrealized_pnl >= 0 ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                        {pos.unrealized_pnl >= 0 ? "+" : ""}
                        {formatINR(pos.unrealized_pnl)} ({formatPercent(pos.unrealized_pnl_pct)})
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <Link
                        href={`/stocks/${pos.symbol}`}
                        className="px-2 py-1 bg-[#1A2230] hover:bg-[#252E3E] rounded text-[11px] text-blue-400 transition-colors"
                      >
                        Trade
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Simulated Orders Table */}
      <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-5 space-y-4">
        <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <History className="w-4 h-4 text-purple-400" />
          Recent Simulated Order Log
        </h2>

        {portfolio?.recent_orders && portfolio.recent_orders.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-[#252E3E] text-slate-400 bg-[#0E121A]">
                  <th className="p-3">TIMESTAMP</th>
                  <th className="p-3">SYMBOL</th>
                  <th className="p-3">SIDE</th>
                  <th className="p-3 text-right">QTY</th>
                  <th className="p-3 text-right">PRICE</th>
                  <th className="p-3 text-right">FEE</th>
                  <th className="p-3 text-center">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1C2432]">
                {portfolio.recent_orders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-[#181E29] transition-colors">
                    <td className="p-3 text-slate-400">{formatDate(ord.created_at)}</td>
                    <td className="p-3 font-bold text-slate-200">{ord.symbol}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          ord.side === "BUY"
                            ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                            : "bg-rose-950 text-rose-400 border border-rose-800"
                        }`}
                      >
                        {ord.side}
                      </span>
                    </td>
                    <td className="p-3 text-right text-slate-200">{ord.quantity}</td>
                    <td className="p-3 text-right text-slate-200">{formatINR(ord.executed_price)}</td>
                    <td className="p-3 text-right text-slate-400">{formatINR(ord.transaction_fee)}</td>
                    <td className="p-3 text-center">
                      <span className="text-[10px] text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded">
                        {ord.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-xs font-mono text-slate-500">
            No simulated orders placed yet in this session.
          </div>
        )}
      </div>
    </div>
  )
}
