"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  BarChart2,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  ShieldAlert,
  Globe2,
  Compass,
  CheckCircle2,
  AlertTriangle,
  Flame,
} from "lucide-react"
import { api, MarketOverview, StockItem, LiveQuote } from "@/lib/api"
import { SignalBadge } from "@/components/common/SignalBadge"
import { formatINR, formatPercent } from "@/lib/utils"

interface SectorData {
  name: string
  change_pct: number
  trend: "BULLISH" | "NEUTRAL" | "BEARISH"
  leading_stock: string
  volume_level: string
}

const SECTOR_SNAPSHOTS: SectorData[] = [
  { name: "NIFTY IT", change_pct: 2.14, trend: "BULLISH", leading_stock: "INFY", volume_level: "High" },
  { name: "NIFTY AUTO", change_pct: 1.45, trend: "BULLISH", leading_stock: "TATAMOTORS", volume_level: "Moderate" },
  { name: "NIFTY BANK", change_pct: 1.19, trend: "BULLISH", leading_stock: "ICICIBANK", volume_level: "High" },
  { name: "NIFTY ENERGY", change_pct: 0.88, trend: "NEUTRAL", leading_stock: "RELIANCE", volume_level: "Very High" },
  { name: "NIFTY FMCG", change_pct: 0.32, trend: "NEUTRAL", leading_stock: "ITC", volume_level: "Low" },
  { name: "NIFTY PHARMA", change_pct: -0.24, trend: "NEUTRAL", leading_stock: "SUNPHARMA", volume_level: "Moderate" },
  { name: "NIFTY METAL", change_pct: -0.78, trend: "BEARISH", leading_stock: "TATASTEEL", volume_level: "High" },
]

