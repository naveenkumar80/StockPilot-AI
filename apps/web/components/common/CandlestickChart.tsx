"use client"

import React, { useState } from "react"
import { Candle } from "@/lib/api"
import { formatINR } from "@/lib/utils"

interface CandlestickChartProps {
  candles: Candle[]
  height?: number
  symbol?: string
}

export function CandlestickChart({ candles = [], height = 380, symbol = "EQUITY" }: CandlestickChartProps) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null)
  const [showEMA20, setShowEMA20] = useState(true)
  const [showEMA50, setShowEMA50] = useState(false)
  const [showBB, setShowBB] = useState(false)

  if (!candles || candles.length === 0) {
    return (
      <div className="w-full flex items-center justify-center bg-[#12161F] border border-[#252E3E] rounded-lg p-8 text-slate-500 font-mono text-sm" style={{ height }}>
        No historical candle data available
      </div>
    )
  }

  // Pre-calculate indicators on the full series (Pure computation, zero hooks after early return)
  const closes = candles.map((c) => c.close)
  const totalN = closes.length

  // EMA calculation helper
  const calcEMA = (period: number) => {
    const k = 2 / (period + 1)
    const ema: (number | null)[] = new Array(totalN).fill(null)
    if (totalN < period) return ema

    let sum = 0
    for (let i = 0; i < period; i++) sum += closes[i]
    ema[period - 1] = sum / period

    for (let i = period; i < totalN; i++) {
      ema[i] = closes[i] * k + (ema[i - 1] as number) * (1 - k)
    }
    return ema
  }

  // Bollinger Bands (20 period, 2 std dev)
  const calcBB = (period = 20, mult = 2) => {
    const upper: (number | null)[] = new Array(totalN).fill(null)
    const lower: (number | null)[] = new Array(totalN).fill(null)
    const mid: (number | null)[] = new Array(totalN).fill(null)

    for (let i = period - 1; i < totalN; i++) {
      const slice = closes.slice(i - period + 1, i + 1)
      const mean = slice.reduce((a, b) => a + b, 0) / period
      const variance = slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / period
      const std = Math.sqrt(variance)

      mid[i] = mean
      upper[i] = mean + mult * std
      lower[i] = mean - mult * std
    }
    return { upper, lower, mid }
  }

  const indicators = {
    ema20: calcEMA(20),
    ema50: calcEMA(50),
    bb: calcBB(20, 2),
  }

  // Slice to last 60 candles for crisp display
  const displayCandles = candles.slice(-60)
  const displaySliceStart = Math.max(0, candles.length - 60)
  const n = displayCandles.length

  const minPrice = Math.min(...displayCandles.map((c) => c.low))
  const maxPrice = Math.max(...displayCandles.map((c) => c.high))
  const priceRange = maxPrice - minPrice || 1.0

  const maxVolume = Math.max(...displayCandles.map((c) => c.volume)) || 1

  const padding = { top: 25, right: 65, bottom: 40, left: 20 }
  const chartHeight = height - padding.top - padding.bottom
  const priceHeight = chartHeight * 0.74
  const volumeHeight = chartHeight * 0.22
  const volumeTop = padding.top + priceHeight + 10

  const candleWidth = 6
  const spacing = (800 - padding.left - padding.right) / Math.max(n - 1, 1)

  const getY = (val: number) => {
    return padding.top + (1.0 - (val - minPrice) / priceRange) * priceHeight
  }

  const activeCandle = hoverIdx !== null && displayCandles[hoverIdx] ? displayCandles[hoverIdx] : displayCandles[displayCandles.length - 1]
  const activeFullIdx = hoverIdx !== null ? displaySliceStart + hoverIdx : candles.length - 1

  // Path generators for indicators
  let ema20Path = ""
  if (showEMA20) {
    for (let i = 0; i < n; i++) {
      const fullIdx = displaySliceStart + i
      const val = indicators.ema20[fullIdx]
      if (val !== null) {
        const x = padding.left + i * spacing
        const y = getY(val)
        ema20Path += ema20Path === "" ? `M${x},${y}` : ` L${x},${y}`
      }
    }
  }

  let ema50Path = ""
  if (showEMA50) {
    for (let i = 0; i < n; i++) {
      const fullIdx = displaySliceStart + i
      const val = indicators.ema50[fullIdx]
      if (val !== null) {
        const x = padding.left + i * spacing
        const y = getY(val)
        ema50Path += ema50Path === "" ? `M${x},${y}` : ` L${x},${y}`
      }
    }
  }

  let bbUpperPath = ""
  let bbLowerPath = ""
  if (showBB) {
    for (let i = 0; i < n; i++) {
      const fullIdx = displaySliceStart + i
      const upperVal = indicators.bb.upper[fullIdx]
      const lowerVal = indicators.bb.lower[fullIdx]
      const x = padding.left + i * spacing
      if (upperVal !== null) {
        const yUpper = getY(upperVal)
        bbUpperPath += bbUpperPath === "" ? `M${x},${yUpper}` : ` L${x},${yUpper}`
      }
      if (lowerVal !== null) {
        const yLower = getY(lowerVal)
        bbLowerPath += bbLowerPath === "" ? `M${x},${yLower}` : ` L${x},${yLower}`
      }
    }
  }

  return (
    <div className="w-full bg-[#12161F] border border-[#252E3E] rounded-xl p-4 flex flex-col gap-2.5 shadow-sm">
      {/* Legend / Hover bar & Overlay Controls */}
      <div className="flex flex-wrap items-center justify-between text-xs font-mono text-slate-400 border-b border-[#1C2432] pb-2.5 gap-2">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-bold text-slate-100">{symbol} • 1D</span>
          <span>
            O: <span className="text-slate-100">{formatINR(activeCandle.open)}</span>
          </span>
          <span>
            H: <span className="text-slate-100">{formatINR(activeCandle.high)}</span>
          </span>
          <span>
            L: <span className="text-slate-100">{formatINR(activeCandle.low)}</span>
          </span>
          <span>
            C:{" "}
            <span
              className={
                activeCandle.close >= activeCandle.open
                  ? "text-emerald-400 font-semibold"
                  : "text-rose-400 font-semibold"
              }
            >
              {formatINR(activeCandle.close)}
            </span>
          </span>
          <span>
            Vol: <span className="text-slate-300">{activeCandle.volume.toLocaleString()}</span>
          </span>

          {/* Indicator values on hover */}
          {showEMA20 && indicators.ema20[activeFullIdx] !== null && (
            <span className="text-cyan-400 hidden sm:inline">
              EMA20: {indicators.ema20[activeFullIdx]?.toFixed(1)}
            </span>
          )}
          {showEMA50 && indicators.ema50[activeFullIdx] !== null && (
            <span className="text-amber-400 hidden sm:inline">
              EMA50: {indicators.ema50[activeFullIdx]?.toFixed(1)}
            </span>
          )}
        </div>

        {/* Indicator Toggle Buttons */}
        <div className="flex items-center gap-1.5 font-sans">
          <button
            onClick={() => setShowEMA20(!showEMA20)}
            className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors border ${
              showEMA20
                ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/50"
                : "bg-slate-800/60 text-slate-400 border-slate-700 hover:text-slate-200"
            }`}
          >
            EMA 20
          </button>
          <button
            onClick={() => setShowEMA50(!showEMA50)}
            className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors border ${
              showEMA50
                ? "bg-amber-500/20 text-amber-300 border-amber-500/50"
                : "bg-slate-800/60 text-slate-400 border-slate-700 hover:text-slate-200"
            }`}
          >
            EMA 50
          </button>
          <button
            onClick={() => setShowBB(!showBB)}
            className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors border ${
              showBB
                ? "bg-purple-500/20 text-purple-300 border-purple-500/50"
                : "bg-slate-800/60 text-slate-400 border-slate-700 hover:text-slate-200"
            }`}
          >
            Bollinger (20,2)
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 800 ${height}`}
          className="w-full h-auto select-none"
          onMouseLeave={() => setHoverIdx(null)}
        >
          {/* Price Grid Lines */}
          {[0, 0.25, 0.5, 0.75, 1.0].map((ratio, i) => {
            const priceVal = minPrice + priceRange * (1.0 - ratio)
            const y = padding.top + ratio * priceHeight
            return (
              <g key={i}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={800 - padding.right}
                  y2={y}
                  stroke="#1E2634"
                  strokeDasharray="3 3"
                />
                <text
                  x={800 - padding.right + 8}
                  y={y + 4}
                  fill="#64748B"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  ₹{priceVal.toFixed(1)}
                </text>
              </g>
            )
          })}

          {/* Volume separator */}
          <line
            x1={padding.left}
            y1={volumeTop}
            x2={800 - padding.right}
            y2={volumeTop}
            stroke="#1E2634"
          />

          {/* Bollinger Bands Paths */}
          {showBB && bbUpperPath && (
            <path
              d={bbUpperPath}
              fill="none"
              stroke="#A855F7"
              strokeWidth="1.2"
              strokeDasharray="2 2"
              opacity="0.8"
            />
          )}
          {showBB && bbLowerPath && (
            <path
              d={bbLowerPath}
              fill="none"
              stroke="#A855F7"
              strokeWidth="1.2"
              strokeDasharray="2 2"
              opacity="0.8"
            />
          )}

          {/* EMA 50 Line */}
          {showEMA50 && ema50Path && (
            <path
              d={ema50Path}
              fill="none"
              stroke="#F59E0B"
              strokeWidth="1.6"
              opacity="0.9"
            />
          )}

          {/* EMA 20 Line */}
          {showEMA20 && ema20Path && (
            <path
              d={ema20Path}
              fill="none"
              stroke="#06B6D4"
              strokeWidth="1.6"
              opacity="0.9"
            />
          )}

          {/* Candlesticks and Volume Bars */}
          {displayCandles.map((c, i) => {
            const x = padding.left + i * spacing
            const isBullish = c.close >= c.open
            const candleColor = isBullish ? "#10B981" : "#EF4444"

            const openY = getY(c.open)
            const closeY = getY(c.close)
            const highY = getY(c.high)
            const lowY = getY(c.low)

            const bodyTop = Math.min(openY, closeY)
            const bodyHeight = Math.max(Math.abs(closeY - openY), 1.5)

            // Volume bar
            const vHeight = (c.volume / maxVolume) * volumeHeight
            const vY = volumeTop + volumeHeight - vHeight

            return (
              <g
                key={i}
                className="cursor-pointer"
                onMouseEnter={() => setHoverIdx(i)}
              >
                {/* Wick */}
                <line
                  x1={x}
                  y1={highY}
                  x2={x}
                  y2={lowY}
                  stroke={candleColor}
                  strokeWidth="1.2"
                />
                {/* Real body */}
                <rect
                  x={x - candleWidth / 2}
                  y={bodyTop}
                  width={candleWidth}
                  height={bodyHeight}
                  fill={candleColor}
                  rx="1"
                />
                {/* Volume Bar */}
                <rect
                  x={x - candleWidth / 2}
                  y={vY}
                  width={candleWidth}
                  height={Math.max(vHeight, 1)}
                  fill={isBullish ? "#064E3B" : "#7F1D1D"}
                  opacity="0.8"
                />
              </g>
            )
          })}

          {/* Active Hover Crosshair */}
          {hoverIdx !== null && (
            <line
              x1={padding.left + hoverIdx * spacing}
              y1={padding.top}
              x2={padding.left + hoverIdx * spacing}
              y2={height - padding.bottom}
              stroke="#60A5FA"
              strokeDasharray="2 2"
              strokeWidth="1"
            />
          )}
        </svg>
      </div>
    </div>
  )
}
