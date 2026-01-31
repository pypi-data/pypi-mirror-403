from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_account.types import PrivateKeyType
from eth_account.datastructures import SignedTransaction
from web3 import Web3
from typing import Dict, Any, Optional


def sign_transaction(
    transaction: Dict[str, Any],
    private_key: PrivateKeyType,
    chain_id: Optional[int] = None,
) -> SignedTransaction:
    """
    Signs an Ethereum transaction with the given private key.

    Args:
        transaction: Unsigned transaction dictionary.
        private_key: Private key (bytes, hex str, or int)
        chain_id: Optional chain ID to override or set in the transaction.

    Returns:
        SignedTransaction object.
    """
    if chain_id is not None:
        transaction = {**transaction, "chainId": chain_id}

    # Basic validation
    required = {"gas", "nonce"}
    if "maxFeePerGas" in transaction or "maxPriorityFeePerGas" in transaction:
        # EIP-1559
        if "chainId" not in transaction:
            raise ValueError("chainId is required for EIP-1559 transactions")
    elif "gasPrice" not in transaction:
        required.add("gasPrice")

    missing = required - set(transaction.keys())
    if missing:
        raise ValueError(f"Transaction missing required fields: {missing}")

    # 1. Create account signer from private key
    account: LocalAccount = Account.from_key(private_key)

    # 2. Sign the transaction
    signed_tx = account.sign_transaction(transaction)

    return signed_tx
