"""
UserClient - Simulates a real user's wallet client

Used for testing Builder mode. UserClient holds the user's private key and can sign orders.
In production, signing is done by the user's wallet (e.g., MetaMask).
"""

import json
import os
from typing import Optional
from eth_account import Account
from eth_account.messages import encode_typed_data


class UserClient:
    """
    Simulates a real user's wallet client.
    
    Holds user's private key and can sign EIP-712 typed data.
    Used for testing the complete Builder order flow.
    
    Example:
        ```python
        # Create a random user
        user = UserClient.create_random()
        
        # Or load from file
        user = UserClient.load_from_file(".test_user.json")
        
        # Sign an order
        signature = user.sign_typed_data(typed_data)
        ```
    """
    
    def __init__(self, private_key: str):
        """
        Initialize UserClient.
        
        Args:
            private_key: User's private key (hex string, with or without 0x prefix)
        """
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self._private_key = private_key
    
    @classmethod
    def create_random(cls) -> "UserClient":
        """
        Generate a random test user.
        
        Returns:
            New UserClient instance
        """
        account = Account.create()
        return cls(account.key.hex())
    
    @classmethod
    def load_from_file(cls, path: str) -> "UserClient":
        """
        Load user from JSON file.
        
        Args:
            path: JSON file path
            
        Returns:
            UserClient instance
            
        Raises:
            FileNotFoundError: File does not exist
            KeyError: Invalid file format
        """
        with open(path, "r") as f:
            data = json.load(f)
        
        private_key = data.get("private_key")
        if not private_key:
            raise KeyError("JSON file must contain 'private_key' field")
        
        return cls(private_key)
    
    @classmethod
    def load_or_create(cls, path: str) -> "UserClient":
        """
        Load user from file, or create new user and save if file doesn't exist.
        
        Args:
            path: JSON file path
            
        Returns:
            UserClient instance
        """
        if os.path.exists(path):
            return cls.load_from_file(path)
        else:
            user = cls.create_random()
            user.save_to_file(path)
            return user
    
    def save_to_file(self, path: str):
        """
        Save user to JSON file.
        
        Args:
            path: JSON file path
        """
        data = {
            "address": self.address,
            "private_key": self._private_key,
        }
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"User saved to {path}")
        print(f"   Address: {self.address}")
    
    def sign_typed_data(self, typed_data: dict) -> str:
        """
        Sign EIP-712 typed data.
        
        This is the core method for user signing Safe transactions in Builder mode.
        In production, this signing is done by the user's wallet.
        
        Args:
            typed_data: EIP-712 typed data containing domain, types, message
            
        Returns:
            Signature (hex string with 0x prefix)
        """
        signable_message = encode_typed_data(full_message=typed_data)
        signed = self.account.sign_message(signable_message)
        return signed.signature.hex()
    
    def sign_hash(self, hash_to_sign: str) -> str:
        """
        Sign a hash directly (for order signing).
        
        This is the core method for user signing orders in Builder mode.
        Uses the same signing method as the original SDK.
        
        Args:
            hash_to_sign: Hash to sign (hex string, with or without 0x prefix)
            
        Returns:
            Signature (hex string with 0x prefix)
        """
        if not hash_to_sign.startswith("0x"):
            hash_to_sign = "0x" + hash_to_sign
        signed = Account._sign_hash(hash_to_sign, self._private_key)
        sig = signed.signature.hex()
        if not sig.startswith("0x"):
            sig = "0x" + sig
        return sig
    
    def __repr__(self) -> str:
        return f"UserClient(address={self.address})"
