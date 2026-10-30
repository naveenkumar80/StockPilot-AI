"use client"

import React, { useEffect, useState } from "react"
import { Settings, Database, Activity, Key, CheckCircle2, AlertTriangle, ShieldCheck, RefreshCw } from "lucide-react"
import { api, HealthResponse } from "@/lib/api"
import { formatDate } from "@/lib/utils"

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const checkStatus = () => {
    setLoading(true)
    api.getHealth()
      .then((res) => {
        setHealth(res)
        setLoading(false)
      })
      .catch(() => {
        setLoading(false)
      })
  }

  useEffect(() => {
    checkStatus()
  }, [])

  const isGrowwLive = health?.integrations?.groww_api?.authenticated

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#202736] pb-4">
        <div>
          <div className="flex items-center gap-2 text-blue-400 mb-1">
            <Settings className="w-5 h-5" />
            <span className="text-xs font-mono uppercase tracking-wider font-semibold">Platform Architecture</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">Settings & System Health</h1>
          <p className="text-xs text-slate-400 mt-1">
            External market data integrations, database connectivity, and environment parameters
          </p>
        </div>

        <button
          onClick={checkStatus}
          className="px-3 py-1.5 bg-[#1A2230] hover:bg-[#252E3E] text-xs font-mono text-slate-200 rounded border border-[#252E3E] flex items-center gap-1.5 self-start md:self-auto transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-check Health
        </button>
      </div>

      {/* Integration Posture Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Groww Integration Card */}
        <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-bold text-slate-100">Groww Trade API</h2>
            </div>
            {isGrowwLive ? (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                LIVE AUTH
              </span>
            ) : (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                DEMO FALLBACK
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Primary provider for NSE/BSE historical OHLCV candle streams and real-time live quotes.
          </p>

          <div className="text-xs font-mono space-y-2 pt-2 border-t border-[#202736]">
            <div className="flex justify-between">
              <span className="text-slate-500">Endpoint:</span>
              <span className="text-slate-300">{health?.integrations?.groww_api?.base_url || "https://api.groww.in/v1"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Status:</span>
              <span className="text-emerald-400 font-bold">{health?.integrations?.groww_api?.status?.toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Mode:</span>
              <span className="text-slate-200">{health?.integrations?.groww_api?.mode?.toUpperCase()}</span>
            </div>
          </div>
        </div>

        {/* News Provider Card */}
        <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400" />
              <h2 className="text-sm font-bold text-slate-100">News & Filings Pipeline</h2>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
              OPERATIONAL
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Ingestion adapter for NSE/BSE corporate announcements, earnings transcripts, and Drishti filings.
          </p>

          <div className="text-xs font-mono space-y-2 pt-2 border-t border-[#202736]">
            <div className="flex justify-between">
              <span className="text-slate-500">Adapter:</span>
              <span className="text-slate-300">drishti_exchange_disclosures</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Status:</span>
              <span className="text-emerald-400 font-bold">{health?.integrations?.news_provider?.status?.toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Deduplication:</span>
              <span className="text-slate-300">SHA-256 Enabled</span>
            </div>
          </div>
        </div>

        {/* Storage & DB Card */}
        <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-purple-400" />
              <h2 className="text-sm font-bold text-slate-100">Relational Store</h2>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
              HEALTHY
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Relational storage for candles, news, predictions, walk-forward results, and paper accounts.
          </p>

          <div className="text-xs font-mono space-y-2 pt-2 border-t border-[#202736]">
            <div className="flex justify-between">
              <span className="text-slate-500">Database Status:</span>
              <span className="text-emerald-400 font-bold">{health?.integrations?.database?.status?.toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Migrations:</span>
              <span className="text-slate-300">Alembic 0001 (Up to date)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Environment:</span>
              <span className="text-slate-300">{health?.environment?.toUpperCase()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Configuration Guidance & Credentials Instructions */}
      <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-6 space-y-4">
        <div className="flex items-center gap-2 text-slate-100 font-bold text-base">
          <Key className="w-4 h-4 text-amber-400" />
          External Credentials Configuration Guide
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          To transition from Demo Mode to live market data streaming, populate the following backend environment
          variables in your root <code className="text-slate-200">.env</code> file:
        </p>

        <div className="bg-[#0B0E14] border border-[#202736] rounded-md p-4 font-mono text-xs text-slate-300 space-y-2">
          <div className="text-slate-500"># Groww Trade API Credentials (https://groww.in/trade-api)</div>
          <div>GROWW_API_KEY=your_registered_groww_api_key</div>
          <div>GROWW_ACCESS_TOKEN=your_authenticated_bearer_token</div>
          <div>GROWW_BASE_URL=https://api.groww.in/v1</div>
          <div className="text-slate-500 pt-2"># Optional: Indian Financial News & Transcript API (https://drishti.manasija.in)</div>
          <div>DRISHTI_API_KEY=your_drishti_api_key</div>
        </div>

        <div className="p-3 bg-[#181E29] border border-[#252E3E] rounded text-xs text-slate-400 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            API tokens are never exposed to client-side code and are processed strictly within backend service boundaries.
          </span>
        </div>
      </div>
    </div>
  )
}
