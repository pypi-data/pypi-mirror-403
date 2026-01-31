from typing import Dict, Optional, Any
from dataclasses import dataclass

@dataclass(frozen=True)
class NetworkConfig:
    name: str
    chain_id: int
    rpc_url: str
    currency_symbol: str = "ETH"
    is_testnet: bool = False

DEFAULT_NETWORKS: Dict[str, NetworkConfig] = {
    "mainnet": NetworkConfig(
        name="Ethereum Mainnet",
        chain_id=1,
        rpc_url="https://eth.llamarpc.com",
        currency_symbol="ETH"
    ),
    "sepolia": NetworkConfig(
        name="Sepolia Testnet",
        chain_id=11155111,
        rpc_url="https://rpc.sepolia.org",
        currency_symbol="ETH",
        is_testnet=True
    ),
    "polygon": NetworkConfig(
        name="Polygon Mainnet",
        chain_id=137,
        rpc_url="https://polygon-rpc.com",
        currency_symbol="POL"
    ),
    "amoy": NetworkConfig(
        name="Polygon Amoy Testnet",
        chain_id=80002,
        rpc_url="https://rpc-amoy.polygon.technology",
        currency_symbol="POL",
        is_testnet=True
    ),
}

def get_network(name: str) -> Optional[NetworkConfig]:
    return DEFAULT_NETWORKS.get(name.lower())
