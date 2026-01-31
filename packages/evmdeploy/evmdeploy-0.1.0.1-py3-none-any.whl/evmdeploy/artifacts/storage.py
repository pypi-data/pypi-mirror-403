import json
from pathlib import Path
from typing import Dict, Union

from evmdeploy.artifacts.model import ContractArtifact

class ArtifactStorage:
    """
    Handles persisting and retrieving contract artifacts from disk.
    """

    def __init__(self, base_path: Union[str, Path] = "artifacts"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_artifact(self, artifact: ContractArtifact) -> Path:
        """Saves a single ContractArtifact to a JSON file."""
        file_path = self.base_path / f"{artifact.name}.json"
        
        data = {
            "name": artifact.name,
            "abi": artifact.abi,
            "bytecode": artifact.bytecode,
            "compiler_version": artifact.compiler_version,
            "source_hash": artifact.source_hash,
        }
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        
        return file_path

    def save_artifacts(self, artifacts: Dict[str, ContractArtifact]):
        """Saves a dictionary of artifacts."""
        for artifact in artifacts.values():
            self.save_artifact(artifact)

    def load_artifact(self, name: str) -> ContractArtifact:
        """Loads a ContractArtifact by name."""
        file_path = self.base_path / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Artifact not found: {file_path}")
            
        with open(file_path, "r") as f:
            data = json.load(f)
            
        return ContractArtifact(
            name=data["name"],
            abi=data["abi"],
            bytecode=data["bytecode"],
            compiler_version=data["compiler_version"],
            source_hash=data["source_hash"],
        )
