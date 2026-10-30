"""Initial schema for instruments, candles, news, predictions, and paper trading

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-28 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Instruments
    op.create_table(
        'instruments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('symbol', sa.String(32), nullable=False, unique=True, index=True),
        sa.Column('exchange', sa.String(16), nullable=False, server_default='NSE'),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('isin', sa.String(32), nullable=True),
        sa.Column('sector', sa.String(64), nullable=True),
        sa.Column('lot_size', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('tick_size', sa.Numeric(8, 4), nullable=False, server_default='0.05'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 2. Market Candles
    op.create_table(
        'market_candles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('instrument_id', sa.String(36), sa.ForeignKey('instruments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('interval', sa.String(16), nullable=False),
        sa.Column('open', sa.Numeric(14, 4), nullable=False),
        sa.Column('high', sa.Numeric(14, 4), nullable=False),
        sa.Column('low', sa.Numeric(14, 4), nullable=False),
        sa.Column('close', sa.Numeric(14, 4), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('source', sa.String(32), nullable=False, server_default='groww'),
        sa.Column('ingested_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('instrument_id', 'timestamp', 'interval', name='uq_candle_instrument_time_interval')
    )

    # 3. News Articles
    op.create_table(
        'news_articles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('url', sa.Text(), nullable=False, unique=True),
        sa.Column('headline', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('publisher', sa.String(128), nullable=False),
        sa.Column('source_type', sa.String(64), nullable=False, server_default='FINANCIAL_NEWS'),
        sa.Column('published_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('ingested_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='PROCESSED'),
    )

    # 4. News Company Associations
    op.create_table(
        'news_company_associations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('article_id', sa.String(36), sa.ForeignKey('news_articles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('instrument_id', sa.String(36), sa.ForeignKey('instruments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('relevance_score', sa.Numeric(5, 4), nullable=False, server_default='1.0'),
        sa.UniqueConstraint('article_id', 'instrument_id', name='uq_news_instrument')
    )

    # 5. News Sentiment Results
    op.create_table(
        'news_sentiment_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('article_id', sa.String(36), sa.ForeignKey('news_articles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sentiment_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('sentiment_label', sa.String(16), nullable=False),
        sa.Column('confidence', sa.Numeric(5, 4), nullable=False),
        sa.Column('event_category', sa.String(64), nullable=False),
        sa.Column('model_version', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 6. Model Registry
    op.create_table(
        'models_registry',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('model_version', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('algorithm', sa.String(64), nullable=False),
        sa.Column('features_schema_version', sa.String(32), nullable=False),
        sa.Column('training_start_date', sa.DateTime(), nullable=False),
        sa.Column('training_end_date', sa.DateTime(), nullable=False),
        sa.Column('artifact_path', sa.Text(), nullable=False),
        sa.Column('calibration_method', sa.String(32), nullable=False, server_default='ISOTONIC'),
        sa.Column('roc_auc', sa.Numeric(6, 4), nullable=True),
        sa.Column('brier_score', sa.Numeric(6, 4), nullable=True),
        sa.Column('log_loss', sa.Numeric(6, 4), nullable=True),
        sa.Column('is_active', sa.Numeric(1, 0), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 7. Predictions
    op.create_table(
        'predictions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('instrument_id', sa.String(36), sa.ForeignKey('instruments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('model_id', sa.String(36), sa.ForeignKey('models_registry.id'), nullable=True, index=True),
        sa.Column('as_of', sa.DateTime(), nullable=False, index=True),
        sa.Column('forecast_horizon', sa.String(32), nullable=False, server_default='5_trading_sessions'),
        sa.Column('probability_up', sa.Numeric(5, 4), nullable=True),
        sa.Column('probability_down', sa.Numeric(5, 4), nullable=True),
        sa.Column('expected_return', sa.Numeric(8, 4), nullable=True),
        sa.Column('signal', sa.String(16), nullable=False, index=True),
        sa.Column('risk_level', sa.String(16), nullable=False),
        sa.Column('supporting_factors', sa.JSON(), nullable=False),
        sa.Column('contradicting_factors', sa.JSON(), nullable=False),
        sa.Column('data_quality_status', sa.String(32), nullable=False, server_default='VERIFIED_FRESH'),
        sa.Column('news_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 8. Paper Portfolios
    op.create_table(
        'paper_portfolios',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(64), nullable=False, server_default='Default Virtual Portfolio'),
        sa.Column('initial_capital', sa.Numeric(14, 2), nullable=False, server_default='1000000.00'),
        sa.Column('cash_balance', sa.Numeric(14, 2), nullable=False, server_default='1000000.00'),
        sa.Column('total_equity', sa.Numeric(14, 2), nullable=False, server_default='1000000.00'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 9. Paper Orders
    op.create_table(
        'paper_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portfolio_id', sa.String(36), sa.ForeignKey('paper_portfolios.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('instrument_id', sa.String(36), sa.ForeignKey('instruments.id'), nullable=False, index=True),
        sa.Column('idempotency_key', sa.String(128), nullable=False, unique=True, index=True),
        sa.Column('side', sa.String(8), nullable=False),
        sa.Column('quantity', sa.Numeric(12, 4), nullable=False),
        sa.Column('order_type', sa.String(16), nullable=False, server_default='MARKET'),
        sa.Column('status', sa.String(16), nullable=False, server_default='PENDING'),
        sa.Column('executed_price', sa.Numeric(14, 4), nullable=True),
        sa.Column('transaction_fee', sa.Numeric(10, 4), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
    )

    # 10. Paper Positions
    op.create_table(
        'paper_positions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portfolio_id', sa.String(36), sa.ForeignKey('paper_portfolios.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('instrument_id', sa.String(36), sa.ForeignKey('instruments.id'), nullable=False, index=True),
        sa.Column('quantity', sa.Numeric(12, 4), nullable=False, server_default='0.0'),
        sa.Column('average_buy_price', sa.Numeric(14, 4), nullable=False, server_default='0.0'),
        sa.Column('current_price', sa.Numeric(14, 4), nullable=False, server_default='0.0'),
        sa.Column('unrealized_pnl', sa.Numeric(14, 4), nullable=False, server_default='0.0'),
        sa.Column('realized_pnl', sa.Numeric(14, 4), nullable=False, server_default='0.0'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('portfolio_id', 'instrument_id', name='uq_portfolio_instrument')
    )


def downgrade() -> None:
    op.drop_table('paper_positions')
    op.drop_table('paper_orders')
    op.drop_table('paper_portfolios')
    op.drop_table('predictions')
    op.drop_table('models_registry')
    op.drop_table('news_sentiment_results')
    op.drop_table('news_company_associations')
    op.drop_table('news_articles')
    op.drop_table('market_candles')
    op.drop_table('instruments')