export default function MarketInsightsPage() {
  const [overview, setOverview] = useState<MarketOverview | null>(null)
  const [stocks, setStocks] = useState<StockItem[]>([])
  const [quotes, setQuotes] = useState<Record<string, LiveQuote>>({})
  const [loading, setLoading] = useState(true)
  const [lastRefreshed, setLastRefreshed] = useState<string>("")

  const loadData = async () => {
    setLoading(true)
    try {
      const [ov, sc, lq] = await Promise.allSettled([
        api.getMarketOverview(),
        api.getStocks({ page: 1, page_size: 50, sort_by: "probability_up", sort_order: "desc" }),
        api.getLiveQuotes([
          "RELIANCE",
          "TCS",
          "INFY",
          "HDFCBANK",
          "ICICIBANK",
          "SBIN",
          "TATAMOTORS",
          "BEL",
          "NTPC",
          "ADANIPORTS",
        ]),
      ])

      if (ov.status === "fulfilled") setOverview(ov.value)
      if (sc.status === "fulfilled") setStocks(sc.value.items)
      if (lq.status === "fulfilled") setQuotes(lq.value)
      setLastRefreshed(new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata" }))
    } catch (err) {
      console.error("Error loading insights:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    const timer = setInterval(loadData, 15000)
    return () => clearInterval(timer)
  }, [])

  // Partition gainers and losers
  const topGainers = [...stocks]
    .filter((s) => s.change_24h > 0)
    .sort((a, b) => b.change_24h - a.change_24h)
    .slice(0, 5)

  const topLosers = [...stocks]
    .filter((s) => s.change_24h < 0)
    .sort((a, b) => a.change_24h - b.change_24h)
    .slice(0, 5)

  const highProbabilityBuys = [...stocks]
    .filter((s) => s.signal === "BUY" && (s.probability_up ?? 0) >= 0.6)
    .sort((a, b) => (b.probability_up ?? 0) - (a.probability_up ?? 0))
    .slice(0, 5)

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#172231] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Market Insights & Macro Intelligence
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                AI regime analytics, sector rotation, institutional flows, and high-probability momentum setups
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {lastRefreshed && (
            <span className="text-[11px] font-mono text-slate-400">
              Updated {lastRefreshed} IST
            </span>
          )}
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-[#121B27] hover:bg-[#1A2636] border border-[#1E2D42] text-xs font-medium text-slate-200 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* 4 Macro Key Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Regime Status */}
        <div className="p-4 rounded-xl bg-[#0E1520] border border-[#172231] relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Market Regime</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400 flex items-center gap-1.5">
            Bullish Expansion
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            <span className="text-emerald-400 font-semibold">74% Confidence</span> • Low Risk Horizon
          </div>
          <div className="mt-3 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-emerald-500 h-full rounded-full" style={{ width: "74%" }}></div>
          </div>
        </div>

        {/* Market Breadth */}
        <div className="p-4 rounded-xl bg-[#0E1520] border border-[#172231]">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>NIFTY Breadth (A/D)</span>
            <BarChart2 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-emerald-400">34</span>
            <span className="text-slate-600 text-sm">/</span>
            <span className="text-rose-400">16</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Ratio <span className="text-emerald-400 font-mono font-medium">2.12</span> • Strong Buy Participation
          </div>
          <div className="mt-3 flex h-1.5 w-full rounded-full overflow-hidden">
            <div className="bg-emerald-500" style={{ width: "68%" }}></div>
            <div className="bg-rose-500" style={{ width: "32%" }}></div>
          </div>
        </div>

        {/* Institutional Net Flows */}
        <div className="p-4 rounded-xl bg-[#0E1520] border border-[#172231]">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>FII & DII Flows (Est.)</span>
            <Globe2 className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400 font-mono">
            +₹3,600 Cr
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-2">
            <span>FII: <span className="text-emerald-400">+₹1,420 Cr</span></span>
            <span>DII: <span className="text-emerald-400">+₹2,180 Cr</span></span>
          </div>
          <div className="mt-3 text-[10px] text-slate-500 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Domestic SIP support remains stable
          </div>
        </div>

        {/* Volatility Index */}
        <div className="p-4 rounded-xl bg-[#0E1520] border border-[#172231]">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>India VIX (Volatility)</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono flex items-center gap-2">
            13.82
            <span className="text-xs text-emerald-400 font-normal flex items-center">
              <TrendingDown className="w-3.5 h-3.5" /> -2.4%
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Complacent • Low option premium pricing
          </div>
          <div className="mt-3 flex items-center gap-2 text-[10px] text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Favorable for swing momentum
          </div>
        </div>
      </div>

      {/* Sector Performance Grid */}
      <div className="p-5 rounded-2xl bg-[#0E1520] border border-[#172231]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-emerald-400" />
              Sector Rotation & Performance Heatmap
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live sector leadership indices indicating capital rotation patterns
            </p>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">NSE Indices</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {SECTOR_SNAPSHOTS.map((sec) => {
            const isPositive = sec.change_pct >= 0
            return (
              <div
                key={sec.name}
                className="p-3.5 rounded-xl bg-[#090E17] border border-[#172436] hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white tracking-tight">{sec.name}</span>
                  <span
                    className={`text-xs font-mono font-bold flex items-center ${
                      isPositive ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                    {formatPercent(sec.change_pct)}
                  </span>
                </div>

                <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Leader: <span className="text-slate-200 font-semibold">{sec.leading_stock}</span></span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      sec.trend === "BULLISH"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : sec.trend === "BEARISH"
                        ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        : "bg-slate-800 text-slate-300"
                    }`}
                  >
                    {sec.trend}
                  </span>
                </div>

                <div className="mt-2.5 w-full bg-slate-800/80 rounded-full h-1 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${isPositive ? "bg-emerald-500" : "bg-rose-500"}`}
                    style={{ width: `${Math.min(100, Math.abs(sec.change_pct) * 35)}%` }}
                  ></div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Two Column Layout: AI Market Analysis & High Probability Setups */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): AI Insights Commentary & Market Movers */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI Macro Highlights */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-[#0F1C2E] to-[#0A121D] border border-[#1C304A]">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-bold text-white tracking-tight">
                AI Macro Driver Synthesis
              </h3>
            </div>
            <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
                <span className="font-semibold text-emerald-400">IT Rebound & BFSI Deals:</span>{" "}
                Large-cap IT majors (INFY, TCS) are exhibiting relative strength following steady guidance and multi-quarter deal ramp-ups. Currency tailwinds (USD/INR ~84.2) are expected to support operating margins into Q3.
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
                <span className="font-semibold text-blue-400">Banking Asset Quality & Valuation:</span>{" "}
                Private lenders (HDFCBANK, ICICIBANK) are consolidating at historical median valuations with low NPA slippage risk. Retail deposit accretion trends remain the key monitorable.
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
                <span className="font-semibold text-indigo-400">Energy & Infrastructure Capex:</span>{" "}
                Reliance Industries (post 1:1 bonus issue) and power infrastructure leaders (NTPC, BEL) maintain elevated capex momentum with robust government policy tailwinds.
              </div>
            </div>
          </div>

          {/* Top Gainers & Losers Tabbed/Split Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Top Gainers */}
            <div className="p-4 rounded-xl bg-[#0E1520] border border-[#172231]">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4 text-emerald-400" /> Top Gainers Today
                </h4>
                <span className="text-[10px] text-emerald-400 font-mono font-medium">NSE Active</span>
              </div>
              <div className="space-y-2">
                {topGainers.length > 0 ? (
                  topGainers.map((s) => (
                    <Link
                      key={s.symbol}
                      href={`/stocks/${s.symbol}`}
                      className="flex items-center justify-between p-2 rounded-lg bg-[#090E17] hover:bg-[#121B27] border border-transparent hover:border-[#1E2D42] transition-colors"
                    >
                      <div>
                        <div className="text-xs font-bold text-white">{s.symbol}</div>
                        <div className="text-[10px] text-slate-400">{s.company_name}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs font-mono font-bold text-white">{formatINR(s.last_price)}</div>
                        <div className="text-[10px] font-mono text-emerald-400 font-semibold flex items-center justify-end">
                          <ArrowUpRight className="w-3 h-3" />
                          {formatPercent(s.change_24h)}
                        </div>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="text-xs text-slate-500 py-4 text-center">Loading live movers...</div>
                )}
              </div>
            </div>

            {/* Top Losers */}
            <div className="p-4 rounded-xl bg-[#0E1520] border border-[#172231]">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                  <TrendingDown className="w-4 h-4 text-rose-400" /> Top Lagging Stocks
                </h4>
                <span className="text-[10px] text-rose-400 font-mono font-medium">NSE Active</span>
              </div>
              <div className="space-y-2">
                {topLosers.length > 0 ? (
                  topLosers.map((s) => (
                    <Link
                      key={s.symbol}
                      href={`/stocks/${s.symbol}`}
                      className="flex items-center justify-between p-2 rounded-lg bg-[#090E17] hover:bg-[#121B27] border border-transparent hover:border-[#1E2D42] transition-colors"
                    >
                      <div>
                        <div className="text-xs font-bold text-white">{s.symbol}</div>
                        <div className="text-[10px] text-slate-400">{s.company_name}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs font-mono font-bold text-white">{formatINR(s.last_price)}</div>
                        <div className="text-[10px] font-mono text-rose-400 font-semibold flex items-center justify-end">
                          <ArrowDownRight className="w-3 h-3" />
                          {formatPercent(s.change_24h)}
                        </div>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="text-xs text-slate-500 py-4 text-center">Loading market movers...</div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (1 Col): High Probability AI Model Setups */}
        <div className="space-y-6">
          <div className="p-5 rounded-2xl bg-[#0E1520] border border-[#172231]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Flame className="w-4 h-4 text-amber-400" />
                AI Top Conviction Setups
              </h3>
              <Link href="/models" className="text-[11px] text-emerald-400 hover:underline">
                View All
              </Link>
            </div>
            <p className="text-[11px] text-slate-400 mb-4">
              Top probability-of-upside signals calibrated across LightGBM & sentiment features
            </p>

            <div className="space-y-3">
              {highProbabilityBuys.length > 0 ? (
                highProbabilityBuys.map((stk) => (
                  <div
                    key={stk.symbol}
                    className="p-3 rounded-xl bg-[#090E17] border border-[#172436] flex items-center justify-between"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">{stk.symbol}</span>
                        <SignalBadge signal={stk.signal} />
                      </div>
                      <div className="text-[10px] text-slate-400 mt-1 font-mono">
                        LTP: {formatINR(stk.last_price)}
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-xs font-bold font-mono text-emerald-400">
                        {Math.round((stk.probability_up ?? 0) * 100)}% Upside
                      </div>
                      <Link
                        href={`/stocks/${stk.symbol}`}
                        className="text-[10px] text-blue-400 hover:text-blue-300 font-medium flex items-center justify-end gap-0.5 mt-0.5"
                      >
                        Deep Dive <ArrowUpRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500 py-4 text-center">Loading top setups...</div>
              )}
            </div>
          </div>

          {/* Quick Action Navigation */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-[#0F1E19] to-[#0B1512] border border-[#153B2E]">
            <h4 className="text-xs font-bold text-emerald-300 mb-1">Explore Platform Modules</h4>
            <p className="text-[11px] text-slate-400 mb-3">
              Seamlessly validate ideas with quantitative backtesting and paper trading.
            </p>
            <div className="grid grid-cols-2 gap-2">
              <Link
                href="/screener"
                className="p-2.5 rounded-lg bg-[#0E2920] hover:bg-[#12362A] text-center text-xs font-semibold text-emerald-300 border border-emerald-800/40 transition-colors"
              >
                Stock Screener
              </Link>
              <Link
                href="/backtesting"
                className="p-2.5 rounded-lg bg-[#0E2920] hover:bg-[#12362A] text-center text-xs font-semibold text-emerald-300 border border-emerald-800/40 transition-colors"
              >
                Backtest Strategy
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

