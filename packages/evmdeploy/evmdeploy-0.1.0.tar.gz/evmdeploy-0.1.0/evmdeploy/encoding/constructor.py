from typing import Any, List, Dict
from eth_abi.abi import encode


def encode_constructor_args(
    abi: List[Dict[str, Any]],
    *args: Any,
    **kwargs: Any,
) -> bytes:
    """
    Encodes constructor arguments according to the contract's ABI.

    This returns ONLY the encoded argument data (as bytes) — ready to append
    to the deployment bytecode.

    Usage for deployment:
        deployment_data = bytecode + encode_constructor_args(abi, arg1, arg2, ...)

    Args:
        abi: The full contract ABI (list of dicts) — usually from compilation output
        *args, **kwargs: Positional or keyword constructor arguments
                         (web3.py style — matches constructor inputs order)

    Returns:
        bytes: ABI-encoded constructor parameters (empty b'' if no constructor args)

    Raises:
        ValueError: If constructor not found, wrong number of args, type mismatch, etc.
    """
    # Find the constructor entry (there should be only one)
    constructor_abi = None
    for item in abi:
        if item.get("type") == "constructor":
            constructor_abi = item
            break

    if constructor_abi is None:
        if args or kwargs:
            raise ValueError("Constructor arguments provided but no constructor in ABI")
        return b""  # no constructor → nothing to encode

    inputs = constructor_abi.get("inputs", [])
    if not inputs:
        if args or kwargs:
            raise ValueError("Constructor takes no arguments but some were provided")
        return b""  # constructor() with no params

    # Build the types list + values list
    types: List[str] = []
    values: List[Any] = []

    # Handle positional args first
    if args:
        if len(args) != len(inputs):
            raise ValueError(
                f"Wrong number of positional args: expected {len(inputs)}, got {len(args)}"
            )
        for i, inp in enumerate(inputs):
            types.append(inp["type"])
            values.append(args[i])

    # Handle keyword args (overrides positional if mixed — but positional usually preferred)
    elif kwargs:
        if set(kwargs) != {inp["name"] for inp in inputs if inp.get("name")}:
            raise ValueError(
                "Keyword args keys do not match constructor parameter names"
            )
        for inp in inputs:
            name = inp["name"]
            if name not in kwargs:
                raise ValueError(f"Missing required constructor arg: {name}")
            types.append(inp["type"])
            values.append(kwargs[name])

    else:
        raise ValueError("Constructor requires arguments but none provided")

    # Now encode
    try:
        encoded = encode(types, values)
    except Exception as e:
        raise ValueError(f"Failed to ABI-encode constructor args: {e}") from e

    return encoded
