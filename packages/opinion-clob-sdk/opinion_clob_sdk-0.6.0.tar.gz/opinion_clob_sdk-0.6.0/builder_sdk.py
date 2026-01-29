"""
Builder SDK for Opinion CLOB

This module provides the BuilderClient class for builder mode operations:
- Creating and managing user sub-account API keys
- Building order structures for user signing
- Placing orders on behalf of users with their signatures
- Building and submitting Safe transactions for chain operations
"""

from typing import Dict, Any, Optional, List
import logging
import secrets
from time import time
from decimal import Decimal

from eth_typing import ChecksumAddress
from eth_account import Account
from eth_account.messages import encode_typed_data
from hexbytes import HexBytes
from web3 import Web3
from web3.providers import HTTPProvider

# Handle both old and new web3.py versions
try:
    from web3.middleware import ExtraDataToPOAMiddleware
    geth_poa_middleware = ExtraDataToPOAMiddleware
except ImportError:
    from web3.middleware import geth_poa_middleware

from opinion_api.api.prediction_market_api import PredictionMarketApi
from opinion_api.api_client import ApiClient
from opinion_api.configuration import Configuration
from opinion_clob_sdk.chain.safe.utils import fast_to_checksum_address, get_empty_tx_params
from opinion_clob_sdk.chain.safe.safe_tx_builder import SafeTxBuilder
from opinion_clob_sdk.chain.safe.safe_tx import SafeTx
from opinion_clob_sdk.chain.safe.multisend import MultiSendTx, MultiSendOperation
from opinion_clob_sdk.chain.safe.constants import NULL_ADDRESS, NULL_HASH
from opinion_clob_sdk.chain.py_order_utils.constants import ZERO_ADDRESS
from opinion_clob_sdk.chain.py_order_utils.model.sides import BUY, SELL, OrderSide
from opinion_clob_sdk.chain.py_order_utils.model.order_type import LIMIT_ORDER, MARKET_ORDER
from opinion_clob_sdk.chain.py_order_utils.model.order import Order as EIP712Order
from opinion_clob_sdk.chain.py_order_utils.utils import calculate_order_amounts, normalize_address, prepend_zx
from opinion_clob_sdk.config import DEFAULT_CONTRACT_ADDRESSES
from poly_eip712_structs import make_domain
from eth_utils import keccak


# Constants
CHAIN_ID_BNB_MAINNET = 56
SUPPORTED_CHAIN_IDS = [CHAIN_ID_BNB_MAINNET]
MAX_DECIMALS = 18
EOA_SIGNATURE_TYPE = 0
POLY_GNOSIS_SAFE_SIGNATURE_TYPE = 2  # For Safe wallets


class BuilderError(Exception):
    """Base exception for builder operations"""
    pass


class InvalidParamError(BuilderError):
    """Invalid parameter error"""
    pass


class ApiError(BuilderError):
    """API call error"""
    pass


def safe_amount_to_wei(amount: float, decimals: int) -> int:
    """
    Safely convert human-readable amount to wei units without precision loss.
    """
    if amount <= 0:
        raise InvalidParamError(f"Amount must be positive, got: {amount}")

    if decimals < 0 or decimals > MAX_DECIMALS:
        raise InvalidParamError(f"Decimals must be between 0 and {MAX_DECIMALS}, got: {decimals}")

    amount_decimal = Decimal(str(amount))
    multiplier = Decimal(10) ** decimals
    result = int(amount_decimal * multiplier)

    if result >= 2**256:
        raise InvalidParamError(f"Amount too large for uint256: {result}")

    if result <= 0:
        raise InvalidParamError(f"Calculated amount is zero or negative: {result}")

    return result


