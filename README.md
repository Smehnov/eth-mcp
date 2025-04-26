# Ethereum MCP Tools

A collection of Ethereum tools for managing wallets, contacts, and performing transactions through MCP.

## How to run
`fastmcp install eth.py` to add to Claude Desktop 
`uv run --with fastmcp --with web3 fastmcp run <PATH-TO-ETH-MCP>/eth.py`

## Features

### Contact Management
- `list_contacts()`: List all saved contacts
- `add_contact(name, address)`: Add a new contact
- `delete_contact(contact_id)`: Delete a contact

### Wallet Management
- `list_wallets()`: List all saved wallets
- `generate_wallet(name)`: Generate a new wallet
- `add_wallet(name, seed_phrase)`: Add an existing wallet
- `delete_wallet(wallet_id)`: Delete a wallet

### Balance Tools
- `get_eth_balance(address)`: Get ETH balance of any address
- `get_token_balance(address, token_address)`: Get ERC20 token balance
- `list_popular_tokens()`: Get addresses of popular ERC20 tokens

### Transaction Tools
- `transfer_eth(from_address, to_address, amount, private_key)`: Send ETH
- `send_token(wallet_name, token_address, to_address, amount)`: Send ERC20 tokens

## Popular Token Addresses

| Token | Address |
|-------|---------|
| USDT  | 0xdAC17F958D2ee523a2206206994597C13D831ec7 |
| USDC  | 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 |
| DAI   | 0x6B175474E89094C44Da98b954EedeAC495271d0F |
| XRT   | 0x7dE91B204C1C737bcEe6F000AAA6569Cf7061cb7 |
| wETH  | 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 |
| stETH | 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84 |

## Requirements
- web3.py
- eth-account
- fastmcp
- python-dotenv

## Configuration

Create a `.env` file with your Ethereum RPC URL:
```
ETH_RPC_URL=https://mainnet.infura.io/v3/your-project-id
```
