"""
Plaid Bank Balance Monitor Bot
Monitors bank account balances, sends alerts, tracks spending, and generates reports
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import plaid
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PlaidBalanceMonitor:
    """Monitor bank balances using Plaid API"""
    
    def __init__(self):
        """Initialize Plaid client"""
        self.client_id = os.getenv('PLAID_CLIENT_ID')
        self.secret = os.getenv('PLAID_SECRET')
        self.environment = os.getenv('PLAID_ENV', 'sandbox')
        
        if not self.client_id or not self.secret:
            raise ValueError("PLAID_CLIENT_ID and PLAID_SECRET must be set in .env file")
        
        # Configure Plaid client
        configuration = plaid.Configuration(
            host=self._get_plaid_host(),
            api_key={
                'clientId': self.client_id,
                'secret': self.secret,
            }
        )
        
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        
        # Create reports directory
        self.reports_dir = Path('plaid_reports')
        self.reports_dir.mkdir(exist_ok=True)
        
        # Load stored access tokens
        self.tokens_file = Path('plaid_tokens.json')
        self.access_tokens = self._load_tokens()
        
        # Alert thresholds
        self.balance_threshold = float(os.getenv('BALANCE_THRESHOLD', '100.0'))
    
    def _get_plaid_host(self) -> str:
        """Get Plaid API host based on environment"""
        env_map = {
            'sandbox': 'https://sandbox.plaid.com',
            'development': 'https://development.plaid.com',
            'production': 'https://production.plaid.com'
        }
        return env_map.get(self.environment.lower(), 'https://sandbox.plaid.com')
    
    def _load_tokens(self) -> Dict[str, str]:
        """Load stored access tokens"""
        if self.tokens_file.exists():
            with open(self.tokens_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_tokens(self):
        """Save access tokens to file"""
        with open(self.tokens_file, 'w') as f:
            json.dump(self.access_tokens, f, indent=2)
    
    def create_link_token(self, user_id: str = "user-001") -> str:
        """
        Create a link token for Plaid Link initialization
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            link_token string
        """
        try:
            request = LinkTokenCreateRequest(
                products=[Products("auth"), Products("transactions")],
                client_name="Bank Balance Monitor Bot",
                country_codes=[CountryCode('US')],
                language='en',
                user=LinkTokenCreateRequestUser(client_user_id=user_id)
            )
            
            response = self.client.link_token_create(request)
            link_token = response['link_token']
            
            print(f"\n{'='*60}")
            print("LINK TOKEN CREATED SUCCESSFULLY")
            print(f"{'='*60}")
            print(f"\nLink Token: {link_token}")
            print(f"\nTo connect a bank account:")
            print(f"1. Go to: https://cdn.plaid.com/link/v2/stable/link-initialize.js")
            print(f"2. Use this link_token to initialize Plaid Link")
            print(f"3. After successful connection, you'll receive a public_token")
            print(f"4. Exchange the public_token using: exchange_public_token()")
            print(f"\n{'='*60}\n")
            
            return link_token
            
        except plaid.ApiException as e:
            print(f"Error creating link token: {e}")
            return None
    
    def exchange_public_token(self, public_token: str, account_name: str = "default") -> bool:
        """
        Exchange public token for access token
        
        Args:
            public_token: Public token from Plaid Link
            account_name: Name to identify this account
            
        Returns:
            True if successful
        """
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            
            access_token = response['access_token']
            item_id = response['item_id']
            
            self.access_tokens[account_name] = {
                'access_token': access_token,
                'item_id': item_id,
                'added_at': datetime.now().isoformat()
            }
            
            self._save_tokens()
            
            print(f"\n✓ Successfully connected account: {account_name}")
            print(f"  Item ID: {item_id}")
            
            return True
            
        except plaid.ApiException as e:
            print(f"Error exchanging public token: {e}")
            return False
    
    def get_accounts(self, account_name: str = None) -> List[Dict]:
        """
        Get all accounts or accounts for a specific connection
        
        Args:
            account_name: Optional name of specific account connection
            
        Returns:
            List of account dictionaries
        """
        all_accounts = []
        
        tokens_to_check = {}
        if account_name and account_name in self.access_tokens:
            tokens_to_check[account_name] = self.access_tokens[account_name]
        else:
            tokens_to_check = self.access_tokens
        
        for name, token_data in tokens_to_check.items():
            try:
                request = AccountsGetRequest(access_token=token_data['access_token'])
                response = self.client.accounts_get(request)
                
                for account in response['accounts']:
                    all_accounts.append({
                        'connection_name': name,
                        'account_id': account['account_id'],
                        'name': account['name'],
                        'official_name': account.get('official_name', ''),
                        'type': str(account['type']),  # Convert to string
                        'subtype': str(account['subtype']) if account['subtype'] else None,  # Convert to string
                        'mask': account['mask'],
                        'balances': {
                            'current': account['balances']['current'],
                            'available': account['balances']['available'],
                            'currency': account['balances']['iso_currency_code']
                        }
                    })
                    
            except plaid.ApiException as e:
                print(f"Error getting accounts for {name}: {e}")
        
        return all_accounts
    
    def check_balances(self) -> Dict:
        """
        Check all account balances and generate alerts
        
        Returns:
            Dictionary with balance information and alerts
        """
        print(f"\n{'='*60}")
        print(f"BALANCE CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        accounts = self.get_accounts()
        alerts = []
        total_balance = 0
        
        if not accounts:
            print("⚠ No accounts connected. Use create_link_token() to connect accounts.")
            return {'accounts': [], 'alerts': [], 'total_balance': 0}
        
        for account in accounts:
            balances = account['balances']
            current = balances['current'] or 0
            available = balances['available'] or 0
            currency = balances['currency'] or 'USD'
            
            print(f"Account: {account['name']} ({account['connection_name']})")
            print(f"  Type: {account['type']} - {account['subtype']}")
            print(f"  Mask: ****{account['mask']}")
            print(f"  Current Balance: {currency} {current:,.2f}")
            print(f"  Available Balance: {currency} {available:,.2f}")
            
            # Check for low balance alert
            if available and available < self.balance_threshold:
                alert = {
                    'type': 'LOW_BALANCE',
                    'account': account['name'],
                    'balance': available,
                    'threshold': self.balance_threshold,
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert)
                print(f"  ⚠ ALERT: Balance below threshold (${self.balance_threshold})")
            
            print()
            total_balance += current
        
        print(f"{'='*60}")
        print(f"Total Balance Across All Accounts: ${total_balance:,.2f}")
        print(f"{'='*60}\n")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'accounts': accounts,
            'alerts': alerts,
            'total_balance': total_balance
        }
        
        # Save report
        self._save_balance_report(result)
        
        return result
    
    def get_transactions(self, days: int = 30, account_name: str = None) -> List[Dict]:
        """
        Get recent transactions for spending analysis
        
        Args:
            days: Number of days to look back
            account_name: Optional specific account connection
            
        Returns:
            List of transaction dictionaries
        """
        all_transactions = []
        start_date = (datetime.now() - timedelta(days=days)).date()
        end_date = datetime.now().date()
        
        tokens_to_check = {}
        if account_name and account_name in self.access_tokens:
            tokens_to_check[account_name] = self.access_tokens[account_name]
        else:
            tokens_to_check = self.access_tokens
        
        for name, token_data in tokens_to_check.items():
            try:
                request = TransactionsGetRequest(
                    access_token=token_data['access_token'],
                    start_date=start_date,
                    end_date=end_date
                )
                response = self.client.transactions_get(request)
                
                for txn in response['transactions']:
                    all_transactions.append({
                        'connection_name': name,
                        'date': str(txn['date']),
                        'name': txn['name'],
                        'amount': txn['amount'],
                        'category': txn.get('category', []),
                        'pending': txn['pending'],
                        'account_id': txn['account_id']
                    })
                    
            except plaid.ApiException as e:
                print(f"Error getting transactions for {name}: {e}")
        
        return sorted(all_transactions, key=lambda x: x['date'], reverse=True)
    
    def analyze_spending(self, days: int = 30) -> Dict:
        """
        Analyze spending patterns
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with spending analysis
        """
        print(f"\n{'='*60}")
        print(f"SPENDING ANALYSIS - Last {days} Days")
        print(f"{'='*60}\n")
        
        transactions = self.get_transactions(days=days)
        
        if not transactions:
            print("No transactions found.")
            return {'total_spent': 0, 'by_category': {}, 'transaction_count': 0}
        
        total_spent = 0
        by_category = {}
        
        for txn in transactions:
            # Positive amounts are debits (money spent)
            if txn['amount'] > 0:
                total_spent += txn['amount']
                
                # Categorize
                categories = txn.get('category', ['Uncategorized'])
                main_category = categories[0] if categories else 'Uncategorized'
                
                if main_category not in by_category:
                    by_category[main_category] = {'amount': 0, 'count': 0}
                
                by_category[main_category]['amount'] += txn['amount']
                by_category[main_category]['count'] += 1
        
        print(f"Total Spent: ${total_spent:,.2f}")
        print(f"Transaction Count: {len(transactions)}")
        print(f"\nSpending by Category:")
        print(f"{'-'*60}")
        
        for category, data in sorted(by_category.items(), key=lambda x: x[1]['amount'], reverse=True):
            percentage = (data['amount'] / total_spent * 100) if total_spent > 0 else 0
            print(f"{category:30s} ${data['amount']:>10,.2f} ({percentage:>5.1f}%) - {data['count']} txns")
        
        print(f"{'='*60}\n")
        
        analysis = {
            'period_days': days,
            'total_spent': total_spent,
            'transaction_count': len(transactions),
            'by_category': by_category,
            'timestamp': datetime.now().isoformat()
        }
        
        return analysis
    
    def generate_report(self, report_type: str = 'daily') -> Dict:
        """
        Generate comprehensive balance and spending report
        
        Args:
            report_type: 'daily' or 'weekly'
            
        Returns:
            Complete report dictionary
        """
        days = 1 if report_type == 'daily' else 7
        
        print(f"\n{'='*60}")
        print(f"GENERATING {report_type.upper()} REPORT")
        print(f"{'='*60}\n")
        
        balance_info = self.check_balances()
        spending_info = self.analyze_spending(days=days)
        
        report = {
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'balances': balance_info,
            'spending': spending_info
        }
        
        # Save report
        filename = f"plaid_{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Report saved to: {filepath}\n")
        
        return report
    
    def _save_balance_report(self, data: Dict):
        """Save balance check report"""
        filename = f"balance_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def list_connected_accounts(self):
        """List all connected account connections"""
        print(f"\n{'='*60}")
        print("CONNECTED ACCOUNTS")
        print(f"{'='*60}\n")
        
        if not self.access_tokens:
            print("No accounts connected yet.")
            print("\nTo connect an account:")
            print("1. Run: monitor.create_link_token()")
            print("2. Use the link token with Plaid Link")
            print("3. Exchange the public token: monitor.exchange_public_token(public_token, 'account_name')")
        else:
            for name, data in self.access_tokens.items():
                print(f"Connection: {name}")
                print(f"  Item ID: {data['item_id']}")
                print(f"  Added: {data['added_at']}")
                print()
        
        print(f"{'='*60}\n")


def main():
    """Main function with example usage"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         PLAID BANK BALANCE MONITOR BOT                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        monitor = PlaidBalanceMonitor()
        
        print("\n📋 SETUP INSTRUCTIONS:")
        print("="*60)
        print("1. Add to your .env file:")
        print("   PLAID_CLIENT_ID=your_client_id")
        print("   PLAID_SECRET=your_sandbox_secret")
        print("   PLAID_ENV=sandbox")
        print("   BALANCE_THRESHOLD=100.0")
        print()
        print("2. Connect a bank account (Sandbox mode):")
        print("   - Run this script")
        print("   - Use create_link_token() to get a link token")
        print("   - Visit Plaid Quickstart to complete Link flow")
        print("   - Exchange public token with exchange_public_token()")
        print()
        print("3. For Sandbox testing, use these credentials:")
        print("   Username: user_good")
        print("   Password: pass_good")
        print("="*60)
        
        # Show connected accounts
        monitor.list_connected_accounts()
        
        # If accounts are connected, run checks
        if monitor.access_tokens:
            print("\n🔍 Running balance check...")
            monitor.check_balances()
            
            print("\n📊 Analyzing spending patterns...")
            monitor.analyze_spending(days=30)
            
            print("\n📄 Generating daily report...")
            monitor.generate_report('daily')
        else:
            print("\n💡 QUICK START:")
            print("="*60)
            print("Run these commands in Python:")
            print()
            print("from plaid_balance_monitor import PlaidBalanceMonitor")
            print("monitor = PlaidBalanceMonitor()")
            print("link_token = monitor.create_link_token()")
            print()
            print("# After completing Plaid Link flow with the link_token:")
            print("monitor.exchange_public_token('public-sandbox-xxx', 'my_bank')")
            print("monitor.check_balances()")
            print("="*60)
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease add the following to your .env file:")
        print("PLAID_CLIENT_ID=your_client_id")
        print("PLAID_SECRET=your_sandbox_secret")
        print("PLAID_ENV=sandbox")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
