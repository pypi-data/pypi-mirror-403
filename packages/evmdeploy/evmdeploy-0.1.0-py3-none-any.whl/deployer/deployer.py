import time
from typing import Any, Dict
from web3 import Web3
from eth_account.types import PrivateKeyType

from evmdeploy.crypto.signer import sign_transaction
from evmdeploy.deployer.gas import estimate_gas_fees
from evmdeploy.exceptions import DeploymentError

class Deployer:
    """
    Handles sending transactions and waiting for confirmations on the EVM.
    """

    def __init__(self, w3: Web3, private_key: PrivateKeyType):
        self.w3 = w3
        self.private_key = private_key
        self.account = w3.eth.account.from_key(private_key)
        self.address = self.account.address

    def get_nonce(self) -> int:
        return self.w3.eth.get_transaction_count(self.address)

    def send_transaction(self, tx: Dict[str, Any]) -> str:
        """Signs and sends a transaction, returning the tx hash."""
        # Ensure nonce and chainId are set if missing
        if "nonce" not in tx:
            tx["nonce"] = self.get_nonce()
        if "chainId" not in tx:
            tx["chainId"] = self.w3.eth.chain_id
        
        # Estimate gas if missing
        if "gas" not in tx:
            tx["gas"] = self.w3.eth.estimate_gas(tx)

        # Merge in fee estimation if no fee fields are present
        if not any(k in tx for k in ["gasPrice", "maxFeePerGas"]):
            fees = estimate_gas_fees(self.w3)
            tx.update(fees)

        signed_tx = sign_transaction(tx, self.private_key, chain_id=tx["chainId"])
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return self.w3.to_hex(tx_hash)

    def wait_for_receipt(self, tx_hash: str, timeout: int = 120, poll_latency: float = 1.0) -> Dict[str, Any]:
        """Waits for a transaction receipt."""
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout, poll_latency)
            if receipt["status"] == 0:
                raise DeploymentError(f"Transaction failed: {tx_hash}", tx_hash=tx_hash)
            return dict(receipt)
        except Exception as e:
            if isinstance(e, DeploymentError):
                raise
            raise DeploymentError(f"Error waiting for receipt: {e}", tx_hash=tx_hash)
