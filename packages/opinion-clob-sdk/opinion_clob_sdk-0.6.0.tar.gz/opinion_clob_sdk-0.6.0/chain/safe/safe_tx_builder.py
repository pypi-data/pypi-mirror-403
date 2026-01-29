"""
SafeTxBuilder - Builder pattern for creating unsigned Gnosis Safe transactions.

This module provides utilities for building Safe transaction data that can be
signed by users and submitted by builders.
"""

from typing import Dict, Any, Optional, List
from hexbytes import HexBytes
from web3 import Web3
from eth_typing import ChecksumAddress

from .safe_tx import SafeTx
from .safe_contracts.utils import get_safe_contract
from .multisend import MultiSendTx, MultiSendOperation
from .constants import NULL_ADDRESS


class SafeTxBuilder:
    """
    Builder for creating unsigned Gnosis Safe transactions.
    
    This class provides methods to build transaction data that can be
    signed by users (via EIP-712) and submitted by builders.
    """
    
    def __init__(
        self,
        w3: Web3,
        safe_address: ChecksumAddress,
        multisend_address: Optional[ChecksumAddress] = None,
        chain_id: Optional[int] = None,
    ):
        """
        Initialize SafeTxBuilder.
        
        Args:
            w3: Web3 instance
            safe_address: Address of the Gnosis Safe wallet
            multisend_address: Address of the MultiSend contract (optional)
            chain_id: Chain ID (optional, will be fetched from w3 if not provided)
        """
        self.w3 = w3
        self.safe_address = Web3.to_checksum_address(safe_address)
        self.multisend_address = Web3.to_checksum_address(multisend_address) if multisend_address else None
        self._chain_id = chain_id
        self._safe_contract = None
        self._safe_nonce = None
        self._safe_version = None
    
    @property
    def safe_contract(self):
        """Get the Safe contract instance."""
        if self._safe_contract is None:
            self._safe_contract = get_safe_contract(self.w3, address=self.safe_address)
        return self._safe_contract
    
    @property
    def chain_id(self) -> int:
        """Get the chain ID."""
        if self._chain_id is None:
            self._chain_id = self.w3.eth.chain_id
        return self._chain_id
    
    def get_safe_nonce(self) -> int:
        """Get the current nonce of the Safe wallet from chain."""
        return self.safe_contract.functions.nonce().call()
    
    def get_safe_version(self) -> str:
        """Get the version of the Safe contract."""
        if self._safe_version is None:
            self._safe_version = self.safe_contract.functions.VERSION().call()
        return self._safe_version
    
    def build_safe_tx(
        self,
        to: ChecksumAddress,
        value: int = 0,
        data: bytes = b"",
        operation: int = 0,
        safe_tx_gas: int = 0,
        base_gas: int = 0,
        gas_price: int = 0,
        gas_token: Optional[ChecksumAddress] = None,
        refund_receiver: Optional[ChecksumAddress] = None,
        safe_nonce: Optional[int] = None,
    ) -> SafeTx:
        """
        Build a SafeTx object for signing.
        
        Args:
            to: Target address for the transaction
            value: ETH value to send (in wei)
            data: Transaction data
            operation: Operation type (0 = Call, 1 = DelegateCall)
            safe_tx_gas: Gas for the Safe internal transaction
            base_gas: Base gas cost
            gas_price: Gas price for refund calculation
            gas_token: Token for gas refund (None for ETH)
            refund_receiver: Address to receive gas refund
            safe_nonce: Nonce for the transaction (fetched from chain if not provided)
            
        Returns:
            SafeTx object ready for signing
        """
        if safe_nonce is None:
            safe_nonce = self.get_safe_nonce()
        
        return SafeTx(
            w3=self.w3,
            safe_address=self.safe_address,
            to=Web3.to_checksum_address(to) if to else None,
            value=value,
            data=data,
            operation=operation,
            safe_tx_gas=safe_tx_gas,
            base_gas=base_gas,
            gas_price=gas_price,
            gas_token=Web3.to_checksum_address(gas_token) if gas_token else None,
            refund_receiver=Web3.to_checksum_address(refund_receiver) if refund_receiver else None,
            safe_nonce=safe_nonce,
            safe_version=self.get_safe_version(),
            chain_id=self.chain_id,
        )
    
    def build_multisend_tx(
        self,
        transactions: List[MultiSendTx],
        safe_tx_gas: int = 0,
        safe_nonce: Optional[int] = None,
    ) -> SafeTx:
        """
        Build a SafeTx for multiple transactions via MultiSend.
        
        Args:
            transactions: List of MultiSendTx objects
            safe_tx_gas: Gas for the Safe internal transaction
            safe_nonce: Nonce for the transaction (fetched from chain if not provided)
            
        Returns:
            SafeTx object ready for signing
        """
        if not self.multisend_address:
            raise ValueError("MultiSend address is required for multisend transactions")
        
        # Encode multisend data
        multisend_data = self._encode_multisend_data(transactions)
        
        return self.build_safe_tx(
            to=self.multisend_address,
            value=0,
            data=multisend_data,
            operation=1,  # DelegateCall for MultiSend
            safe_tx_gas=safe_tx_gas,
            safe_nonce=safe_nonce,
        )
    
    def _encode_multisend_data(self, transactions: List[MultiSendTx]) -> bytes:
        """Encode transactions for MultiSend contract."""
        from .multisend import MultiSend
        multisend = MultiSend(self.w3, self.multisend_address)
        return multisend.build_tx_data(transactions)
    
    def get_eip712_structured_data(self, safe_tx: SafeTx) -> Dict[str, Any]:
        """
        Get the EIP-712 structured data for user signing.
        
        This data should be passed to the user's wallet for signing.
        
        Args:
            safe_tx: The SafeTx object
            
        Returns:
            EIP-712 structured data dictionary
        """
        return safe_tx.eip712_structured_data
    
    def get_safe_tx_hash(self, safe_tx: SafeTx) -> HexBytes:
        """
        Get the hash of the Safe transaction.
        
        Args:
            safe_tx: The SafeTx object
            
        Returns:
            The Safe transaction hash
        """
        return safe_tx.safe_tx_hash
    
    def to_submission_data(self, safe_tx: SafeTx, signature: str) -> Dict[str, Any]:
        """
        Convert SafeTx to submission data format for backend API.
        
        Args:
            safe_tx: The SafeTx object
            signature: User's signature (hex string, with or without 0x prefix)
            
        Returns:
            Dictionary formatted for backend submission
        """
        # Remove 0x prefix if present
        sig = signature[2:] if signature.startswith('0x') else signature
        
        return {
            "toAddress": safe_tx.to,
            "value": str(safe_tx.value),
            "data": safe_tx.data.hex() if safe_tx.data else "",
            "operation": safe_tx.operation,
            "safeTxGas": str(safe_tx.safe_tx_gas),
            "baseGas": str(safe_tx.base_gas),
            "gasPrice": str(safe_tx.gas_price),
            "gasToken": safe_tx.gas_token if safe_tx.gas_token != NULL_ADDRESS else "",
            "refundReceiver": safe_tx.refund_receiver if safe_tx.refund_receiver != NULL_ADDRESS else "",
            "nonce": str(safe_tx.safe_nonce),
            "signatures": sig,
        }

