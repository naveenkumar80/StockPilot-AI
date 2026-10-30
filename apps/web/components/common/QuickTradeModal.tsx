"use client"

import React, { useState, useEffect } from "react"
import { X, CheckCircle2, AlertCircle, Briefcase, ArrowUpRight, ArrowDownRight } from "lucide-react"
import { api } from "@/lib/api"
import { formatINR } from "@/lib/utils"

interface QuickTradeModalProps {
  isOpen: boolean
  onClose: () => void
  symbol: string
  currentPrice?: number
  onOrderSuccess?: () => void
}

export function QuickTradeModal({
  isOpen,
  onClose,
  symbol,
  currentPrice = 1000,
  onOrderSuccess,
}: QuickTradeModalProps) {
  const [side, setSide] = useState<"BUY" | "SELL">("BUY")
  const [quantity, setQuantity] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successResult, setSuccessResult] = useState<any | null>(null)

  useEffect(() => {
    if (isOpen) {
      setError(null)
      setSuccessResult(null)
    }
  }, [isOpen, symbol])

  if (!isOpen) return null

  const estValue = quantity * (currentPrice || 1000)
  // Standard Indian regulatory model
  const brokerage = Math.min(20, estValue * 0.0003)
  const stt = estValue * 0.001
  const gst = (brokerage + estValue * 0.0000345) * 0.18
  const totalFees = brokerage + stt + gst
  const netTotal = side === "BUY" ? estValue + totalFees : estValue - totalFees

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (quantity <= 0) {
      setError("Please specify a valid quantity greater than 0.")
      return
    }

    setLoading(true)
    setError(null)
    setSuccessResult(null)

    try {
      const idempotencyKey = `qt-${Date.now()}-${symbol}-${Math.random().toString(36).substring(7)}`
      const res = await api.placePaperOrder({
        idempotency_key: idempotencyKey,
        symbol: symbol.toUpperCase(),
        side: side,
        quantity: quantity,
        order_type: "MARKET",
      })

      setSuccessResult(res)
      if (onOrderSuccess) onOrderSuccess()
    } catch (err: any) {
      setError(err.message || "Failed to execute paper order.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm select-none animate-in fade-in duration-150">
      <div className="w-full max-w-md bg-[#0F1724] border border-[#233148] rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1A2638] bg-[#0A101A]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Briefcase className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-bold text-white flex items-center gap-2">
                Quick Paper Trade: <span className="text-emerald-400">{symbol.toUpperCase()}</span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                LTP: {formatINR(currentPrice)} • Zero Real Risk
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {successResult ? (
          /* Success Screen */
          <div className="p-6 text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Order Executed Successfully!</h3>
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Simulated {successResult.side} {successResult.quantity} shares of {symbol} at{" "}
                {formatINR(successResult.executed_price)}
              </p>
            </div>

            <div className="p-3 bg-[#0A101A] border border-[#1A2638] rounded-xl text-left font-mono text-xs space-y-1.5 text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-400">Order ID:</span>
                <span className="text-slate-200">{successResult.id?.slice(0, 12)}...</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Execution Status:</span>
                <span className="text-emerald-400 font-bold">{successResult.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">STT & Transaction Fees:</span>
                <span className="text-slate-200">{formatINR(successResult.transaction_fee || totalFees)}</span>
              </div>
            </div>

            <div className="flex gap-2.5 pt-2">
              <button
                onClick={() => setSuccessResult(null)}
                className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
              >
                Place Another
              </button>
              <button
                onClick={onClose}
                className="flex-1 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          /* Order Form */
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            {/* BUY / SELL Switch */}
            <div className="grid grid-cols-2 gap-2 p-1 bg-[#0A101A] rounded-xl border border-[#1A2638]">
              <button
                type="button"
                onClick={() => setSide("BUY")}
                className={`py-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                  side === "BUY"
                    ? "bg-emerald-600 text-white shadow-md"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <ArrowUpRight className="w-3.5 h-3.5" /> BUY
              </button>
              <button
                type="button"
                onClick={() => setSide("SELL")}
                className={`py-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                  side === "SELL"
                    ? "bg-rose-600 text-white shadow-md"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <ArrowDownRight className="w-3.5 h-3.5" /> SELL
              </button>
            </div>

            {/* Quantity */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono text-slate-400">
                <span>Number of Shares</span>
                <span>Value: {formatINR(estValue)}</span>
              </div>
              <input
                type="number"
                min="1"
                max="10000"
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full px-3 py-2 bg-[#0A101A] border border-[#1A2638] rounded-xl text-sm font-mono text-white focus:outline-none focus:border-emerald-500"
              />

              {/* Quick Qty Preset Buttons */}
              <div className="flex gap-2 pt-1 font-mono">
                {[5, 10, 25, 50, 100].map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => setQuantity(q)}
                    className={`flex-1 py-1 rounded-lg text-[11px] font-semibold border transition-colors ${
                      quantity === q
                        ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/50"
                        : "bg-[#0A101A] text-slate-400 border-[#1A2638] hover:text-white"
                    }`}
                  >
                    +{q}
                  </button>
                ))}
              </div>
            </div>

            {/* Fee & Net Accounting */}
            <div className="p-3 rounded-xl bg-[#0A101A] border border-[#1A2638] space-y-1.5 text-[11px] font-mono">
              <div className="flex justify-between text-slate-400">
                <span>Order Type</span>
                <span className="text-slate-200 font-semibold">MARKET (Guaranteed Fill)</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Brokerage + STT + GST</span>
                <span className="text-slate-200">{formatINR(totalFees)}</span>
              </div>
              <div className="border-t border-slate-800 pt-1.5 flex justify-between text-xs font-bold text-white">
                <span>Estimated Net Total</span>
                <span className={side === "BUY" ? "text-emerald-400" : "text-rose-400"}>
                  {formatINR(netTotal)}
                </span>
              </div>
            </div>

            {error && (
              <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2.5 rounded-xl text-xs font-bold transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50 ${
                side === "BUY"
                  ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                  : "bg-rose-600 hover:bg-rose-500 text-white"
              }`}
            >
              {loading ? (
                "Submitting to Simulated Exchange..."
              ) : (
                <>
                  <Briefcase className="w-3.5 h-3.5" />
                  Execute Simulated {side} Order
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

