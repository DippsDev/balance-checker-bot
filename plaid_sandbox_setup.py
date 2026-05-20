"""
Plaid Sandbox Setup - Direct Access Token Creation
This bypasses the Link UI for testing purposes in sandbox mode
"""

import os
import json
from pathlib import Path
import plaid
from plaid.api import plaid_api
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from dotenv import load_dotenv

load_dotenv()


def create_sandbox_access_token(account_name: str = "test_account"):
    """
    Create a sandbox access token directly (bypasses Link UI)
    This only works in sandbox environment
    """
    
    client_id = os.getenv('PLAID_CLIENT_ID')
    secret = os.getenv('PLAID_SECRET')
    environment = os.getenv('PLAID_ENV', 'sandbox')
    
    if environment.lower() != 'sandbox':
        print("❌ This method only works in sandbox environment!")
        return None
    
    # Configure Plaid client
    configuration = plaid.Configuration(
        host='https://sandbox.plaid.com',
        api_key={
            'clientId': client_id,
            'secret': secret,
        }
    )
    
    api_client = plaid.ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    
    try:
        # Step 1: Create a sandbox public token
        print("\n🔧 Creating sandbox public token...")
        public_token_request = SandboxPublicTokenCreateRequest(
            institution_id='ins_109508',  # Chase (sandbox)
            initial_products=[Products('auth'), Products('transactions')]
        )
        
        public_token_response = client.sandbox_public_token_create(public_token_request)
        public_token = public_token_response['public_token']
        print(f"✓ Public token created: {public_token}")
        
        # Step 2: Exchange for access token
        print("\n🔄 Exchanging for access token...")
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        
        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']
        
        print(f"✓ Access token obtained!")
        print(f"  Item ID: {item_id}")
        
        # Step 3: Save to tokens file
        tokens_file = Path('plaid_tokens.json')
        tokens = {}
        
        if tokens_file.exists():
            with open(tokens_file, 'r') as f:
                tokens = json.load(f)
        
        from datetime import datetime
        tokens[account_name] = {
            'access_token': access_token,
            'item_id': item_id,
            'added_at': datetime.now().isoformat(),
            'institution': 'Chase (Sandbox)'
        }
        
        with open(tokens_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print(f"\n✅ Successfully created sandbox account: {account_name}")
        print(f"📁 Saved to: {tokens_file}")
        print(f"\nYou can now run: python plaid_balance_monitor.py")
        
        return access_token
        
    except plaid.ApiException as e:
        print(f"\n❌ Error: {e}")
        return None


def create_multiple_sandbox_accounts():
    """Create multiple test accounts with different institutions"""
    
    institutions = [
        ('ins_109508', 'Chase', 'chase_checking'),
        ('ins_109509', 'Bank of America', 'bofa_savings'),
        ('ins_109510', 'Wells Fargo', 'wells_checking'),
    ]
    
    print("\n" + "="*60)
    print("CREATING MULTIPLE SANDBOX ACCOUNTS")
    print("="*60)
    
    for inst_id, inst_name, account_name in institutions:
        print(f"\n📍 Setting up {inst_name}...")
        
        client_id = os.getenv('PLAID_CLIENT_ID')
        secret = os.getenv('PLAID_SECRET')
        
        configuration = plaid.Configuration(
            host='https://sandbox.plaid.com',
            api_key={
                'clientId': client_id,
                'secret': secret,
            }
        )
        
        api_client = plaid.ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)
        
        try:
            # Create public token
            public_token_request = SandboxPublicTokenCreateRequest(
                institution_id=inst_id,
                initial_products=[Products('auth'), Products('transactions')]
            )
            
            public_token_response = client.sandbox_public_token_create(public_token_request)
            public_token = public_token_response['public_token']
            
            # Exchange for access token
            exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
            exchange_response = client.item_public_token_exchange(exchange_request)
            
            access_token = exchange_response['access_token']
            item_id = exchange_response['item_id']
            
            # Save token
            tokens_file = Path('plaid_tokens.json')
            tokens = {}
            
            if tokens_file.exists():
                with open(tokens_file, 'r') as f:
                    tokens = json.load(f)
            
            from datetime import datetime
            tokens[account_name] = {
                'access_token': access_token,
                'item_id': item_id,
                'added_at': datetime.now().isoformat(),
                'institution': inst_name
            }
            
            with open(tokens_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            
            print(f"  ✓ {inst_name} connected as '{account_name}'")
            
        except plaid.ApiException as e:
            print(f"  ❌ Failed to connect {inst_name}: {e}")
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("\nRun: python plaid_balance_monitor.py")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║         PLAID SANDBOX SETUP (BYPASS LINK UI)                 ║
╚══════════════════════════════════════════════════════════════╝

This script creates sandbox access tokens directly without
requiring the Plaid Link UI flow.

⚠️  SANDBOX ONLY - This will not work in production!
    """)
    
    print("\nChoose an option:")
    print("1. Create single test account")
    print("2. Create multiple test accounts (Chase, BofA, Wells Fargo)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        account_name = input("\nEnter account name (e.g., 'my_test_account'): ").strip()
        if not account_name:
            account_name = "test_account"
        create_sandbox_access_token(account_name)
    
    elif choice == '2':
        create_multiple_sandbox_accounts()
    
    else:
        print("Exiting...")
