import os
from web3 import Web3
from evmdeploy import SolidityCompiler, Contract
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # 1. Initialize Compiler with OpenZeppelin remappings
    # Change the path to where your OpenZeppelin contracts are located
    # Common paths: "node_modules/@openzeppelin/" or a local lib folder
    compiler = SolidityCompiler(
        solc_version="0.8.20",
        remappings={
            "@openzeppelin/": "contracts/lib/openzeppelin-contracts/" 
        },
        optimizer=True,
        runs=200
    )

    # 2. Compile the ERC20 token
    print("Compiling MyToken.sol...")
    try:
        artifacts = compiler.compile("contracts/MyToken.sol")
    except Exception as e:
        print(f"Compilation failed. Make sure OpenZeppelin is installed or adjust remappings.\nError: {e}")
        return

    token_artifact = artifacts["MyToken"]
    token = Contract(token_artifact)
    print(f"Contract '{token.name}' compiled successfully.")

    # 3. Setup Web3 and Private Key
    # Using a local node for demonstration
    rpc_url = os.getenv("RPC_URL", "http://localhost:8545")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print("Please set the PRIVATE_KEY environment variable.")
        return

    # 4. Deploy the token
    # Constructor: name, symbol, initialSupply
    name = "MyToken"
    symbol = "MTK"
    initial_supply = 1000 * 10**18 # 1000 tokens with 18 decimals

    print(f"Deploying {name} ({symbol}) to {rpc_url}...")
    
    try:
        result = token.deploy(
            w3=w3,
            private_key=private_key,
            constructor_args=[name, symbol, initial_supply]
        )
        
        print("\nDeployment Successful!")
        print(f"Transaction Hash: {result.tx_hash}")
        print(f"Token Address: {result.contract_address}")
        
        # Save artifact for future use
        artifact_path = token.save()
        print(f"Artifact saved to: {artifact_path}")
        
    except Exception as e:
        print(f"Deployment failed: {e}")

if __name__ == "__main__":
    main()
