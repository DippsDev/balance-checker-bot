# Balance Monitoring Bots

This repository contains **two independent balance monitoring bots** for different use cases:

1. **`balance_checker_bot.py`** - Vanilla Gift card balance checker with anti-bot protection bypass
2. **`plaid_balance_monitor.py`** - Bank account balance monitor using Plaid API

## 📋 Table of Contents
- [Bot 1: Vanilla Gift Balance Checker](#bot-1-vanilla-gift-balance-checker)
- [Bot 2: Plaid Bank Balance Monitor](#bot-2-plaid-bank-balance-monitor)
- [Quick Comparison](#quick-comparison)
- [File Structure](#file-structure)

---

## Bot 1: Vanilla Gift Balance Checker

**Purpose:** Check Vanilla Gift card balances via web scraping with anti-bot protection bypass

**File:** `balance_checker_bot.py`

### Features

- ✅ **Advanced TLS fingerprinting** with wreq (JA3/JA4)
- ✅ **HTTP/2 support** like real browsers
- ✅ **27 diverse user agents** (Chrome, Firefox, Edge, Safari)
- ✅ Capsolver integration for CAPTCHA solving
- ✅ Automatic retry logic (3 attempts)
- ✅ Parallel processing (10 concurrent workers)
- ✅ JSON-based proxy configuration
- ✅ Multiple proxy rotation
- ✅ Detailed logging and progress tracking
- ✅ CSV card input / JSON report output

### Setup

### Setup

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Configure Environment
Edit `.env` file:

```env
CAPSOLVER_CLIENT_KEY=your_capsolver_api_key
TARGET_URL=https://balance.vanillagift.com/
CARDS_FILE=cards.csv
PROXY_CONFIG_FILE=proxy_config.json
```

Get Capsolver API key: https://www.capsolver.com

#### 3. Add Cards
Edit `cards.csv`:

```csv
1234567890123456,12,25,123
9876543210987654,06,26,456
```

Format: `card_number,exp_month,exp_year,cvv`

#### 4. Configure Proxies
Edit `proxy_config.json`:

```json
{
  "proxies": [
    {
      "host": "gate.smartproxy.com",
      "port": "7000",
      "user": "your_username",
      "pass": "your_password",
      "enabled": true
    }
  ]
}
```

**Recommended Proxy Providers:**
- [Smartproxy](https://smartproxy.com) - $7.50/GB (best balance)
- [Bright Data](https://brightdata.com) - $10-15/GB (premium)
- [IPRoyal](https://iproyal.com) - $1.75/GB (budget)

### Running

```bash
python balance_checker_bot.py
```

### Output
```
✓ wreq library loaded - Advanced TLS fingerprinting enabled
✓ Capsolver balance: $10.50
✓ Loaded 5 card(s)
✅ SUCCESS: Card ending in 1234 - Balance: $50.00
```

Reports saved to: `reports/balance_check_report_*.json`

---

## Bot 2: Plaid Bank Balance Monitor

**Purpose:** Monitor real bank account balances, track spending, and generate financial reports

**File:** `plaid_balance_monitor.py`

### Features

- ✅ **Multi-account monitoring** - Connect multiple bank accounts
- ✅ **Low balance alerts** - Configurable threshold notifications
- ✅ **Spending analysis** - Track spending by category
- ✅ **Transaction history** - View recent transactions
- ✅ **Daily/Weekly reports** - Comprehensive financial reports
- ✅ **Sandbox testing** - Test with fake data (safe!)
- ✅ **12,000+ institutions** - Works with any major bank

### Setup

### Setup

#### 1. Install Dependencies
```bash
pip install -r requirements_plaid.txt
```

#### 2. Get Plaid API Keys
1. Sign up at [Plaid Dashboard](https://dashboard.plaid.com/signup) (free)
2. Navigate to **Team Settings** → **Keys**
3. Copy your **client_id** and **sandbox secret**

#### 3. Configure Environment
Add to `.env` file:

```env
PLAID_CLIENT_ID=your_plaid_client_id_here
PLAID_SECRET=your_plaid_sandbox_secret_here
PLAID_ENV=sandbox
BALANCE_THRESHOLD=100.0
```

#### 4. Connect a Bank Account

**Option A: Interactive Test Script**
```bash
python test_plaid.py
```
Follow the menu to create link token and connect accounts.

**Option B: Python Script**
```python
from plaid_balance_monitor import PlaidBalanceMonitor

monitor = PlaidBalanceMonitor()

# Step 1: Create link token
link_token = monitor.create_link_token()

# Step 2: Use Plaid Quickstart to complete Link flow
# GitHub: https://github.com/plaid/quickstart

# Step 3: Exchange public token
monitor.exchange_public_token('public-sandbox-xxx', 'my_bank')
```

**Sandbox Test Credentials:**
- Username: `user_good`
- Password: `pass_good`
- 2FA Code: `1234`

### Usage

#### Check Balances
```python
from plaid_balance_monitor import PlaidBalanceMonitor

monitor = PlaidBalanceMonitor()
monitor.check_balances()
```

#### Analyze Spending
```python
monitor.analyze_spending(days=30)
```

#### Generate Reports
```python
monitor.generate_report('daily')   # Daily report
monitor.generate_report('weekly')  # Weekly report
```

#### Get Transactions
```python
transactions = monitor.get_transactions(days=30)
```

### Output Example

```
============================================================
BALANCE CHECK - 2026-05-18 16:30:45
============================================================

Account: Plaid Checking (my_bank)
  Type: depository - checking
  Mask: ****0000
  Current Balance: USD 1,210.45
  Available Balance: USD 1,210.45

Account: Plaid Savings (my_bank)
  Type: depository - savings
  Mask: ****1111
  Current Balance: USD 5,432.10
  Available Balance: USD 5,432.10

============================================================
Total Balance Across All Accounts: $6,642.55
============================================================

SPENDING ANALYSIS - Last 30 Days
============================================================

Total Spent: $2,345.67
Transaction Count: 45

Spending by Category:
------------------------------------------------------------
Food and Drink                  $    567.89 ( 24.2%) - 12 txns
Shopping                        $    432.10 ( 18.4%) - 8 txns
Transportation                  $    321.45 ( 13.7%) - 15 txns
```

Reports saved to: `plaid_reports/`

### Architecture

**Plaid Flow:**
1. Create link token → Initialize Plaid Link
2. User connects bank → Plaid Link UI
3. Get public token → Temporary token
4. Exchange for access token → Permanent token
5. Make API calls → Get balances, transactions

**Key Classes:**
- `PlaidBalanceMonitor` - Main bot class
- Methods:
  - `create_link_token()` - Start connection flow
  - `exchange_public_token()` - Complete connection
  - `check_balances()` - Get account balances
  - `analyze_spending()` - Analyze transactions
  - `generate_report()` - Create comprehensive reports

---

## Quick Comparison

| Feature | balance_checker_bot.py | plaid_balance_monitor.py |
|---------|------------------------|--------------------------|
| **Purpose** | Check gift card balances | Monitor bank accounts |
| **Data Source** | Web scraping | Plaid API |
| **Account Types** | Vanilla Gift cards | Real bank accounts |
| **Institutions** | Vanilla Gift only | 12,000+ banks |
| **Authentication** | Card number + CVV | OAuth (Plaid Link) |
| **CAPTCHA** | Yes (Capsolver) | No |
| **Proxies** | Required | Not needed |
| **Transactions** | No | Yes |
| **Spending Analysis** | No | Yes |
| **Alerts** | No | Yes (low balance) |
| **Reports** | JSON snapshots | Comprehensive JSON |
| **Cost** | Proxy + CAPTCHA fees | Free (Sandbox) |
| **Maintenance** | High (scraping) | Low (stable API) |

**Use Cases:**
- **balance_checker_bot.py** → Check prepaid gift card balances
- **plaid_balance_monitor.py** → Monitor real bank accounts and spending

Both bots are independent and can run simultaneously.

---

## File Structure

```
incapsula-bot/
├── balance_checker_bot.py       # Gift card balance checker
├── plaid_balance_monitor.py     # Bank account monitor
├── test_plaid.py                # Interactive Plaid test script
├── test_wreq.py                 # Test wreq installation
├── cards.csv                    # Gift card data
├── proxy_config.json            # Proxy configuration
├── requirements.txt             # Dependencies for balance_checker_bot
├── requirements_plaid.txt       # Dependencies for plaid_balance_monitor
├── .env                         # Environment variables (both bots)
├── README.md                    # This file
├── reports/                     # Gift card balance reports
│   └── balance_check_report_*.json
└── plaid_reports/               # Bank account reports
    ├── balance_check_*.json
    ├── plaid_daily_report_*.json
    └── plaid_weekly_report_*.json
```

## Environment Variables

```env
# Gift Card Balance Checker (balance_checker_bot.py)
CAPSOLVER_CLIENT_KEY=your_capsolver_api_key
TARGET_URL=https://balance.vanillagift.com/
CARDS_FILE=cards.csv
PROXY_CONFIG_FILE=proxy_config.json
PROXY_HOST=brd.superproxy.io
PROXY_PORT=33335
PROXY_USER=your_proxy_username
PROXY_PASS=your_proxy_password

# Plaid Bank Monitor (plaid_balance_monitor.py)
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox
BALANCE_THRESHOLD=100.0
```

## Quick Start

### Gift Card Balance Checker
```bash
# Install dependencies
pip install -r requirements.txt

# Configure .env with Capsolver key and proxy settings

# Add cards to cards.csv

# Run
python balance_checker_bot.py
```

### Bank Balance Monitor
```bash
# Install dependencies
pip install -r requirements_plaid.txt

# Get Plaid API keys from dashboard.plaid.com

# Configure .env with Plaid credentials

# Run interactive test
python test_plaid.py
```

## Troubleshooting

### Gift Card Bot Issues

**Bot gets blocked:**
- Check Capsolver balance
- Add more residential proxies
- Verify wreq is installed: `python test_wreq.py`

**Proxy connection fails:**
- Verify credentials in `proxy_config.json`
- Test proxy manually
- Try different proxy provider

### Plaid Bot Issues

**"PLAID_CLIENT_ID must be set":**
- Add Plaid credentials to `.env` file

**"No accounts connected":**
- Run `python test_plaid.py`
- Select option 1 to create link token
- Complete Plaid Link flow
- Select option 2 to exchange public token

**Import errors:**
```bash
pip install -r requirements_plaid.txt
```

## Security Notes

⚠️ **Important:**
- Never commit `.env` file (contains API keys)
- Never commit `plaid_tokens.json` (contains access tokens)
- Store card data securely
- Use Sandbox mode for Plaid testing (no real bank data)
- Comply with website Terms of Service
- Use proxies ethically and legally

## API Rate Limits

**Plaid:**
- Sandbox: 100 requests/minute (free, unlimited Items)
- Production: Varies by plan

**Capsolver:**
- Depends on your plan and balance

## Resources

**Plaid:**
- [Plaid Documentation](https://plaid.com/docs/)
- [Plaid Quickstart](https://github.com/plaid/quickstart)
- [Plaid Dashboard](https://dashboard.plaid.com/)
- [Plaid Discord](https://discord.gg/plaid)

**Proxies:**
- [Smartproxy](https://smartproxy.com)
- [Bright Data](https://brightdata.com)
- [IPRoyal](https://iproyal.com)

**CAPTCHA:**
- [Capsolver](https://www.capsolver.com)
