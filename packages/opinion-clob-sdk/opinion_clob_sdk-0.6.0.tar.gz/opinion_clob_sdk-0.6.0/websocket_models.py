"""
WebSocket message models for Opinion CLOB SDK

This module provides data models for WebSocket messages to improve type safety
and ease of use.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketDepthDiffMessage:
    """
    Market depth diff message received from WebSocket.
    
    This message is received when subscribing to 'market.depth.diff' channel.
    """
    market_id: int
    """Market ID"""
    
    token_id: str
    """Position ID of updated token"""
    
    outcome_side: int
    """1 - yes, 2 - no"""
    
    side: str
    """bids | asks"""
    
    price: str
    """Price"""
    
    size: str
    """Size in shares"""
    
    msg_type: str
    """Message type, e.g., 'market.depth.diff'"""
    
    root_market_id: Optional[int] = None
    """Root market ID if belongs to a categorical market"""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MarketDepthDiffMessage':
        """Create MarketDepthDiffMessage from dictionary."""
        return cls(
            market_id=int(data.get('marketId', 0)),
            token_id=str(data.get('tokenId', '')),
            outcome_side=int(data.get('outcomeSide', 0)),
            side=str(data.get('side', '')),
            price=str(data.get('price', '0')),
            size=str(data.get('size', '0')),
            msg_type=str(data.get('msgType', '')),
            root_market_id=int(data['rootMarketId']) if 'rootMarketId' in data else None
        )


@dataclass
class MarketLastPriceMessage:
    """
    Market last price message received from WebSocket.
    
    This message is received when subscribing to 'market.last.price' channel.
    """
    market_id: int
    """Market ID"""
    
    token_id: str
    """Position ID of traded token"""
    
    price: str
    """Price"""
    
    outcome_side: int
    """1 - yes, 2 - no"""
    
    msg_type: str
    """Message type, e.g., 'market.last.price'"""
    
    root_market_id: Optional[int] = None
    """Root market ID if belongs to a categorical market"""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MarketLastPriceMessage':
        """Create MarketLastPriceMessage from dictionary."""
        return cls(
            market_id=int(data.get('marketId', 0)),
            token_id=str(data.get('tokenId', '')),
            price=str(data.get('price', '0')),
            outcome_side=int(data.get('outcomeSide', 0)),
            msg_type=str(data.get('msgType', '')),
            root_market_id=int(data['rootMarketId']) if 'rootMarketId' in data else None
        )


@dataclass
class MarketLastTradeMessage:
    """
    Market last trade message received from WebSocket.
    
    This message is received when subscribing to 'market.last.trade' channel.
    """
    market_id: int
    """Market ID"""
    
    token_id: str
    """Position ID of traded token"""
    
    side: str
    """Buy | Sell | Split | Merge"""
    
    outcome_side: int
    """1 - yes, 2 - no"""
    
    price: str
    """Price"""
    
    shares: str
    """Shares"""
    
    amount: str
    """Amount"""
    
    msg_type: str
    """Message type, e.g., 'market.last.trade'"""
    
    root_market_id: Optional[int] = None
    """Root market ID if belongs to a categorical market"""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MarketLastTradeMessage':
        """Create MarketLastTradeMessage from dictionary."""
        return cls(
            market_id=int(data.get('marketId', 0)),
            token_id=str(data.get('tokenId', '')),
            side=str(data.get('side', '')),
            outcome_side=int(data.get('outcomeSide', 0)),
            price=str(data.get('price', '0')),
            shares=str(data.get('shares', '0')),
            amount=str(data.get('amount', '0')),
            msg_type=str(data.get('msgType', '')),
            root_market_id=int(data['rootMarketId']) if 'rootMarketId' in data else None
        )


@dataclass
class TradeOrderUpdateMessage:
    """
    Trade order update message received from WebSocket.
    
    This message is received when subscribing to 'trade.order.update' channel.
    """
    order_update_type: str
    """orderNew | orderFill | orderCancel | orderConfirm"""
    
    market_id: int
    """Market ID"""
    
    order_id: str
    """Order ID"""
    
    side: int
    """1 - buy, 2 - sell"""
    
    outcome_side: int
    """1 - yes, 2 - no"""
    
    price: str
    """Price"""

    shares: str
    """Shares"""
    
    amount: str
    """Amount"""
    
    status: int
    """1 - pending, 2 - finished, 3 - canceled, 4 - expired, 5 - failed"""
    
    trading_method: int
    """1 - market price, 2 - limit price"""
    
    quote_token: str
    """Contract address of quote token"""
    
    created_at: int
    """Create unix timestamp"""
    
    expires_at: int
    """Expire unix timestamp"""
    
    chain_id: str
    """Chain ID"""
    
    filled_shares: str
    """Filled in shares, update after orderConfirm"""
    
    filled_amount: str
    """Filled in amount, update after orderConfirm"""
    
    msg_type: str
    """Message type, e.g., 'trade.order.update'"""
    
    root_market_id: Optional[int] = None
    """Root market ID if belongs to a categorical market"""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TradeOrderUpdateMessage':
        """Create TradeOrderUpdateMessage from dictionary."""
        return cls(
            order_update_type=str(data.get('orderUpdateType', '')),
            market_id=int(data.get('marketId', 0)),
            order_id=str(data.get('orderId', '')),
            side=int(data.get('side', 0)),
            outcome_side=int(data.get('outcomeSide', 0)),
            price=str(data.get('price', '0')),
            shares=str(data.get('shares', '0')),
            amount=str(data.get('amount', '0')),
            status=int(data.get('status', 0)),
            trading_method=int(data.get('tradingMethod', 0)),
            quote_token=str(data.get('quoteToken', '')),
            created_at=int(data.get('createdAt', 0)),
            expires_at=int(data.get('expiresAt', 0)),
            chain_id=str(data.get('chainId', '')),
            filled_shares=str(data.get('filledShares', '0')),
            filled_amount=str(data.get('filledAmount', '0')),
            msg_type=str(data.get('msgType', '')),
            root_market_id=int(data['rootMarketId']) if 'rootMarketId' in data and data.get('rootMarketId', 0) != 0 else None
        )


@dataclass
class TradeRecordNewMessage:
    """
    Trade record new message received from WebSocket.
    
    This message is received when subscribing to 'trade.record.new' channel.
    """
    order_id: str
    """Order ID"""
    
    trade_no: str
    """Trade ID"""
    
    market_id: int
    """Market ID"""
    
    tx_hash: str
    """Transaction hash on-chain"""
    
    side: str
    """Buy | Sell | Split | Merge"""
    
    outcome_side: int
    """1 - yes, 2 - no"""
    
    price: str
    """Price"""
    
    shares: str
    """Shares"""
    
    amount: str
    """Amount"""
    
    profit: str
    """Profit, applicable for sell/merge"""
    
    status: int
    """2 - finished, 3 - canceled, 5 - failed, 6 - onchain failed"""
    
    quote_token: str
    """Contract address of quote token"""
    
    quote_token_usd_price: str
    """USD price of quote token at the moment"""
    
    usd_amount: str
    """Amount in USD value"""
    
    fee: str
    """Fee applied to this trade"""
    
    chain_id: str
    """Chain ID"""
    
    created_at: int
    """Create unix timestamp"""
    
    msg_type: str
    """Message type, e.g., 'trade.record.new'"""
    
    root_market_id: Optional[int] = None
    """Root market ID if belongs to a categorical market"""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TradeRecordNewMessage':
        """Create TradeRecordNewMessage from dictionary."""
        return cls(
            order_id=str(data.get('orderId', '')),
            trade_no=str(data.get('tradeNo', '')),
            market_id=int(data.get('marketId', 0)),
            tx_hash=str(data.get('txHash', '')),
            side=str(data.get('side', '')),
            outcome_side=int(data.get('outcomeSide', 0)),
            price=str(data.get('price', '0')),
            shares=str(data.get('shares', '0')),
            amount=str(data.get('amount', '0')),
            profit=str(data.get('profit', '0')),
            status=int(data.get('status', 0)),
            quote_token=str(data.get('quoteToken', '')),
            quote_token_usd_price=str(data.get('quoteTokenUsdPrice', '0')),
            usd_amount=str(data.get('usdAmount', '0')),
            fee=str(data.get('fee', '')),
            chain_id=str(data.get('chainId', '')),
            created_at=int(data.get('createdAt', 0)),
            msg_type=str(data.get('msgType', '')),
            root_market_id=int(data['rootMarketId']) if 'rootMarketId' in data and data.get('rootMarketId', 0) != 0 else None
        )