class BuilderClient:
    """
    Builder client for managing user API keys and placing orders on behalf of users.
    
    Builder mode allows:
    1. Creating sub-account API keys for users
    2. Building EIP-712 order structures for users to sign
    3. Submitting orders on behalf of users using their signatures
    
    Example:
        ```python
        client = BuilderClient(
            host="https://api.example.com",
            builder_apikey="your-builder-apikey",
            chain_id=56,
            rpc_url="https://bsc-dataseed.binance.org/"
        )
        
        # Create API key for user
        result = client.create_user("0x1234...")
        
        # Build order for user to sign
        order_data = client.build_order_for_signing(
            market_id=123,
            token_id="token_id",
            user_wallet_address="0x1234...",
            side=OrderSide.BUY,
            order_type=LIMIT_ORDER,
            amount=100.0,
            price="0.5"  # Required for LIMIT_ORDER, optional for MARKET_ORDER
        )
        
        # User signs the order (off-chain)
        signature = "0x..."  # User's signature
        
        # Place order for user
        result = client.place_order_for_user(
            order=order_data["order"],
            signature=signature,
            user_wallet_address="0x1234..."
        )
        ```
    """
    
    def __init__(
        self,
        host: str,
        builder_apikey: str,
        chain_id: int,
        rpc_url: str = '',
        use_beta: bool = False,
        contract_addresses: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize the Builder client.
        
        Args:
            host: API host URL
            builder_apikey: Builder API key (uses builder-apikey header)
            chain_id: Blockchain chain ID (56 for BNB Chain mainnet)
            rpc_url: RPC endpoint URL (optional, for chain queries)
            use_beta: If True, use beta/testnet contract addresses (default: False)
            contract_addresses: Optional dict to override specific contract addresses.
                               Keys: 'conditional_tokens', 'multisend', 'fee_manager', 'weth'
        """
        if chain_id not in SUPPORTED_CHAIN_IDS:
            raise InvalidParamError(f'chain_id must be one of {SUPPORTED_CHAIN_IDS}')
        
        self.chain_id = chain_id
        self.host = host
        self.builder_apikey = builder_apikey
        self.rpc_url = rpc_url
        self.use_beta = use_beta
        
        # Get base addresses from mainnet defaults
        base_addresses = DEFAULT_CONTRACT_ADDRESSES.get(chain_id, {}).copy()
        
        # For beta/testnet, contract_addresses must be provided
        if use_beta and not contract_addresses:
            raise InvalidParamError(
                "contract_addresses is required for beta/testnet environments. "
                "Please provide addresses for: conditional_tokens, multisend, fee_manager, weth"
            )
        
        # Apply custom overrides (required for beta, optional for mainnet)
        if contract_addresses:
            base_addresses.update(contract_addresses)
        
        self.contract_addresses = base_addresses
        
        # Setup API client with builder-apikey header
        self.conf = Configuration(host=host)
        # Use builder-apikey instead of standard apikey
        self.conf.api_key['BuilderApiKeyAuth'] = builder_apikey
        self.api_client = ApiClient(self.conf)
        self.market_api = PredictionMarketApi(self.api_client)
        
        # Cache for quote tokens and market data
        self._quote_tokens_cache: Optional[Any] = None
        self._quote_tokens_cache_time: float = 0
        self._market_cache: Dict[int, tuple] = {}
        self.quote_tokens_cache_ttl = 3600
        self.market_cache_ttl = 300
        
        # Get CTF Exchange address from contract addresses (may be empty, fetched dynamically)
        self.ctf_exchange_addr = self.contract_addresses.get("ctf_exchange", "")

    def _make_builder_request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict:
        """
        Make an API request with builder-apikey header.
        """
        import requests
        
        headers = {
            "builder-apikey": self.builder_apikey,
            "Content-Type": "application/json"
        }
        
        url = f"{self.host}{path}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise InvalidParamError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"API request failed: {e}")
            raise ApiError(f"API request failed: {e}")

    def _validate_response(self, response: Dict, operation: str) -> Any:
        """Validate API response"""
        if response.get("errno", 0) != 0:
            raise ApiError(f"Failed to {operation}: {response.get('errmsg', 'Unknown error')}")
        return response.get("result")

    def _parse_list_response(self, response: Any, operation_name: str = "operation") -> list:
        """Parse response that contains a list"""
        if hasattr(response, 'errno') and response.errno != 0:
            raise ApiError(f"Failed to {operation_name}: {response}")

        if not hasattr(response, 'result') or not hasattr(response.result, 'list'):
            raise ApiError(f"Invalid list response format for {operation_name}")

        return response.result.list

    def _validate_market_response(self, response: Any, operation_name: str = "operation") -> Any:
        """Validate and extract market data from API response"""
        if hasattr(response, 'errno') and response.errno != 0:
            raise ApiError(f"Failed to {operation_name}: {response}")

        if not hasattr(response, 'result') or not hasattr(response.result, 'data'):
            raise ApiError(f"Invalid response format for {operation_name}")

        return response.result.data

    # ============================================================================
    # User Management
    # ============================================================================
    
    def create_user(self, wallet_address: str) -> Dict[str, str]:
        """
        Create a user sub-account under this builder.
        
        This method:
        1. Registers the user in the system if not exists
        2. Initiates Gnosis Safe multi-sig wallet creation (platform pays gas)
        3. Generates an API key for the user
        
        IMPORTANT: The API key is returned ONLY ONCE during creation.
        Store it securely! If lost, use regenerate_user_apikey() to get a new one.
        
        Args:
            wallet_address: User's login wallet address (EOA, 0x...)
            
        Returns:
            Dictionary containing:
                - apikey: The generated API key (SAVE THIS - only returned once!)
                - wallet_address: User's login wallet address (EOA)
                - builder_name: Parent builder name
                - multi_sig_wallet: The multi-sig Safe wallet address (if already created)
                - wallet_creation_tx_hash: Transaction hash of wallet creation (if just initiated)
                - enable_trading: Whether user has enabled trading
                
        Example:
            ```python
            # Create user and SAVE the apikey
            result = builder.create_user("0x1234...")
            user_apikey = result["apikey"]  # SAVE THIS SECURELY!
            
            # Store apikey in your database or secure storage
            save_to_database(result["wallet_address"], user_apikey)
            ```
        """
        if not wallet_address or not wallet_address.startswith("0x"):
            raise InvalidParamError("Invalid wallet address format")
        
        wallet_address = wallet_address.lower()
        
        response = self._make_builder_request(
            "POST",
            f"/openapi/builder/user/{wallet_address}"
        )
        
        result = self._validate_response(response, "create user")
        
        apikey = result.get("apiKey", "")
        if apikey:
            logging.warning(
                "IMPORTANT: Store this API key securely! It will NOT be returned again. "
                "If lost, use regenerate_user_apikey() to generate a new one."
            )
        
        return {
            "apikey": apikey,
            "wallet_address": result.get("walletAddress", wallet_address),
            "builder_name": result.get("builderName", ""),
            "multi_sig_wallet": result.get("multiSigWallet", ""),
            "wallet_creation_tx_hash": result.get("walletCreationTxHash", ""),
            "enable_trading": result.get("enableTrading", False),
        }
    
    def get_user(self, wallet_address: str) -> Dict[str, str]:
        """
        Get user information for a builder's sub-account by login wallet address.
        
        NOTE: API key is NOT returned for security reasons.
        If you need the apikey, you should have saved it when create_user() was called.
        If lost, use regenerate_user_apikey() to generate a new one.
        
        Args:
            wallet_address: User's login wallet address (EOA, 0x...)
            
        Returns:
            Dictionary containing:
                - wallet_address: User's login wallet address (EOA)
                - builder_name: Parent builder name
                - multi_sig_wallet: The multi-sig Safe wallet address (if created)
                - enable_trading: Whether user has enabled trading
        """
        if not wallet_address or not wallet_address.startswith("0x"):
            raise InvalidParamError("Invalid wallet address format")
        
        wallet_address = wallet_address.lower()
        
        response = self._make_builder_request(
            "GET",
            f"/openapi/builder/user/{wallet_address}"
        )
        
        result = self._validate_response(response, "get user")
        return {
            "wallet_address": result.get("walletAddress", wallet_address),
            "builder_name": result.get("builderName", ""),
            "multi_sig_wallet": result.get("multiSigWallet", ""),
            "enable_trading": result.get("enableTrading", False),
        }
    
    def regenerate_user_apikey(self, wallet_address: str) -> Dict[str, str]:
        """
        Regenerate API key for a user. The old key is invalidated immediately.
        
        IMPORTANT: The new API key is returned ONLY ONCE. Store it securely!
        
        Args:
            wallet_address: User's login wallet address (EOA, 0x...)
            
        Returns:
            Dictionary containing:
                - apikey: The new API key (SAVE THIS - only returned once!)
                - wallet_address: User's login wallet address (EOA)
                - builder_name: Parent builder name
                - multi_sig_wallet: The multi-sig Safe wallet address (if created)
                - enable_trading: Whether user has enabled trading
                
        Example:
            ```python
            # Regenerate apikey if the old one was lost
            result = builder.regenerate_user_apikey("0x1234...")
            new_apikey = result["apikey"]  # SAVE THIS SECURELY!
            
            # Update your database with the new apikey
            update_database(result["wallet_address"], new_apikey)
            ```
        """
        if not wallet_address or not wallet_address.startswith("0x"):
            raise InvalidParamError("Invalid wallet address format")
        
        wallet_address = wallet_address.lower()
        
        response = self._make_builder_request(
            "POST",
            f"/openapi/builder/user/{wallet_address}/regenerate-apikey"
        )
        
        result = self._validate_response(response, "regenerate user apikey")
        
        apikey = result.get("apiKey", "")
        if apikey:
            logging.warning(
                "IMPORTANT: Store this new API key securely! It will NOT be returned again."
            )
        
        return {
            "apikey": apikey,
            "wallet_address": result.get("walletAddress", wallet_address),
            "builder_name": result.get("builderName", ""),
            "multi_sig_wallet": result.get("multiSigWallet", ""),
            "enable_trading": result.get("enableTrading", False),
        }

    # ============================================================================
    # Market Data (Read-only)
    # ============================================================================
    
    def get_quote_tokens(self, use_cache: bool = True) -> Any:
        """Get list of supported quote tokens"""
        current_time = time()

        if use_cache and self.quote_tokens_cache_ttl > 0:
            if self._quote_tokens_cache is not None:
                cache_age = current_time - self._quote_tokens_cache_time
                if cache_age < self.quote_tokens_cache_ttl:
                    return self._quote_tokens_cache

        # For builder, we use the same API but with builder-apikey
        result = self.market_api.openapi_quote_token_get(
            apikey=self.builder_apikey,
            chain_id=str(self.chain_id)
        )

        if self.quote_tokens_cache_ttl > 0:
            self._quote_tokens_cache = result
            self._quote_tokens_cache_time = current_time

        return result

    def get_market(self, market_id: int, use_cache: bool = True) -> Any:
        """Get detailed information about a specific market"""
        if not market_id or market_id <= 0:
            raise InvalidParamError("market_id must be a positive integer")

        current_time = time()

        if use_cache and self.market_cache_ttl > 0:
            if market_id in self._market_cache:
                cached_data, cache_time = self._market_cache[market_id]
                cache_age = current_time - cache_time
                if cache_age < self.market_cache_ttl:
                    return cached_data

        result = self.market_api.openapi_market_market_id_get(
            apikey=self.builder_apikey,
            market_id=market_id
        )

        if self.market_cache_ttl > 0:
            self._market_cache[market_id] = (result, current_time)

        return result

    def get_orderbook(self, token_id: str) -> Any:
        """Get orderbook for a specific token"""
        if not token_id:
            raise InvalidParamError("token_id is required")

        result = self.market_api.openapi_token_orderbook_get(
            apikey=self.builder_apikey,
            token_id=token_id
        )
        return result

    # ============================================================================
    # Order Building
    # ============================================================================
    
    def build_order_for_signing(
        self,
        market_id: int,
        token_id: str,
        user_wallet_address: str,
        side: OrderSide,
        order_type: int,
        amount: float,
        price: Optional[str] = None,
        amount_type: str = "quote",
        signer_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build an order structure for a user to sign.
        
        Args:
            market_id: Market ID
            token_id: Token ID to trade
            user_wallet_address: User's wallet address (maker - where funds are held)
                                For Safe wallets, this is the Safe address.
            side: Order side (BUY or SELL)
            order_type: Order type (LIMIT_ORDER=2 or MARKET_ORDER=1)
            amount: Amount in human-readable units
            price: Price per share (e.g., "0.5" for 50 cents). Required for LIMIT_ORDER.
                   For MARKET_ORDER with amount_type="quote", price is not required.
            amount_type: "quote" for quote token amount, "base" for base token amount
            signer_address: Optional signer address (for Safe wallets, this is the owner EOA).
                           If not provided, defaults to user_wallet_address.
            
        Returns:
            Dictionary containing:
                - order: The order structure to be signed
                - domain: EIP-712 domain
                - struct_hash: Hash of the order structure
                - typed_data: Complete EIP-712 typed data for signing
        """
        if not market_id or market_id <= 0:
            raise InvalidParamError("market_id must be a positive integer")
        if not token_id:
            raise InvalidParamError("token_id is required")
        if not user_wallet_address or not user_wallet_address.startswith("0x"):
            raise InvalidParamError("Invalid user_wallet_address format")
        
        # Validate price requirement for LIMIT_ORDER
        if order_type == LIMIT_ORDER and not price:
            raise InvalidParamError("price is required for LIMIT_ORDER")
        
        # Market order: price is ignored and set to "0" (same as original SDK)
        # Also validate amount_type restrictions for market orders
        if order_type == MARKET_ORDER:
            price = "0"
            # Market BUY: only quote amount allowed
            if side == OrderSide.BUY and amount_type == "base":
                raise InvalidParamError("amount_type='base' is not allowed for market BUY orders")
            # Market SELL: only base amount allowed
            if side == OrderSide.SELL and amount_type == "quote":
                raise InvalidParamError("amount_type='quote' is not allowed for market SELL orders")
        
        # maker is always the user_wallet_address (Safe address or EOA)
        maker_address = fast_to_checksum_address(user_wallet_address)
        
        # signer is either explicitly provided (Safe owner) or same as maker (EOA mode)
        if signer_address:
            if not signer_address.startswith("0x"):
                raise InvalidParamError("Invalid signer_address format")
            signer_addr = fast_to_checksum_address(signer_address)
        else:
            signer_addr = maker_address
        
        # For backward compatibility, keep user_wallet_address reference
        user_wallet_address = maker_address
        
        # Get market and quote token info
        market_response = self.get_market(market_id)
        market = self._validate_market_response(market_response, "get market for order building")
        
        if int(market.chain_id) != self.chain_id:
            raise ApiError('Cannot build order for different chain')
        
        quote_token_addr = market.quote_token
        
        # Get quote token details
        quote_token_list_response = self.get_quote_tokens()
        quote_token_list = self._parse_list_response(quote_token_list_response, "get quote tokens")
        
        quote_token = next(
            (item for item in quote_token_list 
             if str.lower(item.quote_token_address) == str.lower(quote_token_addr)),
            None
        )
        if not quote_token:
            raise ApiError('Quote token not found for this market')
        
        exchange_addr = fast_to_checksum_address(quote_token.ctf_exchange_address)
        currency_decimal = int(quote_token.decimal)
        
        # Calculate maker and taker amounts
        price_decimal = Decimal(str(price)) if price else Decimal("0")
        
        if order_type == MARKET_ORDER:
            # Market order: taker_amount is 0, maker_amount is direct conversion
            # (amount_type restrictions are validated above)
            taker_amount = 0
            maker_amount = safe_amount_to_wei(amount, currency_decimal)
        else:  # LIMIT_ORDER
            if amount_type == "quote":
                maker_amount_wei = safe_amount_to_wei(amount, currency_decimal)
            else:
                # Convert base to quote for buy, keep base for sell
                if side == OrderSide.BUY:
                    maker_amount_wei = safe_amount_to_wei(amount * float(price_decimal), currency_decimal)
                else:
                    maker_amount_wei = safe_amount_to_wei(amount, currency_decimal)
            
            maker_amount, taker_amount = calculate_order_amounts(
                price=float(price),  # price is guaranteed to exist for LIMIT_ORDER
                maker_amount=maker_amount_wei,
                side=side,
                decimals=currency_decimal
            )
        
        # Generate order fields
        salt = secrets.randbits(256)
        expiration = int(time()) + 86400 * 30  # 30 days from now
        nonce = 0
        fee_rate_bps = "0"
        
        # Determine signature type:
        # - If maker == signer: EOA mode (signatureType = 0)
        # - If maker != signer: Safe mode (signatureType = 2, POLY_GNOSIS_SAFE)
        is_safe_mode = maker_address.lower() != signer_addr.lower()
        signature_type = POLY_GNOSIS_SAFE_SIGNATURE_TYPE if is_safe_mode else EOA_SIGNATURE_TYPE
        
        # Build order structure
        # maker = where funds are (Safe address or EOA)
        # signer = who signs (Safe owner EOA or same as maker for EOA mode)
        order = {
            "salt": str(salt),
            "maker": maker_address,
            "signer": signer_addr,
            "taker": ZERO_ADDRESS,
            "tokenId": token_id,
            "makerAmount": str(maker_amount),
            "takerAmount": str(taker_amount),
            "expiration": str(expiration),
            "nonce": str(nonce),
            "feeRateBps": fee_rate_bps,
            "side": str(side.value),
            "signatureType": str(signature_type),
        }
        
        # Build EIP-712 domain
        # Must match backend: "OPINION CTF Exchange"
        domain = {
            "name": "OPINION CTF Exchange",
            "version": "1",
            "chainId": self.chain_id,
            "verifyingContract": exchange_addr
        }
        
        # Build EIP-712 types
        types = {
            "Order": [
                {"name": "salt", "type": "uint256"},
                {"name": "maker", "type": "address"},
                {"name": "signer", "type": "address"},
                {"name": "taker", "type": "address"},
                {"name": "tokenId", "type": "uint256"},
                {"name": "makerAmount", "type": "uint256"},
                {"name": "takerAmount", "type": "uint256"},
                {"name": "expiration", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "feeRateBps", "type": "uint256"},
                {"name": "side", "type": "uint8"},
                {"name": "signatureType", "type": "uint8"},
            ]
        }
        
        # Prepare message for signing
        message = {
            "salt": int(order["salt"]),
            "maker": order["maker"],
            "signer": order["signer"],
            "taker": order["taker"],
            "tokenId": int(order["tokenId"]),
            "makerAmount": int(order["makerAmount"]),
            "takerAmount": int(order["takerAmount"]),
            "expiration": int(order["expiration"]),
            "nonce": int(order["nonce"]),
            "feeRateBps": int(order["feeRateBps"]),
            "side": int(order["side"]),
            "signatureType": int(order["signatureType"]),
        }
        
        # Build EIP712 Order using poly_eip712_structs (same as original SDK)
        eip712_order = EIP712Order(
            salt=int(order["salt"]),
            maker=normalize_address(order["maker"]),
            signer=normalize_address(order["signer"]),
            taker=normalize_address(order["taker"]),
            tokenId=int(order["tokenId"]),
            makerAmount=int(order["makerAmount"]),
            takerAmount=int(order["takerAmount"]),
            expiration=int(order["expiration"]),
            nonce=int(order["nonce"]),
            feeRateBps=int(order["feeRateBps"]),
            side=int(order["side"]),
            signatureType=int(order["signatureType"]),
        )
        
        # Build domain separator using poly_eip712_structs (same as original SDK)
        domain_separator = make_domain(
            name="OPINION CTF Exchange",
            version="1",
            chainId=str(self.chain_id),
            verifyingContract=exchange_addr,
        )
        
        # Calculate struct hash using original SDK method
        struct_hash = prepend_zx(
            keccak(eip712_order.signable_bytes(domain=domain_separator)).hex()
        )
        
        # Also build typed_data for reference (optional, for debugging)
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                **types
            },
            "primaryType": "Order",
            "domain": domain,
            "message": message
        }
        
        return {
            "order": order,
            "domain": domain,
            "struct_hash": struct_hash,  # This is the hash to sign
            "typed_data": typed_data,
            "exchange_address": exchange_addr,
            "currency_address": quote_token_addr,
            "currency_decimal": currency_decimal,
            "market_id": market_id,
            "order_type": order_type,
            "price": price,
        }

    # ============================================================================
    # Order Placement
    # ============================================================================
    
    def place_order_for_user(
        self,
        order: Dict[str, Any],
        signature: str,
        user_wallet_address: str,
        market_id: Optional[int] = None,
        order_type: Optional[int] = None,
        price: Optional[str] = None,
        currency_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place an order on behalf of a user using their signature.
        
        Args:
            order: Order structure (from build_order_for_signing)
            signature: User's signature on the order (hex string starting with 0x)
            user_wallet_address: User's wallet address
            market_id: Market ID (can be inferred from order if build_order_for_signing was used)
            order_type: Order type (LIMIT_ORDER=2 or MARKET_ORDER=1)
            price: Price (for display purposes)
            currency_address: Quote token address
            
        Returns:
            API response with order details
        """
        if not signature or not signature.startswith("0x"):
            raise InvalidParamError("signature must be a hex string starting with 0x")
        
        if not user_wallet_address or not user_wallet_address.startswith("0x"):
            raise InvalidParamError("Invalid user_wallet_address format")
        
        user_wallet_address = user_wallet_address.lower()
        
        # Validate that order maker matches user_wallet_address
        if order.get("maker", "").lower() != user_wallet_address:
            raise InvalidParamError("Order maker must match user_wallet_address")
        
        # Validate signature type is EOA (0) or POLY_GNOSIS_SAFE (2)
        sig_type = order.get("signatureType", "1")
        if sig_type not in [str(EOA_SIGNATURE_TYPE), str(POLY_GNOSIS_SAFE_SIGNATURE_TYPE)]:
            raise InvalidParamError("signatureType must be 0 (EOA) or 2 (POLY_GNOSIS_SAFE) for builder orders")
        
        # Generate unique order sign (used by backend to prevent duplicates)
        # Use signature as the unique identifier since it's unique per order
        order_sign = signature[2:66] if len(signature) > 66 else signature[2:]  # First 32 bytes of signature
        
        # Build request payload
        # IMPORTANT: timestamp is required by backend for SignTime and SignExpireTime
        # Without timestamp, backend will use 0, causing order to expire immediately!
        request_data = {
            "order": {
                "salt": order.get("salt", ""),
                "maker": order.get("maker", ""),
                "signer": order.get("signer", ""),
                "taker": order.get("taker", ZERO_ADDRESS),
                "tokenId": order.get("tokenId", ""),
                "makerAmount": order.get("makerAmount", ""),
                "takerAmount": order.get("takerAmount", ""),
                "expiration": order.get("expiration", ""),
                "nonce": order.get("nonce", "0"),
                "feeRateBps": order.get("feeRateBps", "0"),
                "side": order.get("side", "0"),
                "signatureType": order.get("signatureType", "0"),  # Use actual value from order
                "topicId": market_id or 0,
                "price": price or "0",
                "tradingMethod": order_type or LIMIT_ORDER,
                "currencyAddress": currency_address or "",
                "sign": order_sign,  # Unique order identifier
                "timestamp": int(time()),  # Required! Backend uses this for SignTime/SignExpireTime
                "safeRate": "0",
                "orderExpTime": order.get("expiration", "0"),
            },
            "signature": signature,
            "maker": user_wallet_address,
        }
        
        response = self._make_builder_request(
            "POST",
            "/openapi/builder/order",
            request_data
        )
        
        return self._validate_response(response, "place order for user")

    def place_order_for_user_from_build_result(
        self,
        build_result: Dict[str, Any],
        signature: str,
        user_wallet_address: str,
    ) -> Dict[str, Any]:
        """
        Place an order using the result from build_order_for_signing.
        
        This is a convenience method that extracts all necessary fields
        from the build_order_for_signing result.
        
        Args:
            build_result: Result from build_order_for_signing
            signature: User's signature on the order
            user_wallet_address: User's wallet address
            
        Returns:
            API response with order details
        """
        return self.place_order_for_user(
            order=build_result["order"],
            signature=signature,
            user_wallet_address=user_wallet_address,
            market_id=build_result.get("market_id"),
            order_type=build_result.get("order_type"),
            price=build_result.get("price"),
            currency_address=build_result.get("currency_address"),
        )

    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    @staticmethod
    def sign_order_with_private_key(typed_data: Dict[str, Any], private_key: str) -> str:
        """
        Sign an order with a private key (for testing purposes).
        
        In production, the user should sign the order themselves using their wallet.
        
        Args:
            typed_data: EIP-712 typed data from build_order_for_signing
            private_key: Private key (hex string)
            
        Returns:
            Signature as hex string
        """
        try:
            signable_message = encode_typed_data(full_message=typed_data)
            signed = Account.sign_message(signable_message, private_key=private_key)
            return signed.signature.hex()
        except Exception as e:
            logging.error(f"Failed to sign order: {e}")
            raise BuilderError(f"Failed to sign order: {e}")

    # ============================================================================
    # Safe Transaction Operations
    # ============================================================================
    
    def _get_w3(self) -> Web3:
        """Get or create Web3 instance."""
        if not hasattr(self, '_w3') or self._w3 is None:
            if not self.rpc_url:
                raise InvalidParamError("rpc_url is required for Safe operations")
            w3 = Web3(HTTPProvider(self.rpc_url))
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self._w3 = w3
        return self._w3
    
    def _get_safe_tx_builder(self, safe_address: str) -> SafeTxBuilder:
        """Get a SafeTxBuilder instance for the given Safe address."""
        w3 = self._get_w3()
        multisend_addr = self.contract_addresses.get("multisend", "")
        return SafeTxBuilder(
            w3=w3,
            safe_address=Web3.to_checksum_address(safe_address),
            multisend_address=Web3.to_checksum_address(multisend_addr) if multisend_addr else None,
            chain_id=self.chain_id,
        )
    
    def _get_conditional_tokens_contract(self, w3: Web3):
        """Get the ConditionalTokens contract instance."""
        from opinion_clob_sdk.chain.contracts.conditional_tokens import abi
        addr = self.contract_addresses.get("conditional_tokens", "")
        if not addr:
            raise InvalidParamError(f"conditional_tokens address not found for chain {self.chain_id}")
        return w3.eth.contract(Web3.to_checksum_address(addr), abi=abi)
    
    def _get_erc20_contract(self, w3: Web3, token_address: str):
        """Get an ERC20 contract instance."""
        from opinion_clob_sdk.chain.contracts.erc20 import abi
        return w3.eth.contract(Web3.to_checksum_address(token_address), abi=abi)
    
    def build_enable_trading_tx(
        self,
        safe_address: str,
        quote_tokens: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Build an Enable Trading transaction for user to sign.
        
        This creates approval transactions for:
        1. ERC20 tokens to CTF Exchange
        2. ERC20 tokens to ConditionalTokens contract
        3. ConditionalTokens to CTF Exchange (setApprovalForAll)
        
        Args:
            safe_address: User's Safe wallet address
            quote_tokens: Dict of {token_address: ctf_exchange_address} 
                         If not provided, will fetch from API
                         
        Returns:
            Dictionary containing:
                - safe_tx: SafeTx object
                - eip712_data: EIP-712 data for user signing
                - safe_tx_hash: Hash of the Safe transaction
                - submission_data: Data formatted for backend submission (needs signature)
        """
        w3 = self._get_w3()
        builder = self._get_safe_tx_builder(safe_address)
        
        # Get quote tokens if not provided
        if quote_tokens is None:
            quote_token_response = self.get_quote_tokens()
            quote_token_list = self._parse_list_response(quote_token_response, "get quote tokens")
            quote_tokens = {
                item.quote_token_address: item.ctf_exchange_address 
                for item in quote_token_list
                if str(item.chain_id) == str(self.chain_id)
            }
        
        conditional_tokens_addr = self.contract_addresses.get("conditional_tokens", "")
        if not conditional_tokens_addr:
            raise InvalidParamError(f"conditional_tokens address not found for chain {self.chain_id}")
        
        multi_send_txs: List[MultiSendTx] = []
        max_approval = 2**256 - 1
        
        for erc20_address, ctf_exchange_address in quote_tokens.items():
            erc20_contract = self._get_erc20_contract(w3, erc20_address)
            
            # Approve CTF Exchange
            data = HexBytes(
                erc20_contract.functions.approve(
                    Web3.to_checksum_address(ctf_exchange_address), max_approval
                ).build_transaction(get_empty_tx_params())["data"]
            )
            multi_send_txs.append(MultiSendTx(
                operation=MultiSendOperation.CALL.value,
                to=Web3.to_checksum_address(erc20_address),
                value=0,
                data=data,
            ))
            
            # Approve ConditionalTokens
            data = HexBytes(
                erc20_contract.functions.approve(
                    Web3.to_checksum_address(conditional_tokens_addr), max_approval
                ).build_transaction(get_empty_tx_params())["data"]
            )
            multi_send_txs.append(MultiSendTx(
                operation=MultiSendOperation.CALL.value,
                to=Web3.to_checksum_address(erc20_address),
                value=0,
                data=data,
            ))
            
            # setApprovalForAll for ConditionalTokens to CTF Exchange
            ct_contract = self._get_conditional_tokens_contract(w3)
            data = HexBytes(
                ct_contract.functions.setApprovalForAll(
                    Web3.to_checksum_address(ctf_exchange_address), True
                ).build_transaction(get_empty_tx_params())["data"]
            )
            multi_send_txs.append(MultiSendTx(
                operation=MultiSendOperation.CALL.value,
                to=Web3.to_checksum_address(conditional_tokens_addr),
                value=0,
                data=data,
            ))
        
        if not multi_send_txs:
            raise InvalidParamError("No transactions to build for enable trading")
        
        # Build SafeTx
        # safeTxGas is internal gas for Safe execution, not the external tx gas limit
        # 300000 is enough for ~3 approve calls, relayer will set external gas limit
        safe_tx = builder.build_multisend_tx(multi_send_txs, safe_tx_gas=300000)
        
        return self._build_safe_tx_result(builder, safe_tx)
    
    def build_withdraw_tx(
        self,
        safe_address: str,
        token_address: str,
        amount: int,
        to_address: str,
    ) -> Dict[str, Any]:
        """
        Build a Withdraw (ERC20 transfer) transaction for user to sign.
        
        Args:
            safe_address: User's Safe wallet address
            token_address: ERC20 token address to withdraw
            amount: Amount to withdraw (in wei)
            to_address: Recipient address
            
        Returns:
            Dictionary containing safe_tx, eip712_data, safe_tx_hash, submission_data
        """
        w3 = self._get_w3()
        builder = self._get_safe_tx_builder(safe_address)
        
        erc20_contract = self._get_erc20_contract(w3, token_address)
        data = erc20_contract.functions.transfer(
            Web3.to_checksum_address(to_address), amount
        ).build_transaction(get_empty_tx_params())["data"]
        
        safe_tx = builder.build_safe_tx(
            to=Web3.to_checksum_address(token_address),
            value=0,
            data=HexBytes(data),
            operation=0,
            safe_tx_gas=100000,
        )
        
        return self._build_safe_tx_result(builder, safe_tx)
    
    def build_split_tx(
        self,
        safe_address: str,
        collateral_token: str,
        condition_id: str,
        amount: int,
        partition: List[int] = None,
    ) -> Dict[str, Any]:
        """
        Build a Split Position transaction for user to sign.
        
        Args:
            safe_address: User's Safe wallet address
            collateral_token: Collateral token address
            condition_id: Condition ID (bytes32 as hex string)
            amount: Amount to split (in wei)
            partition: Partition array (default: [1, 2] for binary outcomes)
            
        Returns:
            Dictionary containing safe_tx, eip712_data, safe_tx_hash, submission_data
        """
        if partition is None:
            partition = [1, 2]
        
        w3 = self._get_w3()
        builder = self._get_safe_tx_builder(safe_address)
        
        ct_contract = self._get_conditional_tokens_contract(w3)
        
        # Convert condition_id to bytes32
        condition_id_bytes = bytes.fromhex(condition_id.replace('0x', ''))
        
        data = ct_contract.functions.splitPosition(
            Web3.to_checksum_address(collateral_token),
            bytes(32),  # parentCollectionId = 0
            condition_id_bytes,
            partition,
            amount
        ).build_transaction(get_empty_tx_params())["data"]
        
        conditional_tokens_addr = self.contract_addresses.get("conditional_tokens", "")
        
        safe_tx = builder.build_safe_tx(
            to=Web3.to_checksum_address(conditional_tokens_addr),
            value=0,
            data=HexBytes(data),
            operation=0,
            safe_tx_gas=300000,
        )
        
        return self._build_safe_tx_result(builder, safe_tx)
    
    def build_merge_tx(
        self,
        safe_address: str,
        collateral_token: str,
        condition_id: str,
        amount: int,
        partition: List[int] = None,
    ) -> Dict[str, Any]:
        """
        Build a Merge Position transaction for user to sign.
        
        Args:
            safe_address: User's Safe wallet address
            collateral_token: Collateral token address
            condition_id: Condition ID (bytes32 as hex string)
            amount: Amount to merge (in wei)
            partition: Partition array (default: [1, 2] for binary outcomes)
            
        Returns:
            Dictionary containing safe_tx, eip712_data, safe_tx_hash, submission_data
        """
        if partition is None:
            partition = [1, 2]
        
        w3 = self._get_w3()
        builder = self._get_safe_tx_builder(safe_address)
        
        ct_contract = self._get_conditional_tokens_contract(w3)
        
        # Convert condition_id to bytes32
        condition_id_bytes = bytes.fromhex(condition_id.replace('0x', ''))
        
        data = ct_contract.functions.mergePositions(
            Web3.to_checksum_address(collateral_token),
            bytes(32),  # parentCollectionId = 0
            condition_id_bytes,
            partition,
            amount
        ).build_transaction(get_empty_tx_params())["data"]
        
        conditional_tokens_addr = self.contract_addresses.get("conditional_tokens", "")
        
        safe_tx = builder.build_safe_tx(
            to=Web3.to_checksum_address(conditional_tokens_addr),
            value=0,
            data=HexBytes(data),
            operation=0,
            safe_tx_gas=300000,
        )
        
        return self._build_safe_tx_result(builder, safe_tx)
    
    def build_redeem_tx(
        self,
        safe_address: str,
        collateral_token: str,
        condition_id: str,
        partition: List[int] = None,
    ) -> Dict[str, Any]:
        """
        Build a Redeem Position transaction for user to sign.
        
        Args:
            safe_address: User's Safe wallet address
            collateral_token: Collateral token address
            condition_id: Condition ID (bytes32 as hex string)
            partition: Partition array (default: [1, 2] for binary outcomes)
            
        Returns:
            Dictionary containing safe_tx, eip712_data, safe_tx_hash, submission_data
        """
        if partition is None:
            partition = [1, 2]
        
        w3 = self._get_w3()
        builder = self._get_safe_tx_builder(safe_address)
        
        ct_contract = self._get_conditional_tokens_contract(w3)
        
        # Convert condition_id to bytes32
        condition_id_bytes = bytes.fromhex(condition_id.replace('0x', ''))
        
        data = ct_contract.functions.redeemPositions(
            Web3.to_checksum_address(collateral_token),
            bytes(32),  # parentCollectionId = 0
            condition_id_bytes,
            partition
        ).build_transaction(get_empty_tx_params())["data"]
        
        conditional_tokens_addr = self.contract_addresses.get("conditional_tokens", "")
        
        safe_tx = builder.build_safe_tx(
            to=Web3.to_checksum_address(conditional_tokens_addr),
            value=0,
            data=HexBytes(data),
            operation=0,
            safe_tx_gas=300000,
        )
        
        return self._build_safe_tx_result(builder, safe_tx)
    
    def _build_safe_tx_result(self, builder: SafeTxBuilder, safe_tx: SafeTx) -> Dict[str, Any]:
        """Build the result dictionary for a Safe transaction."""
        eip712_data = builder.get_eip712_structured_data(safe_tx)
        safe_tx_hash = builder.get_safe_tx_hash(safe_tx)
        
        return {
            "safe_tx": safe_tx,
            "eip712_data": eip712_data,
            "safe_tx_hash": safe_tx_hash.hex(),
            "submission_data_template": builder.to_submission_data(safe_tx, ""),  # Signature placeholder
        }
    
    def submit_safe_tx(
        self,
        wallet_address: str,
        safe_tx_result: Dict[str, Any],
        signature: str,
    ) -> Dict[str, Any]:
        """
        Submit a signed Safe transaction to the backend.
        
        Args:
            wallet_address: User's wallet address (Safe owner)
            safe_tx_result: Result from build_*_tx methods
            signature: User's signature on the Safe transaction (hex string)
            
        Returns:
            API response containing safeTxHash
        """
        if not wallet_address or not wallet_address.startswith("0x"):
            raise InvalidParamError("Invalid wallet_address format")
        
        if not signature:
            raise InvalidParamError("signature is required")
        
        wallet_address = wallet_address.lower()
        
        # Get submission data and add signature
        safe_tx = safe_tx_result.get("safe_tx")
        if safe_tx is None:
            raise InvalidParamError("safe_tx_result must contain safe_tx")
        
        builder = self._get_safe_tx_builder(wallet_address)  # Address doesn't matter here
        submission_data = builder.to_submission_data(safe_tx, signature)
        
        response = self._make_builder_request(
            "POST",
            f"/openapi/builder/safe/{wallet_address}/tx",
            submission_data
        )
        
        return self._validate_response(response, "submit safe transaction")
    
    @staticmethod
    def sign_safe_tx_with_private_key(eip712_data: Dict[str, Any], private_key: str) -> str:
        """
        Sign a Safe transaction with a private key (for testing purposes).
        
        In production, the user should sign the transaction themselves using their wallet.
        
        Args:
            eip712_data: EIP-712 data from build_*_tx methods
            private_key: Private key (hex string)
            
        Returns:
            Signature as hex string
        """
        try:
            signable_message = encode_typed_data(full_message=eip712_data)
            signed = Account.sign_message(signable_message, private_key=private_key)
            return signed.signature.hex()
        except Exception as e:
            logging.error(f"Failed to sign Safe transaction: {e}")
            raise BuilderError(f"Failed to sign Safe transaction: {e}")

    # ============================================================================
    # Order Cancellation (using user's apikey)
    # ============================================================================
    
    def _get_user_api(self, user_apikey: str) -> PredictionMarketApi:
        """
        Get a PredictionMarketApi instance configured with user's apikey.
        
        Args:
            user_apikey: User's API key (obtained via get_user)
            
        Returns:
            PredictionMarketApi instance for user operations
        """
        user_conf = Configuration(host=self.host)
        user_conf.api_key['ApiKeyAuth'] = user_apikey
        user_client = ApiClient(user_conf)
        return PredictionMarketApi(user_client)
    
    def cancel_order_for_user(self, user_apikey: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order for a user using their API key.
        
        Args:
            user_apikey: User's API key (obtained via get_user or create_user)
            order_id: Order ID to cancel
            
        Returns:
            API response with cancellation result
            
        Example:
            ```python
            # Get user's apikey
            user_info = builder.get_user("0x1234...")
            user_apikey = user_info["apikey"]
            
            # Cancel an order
            result = builder.cancel_order_for_user(user_apikey, "order123")
            ```
        """
        if not user_apikey:
            raise InvalidParamError("user_apikey is required")
        if not order_id or not isinstance(order_id, str):
            raise InvalidParamError("order_id must be a non-empty string")
        
        from opinion_api.models.openapi_cancel_order_request_open_api import OpenapiCancelOrderRequestOpenAPI
        
        user_api = self._get_user_api(user_apikey)
        request_body = OpenapiCancelOrderRequestOpenAPI(orderId=order_id)
        result = user_api.openapi_order_cancel_post(apikey=user_apikey, cancel_order_req=request_body)
        
        return {"result": True}
    
    def cancel_orders_batch_for_user(self, user_apikey: str, order_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Cancel multiple orders for a user in batch.
        
        Args:
            user_apikey: User's API key
            order_ids: List of order IDs to cancel
            
        Returns:
            List of results, each containing:
                - index: Position in the input list
                - success: Whether the cancellation succeeded
                - result: API response (if success)
                - error: Error message (if failed)
                - order_id: The order ID
                
        Example:
            ```python
            user_info = builder.get_user("0x1234...")
            results = builder.cancel_orders_batch_for_user(
                user_info["apikey"], 
                ["order1", "order2", "order3"]
            )
            for r in results:
                if r["success"]:
                    print(f"Cancelled: {r['order_id']}")
                else:
                    print(f"Failed: {r['order_id']}, Error: {r['error']}")
            ```
        """
        if not user_apikey:
            raise InvalidParamError("user_apikey is required")
        if not order_ids or not isinstance(order_ids, list):
            raise InvalidParamError("order_ids must be a non-empty list")
        if len(order_ids) == 0:
            raise InvalidParamError("order_ids list cannot be empty")
        
        results = []
        errors = []
        
        for i, order_id in enumerate(order_ids):
            try:
                result = self.cancel_order_for_user(user_apikey, order_id)
                results.append({
                    "index": i,
                    "success": True,
                    "result": result,
                    "order_id": order_id
                })
            except Exception as e:
                logging.error(f"Failed to cancel order {order_id}: {e}")
                errors.append({
                    "index": i,
                    "success": False,
                    "error": str(e),
                    "order_id": order_id
                })
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e),
                    "order_id": order_id
                })
        
        if errors:
            logging.warning(f"Batch order cancellation completed with {len(errors)} errors out of {len(order_ids)} orders")
        
        return results
    
    def get_user_orders(
        self, 
        user_apikey: str, 
        market_id: int = 0, 
        status: str = "", 
        limit: int = 10, 
        page: int = 1
    ) -> Any:
        """
        Get orders for a user using their API key.
        
        Args:
            user_apikey: User's API key
            market_id: Optional market ID filter (0 for all markets)
            status: Optional status filter. 
                    Values: "1"=pending, "2"=filled, "3"=canceled, "4"=expired, "5"=failed
                    Can be comma-separated (e.g., "1,2,3")
            limit: Number of orders per page (max 20)
            page: Page number
            
        Returns:
            API response containing order list
        """
        if not user_apikey:
            raise InvalidParamError("user_apikey is required")
        
        user_api = self._get_user_api(user_apikey)
        result = user_api.openapi_order_get(
            apikey=user_apikey,
            market_id=market_id if market_id > 0 else None,
            status=status if status else None,
            limit=min(limit, 20),
            page=page,
            chain_id=str(self.chain_id)
        )
        return result
    
    def cancel_all_orders_for_user(
        self, 
        user_apikey: str, 
        market_id: Optional[int] = None,
        side: Optional[OrderSide] = None,
    ) -> Dict[str, Any]:
        """
        Cancel all open orders for a user.
        
        Args:
            user_apikey: User's API key
            market_id: Optional - only cancel orders for this market
            side: Optional - only cancel BUY or SELL orders
            
        Returns:
            Dictionary with cancellation summary:
                - total_orders: Total number of open orders found
                - cancelled: Number successfully cancelled
                - failed: Number that failed to cancel
                - results: List of individual results
                
        Example:
            ```python
            user_info = builder.get_user("0x1234...")
            
            # Cancel all orders
            result = builder.cancel_all_orders_for_user(user_info["apikey"])
            print(f"Cancelled {result['cancelled']} of {result['total_orders']} orders")
            
            # Cancel only BUY orders in a specific market
            from opinion_clob_sdk.chain.py_order_utils.model.sides import OrderSide
            result = builder.cancel_all_orders_for_user(
                user_info["apikey"],
                market_id=123,
                side=OrderSide.BUY
            )
            ```
        """
        if not user_apikey:
            raise InvalidParamError("user_apikey is required")
        
        # Collect all open orders using pagination
        all_orders = []
        current_page = 1
        limit = 20  # Max page size
        max_pages = 100  # Safety limit
        
        while current_page <= max_pages:
            orders_response = self.get_user_orders(
                user_apikey,
                market_id=market_id if market_id else 0,
                status="1",  # 1 = pending/open orders
                limit=limit,
                page=current_page
            )
            
            # Parse response - handle API response object
            if hasattr(orders_response, 'result') and hasattr(orders_response.result, 'list'):
                order_list = orders_response.result.list or []
            elif hasattr(orders_response, 'list'):
                order_list = orders_response.list or []
            elif isinstance(orders_response, dict):
                order_list = orders_response.get("result", {}).get("list", []) or orders_response.get("list", [])
            else:
                order_list = []
            
            if not order_list or len(order_list) == 0:
                break
            
            all_orders.extend(order_list)
            
            if len(order_list) < limit:
                break
            
            current_page += 1
        
        if current_page > max_pages:
            logging.warning(f"Reached maximum page limit ({max_pages}), there may be more orders")
        
        if not all_orders:
            logging.info("No open orders to cancel")
            return {
                "total_orders": 0,
                "cancelled": 0,
                "failed": 0,
                "results": []
            }
        
        # Filter by side if specified
        if side is not None:
            side_value = str(side.value)
            filtered_orders = []
            for order in all_orders:
                order_side = str(getattr(order, "side", "") if hasattr(order, "side") else order.get("side", ""))
                if order_side == side_value:
                    filtered_orders.append(order)
            all_orders = filtered_orders
        
        # Extract order IDs
        order_ids = []
        for order in all_orders:
            if hasattr(order, "order_id"):
                order_id = order.order_id
            elif hasattr(order, "orderId"):
                order_id = order.orderId
            elif isinstance(order, dict):
                order_id = order.get("orderId") or order.get("order_id")
            else:
                order_id = None
            if order_id:
                order_ids.append(str(order_id))
        
        if not order_ids:
            logging.info("No orders match the filter criteria")
            return {
                "total_orders": 0,
                "cancelled": 0,
                "failed": 0,
                "results": []
            }
        
        logging.info(f"Found {len(order_ids)} orders to cancel")
        
        # Cancel all orders
        results = self.cancel_orders_batch_for_user(user_apikey, order_ids)
        
        # Count successes and failures
        cancelled = sum(1 for r in results if r.get("success"))
        failed = sum(1 for r in results if not r.get("success"))
        
        logging.info(f"Cancelled {cancelled} orders, {failed} failed out of {len(order_ids)} total")
        
        return {
            "total_orders": len(order_ids),
            "cancelled": cancelled,
            "failed": failed,
            "results": results
        }

