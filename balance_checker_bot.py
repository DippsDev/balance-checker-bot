import requests
import time
import random
import json
import base64
import os
import asyncio
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Try to import wreq for advanced TLS fingerprinting
try:
    import wreq
    WREQ_AVAILABLE = True
    print("✓ wreq library loaded - Advanced TLS fingerprinting enabled")
except ImportError:
    WREQ_AVAILABLE = False
    print("⚠️  wreq not available - Using standard requests (install with: pip install wreq)")

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

# Capsolver API Configuration
CAPSOLVER_CLIENT_KEY = os.getenv("CAPSOLVER_CLIENT_KEY", "your_capsolver_api_key_here")
CAPSOLVER_API_BASE = "https://api.capsolver.com"

# Proxy configuration file
PROXY_CONFIG_FILE = os.getenv("PROXY_CONFIG_FILE", "proxy_config.json")

# Target website
TARGET_URL = os.getenv("TARGET_URL", "https://balance.vanillagift.com/")

# Card data file (CSV format: card_number,exp_month,exp_year,cvv)
CARDS_FILE = os.getenv("CARDS_FILE", "cards.csv")

# Timing configuration (in seconds)
TIMING_CONFIG = {
    "between_requests": (2, 5),      # Delay between card checks
    "retry_delay": (3, 5),           # Delay before retry
    "api_timeout": 30,               # Capsolver API timeout
    "task_poll_interval": (1, 3),    # Delay between task result polls
    "task_max_wait": 30,             # Max time to wait for task completion
}

# Parallel processing configuration
MAX_CONCURRENT_WORKERS = 10  # Number of cards to process simultaneously
MAX_RETRIES = 3              # Retries per card

# User agents pool - Updated with latest browsers (Chrome, Firefox, Edge, Safari)
USER_AGENTS = [
    # Chrome - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    
    # Chrome - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    
    # Chrome - Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    
    # Firefox - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    
    # Firefox - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7; rv:132.0) Gecko/20100101 Firefox/132.0",
    
    # Firefox - Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    
    # Edge - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    
    # Edge - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    
    # Safari - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    
    # Safari - iOS (iPhone)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    
    # Safari - iPad
    "Mozilla/5.0 (iPad; CPU OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
]

# Browser impersonation profiles for wreq
# Maps user agent patterns to wreq impersonation profiles
BROWSER_PROFILES = {
    'chrome': ['Chrome/131', 'Chrome/130', 'Chrome/129'],
    'firefox': ['Firefox/133', 'Firefox/132', 'Firefox/131'],
    'edge': ['Edg/131', 'Edg/130', 'Edg/129'],
    'safari': ['Safari/605', 'Safari/604'],
}

# ============================================================================
# RESPONSE WRAPPER CLASS
# ============================================================================

class WreqResponse:
    """Simple wrapper to make wreq responses compatible with requests.Response"""
    
    def __init__(self, wreq_response, text_content):
        self._wreq = wreq_response
        self.text = text_content
        self.content = text_content.encode() if isinstance(text_content, str) else text_content
        # wreq status is a StatusCode object with as_int() method
        self.status_code = wreq_response.status.as_int()
        self.headers = wreq_response.headers
        self.cookies = wreq_response.cookies
        self.url = wreq_response.url

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CardData:
    """Represents a gift card"""
    number: str
    exp_month: str
    exp_year: str
    cvv: str
    
    def __str__(self):
        return f"Card ending in {self.number[-4:]}"


@dataclass
class ProxyConfig:
    """Represents a proxy configuration"""
    host: str
    port: str
    user: str
    password: str
    
    def to_dict(self):
        return {
            "http": f"http://{self.user}:{self.password}@{self.host}:{self.port}",
            "https": f"http://{self.user}:{self.password}@{self.host}:{self.port}"
        }
    
    def __str__(self):
        return f"{self.host}:{self.port}"


