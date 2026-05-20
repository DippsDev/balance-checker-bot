"""
Test script for Plaid Balance Monitor Bot
Run this to test the bot functionality
"""

from plaid_balance_monitor import PlaidBalanceMonitor
import sys


def print_menu():
    """Display interactive menu"""
    print("\n" + "="*60)
    print("PLAID BALANCE MONITOR - TEST MENU")
    print("="*60)
    print("1. Create Link Token (Step 1 of connecting account)")
    print("2. Exchange Public Token (Step 2 of connecting account)")
    print("3. List Connected Accounts")
    print("4. Check All Balances")
    print("5. Analyze Spending (Last 30 Days)")
    print("6. Generate Daily Report")
    print("7. Generate Weekly Report")
    print("8. Get Recent Transactions")
    print("9. Exit")
    print("="*60)


def main():
    """Main test function"""
    try:
        monitor = PlaidBalanceMonitor()
        print("\n✓ Plaid Balance Monitor initialized successfully!")
        
        while True:
            print_menu()
            choice = input("\nEnter your choice (1-9): ").strip()
            
            if choice == '1':
                print("\n📝 Creating Link Token...")
                user_id = input("Enter user ID (or press Enter for default 'user-001'): ").strip() or "user-001"
                link_token = monitor.create_link_token(user_id)
                
                if link_token:
                    print("\n" + "="*60)
                    print("NEXT STEPS:")
                    print("="*60)
                    print("1. Use the Plaid Quickstart app to complete the Link flow")
                    print("   GitHub: https://github.com/plaid/quickstart")
                    print()
                    print("2. Or use Plaid's Link demo:")
                    print("   https://plaid.com/docs/link/")
                    print()
                    print("3. After completing Link, you'll receive a public_token")
                    print("4. Come back here and select option 2 to exchange it")
                    print("="*60)
            
            elif choice == '2':
                print("\n🔄 Exchange Public Token...")
                public_token = input("Enter your public_token: ").strip()
                
                if not public_token:
                    print("❌ Public token cannot be empty")
                    continue
                
                account_name = input("Enter a name for this account (e.g., 'chase_checking'): ").strip()
                
                if not account_name:
                    account_name = "default"
                
                success = monitor.exchange_public_token(public_token, account_name)
                
                if success:
                    print("\n✓ Account connected successfully!")
                    print("You can now check balances and analyze spending.")
            
            elif choice == '3':
                monitor.list_connected_accounts()
            
            elif choice == '4':
                if not monitor.access_tokens:
                    print("\n⚠ No accounts connected yet.")
                    print("Please connect an account first (options 1-2)")
                else:
                    monitor.check_balances()
            
            elif choice == '5':
                if not monitor.access_tokens:
                    print("\n⚠ No accounts connected yet.")
                    print("Please connect an account first (options 1-2)")
                else:
                    days = input("Enter number of days to analyze (default 30): ").strip()
                    days = int(days) if days.isdigit() else 30
                    monitor.analyze_spending(days=days)
            
            elif choice == '6':
                if not monitor.access_tokens:
                    print("\n⚠ No accounts connected yet.")
                    print("Please connect an account first (options 1-2)")
                else:
                    monitor.generate_report('daily')
            
            elif choice == '7':
                if not monitor.access_tokens:
                    print("\n⚠ No accounts connected yet.")
                    print("Please connect an account first (options 1-2)")
                else:
                    monitor.generate_report('weekly')
            
            elif choice == '8':
                if not monitor.access_tokens:
                    print("\n⚠ No accounts connected yet.")
                    print("Please connect an account first (options 1-2)")
                else:
                    days = input("Enter number of days (default 30): ").strip()
                    days = int(days) if days.isdigit() else 30
                    
                    transactions = monitor.get_transactions(days=days)
                    
                    print(f"\n{'='*60}")
                    print(f"RECENT TRANSACTIONS - Last {days} Days")
                    print(f"{'='*60}\n")
                    
                    if not transactions:
                        print("No transactions found.")
                    else:
                        for i, txn in enumerate(transactions[:20], 1):  # Show first 20
                            status = "PENDING" if txn['pending'] else "POSTED"
                            print(f"{i}. {txn['date']} - {txn['name']}")
                            print(f"   Amount: ${txn['amount']:.2f} ({status})")
                            if txn['category']:
                                print(f"   Category: {', '.join(txn['category'])}")
                            print()
                        
                        if len(transactions) > 20:
                            print(f"... and {len(transactions) - 20} more transactions")
                    
                    print(f"{'='*60}\n")
            
            elif choice == '9':
                print("\n👋 Goodbye!")
                sys.exit(0)
            
            else:
                print("\n❌ Invalid choice. Please enter a number between 1-9.")
            
            input("\nPress Enter to continue...")
    
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease add the following to your .env file:")
        print("PLAID_CLIENT_ID=your_client_id")
        print("PLAID_SECRET=your_sandbox_secret")
        print("PLAID_ENV=sandbox")
        print("BALANCE_THRESHOLD=100.0")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║         PLAID BALANCE MONITOR - TEST SCRIPT                  ║
║                                                              ║
║  This script helps you test the Plaid Balance Monitor Bot   ║
║                                                              ║
║  REQUIREMENTS:                                               ║
║  1. Plaid API keys in .env file                             ║
║  2. pip install -r requirements_plaid.txt                   ║
║                                                              ║
║  SANDBOX CREDENTIALS:                                        ║
║  Username: user_good                                         ║
║  Password: pass_good                                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    main()
