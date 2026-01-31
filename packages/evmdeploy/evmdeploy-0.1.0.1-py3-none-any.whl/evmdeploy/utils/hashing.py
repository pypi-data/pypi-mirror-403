from eth_utils import keccak, to_hex

def compute_keccak256(data: bytes | str) -> str:
    """Computes Keccak-256 hash of bytes or hex string."""
    if isinstance(data, str) and data.startswith("0x"):
        data = bytes.fromhex(data[2:])
    elif isinstance(data, str):
        data = data.encode()
    return to_hex(keccak(data))
