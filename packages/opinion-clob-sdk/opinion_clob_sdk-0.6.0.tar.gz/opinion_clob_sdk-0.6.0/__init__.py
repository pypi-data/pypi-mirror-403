"""Opinion CLOB SDK - Python SDK for Opinion Prediction Market CLOB API"""

from opinion_clob_sdk.sdk import (
    Client,
    CHAIN_ID_BNB_MAINNET,
    SUPPORTED_CHAIN_IDS
)
from opinion_clob_sdk.builder_sdk import (
    BuilderClient,
    BuilderError,
    InvalidParamError as BuilderInvalidParamError,
    ApiError as BuilderApiError
)
from opinion_clob_sdk.user_client import UserClient
from opinion_clob_sdk.model import TopicStatus, TopicType, TopicStatusFilter, CollectionType
from opinion_clob_sdk.chain.exception import (
    BalanceNotEnough,
    NoPositionsToRedeem,
    InsufficientGasBalance
)
from opinion_clob_sdk.websocket_client import WebSocketClient
from opinion_clob_sdk.websocket_models import (
    MarketDepthDiffMessage,
    MarketLastPriceMessage,
    MarketLastTradeMessage,
    TradeOrderUpdateMessage,
    TradeRecordNewMessage
)

__version__ = "0.6.0"
__all__ = [
    "Client",
    "BuilderClient",
    "UserClient",
    "WebSocketClient",
    "MarketDepthDiffMessage",
    "MarketLastPriceMessage",
    "MarketLastTradeMessage",
    "TradeOrderUpdateMessage",
    "TradeRecordNewMessage",
    "TopicStatus",
    "TopicType",
    "TopicStatusFilter",
    "CollectionType",
    "CHAIN_ID_BNB_MAINNET",
    "SUPPORTED_CHAIN_IDS",
    "BalanceNotEnough",
    "NoPositionsToRedeem",
    "InsufficientGasBalance",
    "BuilderError",
    "BuilderInvalidParamError",
    "BuilderApiError"
]
