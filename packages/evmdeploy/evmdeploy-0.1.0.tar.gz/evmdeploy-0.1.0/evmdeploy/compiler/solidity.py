from pathlib import Path
from hashlib import sha256
from typing import Dict, Optional

from solcx import compile_standard, install_solc, set_solc_version

from evmdeploy.compiler.linker import link_bytecode
from evmdeploy.artifacts.model import ContractArtifact
from evmdeploy.exceptions import CompilationError


def compile_solidity(
    path: str,
    solc_version: str = "0.8.23",
    remappings: Optional[Dict[str, str]] = None,
    libraries: Optional[Dict[str, str]] = None,
    optimizer: bool = True,
    runs: int = 200,
) -> Dict[str, ContractArtifact]:
    """
    Compile Solidity file(s) using py-solc-x and return ContractArtifact dict.

    Args:
        path: Path to Solidity file.
        solc_version: Solidity compiler version to use.
        remappings: dict of import remappings, e.g., {"@openzeppelin/": "node_modules/@openzeppelin/"}
        libraries: optional dict of {library_name: deployed_address} for linking
        optimizer: Whether to enable Solidity optimizer (default: True)
        runs: Optimizer runs (default: 200)

    Returns:
        Dict of ContractArtifact objects, keyed by contract name.
    """
    remappings = remappings or {}
    libraries = libraries or {}

    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Solidity file not found: {path}")

    # Ensure compiler version is installed
    install_solc(solc_version)
    set_solc_version(solc_version)

    # Read Solidity source
    source = path_obj.read_text()

    # Prepare sources dict for py-solc-x
    sources = {str(path_obj.name): {"content": source}}

    # Handle remappings for py-solc-x
    # remapping format: "@openzeppelin/": "node_modules/@openzeppelin/"
    import_remaps = [f"{k}={v}" for k, v in remappings.items()]

    # Compile
    try:
        compiled = compile_standard(
            {
                "language": "Solidity",
                "sources": sources,
                "settings": {
                    "optimizer": {"enabled": optimizer, "runs": runs},
                    "outputSelection": {
                        "*": {
                            "*": [
                                "abi",
                                "evm.bytecode.object",
                                "evm.deployedBytecode.object",
                                "metadata",
                                "evm.bytecode.linkReferences",
                            ]
                        }
                    },
                    "remappings": import_remaps,
                },
            },
            allow_paths=".",  # required for relative imports
        )
    except Exception as e:
        raise CompilationError(
            f"Compilation failed: {e}", source_path=path, compiler_output=str(e)
        )

    source_hash = sha256(source.encode()).hexdigest()
    artifacts = {}

    contracts = compiled.get("contracts", {}).get(path_obj.name, {})
    for contract_name, data in contracts.items():
        bytecode = data["evm"]["bytecode"]["object"]
        link_refs = data["evm"]["bytecode"].get("linkReferences", {})

        if bytecode == "":
            # abstract contract or interface
            continue

        if link_refs and libraries:
            bytecode = link_bytecode(bytecode, link_refs, libraries)

        artifact = ContractArtifact(
            name=contract_name,
            abi=data.get("abi", []),
            bytecode="0x" + bytecode,
            compiler_version=solc_version,
            source_hash=source_hash,
        )
        artifacts[contract_name] = artifact

    if not artifacts:
        raise CompilationError("No deployable contracts found in file")

    return artifacts


class SolidityCompiler:
    """
    Compiler object that holds configuration and compiles Solidity files.
    """

    def __init__(
        self,
        solc_version: str = "0.8.23",
        remappings: Optional[Dict[str, str]] = None,
        libraries: Optional[Dict[str, str]] = None,
        optimizer: bool = True,
        runs: int = 200,
    ):
        self.solc_version = solc_version
        self.remappings = remappings
        self.libraries = libraries
        self.optimizer = optimizer
        self.runs = runs

    def compile(self, path: str) -> Dict[str, ContractArtifact]:
        """
        Compile a Solidity file using the stored configuration.
        """
        return compile_solidity(
            path=path,
            solc_version=self.solc_version,
            remappings=self.remappings,
            libraries=self.libraries,
            optimizer=self.optimizer,
            runs=self.runs,
        )
