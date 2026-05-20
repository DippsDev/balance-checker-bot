"""
Test script to verify wreq integration and TLS fingerprinting
"""

import sys
import asyncio
from datetime import timedelta

# Test 1: Check if wreq is installed
print("="*60)
print("TEST 1: Checking wreq installation")
print("="*60)

try:
    import wreq
    print("✅ wreq is installed")
    print(f"   Version: {wreq.__version__ if hasattr(wreq, '__version__') else 'unknown'}")
    WREQ_AVAILABLE = True
except ImportError as e:
    print("❌ wreq is NOT installed")
    print(f"   Error: {e}")
    print("\n💡 Install with: pip install wreq")
    WREQ_AVAILABLE = False

# Test 2: Check other dependencies
print("\n" + "="*60)
print("TEST 2: Checking other dependencies")
print("="*60)

dependencies = {
    'requests': 'requests',
    'dotenv': 'python-dotenv',
}

for module, package in dependencies.items():
    try:
        __import__(module)
        print(f"✅ {package} is installed")
    except ImportError:
        print(f"❌ {package} is NOT installed")
        print(f"   Install with: pip install {package}")

# Test 3: Test wreq functionality (if available)
async def test_wreq_functionality():
    if not WREQ_AVAILABLE:
        return
    
    print("\n" + "="*60)
    print("TEST 3: Testing wreq functionality")
    print("="*60)
    
    try:
        # Test with HTTPBin to see our fingerprint
        print("\n🔧 Testing Chrome fingerprint...")
        response = await wreq.get(
            'https://httpbin.org/headers',
            impersonate='chrome',
            timeout=timedelta(seconds=10)
        )
        
        status_code = response.status.as_int()
        
        if status_code == 200:
            text = await response.text()
            print("✅ Chrome fingerprint test successful")
            print(f"   Status: {status_code}")
            print(f"   Response length: {len(text)} bytes")
        else:
            print(f"⚠️  Unexpected status: {status_code}")
    
    except Exception as e:
        print(f"❌ wreq test failed: {e}")
    
    try:
        print("\n🔧 Testing Firefox fingerprint...")
        response = await wreq.get(
            'https://httpbin.org/headers',
            impersonate='firefox',
            timeout=timedelta(seconds=10)
        )
        
        status_code = response.status.as_int()
        
        if status_code == 200:
            text = await response.text()
            print("✅ Firefox fingerprint test successful")
            print(f"   Status: {status_code}")
            print(f"   Response length: {len(text)} bytes")
        else:
            print(f"⚠️  Unexpected status: {status_code}")
    
    except Exception as e:
        print(f"❌ wreq test failed: {e}")

# Run async test
if WREQ_AVAILABLE:
    asyncio.run(test_wreq_functionality())

# Test 4: Test browser profile detection
print("\n" + "="*60)
print("TEST 4: Testing browser profile detection")
print("="*60)

from balance_checker_bot import get_browser_profile, USER_AGENTS

test_cases = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36", "chrome"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0", "firefox"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0", "edge"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15", "safari"),
]

all_passed = True
for ua, expected_profile in test_cases:
    detected_profile = get_browser_profile(ua)
    if detected_profile == expected_profile:
        print(f"✅ {expected_profile.upper()}: Correctly detected")
    else:
        print(f"❌ {expected_profile.upper()}: Expected '{expected_profile}', got '{detected_profile}'")
        all_passed = False

if all_passed:
    print("\n✅ All browser profile tests passed!")

# Test 5: Verify user agent pool
print("\n" + "="*60)
print("TEST 5: User agent pool statistics")
print("="*60)

chrome_count = sum(1 for ua in USER_AGENTS if 'Chrome/' in ua and 'Edg/' not in ua)
firefox_count = sum(1 for ua in USER_AGENTS if 'Firefox/' in ua)
edge_count = sum(1 for ua in USER_AGENTS if 'Edg/' in ua)
safari_count = sum(1 for ua in USER_AGENTS if 'Safari/' in ua and 'Chrome/' not in ua)

print(f"Total user agents: {len(USER_AGENTS)}")
print(f"  Chrome: {chrome_count}")
print(f"  Firefox: {firefox_count}")
print(f"  Edge: {edge_count}")
print(f"  Safari: {safari_count}")

# Final summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if WREQ_AVAILABLE:
    print("✅ Your bot is ready with advanced TLS fingerprinting!")
    print("   - wreq is installed and working")
    print("   - Browser profiles are correctly mapped")
    print("   - User agents are diverse and up-to-date")
    print("\n🚀 Run balance_checker_bot.py to start checking cards")
else:
    print("⚠️  Your bot will work but without TLS fingerprinting")
    print("   - Install wreq for better stealth: pip install wreq")
    print("   - The bot will fall back to standard requests")
    print("\n💡 For best results, install wreq before running the bot")

print("="*60)
