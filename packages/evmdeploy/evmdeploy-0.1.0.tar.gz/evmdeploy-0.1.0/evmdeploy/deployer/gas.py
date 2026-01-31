from typing import Dict
from web3 import Web3

def estimate_gas_fees(w3: Web3) -> Dict[str, int]:
    """
    Estimates gas fees for the current network.
    Returns a dict with 'maxFeePerGas' and 'maxPriorityFeePerGas' (EIP-1559)
    or just 'gasPrice' (Legacy).
    """
    try:
        # Try EIP-1559 fees first
        fee_data = w3.eth.fee_history(1, "latest", [25.0])
        base_fee = fee_data["baseFeePerGas"][-1]
        priority_fee = fee_data["reward"][0][0]
        
        # Buffer the base fee slightly for stability
        max_fee = int(base_fee * 2 + priority_fee)
        
        return {
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": priority_fee
        }
    except Exception:
        # Fallback to legacy gas price
        return {"gasPrice": w3.eth.gas_price}
