"""Chrome cookie extraction for testing automation and session persistence"""

import os
import sys
from typing import Dict

import browser_cookie3


def get_chrome_cookies(domain: str, profile: str = "Default") -> Dict[str, str]:
    """
    Extract cookies from Chrome for testing automation.
    
    Args:
        domain: Domain to get cookies for (e.g., "github.com")
        profile: Chrome profile name (default: "Default")
    
    Returns:
        Dictionary of cookie name-value pairs
    """
    # Normalize domain
    domain = domain.strip().lower().replace('https://', '').replace('http://', '').split('/')[0]
    
    # Get Chrome cookie file path based on OS
    if sys.platform == "darwin":
        profiles_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome/")
        cookie_file = os.path.join(profiles_dir, profile, "Cookies")
    elif sys.platform == "win32":
        profiles_dir = os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data\\")
        cookie_file = os.path.join(profiles_dir, profile, "Network", "Cookies")
    else:
        profiles_dir = os.path.expanduser("~/.config/google-chrome/")
        cookie_file = os.path.join(profiles_dir, profile, "Cookies")
    
    if not os.path.exists(cookie_file):
        raise FileNotFoundError(f"Chrome cookie file not found: {cookie_file}")
    
    # Use browser-cookie3 to get and decrypt cookies
    try:
        cj = browser_cookie3.chrome(cookie_file=cookie_file, domain_name=domain)
    except Exception as e:
        if "locked" in str(e).lower():
            raise RuntimeError("Chrome is open. Close Chrome and try again.")
        raise
    
    cookies = {cookie.name: cookie.value for cookie in cj}
    return cookies