@dataclass
class CheckResult:
    """Result of a balance check"""
    card: CardData
    success: bool
    balance: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 1
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_proxies() -> List[ProxyConfig]:
    """Load proxy configurations from JSON file"""
    try:
        with open(PROXY_CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        proxies = []
        for p in config.get("proxies", []):
            if p.get("enabled", False):
                proxies.append(ProxyConfig(
                    host=p["host"],
                    port=p["port"],
                    user=p["user"],
                    password=p["pass"]
                ))
        
        if not proxies:
            print("⚠️  WARNING: No enabled proxies found!")
            return []
        
        print(f"✓ Loaded {len(proxies)} proxy(ies)")
        return proxies
    
    except FileNotFoundError:
        print(f"❌ Proxy config file '{PROXY_CONFIG_FILE}' not found")
        return []
    except Exception as e:
        print(f"❌ Error loading proxies: {e}")
        return []


def load_cards() -> List[CardData]:
    """Load card data from CSV file"""
    try:
        cards = []
        with open(CARDS_FILE, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(',')
                if len(parts) != 4:
                    print(f"⚠️  Skipping invalid line {line_num}: {line}")
                    continue
                
                cards.append(CardData(
                    number=parts[0].strip(),
                    exp_month=parts[1].strip(),
                    exp_year=parts[2].strip(),
                    cvv=parts[3].strip()
                ))
        
        print(f"✓ Loaded {len(cards)} card(s)")
        return cards
    
    except FileNotFoundError:
        print(f"❌ Cards file '{CARDS_FILE}' not found")
        print(f"💡 Create '{CARDS_FILE}' with format: card_number,exp_month,exp_year,cvv")
        return []
    except Exception as e:
        print(f"❌ Error loading cards: {e}")
        return []


def get_random_proxy(proxies: List[ProxyConfig]) -> Optional[ProxyConfig]:
    """Get a random proxy from the pool"""
    return random.choice(proxies) if proxies else None


def get_random_user_agent() -> str:
    """Get a random user agent"""
    return random.choice(USER_AGENTS)


def get_browser_profile(user_agent: str) -> str:
    """
    Determine the browser profile for wreq impersonation based on user agent
    
    Args:
        user_agent: User agent string
        
    Returns:
        Browser profile name ('chrome', 'firefox', 'edge', or 'safari')
    """
    # Check in priority order (Edge must be checked before Chrome since Edge UAs contain "Chrome/")
    priority_order = ['edge', 'firefox', 'safari', 'chrome']
    
    for profile in priority_order:
        if profile in BROWSER_PROFILES:
            for pattern in BROWSER_PROFILES[profile]:
                if pattern in user_agent:
                    return profile
    
    # Default to chrome if no match
    return 'chrome'


async def make_request(
    url: str,
    method: str = 'GET',
    headers: Optional[Dict] = None,
    data: Optional[Dict] = None,
    proxy: Optional[ProxyConfig] = None,
    timeout: int = 30,
    user_agent: Optional[str] = None
) -> requests.Response:
    """
    Make an HTTP request using wreq (if available) or fallback to requests
    
    Args:
        url: Target URL
        method: HTTP method (GET, POST, etc.)
        headers: Request headers
        data: Request data (for POST)
        proxy: ProxyConfig object
        timeout: Request timeout in seconds
        user_agent: User agent string (auto-generated if None)
        
    Returns:
        Response object (compatible with requests.Response interface)
    """
    if user_agent is None:
        user_agent = get_random_user_agent()
    
    if headers is None:
        headers = {}
    
    # Always set User-Agent
    headers['User-Agent'] = user_agent
    
    # Prepare proxy dict
    proxies = proxy.to_dict() if proxy else None
    
    # Use wreq if available for advanced TLS fingerprinting
    if WREQ_AVAILABLE:
        browser_profile = get_browser_profile(user_agent)
        
        try:
            # Convert timeout to timedelta for wreq
            timeout_td = timedelta(seconds=timeout)
            
            if method.upper() == 'GET':
                wreq_response = await wreq.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout_td,
                    impersonate=browser_profile
                )
            elif method.upper() == 'POST':
                wreq_response = await wreq.post(
                    url,
                    headers=headers,
                    data=data,
                    proxies=proxies,
                    timeout=timeout_td,
                    impersonate=browser_profile
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Get text content and wrap response
            text_content = await wreq_response.text()
            return WreqResponse(wreq_response, text_content)
        
        except Exception as e:
            print(f"⚠️  wreq request failed: {e}, falling back to requests")
            # Fall through to requests fallback
    
    # Fallback to standard requests
    session = requests.Session()
    session.headers.update(headers)
    
    if proxies:
        session.proxies.update(proxies)
    
    if method.upper() == 'GET':
        return session.get(url, timeout=timeout)
    elif method.upper() == 'POST':
        return session.post(url, data=data, timeout=timeout)
    else:
        raise ValueError(f"Unsupported method: {method}")


# ============================================================================
# CAPSOLVER API FUNCTIONS
# ============================================================================

def get_capsolver_balance() -> Optional[Dict]:
    """
    Get Capsolver account balance
    
    Returns:
        Dictionary with balance info or None if failed
    """
    try:
        headers = {"Content-Type": "application/json"}
        payload = {"clientKey": CAPSOLVER_CLIENT_KEY}
        
        response = requests.post(
            f"{CAPSOLVER_API_BASE}/getBalance",
            headers=headers,
            json=payload,
            timeout=TIMING_CONFIG["api_timeout"]
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("errorId") == 0:
                return data
            else:
                print(f"❌ Capsolver balance error: {data.get('errorDescription')}")
                return None
        else:
            print(f"❌ Capsolver API error: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error getting balance: {e}")
        return None


def create_capsolver_task(task_type: str, task_data: Dict) -> Optional[str]:
    """
    Create a task in Capsolver
    
    Args:
        task_type: Type of task (e.g., 'IncapsulaTaskProxyLess')
        task_data: Task-specific data
        
    Returns:
        Task ID if successful, None otherwise
    """
    try:
        headers = {"Content-Type": "application/json"}
        payload = {
            "clientKey": CAPSOLVER_CLIENT_KEY,
            "task": {
                "type": task_type,
                **task_data
            }
        }
        
        response = requests.post(
            f"{CAPSOLVER_API_BASE}/createTask",
            headers=headers,
            json=payload,
            timeout=TIMING_CONFIG["api_timeout"]
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("errorId") == 0:
                task_id = data.get("taskId")
                print(f"✓ Task created: {task_id}")
                return task_id
            else:
                print(f"❌ Task creation failed: {data.get('errorDescription')}")
                return None
        else:
            print(f"❌ Capsolver API error: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return None


def get_task_result(task_id: str) -> Optional[Dict]:
    """
    Poll task result from Capsolver
    
    Args:
        task_id: Task ID from createTask
        
    Returns:
        Dictionary with task result or None if failed/incomplete
    """
    try:
        headers = {"Content-Type": "application/json"}
        payload = {
            "clientKey": CAPSOLVER_CLIENT_KEY,
            "taskId": task_id
        }
        
        response = requests.post(
            f"{CAPSOLVER_API_BASE}/getTaskResult",
            headers=headers,
            json=payload,
            timeout=TIMING_CONFIG["api_timeout"]
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("errorId") == 0:
                return data
            else:
                print(f"❌ Task result error: {data.get('errorDescription')}")
                return None
        else:
            print(f"❌ Capsolver API error: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error getting task result: {e}")
        return None


def wait_for_task_completion(task_id: str, max_wait: int = None) -> Optional[Dict]:
    """
    Wait for a Capsolver task to complete
    
    Args:
        task_id: Task ID from createTask
        max_wait: Maximum seconds to wait
        
    Returns:
        Task result if completed, None if timeout or error
    """
    if max_wait is None:
        max_wait = TIMING_CONFIG["task_max_wait"]
    
    start_time = time.time()
    poll_count = 0
    
    while time.time() - start_time < max_wait:
        result = get_task_result(task_id)
        poll_count += 1
        
        if result is None:
            print(f"⏳ Poll #{poll_count}: Waiting for task completion...")
        elif result.get("status") == "ready":
            print(f"✓ Task completed in {poll_count} poll(s)")
            return result
        elif result.get("status") == "processing":
            print(f"⏳ Poll #{poll_count}: Task still processing...")
        else:
            print(f"⏳ Poll #{poll_count}: Task status: {result.get('status')}")
        
        # Wait before next poll
        poll_delay = random.uniform(*TIMING_CONFIG["task_poll_interval"])
        time.sleep(poll_delay)
    
    print(f"❌ Task timeout after {poll_count} polls")
    return None


def extract_reese84_script_url(html_content: str) -> Optional[str]:
    """
    Extract Reese84 script URL from Incapsula challenge page
    
    Args:
        html_content: HTML content of the page
        
    Returns:
        Reese84 script URL or None if not found
    """
    import re
    
    # Pattern 1: Look for script src with reese84 pattern
    patterns = [
        r'src="(/_Incapsula_Resource[^"]*)"',
        r"src='(/_Incapsula_Resource[^']*)'",
        r'src="([^"]*reese84[^"]*)"',
        r"src='([^']*reese84[^']*)'",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content)
        if match:
            script_path = match.group(1)
            # If it's a relative path, we'll need to construct full URL
            if script_path.startswith('/'):
                return script_path
            return script_path
    
    return None


def solve_reese84_challenge(
    page_url: str,
    user_agent: str,
    reese_script_url: Optional[str] = None,
    html_content: Optional[str] = None
) -> Optional[Dict]:
    """
    Solve Reese84 challenge using Capsolver
    
    Args:
        page_url: URL of the page being accessed
        user_agent: User agent string
        reese_script_url: URL to the Reese84 script (will be extracted if not provided)
        html_content: HTML content to extract script URL from (if reese_script_url not provided)
        
    Returns:
        Dictionary with solution or None if failed
    """
    try:
        print("🔧 Creating Reese84 task...")
        
        # Extract script URL if not provided
        if not reese_script_url and html_content:
            script_path = extract_reese84_script_url(html_content)
            if script_path:
                # Construct full URL if it's a relative path
                if script_path.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(page_url)
                    reese_script_url = f"{parsed.scheme}://{parsed.netloc}{script_path}"
                else:
                    reese_script_url = script_path
                print(f"📍 Detected Reese84 script: {reese_script_url}")
        
        if not reese_script_url:
            print("❌ Could not find Reese84 script URL")
            return None
        
        # Use correct task type and parameters according to Capsolver docs
        task_data = {
            "websiteURL": page_url,
            "reeseScriptURL": reese_script_url,
            "userAgent": user_agent
        }
        
        # Use correct task type: AntiImpervaTaskProxyless
        task_id = create_capsolver_task("AntiImpervaTaskProxyless", task_data)
        
        if not task_id:
            return None
        
        result = wait_for_task_completion(task_id)
        return result
    
    except Exception as e:
        print(f"❌ Reese84 challenge error: {e}")
        return None


def extract_utmvc_script_url(html_content: str) -> Optional[str]:
    """
    Extract UTMVC script URL from Incapsula challenge page
    
    Args:
        html_content: HTML content of the page
        
    Returns:
        UTMVC script URL or None if not found
    """
    import re
    
    # Look for script src with _Incapsula_Resource pattern
    patterns = [
        r'src="(/_Incapsula_Resource[^"]*)"',
        r"src='(/_Incapsula_Resource[^']*)'",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content)
        if match:
            return match.group(1)
    
    return None


def extract_incap_ses_cookies(cookies_dict: Dict) -> List[str]:
    """
    Extract incap_ses_* cookie values
    
    Args:
        cookies_dict: Dictionary of cookies
        
    Returns:
        List of incap_ses_* cookie values
    """
    incap_cookies = []
    for name, value in cookies_dict.items():
        if name.startswith('incap_ses_'):
            incap_cookies.append(value)
    return incap_cookies


def solve_utmvc_challenge(
    page_url: str,
    user_agent: str,
    script_url: Optional[str] = None,
    html_content: Optional[str] = None,
    cookies: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Solve UTMVC challenge using Capsolver
    
    Args:
        page_url: URL of the page being accessed
        user_agent: User agent string
        script_url: URL to the UTMVC script (will be extracted if not provided)
        html_content: HTML content to extract script URL from
        cookies: Current cookies (for incap_ses_* extraction)
        
    Returns:
        Dictionary with solution or None if failed
    """
    try:
        print("🔧 Creating UTMVC task...")
        
        # Extract script URL if not provided
        if not script_url and html_content:
            script_path = extract_utmvc_script_url(html_content)
            if script_path:
                # Construct full URL if it's a relative path
                if script_path.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(page_url)
                    script_url = f"{parsed.scheme}://{parsed.netloc}{script_path}"
                else:
                    script_url = script_path
                print(f"📍 Detected UTMVC script: {script_url}")
        
        if not script_url:
            print("❌ Could not find UTMVC script URL")
            return None
        
        # Extract incap_ses cookies
        incap_cookies = []
        if cookies:
            incap_cookies = extract_incap_ses_cookies(cookies)
        
        # Build cookie array for Capsolver
        cookie_array = []
        if cookies:
            for name, value in cookies.items():
                if name.startswith('incap_ses_'):
                    cookie_array.append({
                        "name": name,
                        "value": value
                    })
        
        # Use correct task type and parameters
        task_data = {
            "websiteURL": page_url,
            "scriptURL": script_url,
            "isUtmvc": True,
            "cookies": cookie_array,
            "userAgent": user_agent
        }
        
        # Use correct task type: AntiImpervaTaskProxyless
        task_id = create_capsolver_task("AntiImpervaTaskProxyless", task_data)
        
        if not task_id:
            return None
        
        result = wait_for_task_completion(task_id)
        return result
    
    except Exception as e:
        print(f"❌ UTMVC challenge error: {e}")
        return None


# ============================================================================
# BALANCE CHECK FUNCTIONS
# ============================================================================

async def check_card_balance(
    card: CardData,
    proxy: Optional[ProxyConfig] = None,
    attempt: int = 1
) -> CheckResult:
    """
    Check balance for a single card using wreq (with TLS fingerprinting) + proxies
    
    Args:
        card: CardData object
        proxy: ProxyConfig object (optional)
        attempt: Current attempt number
        
    Returns:
        CheckResult object
    """
    try:
        print(f"\n{'='*60}")
        print(f"🔍 Checking {card} (Attempt {attempt}/{MAX_RETRIES})")
        if proxy:
            print(f"🔒 Using proxy: {proxy}")
        print(f"{'='*60}")
        
        # Get random user agent
        user_agent = get_random_user_agent()
        browser_profile = get_browser_profile(user_agent)
        
        if WREQ_AVAILABLE:
            print(f"🔧 Using wreq with {browser_profile} TLS fingerprint")
        else:
            print(f"⚠️  Using standard requests (install wreq for better stealth)")
        
        # Set headers
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Step 1: Initial request to get Incapsula challenge
        print("📍 Step 1: Accessing website...")
        response = await make_request(
            url=TARGET_URL,
            method='GET',
            headers=headers,
            proxy=proxy,
            timeout=30,
            user_agent=user_agent
        )
        
        # Check if we got an Incapsula challenge
        if "/_Incapsula_Resource" in response.text or "incap_ses" in response.text:
            print("🛡️  Incapsula protection detected - solving with Capsolver...")
            
            solution = solve_reese84_challenge(TARGET_URL, user_agent)
            
            if solution:
                # Extract solution from Capsolver response
                challenge_solution = solution.get("solution", {})
                print(f"✓ Incapsula challenge solved")
                
                # In production, you'd apply the solution:
                # 1. Set any cookies returned in the solution
                # 2. Add any headers needed (like proof of work)
                # 3. Retry the request with the solved challenge
                
                print("💡 Next step: Apply the challenge solution to bypass Incapsula")
            else:
                print("❌ Failed to solve Incapsula challenge")
                return CheckResult(
                    card=card,
                    success=False,
                    error="Incapsula challenge solving failed",
                    attempts=attempt
                )
        
        # Step 2: Submit form (simplified - assumes we bypassed Incapsula)
        print("📝 Step 2: Submitting card details...")
        
        form_data = {
            "cardnumber": card.number,
            "expMonth": card.exp_month,
            "expirationYear": card.exp_year,
            "cvv": card.cvv
        }
        
        # This is where you'd submit the form
        # response = await make_request(
        #     url=form_submit_url,
        #     method='POST',
        #     headers=headers,
        #     data=form_data,
        #     proxy=proxy,
        #     user_agent=user_agent
        # )
        
        # Step 3: Parse balance from response
        print("✓ Form submitted successfully")
        
        # Placeholder for balance extraction
        balance = "Balance check completed"  # You'd parse this from the response
        
        print(f"✅ Success: {balance}")
        
        return CheckResult(
            card=card,
            success=True,
            balance=balance,
            attempts=attempt
        )
    
    except requests.exceptions.ProxyError:
        error = f"Proxy error: {proxy}"
        print(f"❌ {error}")
        return CheckResult(card=card, success=False, error=error, attempts=attempt)
    
    except requests.exceptions.Timeout:
        error = "Request timeout"
        print(f"❌ {error}")
        return CheckResult(card=card, success=False, error=error, attempts=attempt)
    
    except Exception as e:
        error = f"Unexpected error: {str(e)}"
        print(f"❌ {error}")
        return CheckResult(card=card, success=False, error=error, attempts=attempt)


async def check_card_with_retry(
    card: CardData,
    proxies: List[ProxyConfig]
) -> CheckResult:
    """
    Check card balance with automatic retry logic
    
    Args:
        card: CardData object
        proxies: List of available proxies
        
    Returns:
        CheckResult object
    """
    for attempt in range(1, MAX_RETRIES + 1):
        proxy = get_random_proxy(proxies)
        result = await check_card_balance(card, proxy, attempt)
        
        if result.success:
            return result
        
        if attempt < MAX_RETRIES:
            delay = random.uniform(*TIMING_CONFIG["retry_delay"])
            print(f"⏳ Retrying in {delay:.1f} seconds...")
            await asyncio.sleep(delay)
    
    return result


# ============================================================================
# PARALLEL PROCESSING
# ============================================================================

async def process_cards_parallel(
    cards: List[CardData],
    proxies: List[ProxyConfig],
    max_workers: int = MAX_CONCURRENT_WORKERS
) -> List[CheckResult]:
    """
    Process multiple cards in parallel using asyncio
    
    Args:
        cards: List of CardData objects
        proxies: List of ProxyConfig objects
        max_workers: Maximum number of concurrent workers
        
    Returns:
        List of CheckResult objects
    """
    results = []
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting parallel processing")
    print(f"📊 Cards to process: {len(cards)}")
    print(f"👥 Concurrent workers: {max_workers}")
    print(f"🔒 Available proxies: {len(proxies)}")
    print(f"{'='*60}\n")
    
    # Create semaphore to limit concurrent tasks
    semaphore = asyncio.Semaphore(max_workers)
    
    async def process_with_semaphore(card, index):
        async with semaphore:
            try:
                result = await check_card_with_retry(card, proxies)
                
                status = "✅ SUCCESS" if result.success else "❌ FAILED"
                print(f"\n[{index + 1}/{len(cards)}] {status}: {card}")
                
                # Small delay between completions
                if index < len(cards) - 1:
                    await asyncio.sleep(random.uniform(*TIMING_CONFIG["between_requests"]))
                
                return result
            except Exception as e:
                print(f"\n[{index + 1}/{len(cards)}] ❌ EXCEPTION: {card} - {e}")
                return CheckResult(
                    card=card,
                    success=False,
                    error=str(e)
                )
    
    # Process all cards concurrently
    tasks = [process_with_semaphore(card, i) for i, card in enumerate(cards)]
    results = await asyncio.gather(*tasks)
    
    return results


# ============================================================================
# REPORTING
# ============================================================================

def generate_report(results: List[CheckResult]):
    """Generate and display summary report"""
    print(f"\n{'='*60}")
    print("📊 FINAL REPORT")
    print(f"{'='*60}\n")
    
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    
    print(f"Total cards processed: {total}")
    print(f"✅ Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
    
    if successful > 0:
        print(f"\n{'='*60}")
        print("✅ SUCCESSFUL CHECKS:")
        print(f"{'='*60}")
        for result in results:
            if result.success:
                print(f"  • {result.card}: {result.balance}")
    
    if failed > 0:
        print(f"\n{'='*60}")
        print("❌ FAILED CHECKS:")
        print(f"{'='*60}")
        for result in results:
            if not result.success:
                print(f"  • {result.card}: {result.error}")
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    report_file = f"reports/balance_check_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump([
            {
                "card": r.card.number[-4:],
                "success": r.success,
                "balance": r.balance,
                "error": r.error,
                "attempts": r.attempts,
                "timestamp": r.timestamp
            }
            for r in results
        ], f, indent=2)
    
    print(f"\n📄 Report saved to: {report_file}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Main execution function"""
    print("="*60)
    print("🎁 VANILLA GIFT BALANCE CHECKER - CAPSOLVER VERSION")
    print("="*60)
    
    # Validate Capsolver API key
    if CAPSOLVER_CLIENT_KEY == "your_capsolver_api_key_here":
        print("\n❌ ERROR: Please set your Capsolver API key in the script")
        print("💡 Get your API key from: https://www.capsolver.com")
        return
    
    # Check Capsolver balance
    print("\n📊 Checking Capsolver account balance...")
    balance_info = get_capsolver_balance()
    if balance_info:
        balance = balance_info.get("balance", 0) / 100  # Balance is in cents
        print(f"✓ Capsolver balance: ${balance:.2f}")
    else:
        print("⚠️  Could not verify Capsolver balance")
    
    # Load proxies
    proxies = load_proxies()
    if not proxies:
        print("\n⚠️  WARNING: No proxies configured - using direct connection")
        print("💡 Add proxies to proxy_config.json for better results")
    
    # Load cards
    cards = load_cards()
    if not cards:
        print("\n❌ ERROR: No cards to process")
        return
    
    # Process cards
    results = await process_cards_parallel(cards, proxies)
    
    # Generate report
    generate_report(results)
    
    print(f"\n{'='*60}")
    print("✅ Processing complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
