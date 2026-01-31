from web3 import Web3
from evmdeploy import compile_solidity, Contract, get_network

def test_deployment_flow():
    # 1. Compile
    artifacts = compile_solidity("contracts/Vault.sol")
    vault_contract = Contract(artifacts["Vault"])
    
    # 2. Setup mock provider (using Eth-Tester or just mocking for logic check)
    # For a real test, one might use a local node, but here we just check integration
    w3 = Web3(Web3.HTTPProvider("http://localhost:8545"))
    
    # 3. Network check
    sepolia = get_network("sepolia")
    print(f"Network: {sepolia.name}, Chain ID: {sepolia.chain_id}")
    
    # 4. Check Contract.deploy exists
    print(f"Contract 'deploy' method exists: {hasattr(vault_contract, 'deploy')}")

if __name__ == "__main__":
    test_deployment_flow()
