"use client"

import React, { useState } from "react"
import { BrainCircuit, Search, Send, FileText, CheckCircle, AlertTriangle, ShieldCheck } from "lucide-react"
import { api } from "@/lib/api"

interface QueryQA {
  question: string
  answer: string
  facts: string[]
  sources: Array<{ title: string; publisher: string; date: string; url: string }>
  caveat: string
}

const SAMPLE_RESEARCH_PROMPTS = [
  "Why did TCS receive its current BUY signal?",
  "What important company news appeared recently for Reliance?",
  "Summarize Q3 earnings disclosures and growth outlook across Indian IT majors.",
  "What are the primary risk factors flagged for Tata Motors?",
]

export default function ResearchPage() {
  const [selectedPrompt, setSelectedPrompt] = useState("")
  const [activeQA, setActiveQA] = useState<QueryQA | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleQuery = async (queryText: string) => {
    if (!queryText.trim()) return
    setSelectedPrompt(queryText)
    setIsProcessing(true)

    try {
      const res = await api.askResearchAssistant(queryText)
      setActiveQA(res)
    } catch (err) {
      console.error("Research query error:", err)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-[#202736] pb-4">
        <div className="flex items-center gap-2 text-blue-400 mb-1">
          <BrainCircuit className="w-5 h-5" />
          <span className="text-xs font-mono uppercase tracking-wider font-semibold">Grounded AI Research</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Evidence-Based Research Assistant</h1>
        <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
          Ask questions regarding monitored Indian equities, corporate filings, and ML signal attribution. Every claim is
          rigorously grounded in verified stored database records and cited sources.
        </p>
      </div>

      {/* Query Bar */}
      <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-4 space-y-3">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Ask a question about stocks, earnings disclosures, or signal rationale..."
              value={selectedPrompt}
              onChange={(e) => setSelectedPrompt(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && selectedPrompt.trim() && handleQuery(selectedPrompt)}
              className="w-full bg-[#181E29] border border-[#252E3E] rounded-md pl-9 pr-4 py-2.5 text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            onClick={() => selectedPrompt.trim() && handleQuery(selectedPrompt)}
            disabled={isProcessing || !selectedPrompt.trim()}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-md text-xs font-mono font-bold flex items-center gap-1.5 transition-colors"
          >
            {isProcessing ? "Researching..." : "Analyze"} <Send className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Suggested Queries */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] font-mono text-slate-500">Suggested:</span>
          {SAMPLE_RESEARCH_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleQuery(p)}
              className="text-[11px] font-mono px-2.5 py-1 rounded bg-[#181E29] border border-[#252E3E] text-slate-300 hover:text-blue-300 hover:border-blue-500 transition-colors"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Answer Output View */}
      {activeQA ? (
        <div className="bg-[#12161F] border border-[#252E3E] rounded-lg p-6 space-y-6">
          <div className="border-b border-[#202736] pb-3">
            <div className="text-[10px] font-mono text-blue-400 uppercase tracking-wider">Research Query</div>
            <h2 className="text-base font-bold text-slate-100 mt-0.5">{activeQA.question}</h2>
          </div>

          {/* Sourced Interpretation */}
          <div className="space-y-2">
            <div className="text-xs font-mono font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-purple-400" />
              Grounded Quantitative Synthesis
            </div>
            <p className="text-sm text-slate-200 leading-relaxed bg-[#181E29] border border-[#252E3E] p-4 rounded-lg">
              {activeQA.answer}
            </p>
          </div>

          {/* Verified Facts List */}
          <div className="space-y-2">
            <div className="text-xs font-mono font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              Verified Empirical Facts (Database Record Grounding)
            </div>
            <div className="bg-[#181E29] border border-[#252E3E] rounded-lg p-4 space-y-2">
              {activeQA.facts.map((fact, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
                  <span className="text-emerald-400 font-bold font-mono">[{i + 1}]</span>
                  <span>{fact}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Sourced Citations */}
          <div className="space-y-2">
            <div className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-400" />
              Source Citations & Provenance
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {activeQA.sources.map((src, i) => (
                <div key={i} className="p-3 bg-[#181E29] border border-[#252E3E] rounded text-xs space-y-1">
                  <div className="font-semibold text-slate-200">{src.title}</div>
                  <div className="text-[11px] font-mono text-slate-400">
                    Publisher: {src.publisher} • Date: {src.date}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Safety & Risk Caveat */}
          <div className="p-3 bg-amber-950/20 border border-amber-800/40 rounded flex items-center gap-3 text-xs text-amber-300">
            <ShieldCheck className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{activeQA.caveat}</span>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center bg-[#12161F] border border-[#252E3E] rounded-lg space-y-2 text-slate-500 font-mono text-xs">
          <div>Select a research question above or input your own query.</div>
          <div>Answers are produced strictly from stored candles, sentiment results, and model weights.</div>
        </div>
      )}
    </div>
  )
}
