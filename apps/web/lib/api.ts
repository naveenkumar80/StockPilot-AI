const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1"

export interface HealthResponse {
  status: string
  version: string
  timestamp: string
  environment: string
  integrations: {
    database: { status: string }
    groww_api: { status: string; authenticated: boolean; mode: string; base_url?: string }
    news_provider: { status: string; provider: string }
    model_engine: { status: string; active_version: string }
  }
}

export interface MarketOverview {
  as_of: string
  market_status: string
  monitored_stocks_count: number
  data_source_mode: string
  last_successful_market_update: string
  latest_model_training: string
  active_signals_summary: {
    BUY: number
    HOLD: number
    SELL: number
    NO_TRADE: number
  }
  paper_portfolio_snapshot: {
    total_value: number
    cash_balance: number
    unrealized_pnl: number
    unrealized_pnl_pct: number
  }
  recent_predictions: Array<{
    symbol: string
    signal: "BUY" | "HOLD" | "SELL" | "NO_TRADE"
    probability_up: number | null
    expected_return: number | null
    horizon: string
    as_of: string
  }>
  upcoming_events: Array<{ symbol: string; event: string; date: string }>
  data_quality_warnings: string[]
}

export interface StockItem {
  id: string
  symbol: string
  exchange: string
  company_name: string
  isin?: string
  sector?: string
  last_price: number
  change_24h: number
  volume_24h: number
  signal: "BUY" | "HOLD" | "SELL" | "NO_TRADE"
  probability_up: number | null
  expected_return: number | null
  volatility_20d: number | null
  momentum_5d: number | null
  news_sentiment_score: number | null
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "EXTREME"
  as_of?: string
}

export interface ScreenerResponse {
  items: StockItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface Candle {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface CandlesResponse {
  symbol: string
  exchange: string
  interval: string
  source: string
  is_demo: boolean
  candles: Candle[]
}

export interface PredictionDetail {
  symbol: string
  exchange: string
  as_of: string
  forecast_horizon: string
  model_version: string
  probability_up: number | null
  probability_down: number | null
  expected_return: number | null
  expected_return_interval: [number, number] | null
  signal: "BUY" | "HOLD" | "SELL" | "NO_TRADE"
  risk_level: string
  supporting_factors: string[]
  contradicting_factors: string[]
  data_quality_status: string
  news_summary?: string
  limitations: string[]
  is_demo: boolean
}

export interface ModelCandidate {
  model_version: string
  algorithm: string
  tag: string
  description: string
  composite_score: number
  roc_auc: number
  brier_score: number
  log_loss: number
  precision_buy: number
  recall_buy: number
  walk_forward_sharpe: number
  status: "CHAMPION" | "CHALLENGER"
  margin_vs_champion?: number
  promoted_at?: string
}

export interface ModelLeaderboard {
  last_updated: string
  tournament_duration_ms: number
  total_samples: number
  champion_version: string
  champion: ModelCandidate
  challengers: ModelCandidate[]
  feature_importances: Array<{ feature: string; importance: number }>
  selection_criteria: string
}

export interface NewsItem {
  id: string
  headline: string
  summary?: string
  publisher: string
  source_type: string
  url: string
  published_at: string
  sentiment_score?: number
  sentiment_label?: string
  event_category?: string
  confidence?: number
}

export interface PaperPortfolio {
  id: string
  name: string
  initial_capital: number
  cash_balance: number
  total_equity: number
  unrealized_pnl: number
  unrealized_pnl_pct: number
  positions: Array<{
    symbol: string
    company_name: string
    quantity: number
    average_buy_price: number
    current_price: number
    unrealized_pnl: number
    unrealized_pnl_pct: number
    market_value: number
  }>
  recent_orders: Array<{
    id: string
    idempotency_key: string
    symbol: string
    side: "BUY" | "SELL"
    quantity: number
    order_type: string
    status: string
    executed_price?: number
    transaction_fee: number
    created_at: string
  }>
  updated_at: string
}

export interface GrowwStatus {
  is_configured: boolean
  base_url: string
  timeout_seconds: number
  data_mode: "live" | "demo"
  auth_header_present: boolean
}

export interface LiveQuote {
  symbol: string
  exchange: string
  last_price: number
  day_change: number
  day_change_perc: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  last_trade_time?: string
  is_live: boolean
  source: string
}

export interface SyncResult {
  symbol: string
  interval: string
  candles_fetched: number
  candles_ingested: number
  candles_updated: number
  candles_dropped: number
  is_demo: boolean
  source: string
  sync_duration_ms: number
  warnings: string[]
}


async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorText = await res.text()
    try {
      const parsed = JSON.parse(errorText)
      throw new Error(parsed.detail || parsed.message || `API Error: ${res.status}`)
    } catch (e: any) {
      throw new Error(e.message || `API Error: ${res.status}`)
    }
  }
  return res.json()
}

