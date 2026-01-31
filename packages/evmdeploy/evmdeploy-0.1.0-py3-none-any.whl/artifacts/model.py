from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass(frozen=True)
class ContractArtifact:
    name: str
    abi: List[Dict[str, Any]]
    bytecode: str
    compiler_version: str
    source_hash: str

@dataclass(frozen=True)
class DeploymentResult:
    tx_hash: str
    contract_address: Optional[str] = None
    receipt: Optional[Dict[str, Any]] = None
