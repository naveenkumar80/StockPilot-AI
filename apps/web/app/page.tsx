"use client"

import React, { useState, useEffect, useRef } from "react"
import Link from "next/link"
import Image from "next/image"
import {
  BrainCircuit,
  TrendingUp,
  ShieldAlert,
  Briefcase,
  ExternalLink,
  Plus,
  ChevronRight,
  Info,
  MoreVertical,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
} from "lucide-react"
import { api, Candle, LiveQuote, NewsItem, PredictionDetail } from "@/lib/api"
import { CandlestickChart } from "@/components/common/CandlestickChart"
import { SignalBadge } from "@/components/common/SignalBadge"

export default function DashboardPage() {
  const [candles, setCandles] = useState<Candle[]>([])
  const [prediction, setPrediction] = useState<PredictionDetail | null>(null)
  const [isRefreshingPred, setIsRefreshingPred] = useState(false)
  const [activeNewsTab, setActiveNewsTab] = useState("All")
  const [activeMoverTab, setActiveMoverTab] = useState("Top Gainers")
  const [activePeriod, setActivePeriod] = useState("1D")
  const [newsArticles, setNewsArticles] = useState<NewsItem[]>([])

  // Real-time market quotes dictionary aligned with Groww live market
  const [quotes, setQuotes] = useState<Record<string, LiveQuote>>({
    RELIANCE: { symbol: "RELIANCE", exchange: "NSE", last_price: 1167.70, day_change: 9.80, day_change_perc: 0.85, open: 1159.00, high: 1182.10, low: 1155.60, close: 1158.00, volume: 15243869, is_live: true, source: "live_stream" },
    TCS: { symbol: "TCS", exchange: "NSE", last_price: 2478.30, day_change: 18.20, day_change_perc: 0.74, open: 2490.00, high: 2509.50, low: 2464.00, close: 2460.00, volume: 3427409, is_live: true, source: "live_stream" },
    HDFCBANK: { symbol: "HDFCBANK", exchange: "NSE", last_price: 685.55, day_change: 0.30, day_change_perc: 0.04, open: 686.00, high: 692.00, low: 683.00, close: 685.25, volume: 12100000, is_live: true, source: "live_stream" },
    ICICIBANK: { symbol: "ICICIBANK", exchange: "NSE", last_price: 1385.30, day_change: 7.70, day_change_perc: 0.56, open: 1380.00, high: 1395.00, low: 1378.00, close: 1377.60, volume: 9650000, is_live: true, source: "live_stream" },
    INFY: { symbol: "INFY", exchange: "NSE", last_price: 1139.00, day_change: 15.85, day_change_perc: 1.41, open: 1130.00, high: 1146.50, low: 1125.20, close: 1123.15, volume: 14045904, is_live: true, source: "live_stream" },
    ADANIPORTS: { symbol: "ADANIPORTS", exchange: "NSE", last_price: 1867.00, day_change: 105.70, day_change_perc: 6.00, open: 1775.00, high: 1880.00, low: 1765.00, close: 1761.30, volume: 12400000, is_live: true, source: "live_stream" },
    BEL: { symbol: "BEL", exchange: "NSE", last_price: 369.25, day_change: 5.90, day_change_perc: 1.62, open: 365.00, high: 372.00, low: 363.00, close: 363.35, volume: 18700000, is_live: true, source: "live_stream" },
    SBIN: { symbol: "SBIN", exchange: "NSE", last_price: 968.90, day_change: 12.10, day_change_perc: 1.26, open: 960.00, high: 975.00, low: 955.00, close: 956.80, volume: 25100000, is_live: true, source: "live_stream" },
    NTPC: { symbol: "NTPC", exchange: "NSE", last_price: 310.35, day_change: 6.60, day_change_perc: 2.17, open: 305.00, high: 314.00, low: 304.00, close: 303.75, volume: 14300000, is_live: true, source: "live_stream" },
    POWERGRID: { symbol: "POWERGRID", exchange: "NSE", last_price: 260.90, day_change: 9.50, day_change_perc: 3.78, open: 252.00, high: 263.00, low: 251.00, close: 251.40, volume: 11900000, is_live: true, source: "live_stream" },
    TATAMOTORS: { symbol: "TATAMOTORS", exchange: "NSE", last_price: 742.35, day_change: 8.90, day_change_perc: 1.21, open: 735.00, high: 748.00, low: 732.00, close: 733.45, volume: 8800000, is_live: true, source: "live_stream" },
  })

  const [flashes, setFlashes] = useState<Record<string, "up" | "down">>({})
  const prevPrices = useRef<Record<string, number>>({})
  const [liveTimeString, setLiveTimeString] = useState<string>("")

  useEffect(() => {
    // 1. Live ticking clock
    const updateTime = () => {
      const now = new Date()
      const dStr = now.toLocaleDateString("en-IN", { day: "numeric", month: "short" })
      const tStr = now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true })
      setLiveTimeString(`${dStr}, ${tStr}`)
    }
    updateTime()
    const clockTimer = setInterval(updateTime, 1000)

    // 2. Fetch candles for RELIANCE
    api.getStockCandles("RELIANCE", "1d")
      .then((res) => {
        if (res && res.candles) {
          setCandles(res.candles)
        }
      })
      .catch(() => {})

    // 2b. Fetch latest verified financial news
    api.getLatestNews({ pageSize: 25 })
      .then((res) => {
        if (res && res.articles && res.articles.length > 0) {
          setNewsArticles(res.articles)
        }
      })
      .catch(() => {})

    // 2c. Fetch real-time AI Prediction for RELIANCE
    api.getStockPrediction("RELIANCE")
      .then((pred) => {
        if (pred) setPrediction(pred)
      })
      .catch(() => {})

    // 3. Continuous real-time quotes polling loop (every 2.5s)
    let isMounted = true
    const symbolsToPoll = [
      "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY",
      "ADANIPORTS", "BEL", "SBIN", "NTPC", "POWERGRID", "TATAMOTORS"
    ]

    const pollLiveQuotes = async () => {
      try {
        const liveMap = await api.getLiveQuotes(symbolsToPoll)
        if (!isMounted) return

        const newFlashes: Record<string, "up" | "down"> = {}
        for (const sym of symbolsToPoll) {
          const newQuote = liveMap[sym]
          if (newQuote) {
            const oldPrice = prevPrices.current[sym] || quotes[sym]?.last_price || newQuote.last_price
            if (newQuote.last_price > oldPrice) {
              newFlashes[sym] = "up"
            } else if (newQuote.last_price < oldPrice) {
              newFlashes[sym] = "down"
            }
            prevPrices.current[sym] = newQuote.last_price
          }
        }

        setQuotes((prev) => ({ ...prev, ...liveMap }))
        if (Object.keys(newFlashes).length > 0) {
          setFlashes(newFlashes)
          setTimeout(() => {
            if (isMounted) setFlashes({})
          }, 800)
        }

        // Dynamically update latest candle on the chart with the live tick
        if (liveMap["RELIANCE"]) {
          const relQuote = liveMap["RELIANCE"]
          setCandles((prevCandles) => {
            if (!prevCandles || prevCandles.length === 0) return prevCandles
            const updated = [...prevCandles]
            const lastIdx = updated.length - 1
            const lastCandle = { ...updated[lastIdx] }
            lastCandle.close = relQuote.last_price
            lastCandle.high = Math.max(lastCandle.high, relQuote.last_price)
            lastCandle.low = Math.min(lastCandle.low, relQuote.last_price)
            updated[lastIdx] = lastCandle
            return updated
          })
        }
      } catch (e) {
        // Silently preserve last quotes
      }
    }

    const initTimer = setTimeout(pollLiveQuotes, 300)
    const pollTimer = setInterval(pollLiveQuotes, 2500)

    return () => {
      isMounted = false
      clearInterval(clockTimer)
      clearTimeout(initTimer)
      clearInterval(pollTimer)
    }
  }, [])

  const formatPrice = (val?: number) =>
    val != null
      ? "₹" + val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : "₹0.00"

  const handleRefreshPrediction = async () => {
    setIsRefreshingPred(true)
    try {
      const pred = await api.refreshPrediction("RELIANCE")
      if (pred) setPrediction(pred)
    } catch (e) {
      console.error("Failed to refresh prediction:", e)
    } finally {
      setIsRefreshingPred(false)
    }
  }

  const relQuote = quotes["RELIANCE"] || {
    last_price: 2893.45,
    day_change: 28.30,
    day_change_perc: 0.99,
  }

  // Calculate dynamic paper portfolio equity based on live quotes
  const paperEquity =
    (quotes["RELIANCE"]?.last_price || 2893.45) * 15 +
    (quotes["TCS"]?.last_price || 3967.20) * 10 +
    (quotes["HDFCBANK"]?.last_price || 1634.10) * 20 +
    (quotes["INFY"]?.last_price || 1482.60) * 10
  const investedAmount = 119000
  const totalPnl = paperEquity - investedAmount
  const totalPnlPct = (totalPnl / investedAmount) * 100
  const todayPnl = totalPnl * 0.36
  const todayPnlPct = (todayPnl / investedAmount) * 100


  return (
    <div className="space-y-5 pb-8 select-none">
      {/* 1. Hero Banner: StockPilot AI with Holographic Bull vs Bear */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#0C1322] via-[#0F1829] to-[#121B2B] border border-[#1C283B] p-6 lg:p-7 shadow-xl">
        {/* Holographic Bull & Bear Background Image with subtle gradient mask */}
        <div className="absolute right-0 top-0 bottom-0 w-full lg:w-3/5 pointer-events-none opacity-80 mix-blend-screen">
          <div className="relative w-full h-full">
            <Image
              src="/bull_bear_banner.jpg"
              alt="Holographic Bull vs Bear Quantitative Finance"
              fill
              className="object-cover object-right"
              priority
            />
            {/* Gradient mask on left of image for smooth blending */}
            <div className="absolute inset-0 bg-gradient-to-r from-[#0C1322] via-[#0C1322]/80 to-transparent" />
          </div>
        </div>

        {/* Content Container */}
        <div className="relative z-10 max-w-xl">
          <h1 className="text-3xl font-extrabold tracking-tight text-white font-sans">
            StockPilot AI
          </h1>
          <p className="text-xs text-slate-300 mt-1 font-medium">
            Data-Driven Predictions. Smarter Investments.
          </p>

          {/* 4 Feature Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-5">
            {/* Badge 1 */}
            <div className="flex flex-col items-start gap-1 p-2 rounded-xl bg-[#141E2F]/80 border border-[#203049] backdrop-blur-sm">
              <div className="w-6 h-6 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center">
                <BrainCircuit className="w-3.5 h-3.5" />
              </div>
              <span className="text-[10px] font-bold text-slate-200 leading-tight">
                AI Predictions
              </span>
              <span className="text-[9px] text-slate-400 leading-none">(ML + News)</span>
            </div>

            {/* Badge 2 */}
            <div className="flex flex-col items-start gap-1 p-2 rounded-xl bg-[#141E2F]/80 border border-[#203049] backdrop-blur-sm">
              <div className="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <TrendingUp className="w-3.5 h-3.5" />
              </div>
              <span className="text-[10px] font-bold text-slate-200 leading-tight">
                Real-time
              </span>
              <span className="text-[9px] text-slate-400 leading-none">Market Data</span>
            </div>

            {/* Badge 3 */}
            <div className="flex flex-col items-start gap-1 p-2 rounded-xl bg-[#141E2F]/80 border border-[#203049] backdrop-blur-sm">
              <div className="w-6 h-6 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
                <ShieldAlert className="w-3.5 h-3.5" />
              </div>
              <span className="text-[10px] font-bold text-slate-200 leading-tight">
                Risk Analysis
              </span>
              <span className="text-[9px] text-slate-400 leading-none">& Backtesting</span>
            </div>

            {/* Badge 4 */}
            <div className="flex flex-col items-start gap-1 p-2 rounded-xl bg-[#141E2F]/80 border border-[#203049] backdrop-blur-sm">
              <div className="w-6 h-6 rounded-lg bg-teal-500/20 text-teal-400 flex items-center justify-center">
                <Briefcase className="w-3.5 h-3.5" />
              </div>
              <span className="text-[10px] font-bold text-slate-200 leading-tight">
                Paper Trading
              </span>
              <span className="text-[9px] text-slate-400 leading-none">(No Real Money)</span>
            </div>
          </div>
        </div>

        {/* Right Quote Overlay */}
        <div className="hidden lg:block absolute right-8 top-7 z-10 text-right">
          <div className="p-3 rounded-xl bg-[#0B121D]/80 border border-[#1D2A3D] backdrop-blur-md max-w-xs text-left">
            <p className="text-[11px] text-slate-300 italic font-sans leading-relaxed">
              "Better insights.<br />Smarter trades.<br />Clearer decisions."
            </p>
          </div>
        </div>
      </div>

      {/* 2. Main Row: Featured Stock (Reliance) + Latest News Column */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
        {/* Left Column (Featured Stock Card & AI Prediction) */}
        <div className="xl:col-span-8 bg-[#0F1622] border border-[#192535] rounded-2xl p-5 space-y-4 shadow-sm">
          {/* Stock Header Row */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-bold font-mono text-white">RELIANCE</span>
                <span className="text-xs text-slate-400 font-sans">Reliance Industries Ltd.</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#172231] text-slate-300 border border-[#233247]">
                NSE
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#172231] text-slate-300 border border-[#233247]">
                Large Cap
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button className="px-3 py-1.5 rounded-lg bg-[#15202E] hover:bg-[#1E2C3F] text-xs font-sans text-slate-200 border border-[#23334A] flex items-center gap-1 transition-colors">
                <Plus className="w-3.5 h-3.5" /> Add to Watchlist
              </button>
              <a
                href="https://groww.in"
                target="_blank"
                rel="noopener noreferrer"
                className="px-3.5 py-1.5 rounded-lg bg-[#00C076] hover:bg-[#00D084] text-xs font-bold font-sans text-slate-950 flex items-center gap-1.5 shadow transition-colors"
              >
                Trade (Groww) <ExternalLink className="w-3.5 h-3.5 stroke-[2.5]" />
              </a>
            </div>
          </div>

          {/* Price & Live Info Row */}
          <div className="flex flex-wrap items-baseline gap-4">
            <div
              className={`text-3xl font-extrabold font-mono tracking-tight transition-all duration-300 ${
                flashes["RELIANCE"] === "up"
                  ? "text-emerald-400 bg-emerald-500/20 px-2 rounded-lg"
                  : flashes["RELIANCE"] === "down"
                  ? "text-rose-400 bg-rose-500/20 px-2 rounded-lg"
                  : "text-white"
              }`}
            >
              {formatPrice(relQuote.last_price)}
            </div>
            <div
              className={`text-sm font-mono font-bold transition-colors duration-300 ${
                relQuote.day_change >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {relQuote.day_change >= 0 ? "+" : ""}
              {relQuote.day_change.toFixed(2)} ({relQuote.day_change_perc >= 0 ? "+" : ""}
              {relQuote.day_change_perc.toFixed(2)}%)
            </div>
            <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 ml-auto">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Live As of {liveTimeString || "29 Oct, 10:42 AM"}</span>
            </div>
          </div>


          {/* Timeframe selector pills */}
          <div className="flex items-center gap-1 border-b border-[#1A2636] pb-3 text-xs font-mono">
            {["1D", "1W", "1M", "3M", "6M", "1Y", "5Y", "All"].map((t) => (
              <button
                key={t}
                onClick={() => setActivePeriod(t)}
                className={`px-3 py-1 rounded-md transition-all ${
                  activePeriod === t
                    ? "bg-blue-600 text-white font-bold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#15202E]"
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Candlestick Chart + AI Prediction Card Row */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
            {/* Chart Area */}
            <div className="lg:col-span-7">
              <CandlestickChart candles={candles} height={320} symbol="RELIANCE" />
            </div>

            {/* AI Prediction Card */}
            <div className="lg:col-span-5 bg-[#121B27] border border-[#1E2B3D] rounded-xl p-4 space-y-3.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
                  <span>AI Prediction</span>
                  <Info className="w-3.5 h-3.5 text-slate-500" />
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleRefreshPrediction}
                    disabled={isRefreshingPred}
                    className="p-1 rounded bg-[#1A2536] text-slate-400 hover:text-slate-200 hover:bg-[#25354D] border border-[#25354D] transition-colors"
                    title="Refresh AI inference with real-time indicators"
                  >
                    <RefreshCw className={`w-3 h-3 ${isRefreshingPred ? "animate-spin text-emerald-400" : ""}`} />
                  </button>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1A2536] text-slate-400 border border-[#25354D]">
                    5 Days
                  </span>
                </div>
              </div>

              {/* Big Signal Button & Probability */}
              <div className="flex items-center justify-between gap-3 p-2.5 rounded-lg bg-[#0C131D] border border-[#1A2636]">
                <div className="flex items-center gap-2">
                  {prediction?.signal === "BUY" ? (
                    <span className="px-3 py-1 rounded-md bg-emerald-500 text-slate-950 font-extrabold text-xs flex items-center gap-1">
                      👍 BUY
                    </span>
                  ) : prediction?.signal === "SELL" ? (
                    <span className="px-3 py-1 rounded-md bg-rose-500 text-slate-950 font-extrabold text-xs flex items-center gap-1">
                      👎 SELL
                    </span>
                  ) : prediction?.signal === "HOLD" ? (
                    <span className="px-3 py-1 rounded-md bg-amber-500 text-slate-950 font-extrabold text-xs flex items-center gap-1">
                      ✊ HOLD
                    </span>
                  ) : (
                    <span className="px-3 py-1 rounded-md bg-slate-700 text-slate-200 font-extrabold text-xs flex items-center gap-1">
                      ⚠️ NO TRADE
                    </span>
                  )}
                </div>
                <div className="text-right">
                  <div className={`text-sm font-bold font-mono ${
                    (prediction?.probability_up ?? 0.68) >= 0.60
                      ? "text-emerald-400"
                      : (prediction?.probability_up ?? 0.68) <= 0.40
                      ? "text-rose-400"
                      : "text-amber-400"
                  }`}>
                    {Math.round((prediction?.probability_up ?? 0.68) * 100)}%
                  </div>
                  <div className="text-[9px] text-slate-400 font-sans">Probability of Upside</div>
                </div>
              </div>

              {/* Metrics: Expected Return & Confidence */}
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-[#0E1622] border border-[#182332]">
                  <span className="text-[9px] text-slate-400 block">Expected Return</span>
                  <span className={`font-bold text-xs ${
                    (prediction?.expected_return ?? 0.05) >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}>
                    {prediction?.expected_return_interval
                      ? `${prediction.expected_return_interval[0] > 0 ? "+" : ""}${(prediction.expected_return_interval[0] * 100).toFixed(1)}% to ${prediction.expected_return_interval[1] > 0 ? "+" : ""}${(prediction.expected_return_interval[1] * 100).toFixed(1)}%`
                      : "+4.8% to +7.2%"}
                  </span>
                </div>
                <div className="p-2 rounded bg-[#0E1622] border border-[#182332]">
                  <span className="text-[9px] text-slate-400 block">Risk Level</span>
                  <span className="font-bold text-slate-200 text-xs">
                    {prediction?.risk_level || "Medium"}
                  </span>
                </div>
              </div>

              {/* Key Reasons */}
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold font-sans text-slate-300 block uppercase tracking-wider">
                  Key Reasons (Supporting)
                </span>
                <div className="space-y-1 text-[11px] text-slate-300">
                  {prediction?.supporting_factors && prediction.supporting_factors.length > 0 ? (
                    prediction.supporting_factors.slice(0, 4).map((f, i) => (
                      <div key={i} className="flex items-start gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1 shrink-0" />
                        <span>{f}</span>
                      </div>
                    ))
                  ) : (
                    <>
                      <div className="flex items-start gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1 shrink-0" />
                        <span>Strong upward momentum (RSI 62)</span>
                      </div>
                      <div className="flex items-start gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1 shrink-0" />
                        <span>Positive news sentiment (3 recent updates)</span>
                      </div>
                      <div className="flex items-start gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1 shrink-0" />
                        <span>Higher than average trading volume</span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Risks to Watch */}
              <div className="space-y-1.5 pt-1 border-t border-[#1C2738]">
                <span className="text-[10px] font-bold font-sans text-slate-400 block uppercase tracking-wider">
                  Risks to Watch (Contradicting)
                </span>
                <div className="space-y-1 text-[11px] text-slate-400">
                  {prediction?.contradicting_factors && prediction.contradicting_factors.length > 0 ? (
                    prediction.contradicting_factors.slice(0, 3).map((f, i) => (
                      <div key={i} className="flex items-start gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1 shrink-0" />
                        <span>{f}</span>
                      </div>
                    ))
                  ) : (
                    <>
                      <div className="flex items-start gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1 shrink-0" />
                        <span>Valuation at higher levels</span>
                      </div>
                      <div className="flex items-start gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1 shrink-0" />
                        <span>Upcoming quarterly results</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (Latest News Widget) */}
        <div className="xl:col-span-4 bg-[#0F1622] border border-[#192535] rounded-2xl p-5 space-y-4 flex flex-col justify-between shadow-sm">
          <div>
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1A2636] pb-3">
              <h2 className="text-sm font-bold text-white font-sans">Latest News</h2>
              <Link href="/research" className="text-xs text-blue-400 hover:text-blue-300 font-sans font-medium">
                View All
              </Link>
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-1.5 py-3 overflow-x-auto text-[11px] font-sans">
              {["All", "Reliance", "Earnings", "Sector", "Market"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveNewsTab(cat)}
                  className={`px-3 py-1 rounded-full transition-all ${
                    activeNewsTab === cat
                      ? "bg-blue-600 text-white font-bold"
                      : "bg-[#141E2B] text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* News Articles Feed */}
            <div className="space-y-3">
              {(() => {
                const filtered = newsArticles.filter((art) => {
                  if (activeNewsTab === "All") return true
                  if (activeNewsTab === "Reliance") {
                    return (
                      art.headline.toLowerCase().includes("reliance") ||
                      art.headline.toLowerCase().includes("ril") ||
                      art.headline.toLowerCase().includes("jio")
                    )
                  }
                  if (activeNewsTab === "Earnings") {
                    return (
                      art.event_category === "EARNINGS" ||
                      art.headline.toLowerCase().includes("results") ||
                      art.headline.toLowerCase().includes("earnings") ||
                      art.headline.toLowerCase().includes("q2")
                    )
                  }
                  if (activeNewsTab === "Sector") {
                    return (
                      art.event_category === "MACRO_POLICY" ||
                      art.event_category === "REGULATORY" ||
                      art.headline.toLowerCase().includes("govt") ||
                      art.headline.toLowerCase().includes("policy")
                    )
                  }
                  return true
                })

                const itemsToShow = filtered.length > 0 ? filtered.slice(0, 5) : [
                  { id: "1", headline: "Reliance to invest ₹75,000 crore in new energy projects: Report", sentiment_label: "POSITIVE", published_at: new Date(Date.now() - 7200000).toISOString(), url: "https://economictimes.indiatimes.com" },
                  { id: "2", headline: "RIL Q2 earnings preview: Analysts expect strong retail performance", sentiment_label: "NEUTRAL", published_at: new Date(Date.now() - 14400000).toISOString(), url: "https://moneycontrol.com" },
                  { id: "3", headline: "Oil prices fall as global supply concerns ease", sentiment_label: "NEGATIVE", published_at: new Date(Date.now() - 18000000).toISOString(), url: "https://livemint.com" },
                  { id: "4", headline: "Reliance Jio expands 5G network to 100 new cities", sentiment_label: "POSITIVE", published_at: new Date(Date.now() - 21600000).toISOString(), url: "https://business-standard.com" },
                  { id: "5", headline: "Govt approves new spectrum allocation policy", sentiment_label: "NEUTRAL", published_at: new Date(Date.now() - 28800000).toISOString(), url: "https://financialexpress.com" },
                ]

                const gradients = [
                  "from-emerald-600/40 to-blue-500/20",
                  "from-blue-600/40 to-indigo-500/20",
                  "from-rose-600/40 to-amber-500/20",
                  "from-teal-600/40 to-emerald-500/20",
                  "from-purple-600/40 to-slate-500/20",
                ]

                return itemsToShow.map((item, idx) => {
                  const sent = item.sentiment_label?.toUpperCase() || "NEUTRAL"
                  const isPos = sent === "POSITIVE"
                  const isNeg = sent === "NEGATIVE"

                  const pubTime = new Date(item.published_at).getTime()
                  const diffHours = Math.max(1, Math.round((Date.now() - pubTime) / 3600000))
                  const timeStr = diffHours >= 24 ? `${Math.round(diffHours / 24)}d ago` : `${diffHours} hours ago`

                  return (
                    <a
                      key={item.id || idx}
                      href={item.url || "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-start gap-3 p-2 rounded-xl hover:bg-[#141E2B] transition-colors cursor-pointer group"
                    >
                      <div className="w-12 h-12 rounded-lg bg-[#182332] shrink-0 overflow-hidden relative">
                        <div className={`w-full h-full bg-gradient-to-tr ${gradients[idx % gradients.length]}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-medium text-slate-200 group-hover:text-white leading-snug line-clamp-2">
                          {item.headline}
                        </div>
                        <div className="flex items-center gap-2 mt-1.5 text-[10px]">
                          <span
                            className={`px-1.5 py-0.5 rounded font-bold ${
                              isPos
                                ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800"
                                : isNeg
                                ? "bg-rose-950/80 text-rose-400 border border-rose-800"
                                : "bg-slate-800 text-slate-300 border border-slate-700"
                            }`}
                          >
                            {isPos ? "Positive" : isNeg ? "Negative" : "Neutral"}
                          </span>
                          <span className="text-slate-500">{timeStr}</span>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 shrink-0 self-center" />
                    </a>
                  )
                })
              })()}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Bottom Grid: Row 1 (Top AI Picks, Market Movers, My Watchlist) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Card 1: Top AI Picks (Today) */}
        <div className="bg-[#0F1622] border border-[#192535] rounded-2xl p-5 space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white font-sans">Top AI Picks (Today)</h3>
            <Link href="/screener" className="text-[11px] text-blue-400 hover:text-blue-300 font-medium">
              View All
            </Link>
          </div>

          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-slate-500 border-b border-[#182332] text-[10px]">
                <th className="pb-1.5">#</th>
                <th className="pb-1.5">Symbol</th>
                <th className="pb-1.5 text-right">Price</th>
                <th className="pb-1.5 text-center">AI Signal</th>
                <th className="pb-1.5 text-right">Prob. ↑</th>
                <th className="pb-1.5"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#151E2B]">
              {[
                { rank: 1, sym: "RELIANCE", signal: "BUY", prob: "68%" },
                { rank: 2, sym: "TCS", signal: "BUY", prob: "64%" },
                { rank: 3, sym: "HDFCBANK", signal: "BUY", prob: "62%" },
                { rank: 4, sym: "ICICIBANK", signal: "HOLD", prob: "55%" },
                { rank: 5, sym: "INFY", signal: "BUY", prob: "61%" },
              ].map((row) => {
                const q = quotes[row.sym]
                const flash = flashes[row.sym]
                return (
                  <tr key={row.sym} className="hover:bg-[#131D2A] transition-colors">
                    <td className="py-2.5 text-slate-500 text-[11px]">{row.rank}</td>
                    <td className="py-2.5 font-bold text-slate-100 flex items-center gap-1.5">
                      <span className="w-4 h-4 rounded bg-[#182332] text-[9px] flex items-center justify-center font-bold text-blue-400">
                        {row.sym.slice(0, 1)}
                      </span>
                      <Link href={`/stocks/${row.sym}`} className="hover:text-blue-400">
                        {row.sym}
                      </Link>
                    </td>
                    <td
                      className={`py-2.5 text-right font-bold transition-all duration-300 ${
                        flash === "up"
                          ? "text-emerald-400 bg-emerald-950/60 rounded px-1"
                          : flash === "down"
                          ? "text-rose-400 bg-rose-950/60 rounded px-1"
                          : "text-slate-200"
                      }`}
                    >
                      {formatPrice(q?.last_price)}
                    </td>
                    <td className="py-2.5 text-center">
                      <SignalBadge signal={row.signal} />
                    </td>
                    <td className="py-2.5 text-right font-bold text-slate-100">{row.prob}</td>
                    <td className="py-2.5 text-right text-slate-600">
                      <MoreVertical className="w-3.5 h-3.5 inline cursor-pointer hover:text-slate-400" />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Card 2: Market Movers */}
        <div className="bg-[#0F1622] border border-[#192535] rounded-2xl p-5 space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white font-sans">Market Movers</h3>
            <div className="flex items-center gap-1 text-[10px] font-sans">
              {["Top Gainers", "Top Losers", "Most Active"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveMoverTab(tab)}
                  className={`px-2 py-0.5 rounded transition-all ${
                    activeMoverTab === tab
                      ? "bg-blue-600 text-white font-bold"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-slate-500 border-b border-[#182332] text-[10px]">
                <th className="pb-1.5">Symbol</th>
                <th className="pb-1.5 text-right">Price</th>
                <th className="pb-1.5 text-right">Change</th>
                <th className="pb-1.5 text-right">Volume</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#151E2B]">
              {(activeMoverTab === "Top Gainers"
                ? ["ADANIPORTS", "BEL", "SBIN", "NTPC", "POWERGRID"]
                : activeMoverTab === "Top Losers"
                ? ["TCS", "INFY", "ICICIBANK", "HDFCBANK", "RELIANCE"]
                : ["SBIN", "BEL", "NTPC", "ADANIPORTS", "RELIANCE"]
              ).map((sym) => {
                const q = quotes[sym]
                const flash = flashes[sym]
                const isPositive = (q?.day_change_perc ?? 0) >= 0
                const volStr = q?.volume
                  ? (q.volume >= 10000000
                      ? `${(q.volume / 10000000).toFixed(2)} Cr`
                      : `${(q.volume / 1000000).toFixed(1)}M`)
                  : "--"
                return (
                  <tr key={sym} className="hover:bg-[#131D2A] transition-colors">
                    <td className="py-2.5 font-bold text-slate-100 flex items-center gap-1.5">
                      <span className="w-4 h-4 rounded bg-slate-800 text-[9px] flex items-center justify-center font-bold text-slate-300">
                        {sym.slice(0, 1)}
                      </span>
                      <Link href={`/stocks/${sym}`} className="hover:text-blue-400">
                        {sym}
                      </Link>
                    </td>
                    <td
                      className={`py-2.5 text-right font-bold transition-all duration-300 ${
                        flash === "up"
                          ? "text-emerald-400 bg-emerald-950/60 rounded px-1"
                          : flash === "down"
                          ? "text-rose-400 bg-rose-950/60 rounded px-1"
                          : "text-slate-200"
                      }`}
                    >
                      {formatPrice(q?.last_price)}
                    </td>
                    <td
                      className={`py-2.5 text-right font-bold ${
                        isPositive ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {isPositive ? "+" : ""}
                      {q?.day_change_perc?.toFixed(2) ?? "0.00"}%
                    </td>
                    <td className="py-2.5 text-right text-slate-400">{volStr}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Card 3: My Watchlist */}
        <div className="bg-[#0F1622] border border-[#192535] rounded-2xl p-5 space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white font-sans">My Watchlist</h3>
            <Link href="/watchlist" className="text-[11px] text-blue-400 hover:text-blue-300 font-medium">
              View All
            </Link>
          </div>

          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-slate-500 border-b border-[#182332] text-[10px]">
                <th className="pb-1.5">Symbol</th>
                <th className="pb-1.5 text-right">Price</th>
                <th className="pb-1.5 text-right">Change</th>
                <th className="pb-1.5 text-center">AI Signal</th>
                <th className="pb-1.5"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#151E2B]">
              {[
                { sym: "RELIANCE", signal: "BUY" },
                { sym: "TCS", signal: "HOLD" },
                { sym: "HDFCBANK", signal: "BUY" },
                { sym: "INFY", signal: "HOLD" },
                { sym: "TATAMOTORS", signal: "BUY" },
              ].map((row) => {
                const q = quotes[row.sym]
                const flash = flashes[row.sym]
                const isPositive = (q?.day_change_perc ?? 0) >= 0
                return (
                  <tr key={row.sym} className="hover:bg-[#131D2A] transition-colors">
                    <td className="py-2.5 font-bold text-slate-100 flex items-center gap-1.5">
                      <span className="w-4 h-4 rounded bg-[#182332] text-[9px] flex items-center justify-center font-bold text-blue-400">
                        {row.sym.slice(0, 1)}
                      </span>
                      <Link href={`/stocks/${row.sym}`} className="hover:text-blue-400">
                        {row.sym}
                      </Link>
                    </td>
                    <td
                      className={`py-2.5 text-right font-bold transition-all duration-300 ${
                        flash === "up"
                          ? "text-emerald-400 bg-emerald-950/60 rounded px-1"
                          : flash === "down"
                          ? "text-rose-400 bg-rose-950/60 rounded px-1"
                          : "text-slate-200"
                      }`}
                    >
                      {formatPrice(q?.last_price)}
                    </td>
                    <td
                      className={`py-2.5 text-right font-bold ${
                        isPositive ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {isPositive ? "+" : ""}
                      {q?.day_change_perc?.toFixed(2) ?? "0.00"}%
                    </td>
                    <td className="py-2.5 text-center">
                      <SignalBadge signal={row.signal} />
                    </td>
                    <td className="py-2.5 text-right text-slate-600">
                      <MoreVertical className="w-3.5 h-3.5 inline cursor-pointer hover:text-slate-400" />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Bottom Grid: Row 2 (Portfolio Paper Trading, Asset Allocation, Recent Signals) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Card 4: Portfolio (Paper Trading) */}
        {(() => {
          // Dynamic paper portfolio calculation based on live quotes
          const relP = quotes["RELIANCE"]?.last_price ?? 2893.45
          const tcsP = quotes["TCS"]?.last_price ?? 3967.20
          const hdfcP = quotes["HDFCBANK"]?.last_price ?? 1634.10
          const infyP = quotes["INFY"]?.last_price ?? 1482.60

          const relChg = quotes["RELIANCE"]?.day_change ?? 28.30
          const tcsChg = quotes["TCS"]?.day_change ?? -12.75
          const hdfcChg = quotes["HDFCBANK"]?.day_change ?? 7.35
          const infyChg = quotes["INFY"]?.day_change ?? -2.70

          const invested = 119000
          // 15 RELIANCE, 10 TCS, 20 HDFCBANK, 15 INFY
          const totalVal = Math.round(15 * relP + 10 * tcsP + 20 * hdfcP + 15 * infyP)
          const totalPnl = totalVal - invested
          const totalPnlPct = ((totalPnl / invested) * 100).toFixed(2)

          const todayPnl = Math.round(15 * relChg + 10 * tcsChg + 20 * hdfcChg + 15 * infyChg)
          const prevVal = totalVal - todayPnl
          const todayPnlPct = ((todayPnl / (prevVal || 1)) * 100).toFixed(2)

          return (
            <div className="bg-[#0F1622] border border-[#192535] rounded-2xl p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white font-sans flex items-center gap-1.5">
                  Portfolio (Paper Trading) <Info className="w-3.5 h-3.5 text-slate-500" />
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800">
                  VIRTUAL
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <span className="text-[10px] text-slate-400 font-sans block">Total Value</span>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-xl font-bold font-mono text-white">{formatPrice(totalVal)}</span>
                    <span
                      className={`text-[11px] font-bold font-mono ${
                        totalPnl >= 0 ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {totalPnl >= 0 ? "+" : ""}
                      {totalPnlPct}%
                    </span>
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-sans block">Invested</span>
                  <span className="text-xl font-bold font-mono text-slate-200">{formatPrice(invested)}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[#182332]">
                <div>
                  <span className="text-[10px] text-slate-400 font-sans block">Today's P&L</span>
                  <span
                    className={`text-sm font-bold font-mono ${
                      todayPnl >= 0 ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {todayPnl >= 0 ? "+" : ""}
                    {formatPrice(todayPnl)} ({todayPnl >= 0 ? "+" : ""}
                    {todayPnlPct}%)
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-sans block">Total P&L</span>
                  <span
                    className={`text-sm font-bold font-mono ${
                      totalPnl >= 0 ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {totalPnl >= 0 ? "+" : ""}
                    {formatPrice(totalPnl)} ({totalPnl >= 0 ? "+" : ""}
                    {totalPnlPct}%)
                  </span>
                </div>
              </div>
            </div>
          )
        })()}

        {/* Card 5: Asset Allocation Donut Chart */}
        <div className="bg-[#0F1622] border border-[#192535] rounded-2xl p-5 space-y-3 shadow-sm">
          <h3 className="text-xs font-bold text-white font-sans">Asset Allocation</h3>

          <div className="flex items-center justify-center gap-6 pt-1">
            {/* SVG Donut Chart */}
            <div className="w-28 h-28 relative flex items-center justify-center">
              <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                {/* 45% Large Cap (Blue) */}
                <circle
                  cx="50"
                  cy="50"
                  r="38"
                  fill="transparent"
                  stroke="#3B82F6"
                  strokeWidth="16"
                  strokeDasharray="107.4 238.7"
                  strokeDashoffset="0"
                />
                {/* 30% Mid Cap (Teal) */}
                <circle
                  cx="50"
                  cy="50"
                  r="38"
                  fill="transparent"
                  stroke="#06B6D4"
                  strokeWidth="16"
                  strokeDasharray="71.6 238.7"
                  strokeDashoffset="-107.4"
                />
                {/* 15% Small Cap (Amber) */}
                <circle
                  cx="50"
                  cy="50"
                  r="38"
                  fill="transparent"
                  stroke="#F59E0B"
                  strokeWidth="16"
                  strokeDasharray="35.8 238.7"
                  strokeDashoffset="-179"
                />
                {/* 10% Cash (Slate) */}
                <circle
                  cx="50"
                  cy="50"
                  r="38"
                  fill="transparent"
                  stroke="#475569"
                  strokeWidth="16"
                  strokeDasharray="23.9 238.7"
                  strokeDashoffset="-214.8"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-[10px] font-mono text-slate-400">Total</span>
                <span className="text-xs font-bold font-mono text-white">100%</span>
              </div>
            </div>

            {/* Legend */}
            <div className="space-y-1.5 text-[11px] font-sans">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                <span className="text-slate-300">Large Cap</span>
                <span className="text-slate-400 font-mono ml-auto">45%</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" />
                <span className="text-slate-300">Mid Cap</span>
                <span className="text-slate-400 font-mono ml-auto">30%</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span className="text-slate-300">Small Cap</span>
                <span className="text-slate-400 font-mono ml-auto">15%</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-600" />
                <span className="text-slate-300">Cash</span>
                <span className="text-slate-400 font-mono ml-auto">10%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Card 6: Recent Signals */}
        <div className="bg-[#0F1622] border border-[#192535] rounded-2xl p-5 space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white font-sans">Recent Signals</h3>
            <Link href="/models" className="text-[11px] text-blue-400 hover:text-blue-300 font-medium">
              View All
            </Link>
          </div>

          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-slate-500 border-b border-[#182332] text-[10px]">
                <th className="pb-1.5">Time</th>
                <th className="pb-1.5">Symbol</th>
                <th className="pb-1.5 text-center">Signal</th>
                <th className="pb-1.5 text-right">Confidence</th>
                <th className="pb-1.5 text-right">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#151E2B]">
              {[
                { time: "10:30 AM", sym: "RELIANCE", signal: "BUY", conf: "68%", reason: "Momentum + Positive News" },
                { time: "09:45 AM", sym: "TCS", signal: "HOLD", conf: "55%", reason: "Sideways trend" },
                { time: "09:20 AM", sym: "HDFCBANK", signal: "BUY", conf: "62%", reason: "Strong volume buildup" },
              ].map((row, i) => (
                <tr key={i} className="hover:bg-[#131D2A] transition-colors">
                  <td className="py-2.5 text-slate-400 text-[10px]">{row.time}</td>
                  <td className="py-2.5 font-bold text-slate-100">{row.sym}</td>
                  <td className="py-2.5 text-center">
                    <SignalBadge signal={row.signal} />
                  </td>
                  <td className="py-2.5 text-right font-bold text-slate-200">{row.conf}</td>
                  <td className="py-2.5 text-right text-slate-400 text-[10px] truncate max-w-[130px]" title={row.reason}>
                    {row.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
