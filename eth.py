from typing import Any, Optional, List, Dict
from web3 import Web3
from fastmcp import FastMCP
import os
from dotenv import load_dotenv
from eth_account import Account
import json
from db import Database

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("ethereum")

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(os.getenv('ETH_RPC_URL', 'https://mainnet.infura.io/v3/<your-infura-key>')))

# Initialize database
db = Database()

# Contact Management Tools
@mcp.tool()
async def list_contacts() -> List[Dict]:
    """List all contacts from the database.
    
    Returns:
        list: List of contacts with id, name, and address
    """
    return db.list_contacts()

@mcp.tool()
async def add_contact(name: str, address: str) -> bool:
    """Add a new contact to the database.
    
    Args:
        name: Contact name
        address: Ethereum address
        
    Returns:
        bool: True if successful, False if address already exists
    """
    return db.add_contact(name, address)

@mcp.tool()
async def delete_contact(contact_id: int) -> bool:
    """Delete a contact from the database.
    
    Args:
        contact_id: ID of the contact to delete
        
    Returns:
        bool: True if contact was deleted, False if not found
    """
    return db.delete_contact(contact_id)

# Wallet Management Tools
@mcp.tool()
async def list_wallets() -> List[Dict]:
    """List all wallets from the database.
    
    Returns:
        list: List of wallets with id, name, and address
    """
    return db.list_wallets()

@mcp.tool()
async def generate_wallet(name: str) -> Dict:
    """Generate a new wallet and store it in the database.
    
    Args:
        name: Wallet name
        
    Returns:
        dict: Wallet information including name, seed phrase, and address
    """
    return db.generate_wallet(name)

@mcp.tool()
async def add_wallet(name: str, seed_phrase: str) -> bool:
    """Add an existing wallet to the database.
    
    Args:
        name: Wallet name
        seed_phrase: Wallet seed phrase
        
    Returns:
        bool: True if successful, False if name or address already exists
    """
    return db.add_wallet(name, seed_phrase)

@mcp.tool()
async def delete_wallet(wallet_id: int) -> bool:
    """Delete a wallet from the database.
    
    Args:
        wallet_id: ID of the wallet to delete
        
    Returns:
        bool: True if wallet was deleted, False if not found
    """
    return db.delete_wallet(wallet_id)

# Transaction Tools
@mcp.tool()
async def send_eth(wallet_name: str, to_address: str, amount: float) -> str:
    """Send ETH from a stored wallet.
    
    Args:
        wallet_name: Name of the wallet to send from
        to_address: Recipient address
        amount: Amount of ETH to send
        
    Returns:
        str: Transaction hash
    """
    # Get wallet seed phrase
    seed_phrase = db.get_wallet_seed(wallet_name)
    if not seed_phrase:
        raise ValueError(f"Wallet '{wallet_name}' not found")
    
    # Create account from seed phrase
    account = Account.from_key(seed_phrase)
    
    # Get nonce
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Build transaction
    transaction = {
        'nonce': nonce,
        'to': to_address,
        'value': w3.to_wei(amount, 'ether'),
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    }
    
    # Sign transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, seed_phrase)
    
    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    return w3.to_hex(tx_hash)

@mcp.tool()
async def send_token(wallet_name: str, token_address: str, to_address: str, amount: float) -> str:
    """Transfer ERC20 tokens from a stored wallet.
    
    Args:
        wallet_name: Name of the wallet to send from
        token_address: ERC20 token contract address
        to_address: Recipient address
        amount: Amount of tokens to transfer
        
    Returns:
        str: Transaction hash
    """
    # Get wallet seed phrase
    seed_phrase = db.get_wallet_seed(wallet_name)
    if not seed_phrase:
        raise ValueError(f"Wallet '{wallet_name}' not found")
    
    # Create account from seed phrase
    account = Account.from_key(seed_phrase)
    
    # Get token decimals
    decimals_abi = [{
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }]
    
    decimals_contract = w3.eth.contract(address=token_address, abi=decimals_abi)
    decimals = decimals_contract.functions.decimals().call()
    
    # ERC20 ABI for transfer function
    transfer_abi = [{
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }]
    
    contract = w3.eth.contract(address=token_address, abi=transfer_abi)
    
    # Build transaction
    transaction = contract.functions.transfer(
        to_address,
        int(amount * (10 ** decimals))
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    })
    
    # Sign and send transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, seed_phrase)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    return w3.to_hex(tx_hash)

# Balance Tools
@mcp.tool()
async def get_eth_balance(address: str) -> str:
    """Get ETH balance of an Ethereum address.
    
    Args:
        address: Ethereum address to check balance for
        
    Returns:
        str: Balance in ETH
    """
    # Validate address
    if not Web3.is_address(address):
        raise ValueError("Invalid Ethereum address")
    
    balance = w3.eth.get_balance(address)
    return w3.from_wei(balance, 'ether')

@mcp.tool()
async def get_token_balance(address: str, token_address: str) -> str:
    """Get ERC20 token balance of an Ethereum address.
    
    Args:
        address: Ethereum address to check balance for
        token_address: ERC20 token contract address
        
    Returns:
        str: Balance in tokens
    """
    # Validate addresses
    if not Web3.is_address(address):
        raise ValueError("Invalid Ethereum address")
    if not Web3.is_address(token_address):
        raise ValueError("Invalid token contract address")
    
    # ERC20 ABI for balanceOf and decimals functions
    token_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        }
    ]
    
    contract = w3.eth.contract(address=token_address, abi=token_abi)
    
    # Get token decimals
    decimals = contract.functions.decimals().call()
    
    # Get token balance
    balance = contract.functions.balanceOf(address).call()
    
    # Convert to human-readable format
    return str(balance / (10 ** decimals))

@mcp.tool()
async def transfer_eth(from_address: str, to_address: str, amount: float, private_key: str) -> str:
    """Transfer ETH from one address to another.
    
    Args:
        from_address: Ethereum address to send from
        to_address: Ethereum address to send to
        amount: Amount of ETH to transfer
        private_key: Private key of the sender address
        
    Returns:
        str: Transaction hash
    """
    # Validate addresses
    if not Web3.is_address(from_address):
        raise ValueError("Invalid sender address")
    if not Web3.is_address(to_address):
        raise ValueError("Invalid recipient address")
    
    # Create account from private key
    account = Account.from_key(private_key)
    if account.address.lower() != from_address.lower():
        raise ValueError("Private key does not match sender address")
    
    # Get nonce
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Build transaction
    transaction = {
        'nonce': nonce,
        'to': to_address,
        'value': w3.to_wei(amount, 'ether'),
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    }
    
    # Sign transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
    
    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    return w3.to_hex(tx_hash)

# Token Addresses
POPULAR_TOKENS = {
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "XRT": "0x7dE91B204C1C737bcEe6F000AAA6569Cf7061cb7",
    "wETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "stETH": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
}

@mcp.tool()
async def list_popular_tokens() -> Dict[str, str]:
    """List addresses of popular ERC20 tokens.
    
    Returns:
        dict: Dictionary of token symbols and their addresses
    """
    return POPULAR_TOKENS

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run() 