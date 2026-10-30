"use client"

import React, { useState, useEffect } from "react"
import {
  History,
  Play,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Layers,
  ShieldCheck,
  Sliders,
  CheckCircle2,
  ListOrdered,
  Download,
} from "lucide-react"
import { api } from "@/lib/api"
import { MetricCard } from "@/components/common/MetricCard"
import { formatINR, formatPercent } from "@/lib/utils"

export default function BacktestingPage() {
  const [symbol, setSymbol] = useState("RELIANCE")
  const [initialCapital, setInitialCapital] = useState(1000000)
  const [buyThresh, setBuyThresh] = useState(0.60)
  const [sellThresh, setSellThresh] = useState(0.40)
  const [stopLossPct, setStopLossPct] = useState(3.0)
  const [takeProfitPct, setTakeProfitPct] = useState(7.0)
  const [selectedPreset, setSelectedPreset] = useState("balanced_momentum")

  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const applyPreset = (presetId: string) => {
    setSelectedPreset(presetId)
    if (presetId === "conservative_trend") {
      setBuyThresh(0.65)
      setSellThresh(0.45)
      setStopLossPct(2.5)
      setTakeProfitPct(8.0)
    } else if (presetId === "balanced_momentum") {
      setBuyThresh(0.60)
      setSellThresh(0.40)
      setStopLossPct(3.0)
      setTakeProfitPct(7.0)
    } else if (presetId === "active_breakout") {
      setBuyThresh(0.55)
      setSellThresh(0.48)
      setStopLossPct(2.0)
      setTakeProfitPct(4.5)
    }
  }

  const handleRunBacktest = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const data = await api.runBacktest({
        symbol: symbol.toUpperCase(),
        initial_capital: initialCapital,
        strategy_params: {
          buy_threshold: buyThresh,
          sell_threshold: sellThresh,
          stop_loss_pct: stopLossPct / 100.0,
          take_profit_pct: takeProfitPct / 100.0,
          transaction_cost_pct: 0.0003,
          slippage_pct: 0.0005,
        },
      })
      setResults(data)
    } catch (err: any) {
      setError(err.message || "Failed to execute backtest")
    } finally {
      setLoading(false)
    }
  }

  // Auto-run once on load
  useEffect(() => {
    handleRunBacktest()
  }, [])

  // Calculate dynamic SVG coordinates for equity curve
  const getSvgPoints = (points: Array<{ equity: number; benchmark_equity: number }>) => {
    if (!points || points.length < 2) return { stratPoints: "", benchPoints: "", minVal: 0, maxVal: 0 }
    const allVals = points.flatMap((p) => [p.equity, p.benchmark_equity])
    const minVal = Math.min(...allVals) * 0.98
    const maxVal = Math.max(...allVals) * 1.02
    const range = maxVal - minVal || 1

    const stratPoints = points
      .map((pt, i) => {
        const x = 20 + (i / (points.length - 1)) * 760
        const y = 220 - ((pt.equity - minVal) / range) * 190
        return `${x.toFixed(1)},${y.toFixed(1)}`
      })
      .join(" ")

    const benchPoints = points
      .map((pt, i) => {
        const x = 20 + (i / (points.length - 1)) * 760
        const y = 220 - ((pt.benchmark_equity - minVal) / range) * 190
        return `${x.toFixed(1)},${y.toFixed(1)}`
      })
      .join(" ")

    return { stratPoints, benchPoints, minVal, maxVal }
  }

  const svgData = results?.equity_curve ? getSvgPoints(results.equity_curve) : null

  const handleExportCSV = () => {
    if (!results || !results.trades || results.trades.length === 0) return

    const headers = [
      "Trade ID",
      "Symbol",
      "Entry Date",
      "Exit Date",
      "Entry Price",
      "Exit Price",
      "Shares",
      "Net PnL",
      "Return Pct",
      "Exit Reason",
    ]
    const rows = results.trades.map((t: any) => [
      t.trade_id,
      symbol,
      t.entry_date,
      t.exit_date,
      t.entry_price,
      t.exit_price,
      t.shares,
      t.pnl,
      t.pnl_pct,
      t.reason,
    ])

    const csvContent = [headers.join(","), ...rows.map((r: any[]) => r.join(","))].join("\n")
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.setAttribute("href", url)
    link.setAttribute("download", `StockPilot_Backtest_${symbol}_${new Date().toISOString().split("T")[0]}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-[#202736] pb-4">
        <div className="flex items-center gap-2 text-blue-400 mb-1">
          <History className="w-5 h-5" />
          <span className="text-xs font-mono uppercase tracking-wider font-semibold">
            Quantitative Backtesting
          </span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">
          Historical Strategy Simulator
        </h1>
        <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
          Evaluate probabilistic ML signal rules on historical Indian market candles with realistic brokerage fees, STT, and slippage. Zero forward-looking leakage.
        </p>
      </div>

      {/* Preset Buttons */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-mono text-slate-400 mr-2 flex items-center gap-1.5">
          <Sliders className="w-3.5 h-3.5" /> Strategy Presets:
        </span>
        {[
          { id: "balanced_momentum", label: "Balanced Momentum (Default)" },
          { id: "conservative_trend", label: "Conservative Trend (P ≥ 0.65)" },
          { id: "active_breakout", label: "Aggressive Mean Reversion (P ≥ 0.55)" },
        ].map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => applyPreset(p.id)}
            className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
              selectedPreset === p.id
                ? "bg-blue-600 text-white font-bold"
                : "bg-[#141A24] text-slate-300 hover:bg-[#1E2634] border border-[#252E3E]"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Configuration & Controls */}
      <form
        onSubmit={handleRunBacktest}
        className="bg-[#12161F] border border-[#252E3E] rounded-lg p-5 space-y-4"
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="space-y-1">
            <label className="text-[10px] font-mono text-slate-400 uppercase">TICKER SYMBOL</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="w-full bg-[#181E29] border border-[#252E3E] rounded p-2 text-xs font-mono text-slate-100 uppercase focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-mono text-slate-400 uppercase">INITIAL CAPITAL</label>
            <input
              type="number"
              step="50000"
              value={initialCapital}
              onChange={(e) => setInitialCapital(parseFloat(e.target.value))}
              className="w-full bg-[#181E29] border border-[#252E3E] rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-mono text-slate-400 uppercase">BUY P(UP) THRESHOLD</label>
            <input
              type="number"
              step="0.05"
              min="0.5"
              max="0.95"
              value={buyThresh}
              onChange={(e) => setBuyThresh(parseFloat(e.target.value))}
              className="w-full bg-[#181E29] border border-[#252E3E] rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-mono text-slate-400 uppercase">SELL P(UP) THRESHOLD</label>
            <input
              type="number"
              step="0.05"
              min="0.2"
              max="0.5"
              value={sellThresh}
              onChange={(e) => setSellThresh(parseFloat(e.target.value))}
              className="w-full bg-[#181E29] border border-[#252E3E] rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-mono text-slate-400 uppercase">STOP LOSS (%)</label>
            <input
              type="number"
              step="0.5"
              min="1.0"
              max="15.0"
              value={stopLossPct}
              onChange={(e) => setStopLossPct(parseFloat(e.target.value))}
              className="w-full bg-[#181E29] border border-[#252E3E] rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-mono font-bold flex items-center justify-center gap-1.5 disabled:opacity-50 transition-colors shadow-sm"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {loading ? "Simulating..." : "Run Backtest"}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800 rounded-md text-xs font-mono text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Simulation Error: {error}</span>
        </div>
      )}

      {/* Results Section */}
      {results && (
        <div className="space-y-6">
          {/* Key Metric Summary Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <MetricCard
              title="Strategy Return"
              value={formatPercent(results.summary.total_return_pct)}
              subtitle={`Final: ${formatINR(results.summary.final_equity)}`}
              change={results.summary.total_return_pct}
              badge="NET OF FEES"
            />
            <MetricCard
              title="Benchmark Return"
              value={formatPercent(results.summary.benchmark_return_pct)}
              subtitle="Buy & Hold Equity"
              badge="BUY & HOLD"
            />
            <MetricCard
              title="CAGR"
              value={`${results.summary.cagr_pct}%`}
              subtitle="Annualized Compound Return"
            />
            <MetricCard
              title="Sharpe / Sortino"
              value={`${results.summary.sharpe_ratio} / ${results.summary.sortino_ratio || "N/A"}`}
              subtitle="Risk-adjusted excess return"
              badge="ANNUALIZED"
            />
            <MetricCard
              title="Max Drawdown"
              value={`${results.summary.max_drawdown_pct}%`}
              subtitle="Peak-to-trough drop"
              change={results.summary.max_drawdown_pct}
            />
            <MetricCard
              title="Win Rate & Trades"
              value={`${results.summary.win_rate_pct}%`}
              subtitle={`${results.summary.winning_trades}W / ${results.summary.losing_trades}L (${results.summary.total_trades} trades)`}
            />
          </div>

          {/* Equity Curve SVG Chart */}
          <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#202736] pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-400" />
                  Simulated Equity Curve vs. Benchmark
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Initial Capital: {formatINR(results.summary.initial_capital)} • Total Fees Paid: {formatINR(results.summary.total_fees_paid)}
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <span className="flex items-center gap-1.5 text-blue-400 font-bold">
                  <span className="w-3 h-0.5 bg-blue-500 inline-block" /> Strategy Equity
                </span>
                <span className="flex items-center gap-1.5 text-slate-400">
                  <span className="w-3 h-0.5 bg-slate-500 inline-block" /> Benchmark
                </span>
              </div>
            </div>

            {/* Dynamic SVG chart */}
            <div className="w-full h-64 overflow-hidden relative">
              <svg viewBox="0 0 800 240" className="w-full h-full">
                {/* Horizontal grid lines */}
                {[40, 90, 140, 190].map((y, i) => (
                  <line key={i} x1="20" y1={y} x2="780" y2={y} stroke="#1C2432" strokeDasharray="3 3" />
                ))}

                {svgData && results.equity_curve && results.equity_curve.length > 1 && (
                  <>
                    {/* Benchmark Polyline */}
                    <polyline
                      fill="none"
                      stroke="#64748B"
                      strokeWidth="1.5"
                      strokeDasharray="4 4"
                      points={svgData.benchPoints}
                    />
                    {/* Strategy Line */}
                    <polyline
                      fill="none"
                      stroke="#3B82F6"
                      strokeWidth="2.5"
                      points={svgData.stratPoints}
                    />
                  </>
                )}
              </svg>
            </div>
          </div>

          {/* Executed Trade Logs Table */}
          {results.trades && results.trades.length > 0 && (
            <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-5 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#202736] pb-3">
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <ListOrdered className="w-4 h-4 text-emerald-400" />
                  Executed Trade Logs ({results.trades.length} Closed Trades)
                </h3>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-mono text-slate-400">
                    Profit Factor: <strong className="text-slate-200">{results.summary.profit_factor}</strong>
                  </span>
                  <button
                    type="button"
                    onClick={handleExportCSV}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#1A2638] hover:bg-[#22334A] text-slate-200 text-[11px] font-mono font-semibold transition-colors border border-[#2A3F5C]"
                  >
                    <Download className="w-3.5 h-3.5 text-emerald-400" />
                    Export CSV
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-[#1E2634] text-slate-400 text-[10px]">
                      <th className="py-2 px-3">TRADE ID</th>
                      <th className="py-2 px-3">ENTRY DATE</th>
                      <th className="py-2 px-3">EXIT DATE</th>
                      <th className="py-2 px-3">ENTRY PRICE</th>
                      <th className="py-2 px-3">EXIT PRICE</th>
                      <th className="py-2 px-3">SHARES</th>
                      <th className="py-2 px-3">NET P&L</th>
                      <th className="py-2 px-3">RETURN</th>
                      <th className="py-2 px-3">REASON</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1A2332]">
                    {results.trades.map((t: any) => (
                      <tr key={t.trade_id} className="hover:bg-[#161D29] transition-colors">
                        <td className="py-2 px-3 text-slate-300 font-bold">{t.trade_id}</td>
                        <td className="py-2 px-3 text-slate-400">{t.entry_date}</td>
                        <td className="py-2 px-3 text-slate-400">{t.exit_date}</td>
                        <td className="py-2 px-3 text-slate-200">{formatINR(t.entry_price)}</td>
                        <td className="py-2 px-3 text-slate-200">{formatINR(t.exit_price)}</td>
                        <td className="py-2 px-3 text-slate-300">{t.shares}</td>
                        <td className={`py-2 px-3 font-bold ${t.pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {t.pnl >= 0 ? "+" : ""}{formatINR(t.pnl)}
                        </td>
                        <td className={`py-2 px-3 font-bold ${t.pnl_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {t.pnl_pct >= 0 ? "+" : ""}{t.pnl_pct}%
                        </td>
                        <td className="py-2 px-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] uppercase font-bold ${
                              t.reason === "TAKE_PROFIT"
                                ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                                : t.reason === "STOP_LOSS"
                                ? "bg-rose-950 text-rose-300 border border-rose-800"
                                : "bg-slate-800 text-slate-300 border border-slate-700"
                            }`}
                          >
                            {t.reason}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Regulatory Cost Accounting Disclosure */}
          <div className="p-4 bg-[#141A24] border border-[#202736] rounded-lg text-xs font-mono text-slate-400 space-y-1">
            <div className="text-slate-200 font-bold flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              INDIAN EQUITIES REGULATORY & FRICTION ACCOUNTING
            </div>
            <p>• Brokerage modeled at 0.03% (capped at ₹20 per executed order).</p>
            <p>• Securities Transaction Tax (STT) modeled at 0.1% on equity delivery trades.</p>
            <p>• GST modeled at 18% on combined brokerage and exchange turnover fees.</p>
            <p>• Execution slippage modeled at 5 basis points (0.05%) on all market orders.</p>
          </div>
        </div>
      )}
    </div>
  )
}
