from fastapi import APIRouter
from app.api.v1.endpoints import health, market, stocks, predictions, models, paper, backtests, news, research

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["System Health"])
api_router.include_router(market.router, prefix="/market", tags=["Market Overview"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stock Universe & Details"])
api_router.include_router(news.router, prefix="/news", tags=["Financial News & Sentiment"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions Engine"])
api_router.include_router(models.router, prefix="/models", tags=["Model Registry & Evaluation"])
api_router.include_router(paper.router, prefix="/paper", tags=["Paper Trading Simulator"])
api_router.include_router(backtests.router, prefix="/backtests", tags=["Backtesting Engine"])
api_router.include_router(research.router, prefix="/research", tags=["AI Research Assistant"])
