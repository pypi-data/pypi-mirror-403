class EvmDeployError(Exception):
    """Base class for all exceptions raised by evmdeploy.

    All other exceptions in this package inherit from this class.
    Catch this if you want to handle *any* evmdeploy-specific failure.
    """

    pass


class CompilationError(EvmDeployError):
    """Solidity compilation failed.

    Attributes:
        source_path: Path to the source file that failed
        compiler_output: Full stdout/stderr from solc/forge/hardhat/etc.
        contract_name: Name of the contract that failed to compile (if known)
    """

    def __init__(
        self,
        message: str,
        source_path: str | None = None,
        contract_name: str | None = None,
        compiler_output: str | None = None,
    ):
        self.source_path = source_path
        self.contract_name = contract_name
        self.compiler_output = compiler_output
        full_msg = message
        if contract_name:
            full_msg += f" ({contract_name})"
        if source_path:
            full_msg += f" in {source_path}"
        super().__init__(full_msg)


class LinkingError(EvmDeployError):
    """Bytecode linking failed (unresolved library addresses, placeholders, etc.).

    Common with older Solidity <0.8 or manual library linking.
    """

    def __init__(
        self,
        message: str,
        library_name: str | None = None,
        placeholder: str | None = None,
    ):
        self.library_name = library_name
        self.placeholder = placeholder
        full_msg = message
        if library_name:
            full_msg += f" for library {library_name!r}"
        if placeholder:
            full_msg += f" (placeholder: {placeholder})"
        super().__init__(full_msg)


class DeploymentError(EvmDeployError):
    """Transaction failed to deploy contract (reverted, out of gas, invalid nonce, etc.).

    Attributes:
        tx_hash: Hash of the failed deployment transaction (if sent)
        receipt: Full tx receipt if available
        revert_reason: Decoded revert string if available
        gas_used: Gas consumed before revert
    """

    def __init__(
        self,
        message: str,
        tx_hash: str | None = None,
        revert_reason: str | None = None,
        gas_used: int | None = None,
        code: int | None = None,  # e.g. RPC error code
    ):
        self.tx_hash = tx_hash
        self.revert_reason = revert_reason
        self.gas_used = gas_used
        self.code = code

        full_msg = message
        if revert_reason:
            full_msg += f": {revert_reason}"
        if tx_hash:
            full_msg += f" (tx: {tx_hash})"
        super().__init__(full_msg)


# Optional: more granular ones people actually need
class ConstructorRevertError(DeploymentError):
    """Deployment reverted during constructor execution."""

    pass


class InsufficientBalanceError(DeploymentError):
    """Sender balance too low for value + gas."""

    pass


class InvalidBytecodeError(EvmDeployError):
    """Bytecode is malformed, wrong length, invalid opcode, etc."""

    def __init__(self, message: str, bytecode_len: int | None = None):
        self.bytecode_len = bytecode_len
        super().__init__(
            f"{message} (length: {bytecode_len})" if bytecode_len else message
        )
