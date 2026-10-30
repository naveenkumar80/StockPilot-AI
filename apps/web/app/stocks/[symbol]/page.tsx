"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import {
  ArrowLeft,
  TrendingUp,
  AlertTriangle,
  FileText,
  Clock,
  ShieldAlert,
  CheckCircle,
  ExternalLink,
  Briefcase,
  Layers,
} from "lucide-react"
import {
  api,
  StockItem,
  Candle,
  PredictionDetail,
  NewsItem,
} from "@/lib/api"
import { CandlestickChart } from "@/components/common/CandlestickChart"
import { SignalBadge } from "@/components/common/SignalBadge"
import { formatINR, formatPercent, formatDate } from "@/lib/utils"

export default function StockDetailPage() {
  const urlParams = useParams()
  const rawSymbol = typeof urlParams?.symbol === "string" ? urlParams.symbol : Array.isArray(urlParams?.symbol) ? urlParams.symbol[0] : "RELIANCE"
  const symbol = (rawSymbol || "RELIANCE").toUpperCase()

  const [stock, setStock] = useState<StockItem | null>(null)
  const [candles, setCandles] = useState<Candle[]>([])
  const [prediction, setPrediction] = useState<PredictionDetail | null>(null)
  const [news, setNews] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Paper order quick modal state
  const [orderQty, setOrderQty] = useState(10)
  const [orderSide, setOrderSide] = useState<"BUY" | "SELL">("BUY")
  const [orderStatus, setOrderStatus] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError(null)

    Promise.all([
      api.getStockDetail(symbol),
      api.getStockCandles(symbol, "1d"),
      api.getStockPrediction(symbol),
      api.getStockNews(symbol),
    ])
      .then(([stockData, candleData, predData, newsData]) => {
        if (mounted) {
          setStock(stockData)
          setCandles(candleData.candles)
          setPrediction(predData)
          setNews(newsData.articles)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message)
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [symbol])

  const handleExecutePaperOrder = async () => {
    if (!stock) return
    setIsSubmitting(true)
    setOrderStatus(null)
    try {
      const idempotencyKey = `ord-${Date.now()}-${symbol}-${Math.random().toString(36).substring(7)}`
      const res = await api.placePaperOrder({
        idempotency_key: idempotencyKey,
        symbol: symbol,
        side: orderSide,
        quantity: orderQty,
        order_type: "MARKET",
      })
      setOrderStatus(`Simulated ${res.side} order for ${res.quantity} shares FILLED at ${formatINR(res.executed_price)}`)
    } catch (e: any) {
      setOrderStatus(`Order failed: ${e.message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-6 bg-[#181E29] rounded w-32" />
        <div className="h-24 bg-[#12161F] border border-[#252E3E] rounded-lg" />
        <div className="h-96 bg-[#12161F] border border-[#252E3E] rounded-lg" />
      </div>
    )
  }

  if (error || !stock) {
    return (
      <div className="p-8 bg-[#181E29] border border-rose-900/50 rounded-lg text-center space-y-4">
        <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-slate-100">Stock '{symbol}' not found in universe</h2>
        <p className="text-xs text-slate-400">{error || "Ensure symbol is listed on NSE/BSE"}</p>
        <Link
          href="/screener"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 rounded text-xs font-mono text-white"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Screener
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Navigation Breadcrumb & Back */}
      <div className="flex items-center justify-between">
        <Link
          href="/screener"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Screener
        </Link>
        <span className="text-xs font-mono text-slate-500">EXCHANGE: {stock.exchange} • CASH SEGMENT</span>
      </div>

      {/* Stock Header Card */}
      <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold font-mono tracking-tight text-slate-100">{stock.symbol}</h1>
            <SignalBadge signal={stock.signal} />
            {prediction?.is_demo && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                DEMO DATA
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">{stock.company_name} • {stock.sector}</p>
        </div>

        <div className="flex items-baseline gap-4 md:text-right">
          <div>
            <div className="text-3xl font-bold font-mono text-slate-100">{formatINR(stock.last_price)}</div>
            <div className="text-xs font-mono font-medium mt-0.5">
              <span className={stock.change_24h >= 0 ? "text-emerald-400" : "text-rose-400"}>
                {formatPercent(stock.change_24h)} (24H)
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Candlestick & Volume Visualization Chart */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-1">
          <span>DAILY OHLCV CANDLESTICK & VOLUME</span>
          <span>SOURCE: {prediction?.is_demo ? "DEMO_GROWW_MOCK" : "GROWW_TRADE_API"}</span>
        </div>
        <CandlestickChart candles={candles} height={380} symbol={stock.symbol} />
      </div>

      {/* Grid: ML Forecast Panel & Paper Trading Execution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ML Prediction Engine Card */}
        <div className="lg:col-span-2 bg-[#12161F] border border-[#252E3E] rounded-lg p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-[#202736] pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-400" />
                Machine Learning Forecast Engine
              </h2>
              <p className="text-xs text-slate-400">
                Model: <span className="font-mono text-slate-300">{prediction?.model_version}</span> • Horizon:{" "}
                <span className="font-mono text-slate-300">{prediction?.forecast_horizon}</span>
              </p>
            </div>
            <div className="text-right">
              <div className="text-[10px] font-mono text-slate-400">AS OF</div>
              <div className="text-xs font-mono text-slate-300">{formatDate(prediction?.as_of)}</div>
            </div>
          </div>

          {/* Probabilities Metric Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 bg-[#181E29] border border-[#252E3E] rounded-lg">
            <div>
              <div className="text-[10px] font-mono text-slate-400 uppercase">Calibrated P(UP)</div>
              <div className="text-2xl font-bold font-mono text-emerald-400">
                {prediction?.probability_up ? `${(prediction.probability_up * 100).toFixed(1)}%` : "N/A"}
              </div>
              <div className="text-[11px] text-slate-400">Isotonic calibrated</div>
            </div>
            <div>
              <div className="text-[10px] font-mono text-slate-400 uppercase">Expected Return</div>
              <div className="text-2xl font-bold font-mono text-slate-100">
                {prediction?.expected_return !== null && prediction?.expected_return !== undefined ? (
                  <span className={prediction.expected_return > 0 ? "text-emerald-400" : "text-rose-400"}>
                    {formatPercent(prediction.expected_return * 100)}
                  </span>
                ) : (
                  "N/A"
                )}
              </div>
              <div className="text-[11px] text-slate-400">
                {prediction?.expected_return_interval
                  ? `[${(prediction.expected_return_interval[0] * 100).toFixed(1)}%, ${(prediction.expected_return_interval[1] * 100).toFixed(1)}%]`
                  : "5-session interval"}
              </div>
            </div>
            <div>
              <div className="text-[10px] font-mono text-slate-400 uppercase">Risk Assessment</div>
              <div className="text-2xl font-bold font-mono text-slate-100">{prediction?.risk_level}</div>
              <div className="text-[11px] text-slate-400">Data Status: {prediction?.data_quality_status}</div>
            </div>
          </div>

          {/* Explainability Attributions: Bullish vs Bearish Factors */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Supporting Factors */}
            <div className="p-4 bg-[#141A24] border border-emerald-950/80 rounded-lg space-y-2">
              <h3 className="text-xs font-bold font-mono text-emerald-400 flex items-center gap-1.5 uppercase">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                Supporting (Bullish) Evidence
              </h3>
              <ul className="text-xs text-slate-300 space-y-1.5 leading-relaxed">
                {prediction?.supporting_factors && prediction.supporting_factors.length > 0 ? (
                  prediction.supporting_factors.map((factor, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{factor}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-slate-500 italic">No significant positive factors identified.</li>
                )}
              </ul>
            </div>

            {/* Contradicting Factors */}
            <div className="p-4 bg-[#141A24] border border-rose-950/80 rounded-lg space-y-2">
              <h3 className="text-xs font-bold font-mono text-rose-400 flex items-center gap-1.5 uppercase">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                Contradicting (Risk) Factors
              </h3>
              <ul className="text-xs text-slate-300 space-y-1.5 leading-relaxed">
                {prediction?.contradicting_factors && prediction.contradicting_factors.length > 0 ? (
                  prediction.contradicting_factors.map((factor, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-rose-500 font-bold">•</span>
                      <span>{factor}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-slate-500 italic">No prominent negative factors.</li>
                )}
              </ul>
            </div>
          </div>

          {/* Model Limitations Disclaimer */}
          <div className="p-3 bg-[#0E121A] border border-[#202736] rounded text-[11px] font-mono text-slate-400 space-y-1">
            <span className="text-slate-300 font-semibold">METHODOLOGY & MODEL LIMITATIONS:</span>
            {prediction?.limitations.map((lim, i) => (
              <p key={i}>• {lim}</p>
            ))}
          </div>
        </div>

        {/* Paper Trading Simulated Order Placement Card */}
        <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-6 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-[#202736] pb-3">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-emerald-400" />
                Paper Execution
              </h2>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                VIRTUAL
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Execute simulated trades in the virtual sandbox with realistic 5 bps slippage and brokerage fees.
            </p>

            {/* Order Side Selector */}
            <div className="grid grid-cols-2 gap-2 pt-2">
              <button
                type="button"
                onClick={() => setOrderSide("BUY")}
                className={`py-2 rounded text-xs font-mono font-bold transition-all ${
                  orderSide === "BUY"
                    ? "bg-emerald-600 text-white shadow"
                    : "bg-[#181E29] text-slate-400 hover:text-slate-200"
                }`}
              >
                BUY
              </button>
              <button
                type="button"
                onClick={() => setOrderSide("SELL")}
                className={`py-2 rounded text-xs font-mono font-bold transition-all ${
                  orderSide === "SELL"
                    ? "bg-rose-600 text-white shadow"
                    : "bg-[#181E29] text-slate-400 hover:text-slate-200"
                }`}
              >
                SELL
              </button>
            </div>

            {/* Quantity Input */}
            <div className="space-y-1 pt-2">
              <label className="text-[11px] font-mono text-slate-400">ORDER QUANTITY (SHARES)</label>
              <input
                type="number"
                min="1"
                value={orderQty}
                onChange={(e) => setOrderQty(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full bg-[#181E29] border border-[#252E3E] rounded p-2 text-sm font-mono text-slate-100 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Simulated Cost Summary */}
            <div className="p-3 bg-[#181E29] border border-[#252E3E] rounded text-xs font-mono space-y-1.5 text-slate-400">
              <div className="flex justify-between">
                <span>Ref Price:</span>
                <span className="text-slate-200">{formatINR(stock.last_price)}</span>
              </div>
              <div className="flex justify-between">
                <span>Estimated Value:</span>
                <span className="text-slate-200">{formatINR(stock.last_price * orderQty)}</span>
              </div>
              <div className="flex justify-between text-[11px]">
                <span>Est. Brokerage & Taxes:</span>
                <span>{formatINR(stock.last_price * orderQty * 0.0003)}</span>
              </div>
            </div>

            {orderStatus && (
              <div
                className={`p-3 rounded text-xs font-mono ${
                  orderStatus.includes("FILLED")
                    ? "bg-emerald-950/60 border border-emerald-800 text-emerald-300"
                    : "bg-rose-950/60 border border-rose-800 text-rose-300"
                }`}
              >
                {orderStatus}
              </div>
            )}
          </div>

          <button
            type="button"
            disabled={isSubmitting}
            onClick={handleExecutePaperOrder}
            className={`w-full py-2.5 rounded font-mono font-bold text-xs uppercase tracking-wider text-white transition-all ${
              orderSide === "BUY" ? "bg-emerald-600 hover:bg-emerald-500" : "bg-rose-600 hover:bg-rose-500"
            } disabled:opacity-50`}
          >
            {isSubmitting ? "Executing..." : `Simulate ${orderSide} Order`}
          </button>
        </div>
      </div>

      {/* Verified News & Disclosures Timeline */}
      <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-[#202736] pb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-400" />
            <h2 className="text-base font-bold text-slate-100">Verified Corporate Announcements & News</h2>
          </div>
          <span className="text-xs font-mono text-slate-400">Total Sourced: {news.length}</span>
        </div>

        {news.length === 0 ? (
          <div className="p-8 text-center text-xs font-mono text-slate-500">
            No recent news stories or filings recorded for {symbol}.
          </div>
        ) : (
          <div className="space-y-3">
            {news.map((item) => (
              <div
                key={item.id}
                className="p-4 bg-[#181E29] border border-[#252E3E] rounded-lg space-y-2 hover:border-[#354257] transition-all"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                      {item.source_type}
                    </span>
                    <span className="text-xs font-medium text-slate-400">{item.publisher}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    <span>Published: {formatDate(item.published_at)}</span>
                  </div>
                </div>

                <h3 className="text-sm font-semibold text-slate-100">{item.headline}</h3>
                {item.summary && <p className="text-xs text-slate-400 leading-relaxed">{item.summary}</p>}

                <div className="flex items-center justify-between pt-1 text-xs font-mono">
                  <div className="flex items-center gap-3">
                    {item.sentiment_label && (
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                          item.sentiment_label === "POSITIVE"
                            ? "bg-emerald-950 text-emerald-400"
                            : item.sentiment_label === "NEGATIVE"
                            ? "bg-rose-950 text-rose-400"
                            : "bg-slate-800 text-slate-300"
                        }`}
                      >
                        {item.sentiment_label} (Score: {item.sentiment_score ?? 0.0})
                      </span>
                    )}
                    {item.event_category && (
                      <span className="text-[10px] text-slate-400">Category: {item.event_category}</span>
                    )}
                  </div>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 flex items-center gap-1 text-[11px]"
                  >
                    Source Filing <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
