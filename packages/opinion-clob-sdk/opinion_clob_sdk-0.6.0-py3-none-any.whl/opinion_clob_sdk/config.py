# Configuration constants for Opinion CLOB SDK

# Supported chain IDs
SUPPORTED_CHAIN_IDS = [56]  # BNB Chain (BSC) mainnet

# ============================================================================
# BNB Chain (BSC) Mainnet Contract Addresses
# ============================================================================
BNB_CHAIN_MAINNET_ADDRESSES = {
    "conditional_tokens": "0xAD1a38cEc043e70E83a3eC30443dB285ED10D774",
    "multisend": "0x38869bf66a61cF6bDB996A6aE40D5853Fd43B526",  # Safe MultiSend v1.4.1
    "fee_manager": "0xC9063Dc52dEEfb518E5b6634A6b8D624bc5d7c36",
}

# Default contract addresses by chain ID (mainnet by default)
# For testnet/beta environments, pass custom addresses via contract_addresses parameter
DEFAULT_CONTRACT_ADDRESSES = {
    56: BNB_CHAIN_MAINNET_ADDRESSES,
}
