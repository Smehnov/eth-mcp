import sqlite3
from typing import List, Dict, Optional
from web3 import Web3
from eth_account import Account
import os
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "/Users/alex/eth-mcp/eth.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_db()

    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")

    def _init_db(self):
        """Initialize database and create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create contacts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS contacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        address TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create wallets table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS wallets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        seed_phrase TEXT NOT NULL,
                        address TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info(f"Database initialized successfully at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def _normalize_address(self, address: str) -> str:
        """Validate Ethereum address format and checksum.
        
        Args:
            address: Ethereum address to validate
            
        Returns:
            str: Validated address
            
        Raises:
            ValueError: If address is invalid
        """
        # Remove any whitespace
        address = address.strip()
        
        # Ensure address starts with 0x
        if not address.startswith('0x'):
            address = '0x' + address
        
        # Validate address format
        if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
            raise ValueError("Invalid Ethereum address format")
        
        # Validate checksum
        if not Web3.is_address(address):
            raise ValueError("Invalid Ethereum address checksum")
        
        return address

    def add_contact(self, name: str, address: str) -> bool:
        """Add a new contact to the database.
        
        Args:
            name: Contact name
            address: Ethereum address
            
        Returns:
            bool: True if successful, False if address already exists
            
        Raises:
            ValueError: If address is invalid
        """
        try:
            normalized_address = self._normalize_address(address)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO contacts (name, address) VALUES (?, ?)",
                    (name, normalized_address)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except ValueError as e:
            logger.error(f"Invalid address format: {e}")
            raise

    def list_contacts(self) -> List[Dict]:
        """List all contacts from the database.
        
        Returns:
            list: List of contacts with id, name, and address
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, address FROM contacts ORDER BY name")
            return [
                {"id": row[0], "name": row[1], "address": row[2]}
                for row in cursor.fetchall()
            ]

    def generate_wallet(self, name: str) -> Dict:
        """Generate a new wallet and store it in the database.
        
        Args:
            name: Wallet name
            
        Returns:
            dict: Wallet information including name, seed phrase, and address
        """
        # Generate new account
        account = Account.create()
        
        # Normalize the address
        normalized_address = self._normalize_address(account.address)
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO wallets (name, seed_phrase, address) VALUES (?, ?, ?)",
                (name, account.key.hex(), normalized_address)
            )
            conn.commit()
        
        return {
            "name": name,
            "address": normalized_address,
            "seed_phrase": account.key.hex()
        }

    def add_wallet(self, name: str, seed_phrase: str) -> bool:
        """Add an existing wallet to the database.
        
        Args:
            name: Wallet name
            seed_phrase: Wallet seed phrase
            
        Returns:
            bool: True if successful, False if name or address already exists
            
        Raises:
            ValueError: If seed phrase is invalid
        """
        try:
            # Create account from seed phrase
            account = Account.from_key(seed_phrase)
            
            # Normalize the address
            normalized_address = self._normalize_address(account.address)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO wallets (name, seed_phrase, address) VALUES (?, ?, ?)",
                    (name, seed_phrase, normalized_address)
                )
                conn.commit()
                return True
        except (sqlite3.IntegrityError, ValueError) as e:
            logger.error(f"Error adding wallet: {e}")
            return False

    def list_wallets(self) -> List[Dict]:
        """List all wallets from the database.
        
        Returns:
            list: List of wallets with id, name, and address
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, address FROM wallets ORDER BY name")
            return [
                {"id": row[0], "name": row[1], "address": row[2]}
                for row in cursor.fetchall()
            ]

    def get_wallet_seed(self, name: str) -> Optional[str]:
        """Get wallet seed phrase by name (for internal use only).
        
        Args:
            name: Wallet name
            
        Returns:
            str: Seed phrase if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seed_phrase FROM wallets WHERE name = ?", (name,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_wallet_by_name(self, name: str) -> Optional[Dict]:
        """Get wallet information by name.
        
        Args:
            name: Wallet name
            
        Returns:
            dict: Wallet information if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, address FROM wallets WHERE name = ?",
                (name,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "address": result[2]
                }
            return None

    def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact from the database.
        
        Args:
            contact_id: ID of the contact to delete
            
        Returns:
            bool: True if contact was deleted, False if not found
            
        Raises:
            ValueError: If contact_id is invalid
        """
        try:
            # Validate contact_id
            if not isinstance(contact_id, int) or contact_id <= 0:
                raise ValueError("Contact ID must be a positive integer")

            # Check if contact exists before deletion
            contact = self.get_contact_by_id(contact_id)
            if not contact:
                logger.warning(f"Contact with ID {contact_id} not found")
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
                conn.commit()
                
                # Verify deletion
                if cursor.rowcount > 0:
                    logger.info(f"Successfully deleted contact: {contact['name']} ({contact['address']})")
                    return True
                else:
                    logger.warning(f"Failed to delete contact with ID {contact_id}")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Database error while deleting contact: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while deleting contact: {e}")
            return False

    def delete_wallet(self, wallet_id: int) -> bool:
        """Delete a wallet from the database.
        
        Args:
            wallet_id: ID of the wallet to delete
            
        Returns:
            bool: True if wallet was deleted, False if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM wallets WHERE id = ?", (wallet_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting wallet: {e}")
            return False

    def get_contact_by_id(self, contact_id: int) -> Optional[Dict]:
        """Get contact information by ID.
        
        Args:
            contact_id: ID of the contact
            
        Returns:
            dict: Contact information if found, None otherwise
            
        Raises:
            ValueError: If contact_id is invalid
        """
        try:
            # Validate contact_id
            if not isinstance(contact_id, int) or contact_id <= 0:
                raise ValueError("Contact ID must be a positive integer")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, address FROM contacts WHERE id = ?",
                    (contact_id,)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        "id": result[0],
                        "name": result[1],
                        "address": result[2]
                    }
                return None
        except sqlite3.Error as e:
            logger.error(f"Database error while fetching contact: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while fetching contact: {e}")
            return None

    def get_wallet_by_id(self, wallet_id: int) -> Optional[Dict]:
        """Get wallet information by ID.
        
        Args:
            wallet_id: ID of the wallet
            
        Returns:
            dict: Wallet information if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, address FROM wallets WHERE id = ?",
                (wallet_id,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "address": result[2]
                }
            return None 