export const api = {
  getHealth: async (): Promise<HealthResponse> => {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" })
    return handleResponse<HealthResponse>(res)
  },

  getMarketOverview: async (): Promise<MarketOverview> => {
    const res = await fetch(`${API_BASE_URL}/market/overview`, { cache: "no-store" })
    return handleResponse<MarketOverview>(res)
  },

  getStocks: async (params?: {
    query?: string
    signal?: string
    sort_by?: string
    sort_order?: string
    page?: number
    page_size?: number
  }): Promise<ScreenerResponse> => {
    const searchParams = new URLSearchParams()
    if (params?.query) searchParams.set("query", params.query)
    if (params?.signal) searchParams.set("signal", params.signal)
    if (params?.sort_by) searchParams.set("sort_by", params.sort_by)
    if (params?.sort_order) searchParams.set("sort_order", params.sort_order)
    if (params?.page) searchParams.set("page", params.page.toString())
    if (params?.page_size) searchParams.set("page_size", params.page_size.toString())

    const url = `${API_BASE_URL}/stocks${searchParams.toString() ? `?${searchParams}` : ""}`
    const res = await fetch(url, { cache: "no-store" })
    return handleResponse<ScreenerResponse>(res)
  },

  getStockDetail: async (symbol: string): Promise<StockItem> => {
    const res = await fetch(`${API_BASE_URL}/stocks/${symbol.toUpperCase()}`, { cache: "no-store" })
    return handleResponse<StockItem>(res)
  },

  getStockCandles: async (symbol: string, interval = "1d"): Promise<CandlesResponse> => {
    const res = await fetch(`${API_BASE_URL}/stocks/${symbol.toUpperCase()}/candles?interval=${interval}`, {
      cache: "no-store",
    })
    return handleResponse<CandlesResponse>(res)
  },

  getStockPrediction: async (symbol: string): Promise<PredictionDetail> => {
    const res = await fetch(`${API_BASE_URL}/stocks/${symbol.toUpperCase()}/prediction`, { cache: "no-store" })
    return handleResponse<PredictionDetail>(res)
  },

  refreshPrediction: async (symbol: string): Promise<PredictionDetail> => {
    const res = await fetch(`${API_BASE_URL}/predictions/${symbol.toUpperCase()}/refresh`, {
      method: "POST",
      cache: "no-store",
    })
    return handleResponse<PredictionDetail>(res)
  },

  listPredictions: async (signal?: string, limit: number = 20): Promise<PredictionDetail[]> => {
    const params = new URLSearchParams()
    if (signal) params.append("signal", signal)
    params.append("limit", limit.toString())
    const res = await fetch(`${API_BASE_URL}/predictions?${params.toString()}`, { cache: "no-store" })
    return handleResponse<PredictionDetail[]>(res)
  },

  batchRefreshPredictions: async (): Promise<PredictionDetail[]> => {
    const res = await fetch(`${API_BASE_URL}/predictions/batch-refresh`, {
      method: "POST",
      cache: "no-store",
    })
    return handleResponse<PredictionDetail[]>(res)
  },

  getModelMetrics: async (): Promise<any> => {
    const res = await fetch(`${API_BASE_URL}/models/metrics`, { cache: "no-store" })
    return handleResponse(res)
  },

  getModelLeaderboard: async (): Promise<ModelLeaderboard> => {
    const res = await fetch(`${API_BASE_URL}/models/leaderboard`, { cache: "no-store" })
    return handleResponse<ModelLeaderboard>(res)
  },

  runModelCompetition: async (lookbackDays: number = 180, nSplits: number = 3): Promise<any> => {
    const res = await fetch(
      `${API_BASE_URL}/models/competition/run?lookback_days=${lookbackDays}&n_splits=${nSplits}`,
      { method: "POST" }
    )
    return handleResponse(res)
  },

  promoteModel: async (modelVersion: string): Promise<any> => {
    const res = await fetch(`${API_BASE_URL}/models/promote/${encodeURIComponent(modelVersion)}`, {
      method: "POST",
    })
    return handleResponse(res)
  },

  getPaperPortfolio: async (): Promise<PaperPortfolio> => {
    const res = await fetch(`${API_BASE_URL}/paper/portfolio`, { cache: "no-store" })
    return handleResponse<PaperPortfolio>(res)
  },

  placePaperOrder: async (order: {
    idempotency_key: string
    symbol: string
    side: "BUY" | "SELL"
    quantity: number
    order_type?: string
  }): Promise<any> => {
    const res = await fetch(`${API_BASE_URL}/paper/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(order),
    })
    return handleResponse(res)
  },

  resetPaperPortfolio: async (): Promise<PaperPortfolio> => {
    const res = await fetch(`${API_BASE_URL}/paper/reset`, {
      method: "POST",
      cache: "no-store",
    })
    return handleResponse<PaperPortfolio>(res)
  },

  runBacktest: async (payload: {
    symbol: string
    start_date?: string
    end_date?: string
    initial_capital?: number
    strategy_params?: Record<string, any>
  }): Promise<any> => {
    const res = await fetch(`${API_BASE_URL}/backtests`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },

  getBacktestPresets: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE_URL}/backtests/presets`, { cache: "no-store" })
    return handleResponse<any[]>(res)
  },

  askResearchAssistant: async (query: string): Promise<{
    question: string
    answer: string
    facts: string[]
    sources: Array<{ title: string; publisher: string; date: string; url: string }>
    caveat: string
  }> => {
    const res = await fetch(`${API_BASE_URL}/research/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    })
    return handleResponse(res)
  },

  getGrowwStatus: async (): Promise<GrowwStatus> => {
    const res = await fetch(`${API_BASE_URL}/market/groww/status`, { cache: "no-store" })
    return handleResponse<GrowwStatus>(res)
  },

  getLiveQuote: async (symbol: string): Promise<LiveQuote> => {
    const res = await fetch(`${API_BASE_URL}/market/live-quote/${symbol.toUpperCase()}`, { cache: "no-store" })
    return handleResponse<LiveQuote>(res)
  },

  getLiveQuotes: async (symbols?: string[]): Promise<Record<string, LiveQuote>> => {
    const query = symbols && symbols.length > 0 ? `?symbols=${symbols.join(",")}` : ""
    const res = await fetch(`${API_BASE_URL}/market/live-quotes${query}`, { cache: "no-store" })
    return handleResponse<Record<string, LiveQuote>>(res)
  },

  syncStock: async (symbol: string, lookbackDays = 90): Promise<SyncResult> => {
    const res = await fetch(`${API_BASE_URL}/market/sync/${symbol.toUpperCase()}?lookback_days=${lookbackDays}`, {
      method: "POST",
    })
    return handleResponse<SyncResult>(res)
  },


  syncAllStocks: async (lookbackDays = 90): Promise<SyncResult[]> => {
    const res = await fetch(`${API_BASE_URL}/market/sync-all?lookback_days=${lookbackDays}`, {
      method: "POST",
    })
    return handleResponse<SyncResult[]>(res)
  },

  getLatestNews: async (params?: {
    symbol?: string
    sentiment?: string
    category?: string
    page?: number
    pageSize?: number
  }): Promise<{ articles: NewsItem[]; total: number; page: number; pageSize: number }> => {
    const query = new URLSearchParams()
    if (params?.symbol) query.set("symbol", params.symbol)
    if (params?.sentiment) query.set("sentiment", params.sentiment)
    if (params?.category) query.set("category", params.category)
    if (params?.page) query.set("page", params.page.toString())
    if (params?.pageSize) query.set("page_size", params.pageSize.toString())
    const qs = query.toString() ? `?${query.toString()}` : ""
    const res = await fetch(`${API_BASE_URL}/news/latest${qs}`, { cache: "no-store" })
    return handleResponse(res)
  },

  getStockNews: async (
    symbol: string,
    limit = 25
  ): Promise<{
    symbol: string
    summary: {
      overall_sentiment: string
      average_score: number
      positive_count: number
      neutral_count: number
      negative_count: number
      total_articles: number
    }
    articles: NewsItem[]
  }> => {
    const res = await fetch(`${API_BASE_URL}/news/stock/${symbol.toUpperCase()}?limit=${limit}`, { cache: "no-store" })
    return handleResponse(res)
  },

  getNewsStats: async (): Promise<any> => {
    const res = await fetch(`${API_BASE_URL}/news/stats`, { cache: "no-store" })
    return handleResponse(res)
  },

  triggerNewsIngest: async (limit = 25): Promise<any> => {
    const res = await fetch(`${API_BASE_URL}/news/ingest?limit=${limit}`, { method: "POST" })
    return handleResponse(res)
  },
}

