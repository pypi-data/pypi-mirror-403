"""
Vero Algo SDK for Python

A Python SDK for the Vero Algo trading platform with authentication,
order management, streaming, market data, and algorithmic trading capabilities.
"""

from .client import VeroClient
from .config import VeroConfig
from .features.orders import OrderService
from .features.market_data import MarketDataService
from .features.streaming import VeroStream
from .utils.defaults import (
    DEFAULT_BACKEND_SERVER,
    DEFAULT_AUTH_SERVER,
    DEFAULT_MICRO_API_SERVER,
    DEFAULT_STREAMING_WS,
)
from .utils.logging_config import setup_logging, get_logger
from .types import (
    OrderSide,
    OrderType,
    OrderStatus,
    NewOrderRequest,
    CancelOrderRequest,
    ModifyOrderRequest,
    OrderData,
    OrderResponse,
    Trade,
    Candle,
    ProductMaster,
    ProductInfo,
    ProductStat,
    Depth,
    PriceLevel,
    AlgoStatus,
)

# Strategy framework
from .strategy import Strategy, RunMode, TradingContext, Position, PositionSide, Symbol, Bars

# Risk management
from .risk import RiskManager, RiskSettings

# Backtesting
from .backtest import BacktestEngine, BacktestResult, PerformanceReport, BacktestSettings, DatePreset, Timeframe

from .core import Vero

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"
__all__ = [
    # Core
    "VeroClient",
    "VeroConfig",
    "OrderService",
    "MarketDataService",
    "VeroStream",
    # Types
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "NewOrderRequest",
    "CancelOrderRequest",
    "ModifyOrderRequest",
    "OrderData",
    "OrderResponse",
    "Trade",
    "Candle",
    "ProductMaster",
    "ProductInfo",
    "ProductStat",
    "Depth",
    "PriceLevel",
    "AlgoStatus",
    # Strategy
    "Strategy",
    "RunMode",
    "TradingContext",
    "Position",
    "PositionSide",
    "Symbol",
    "Bars",
    # Risk
    "RiskManager",
    "RiskSettings",
    # Backtest
    "BacktestEngine",
    "BacktestResult",
    "PerformanceReport",
    "BacktestSettings",
    "DatePreset",
    "Timeframe",
    "Vero",
    # Logging
    "setup_logging",
    "get_logger",
]
