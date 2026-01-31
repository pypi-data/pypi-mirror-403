from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from eth_account.datastructures import SignedTransaction
from eth_account.types import PrivateKeyType
from web3 import Web3

from evmdeploy.artifacts.model import ContractArtifact, DeploymentResult
from evmdeploy.crypto.signer import sign_transaction
from evmdeploy.encoding.constructor import encode_constructor_args
from evmdeploy.deployer.deployer import Deployer
from evmdeploy.artifacts.storage import ArtifactStorage


class Contract:
    """
    Combined object representing a compiled contract, providing utilities for
    encoding arguments and signing deployment transactions.
    """

    def __init__(self, artifact: ContractArtifact):
        self.artifact = artifact
        self.name = artifact.name
        self.abi = artifact.abi
        self.bytecode = artifact.bytecode

    @classmethod
    def from_storage(cls, name: str, base_path: Union[str, Path] = "artifacts") -> "Contract":
        """
        Loads a contract from the artifact storage.
        """
        storage = ArtifactStorage(base_path)
        artifact = storage.load_artifact(name)
        return cls(artifact)

    def save(self, base_path: Union[str, Path] = "artifacts_output") -> Path:
        """
        Saves the contract's artifact to the artifact storage.
        """
        storage = ArtifactStorage(base_path)
        return storage.save_artifact(self.artifact)

    @property
    def hex_bytecode(self) -> str:
        """Bytecode as a hex string (ensures 0x prefix)."""
        if not self.bytecode.startswith("0x"):
            return "0x" + self.bytecode
        return self.bytecode

    def encode_constructor_args(self, *args, **kwargs) -> bytes:
        """
        Encodes constructor arguments according to the contract's ABI.
        """
        return encode_constructor_args(self.abi, *args, **kwargs)

    def prepare_deployment_transaction(
        self,
        deployer_address: str,
        nonce: int,
        gas: int,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        value: int = 0,
        chain_id: Optional[int] = None,
        constructor_args: Optional[List[Any]] = None,
        constructor_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Prepares a deployment transaction dictionary.
        """
        constructor_args = constructor_args or []
        constructor_kwargs = constructor_kwargs or {}

        encoded_args = self.encode_constructor_args(*constructor_args, **constructor_kwargs)
        data = self.hex_bytecode + encoded_args.hex()

        tx: Dict[str, Any] = {
            "from": deployer_address,
            "nonce": nonce,
            "gas": gas,
            "data": data,
            "value": value,
        }

        if max_fee_per_gas is not None:
            tx["maxFeePerGas"] = max_fee_per_gas
            if max_priority_fee_per_gas is not None:
                tx["maxPriorityFeePerGas"] = max_priority_fee_per_gas
            if chain_id is not None:
                tx["chainId"] = chain_id
        elif gas_price is not None:
            tx["gasPrice"] = gas_price
            if chain_id is not None:
                tx["chainId"] = chain_id

        return tx

    def sign_deployment(
        self,
        private_key: PrivateKeyType,
        nonce: int,
        gas: int,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        value: int = 0,
        chain_id: Optional[int] = None,
        constructor_args: Optional[List[Any]] = None,
        constructor_kwargs: Optional[Dict[str, Any]] = None,
    ) -> SignedTransaction:
        """
        Prepares and signs a deployment transaction.
        """
        # We need the address for the 'from' field, though sign_transaction might not strictly require it
        # but it's good practice.
        from eth_account import Account
        deployer_address = Account.from_key(private_key).address

        tx = self.prepare_deployment_transaction(
            deployer_address=deployer_address,
            nonce=nonce,
            gas=gas,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            gas_price=gas_price,
            value=value,
            chain_id=chain_id,
            constructor_args=constructor_args,
            constructor_kwargs=constructor_kwargs,
        )

        return sign_transaction(tx, private_key, chain_id=chain_id)

    def deploy(
        self,
        w3: Web3,
        private_key: PrivateKeyType,
        constructor_args: Optional[List[Any]] = None,
        constructor_kwargs: Optional[Dict[str, Any]] = None,
        gas: Optional[int] = None,
        value: int = 0,
        wait: bool = True,
    ) -> DeploymentResult:
        """
        Deploys the contract to the network.
        Returns a DeploymentResult containing the tx hash and optionally the receipt/address.
        """
        deployer = Deployer(w3, private_key)
        
        # Prepare transaction
        tx = self.prepare_deployment_transaction(
            deployer_address=deployer.address,
            nonce=deployer.get_nonce(),
            gas=gas or 0, # Deployer will estimate if 0
            value=value,
            constructor_args=constructor_args,
            constructor_kwargs=constructor_kwargs,
        )
        
        # Remove gas if 0 so Deployer estimates it
        if tx.get("gas") == 0:
            del tx["gas"]

        tx_hash = deployer.send_transaction(tx)
        
        if not wait:
            return DeploymentResult(tx_hash=tx_hash)

        receipt = deployer.wait_for_receipt(tx_hash)
        return DeploymentResult(
            tx_hash=tx_hash,
            contract_address=receipt.get("contractAddress"),
            receipt=receipt
        )
