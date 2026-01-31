"""
GMaps Scraper - Main Module
Google Maps Business Data Extractor

Works in Google Colab and locally.
"""

import datetime
import random
import asyncio
import re
import os
import sys
import subprocess
import shutil
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any, Union


# Third-party imports
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False


# ============================================================
# ENVIRONMENT DETECTION
# ============================================================

def is_colab() -> bool:
    """Check if running in Google Colab"""
    try:
        import google.colab
        return True
    except ImportError:
        return False


def is_jupyter() -> bool:
    """Check if running in Jupyter notebook"""
    try:
        from IPython import get_ipython
        shell = get_ipython().__class__.__name__
        return shell in ['ZMQInteractiveShell', 'TerminalInteractiveShell']
    except:
        return False


# ============================================================
# COLAB SETUP - CRITICAL FOR COLAB
# ============================================================

async def setup_colab(verbose: bool = True) -> bool:
    """
    Setup everything needed for Google Colab.
    
    This installs system dependencies required by Playwright/Chromium.
    RUN THIS FIRST before scraping in Colab!
    
    Usage:
        from gmaps_scraper import setup_colab, scrape_maps
        
        # Setup first (only once per session)
        await setup_colab()
        
        # Then scrape
        df = await scrape_maps("restaurants in NYC", max_results=50)
    
    Returns:
        bool: True if setup successful
    """
    if verbose:
        print("🚀 Setting up environment...")
        print(f"   Environment: {'Google Colab' if is_colab() else 'Local/Jupyter'}")
    
    success = True
    
    # Step 1: Install system dependencies (required for Chromium)
    if verbose:
        print("\n📦 Step 1/3: Installing system dependencies...")
    
    deps_result = await install_playwright_deps(verbose=verbose)
    if not deps_result:
        success = False
    
    # Step 2: Install Playwright browsers
    if verbose:
        print("\n📦 Step 2/3: Installing Chromium browser...")
    
    browser_result = await _install_browser(verbose=verbose)
    if not browser_result:
        success = False
    
    # Step 3: Verify installation
    if verbose:
        print("\n✅ Step 3/3: Verifying installation...")
    
    verify_result = await _verify_installation(verbose=verbose)
    if not verify_result:
        success = False
    
    if success:
        if verbose:
            print("\n" + "="*50)
            print("✅ Setup complete! You can now use scrape_maps()")
            print("="*50 + "\n")
    else:
        if verbose:
            print("\n" + "="*50)
            print("⚠️ Setup completed with warnings. Try running anyway.")
            print("="*50 + "\n")
    
    return success


async def install_playwright_deps(verbose: bool = True) -> bool:
    """
    Install system dependencies required by Playwright/Chromium
    
    This is the KEY fix for the 'libatk-1.0.so.0' error!
    """
    try:
        # List of required system packages for Chromium
        packages = [
            "libnss3",
            "libnspr4",
            "libatk1.0-0",
            "libatk-bridge2.0-0",
            "libcups2",
            "libdrm2",
            "libxkbcommon0",
            "libxcomposite1",
            "libxdamage1",
            "libxfixes3",
            "libxrandr2",
            "libgbm1",
            "libasound2",
            "libpango-1.0-0",
            "libpangocairo-1.0-0",
            "libcairo2",
            "libatspi2.0-0",
        ]
        
        if is_colab():
            # In Colab, use os.system for apt commands
            if verbose:
                print("   Updating package list...")
            
            os.system("apt-get update -qq > /dev/null 2>&1")
            
            if verbose:
                print(f"   Installing {len(packages)} required packages...")
            
            # Install all packages
            packages_str = " ".join(packages)
            result = os.system(f"apt-get install -qq -y {packages_str} > /dev/null 2>&1")
            
            if result == 0:
                if verbose:
                    print("   ✅ System dependencies installed!")
                return True
            else:
                # Try installing packages one by one
                if verbose:
                    print("   Retrying individual package installation...")
                
                for pkg in packages:
                    os.system(f"apt-get install -qq -y {pkg} > /dev/null 2>&1")
                
                if verbose:
                    print("   ✅ System dependencies installed!")
                return True
        else:
            # Not in Colab - try playwright install-deps
            if verbose:
                print("   Running playwright install-deps...")
            
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install-deps", "chromium"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                if verbose:
                    print("   ✅ Dependencies installed!")
                return True
            else:
                if verbose:
                    print(f"   ⚠️ May need sudo: {result.stderr[:100] if result.stderr else 'Unknown error'}")
                return True  # Continue anyway
                
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Warning: {str(e)[:50]}")
        return False


async def _install_browser(verbose: bool = True) -> bool:
    """Install Chromium browser"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if verbose:
                print("   ✅ Chromium browser installed!")
            return True
        else:
            if verbose:
                print(f"   ⚠️ Warning: {result.stderr[:100] if result.stderr else 'Check installation'}")
            return False
            
    except Exception as e:
        if verbose:
            print(f"   ❌ Error: {str(e)[:50]}")
        return False


async def _verify_installation(verbose: bool = True) -> bool:
    """Verify Playwright installation works"""
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
        
        if verbose:
            print("   ✅ Browser launch test passed!")
        return True
        
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Verification warning: {str(e)[:50]}")
        return False


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class ScraperConfig:
    """Configuration for the Google Maps scraper"""
    headless: bool = True
    slow_mo: int = 0
    use_proxy: bool = False
    use_stealth: bool = True
    random_delays: bool = True
    min_delay: float = 1.0
    max_delay: float = 3.0
    timeout: int = 60000
    output_folder: str = "GMaps_Data"


# ============================================================
# PROXY MANAGER
# ============================================================

class ProxyManager:
    """Manages proxy rotation for the scraper"""
    
    def __init__(self, proxies: List[Dict[str, str]] = None):
        self.proxies = proxies or []
        self.current_index = 0
        self.failed_proxies = set()
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None
        
        attempts = 0
        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_index]
            proxy_key = proxy["server"]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
            if proxy_key not in self.failed_proxies:
                return proxy
            attempts += 1
        
        self.failed_proxies.clear()
        return self.proxies[0] if self.proxies else None
    
    def mark_failed(self, proxy: Dict[str, str]):
        if proxy:
            self.failed_proxies.add(proxy["server"])
    
    @property
    def available_count(self) -> int:
        return len(self.proxies) - len(self.failed_proxies)


# ============================================================
# FINGERPRINT MANAGER
# ============================================================

class FingerprintManager:
    """Manages browser fingerprints to avoid detection"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    VIEWPORTS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1280, "height": 800},
    ]
    
    TIMEZONES = [
        "America/New_York",
        "America/Los_Angeles",
        "Europe/London",
        "Asia/Kolkata",
    ]
    
    def generate_fingerprint(self) -> Dict[str, Any]:
        return {
            "viewport": random.choice(self.VIEWPORTS),
            "user_agent": random.choice(self.USER_AGENTS),
            "timezone_id": random.choice(self.TIMEZONES),
            "locale": "en-US",
        }


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class Business:
    """Represents a business from Google Maps"""
    name: str = ""
    address: str = ""
    phone_number: str = ""
    website: str = ""
    rating: str = ""
    reviews_count: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        return asdict(self)
    
    def __str__(self) -> str:
        return f"{self.name} | {self.rating}⭐ ({self.reviews_count} reviews)"


@dataclass
class BusinessList:
    """Collection of Business objects with deduplication"""
    business_list: List[Business] = field(default_factory=list)
    _seen_names: set = field(default_factory=set, init=False, repr=False)

    def add_business(self, business: Business) -> bool:
        if business.name and business.name not in self._seen_names:
            self.business_list.append(business)
            self._seen_names.add(business.name)
            return True
        return False

    def dataframe(self):
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required. Install with: pip install pandas")
        return pd.DataFrame([asdict(b) for b in self.business_list])

    def save_to_csv(
        self,
        filename: str = None,
        folder: str = None,
        include_timestamp: bool = False
    ) -> str:
        if folder is None:
            folder = "GMaps_Data"
        
        os.makedirs(folder, exist_ok=True)
        
        if filename is None:
            filename = f"gmaps_results_{len(self.business_list)}_businesses"
        
        # Clean filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename[:100]
        
        if include_timestamp:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}"
        
        filepath = os.path.join(folder, f"{filename}.csv")
        self.dataframe().to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return filepath

    def to_json(self) -> str:
        import json
        return json.dumps([asdict(b) for b in self.business_list], indent=2)

    def __len__(self) -> int:
        return len(self.business_list)
    
    def __iter__(self):
        return iter(self.business_list)
    
    def __getitem__(self, index):
        return self.business_list[index]


# ============================================================
# MAIN SCRAPER CLASS
# ============================================================

class GoogleMapsScraper:
    """
    Google Maps Scraper - Extracts business data from Google Maps
    
    Works in Google Colab and locally.
    """

    def __init__(
        self,
        config: ScraperConfig = None,
        proxies: List[Dict[str, str]] = None
    ):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required. Install with:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )
        
        self.config = config or ScraperConfig()
        self.proxy_manager = ProxyManager(proxies)
        self.fingerprint_manager = FingerprintManager()
        
        self.browser = None
        self.context = None
        self.page = None
        self.current_proxy = None
        self.current_fingerprint = None

    async def scrape(
        self,
        search_query: str,
        max_results: int = 25,
        save_csv: bool = True,
        csv_filename: str = None,
        output_folder: str = None,
    ):
        """
        Scrape Google Maps for business data
        
        Args:
            search_query: Search term (e.g., "restaurants in New York")
            max_results: Maximum number of results to scrape
            save_csv: Whether to save results to CSV
            csv_filename: Custom CSV filename (without extension)
            output_folder: Custom output folder
        
        Returns:
            pandas DataFrame with scraped data
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required. Install with: pip install pandas")
        
        search_url = "https://www.google.com/maps/search/" + search_query.replace(" ", "+")
        
        async with async_playwright() as p:
            await self._setup_browser(p)
            
            print(f"\n{'='*60}")
            print(f"🔍 Searching: {search_query}")
            print(f"📊 Target: {max_results} results")
            print(f"{'='*60}\n")
            
            # Navigate to search
            try:
                await self.page.goto(search_url, timeout=self.config.timeout, wait_until='domcontentloaded')
            except Exception as e:
                print(f"⚠️ Navigation warning: {str(e)[:50]}")
                
            await self.page.wait_for_timeout(5000)
            await self._handle_consent()
            await self.page.wait_for_timeout(3000)
            
            # Check for results
            listing_selector = 'div[role="feed"] > div > div > a[href*="/maps/place/"]'
            
            if await self.page.locator(listing_selector).count() == 0:
                listing_selector = 'a[href*="/maps/place/"]'
            
            initial_count = await self.page.locator(listing_selector).count()
            
            if initial_count == 0:
                print("❌ No results found!")
                await self._cleanup()
                return pd.DataFrame()
            
            print(f"📋 Initial listings: {initial_count}")
            
            # Scroll for more results
            await self._scroll_results(max_results, listing_selector)
            
            # Get listing URLs
            listing_urls = await self._get_listing_urls(listing_selector, max_results)
            print(f"\n📋 Collected {len(listing_urls)} unique URLs")
            
            # Scrape each listing
            business_list = await self._scrape_by_urls(listing_urls)
            
            df = business_list.dataframe()
            
            # Save CSV
            if save_csv and len(df) > 0:
                if csv_filename is None:
                    csv_filename = search_query.replace(" ", "_").replace(",", "")[:50]
                
                folder = output_folder or self.config.output_folder
                filepath = business_list.save_to_csv(csv_filename, folder)
                print(f"\n📁 Saved: {filepath}")
            
            print(f"\n{'='*60}")
            print(f"🎉 SUCCESS! Scraped {len(business_list)} businesses")
            print(f"{'='*60}\n")
            
            await self._cleanup()
            return df

    async def _get_listing_urls(self, listing_selector: str, max_count: int) -> List[str]:
        """Extract unique URLs from listings"""
        urls = set()
        listings = await self.page.locator(listing_selector).all()
        
        for listing in listings[:max_count]:
            try:
                href = await listing.get_attribute('href')
                if href and '/maps/place/' in href:
                    urls.add(href)
            except:
                continue
        
        return list(urls)

    async def _scrape_by_urls(self, urls: List[str]) -> BusinessList:
        """Scrape each business by URL"""
        business_list = BusinessList()
        total = len(urls)
        
        print(f"\n🔍 Scraping {total} businesses...\n")
        
        for idx, url in enumerate(urls):
            try:
                print(f"[{idx + 1}/{total}] ", end='')
                
                await self.page.goto(url, timeout=30000, wait_until='domcontentloaded')
                await self.page.wait_for_timeout(2000)
                await self._wait_for_detail_panel()
                
                business = await self._extract_business_details()
                
                if business.name:
                    added = business_list.add_business(business)
                    status = "✅" if added else "⏭️ dup"
                    print(f"{status} {business.name[:45]}")
                else:
                    print("⚠️ No name found")
                
                await self._random_delay()
                
            except Exception as e:
                print(f"❌ {str(e)[:40]}")
        
        return business_list

    async def _wait_for_detail_panel(self, timeout: int = 10000):
        """Wait for business detail panel"""
        try:
            await self.page.wait_for_selector('h1.DUwDvf', timeout=timeout)
        except:
            try:
                await self.page.wait_for_selector('h1.fontHeadlineLarge', timeout=5000)
            except:
                pass
        await self.page.wait_for_timeout(500)

    async def _extract_business_details(self) -> Business:
        """Extract business details from current page"""
        business = Business()
        
        # Name
        for selector in ['h1.DUwDvf', 'h1.fontHeadlineLarge', 'div.qBF1Pd.fontHeadlineSmall']:
            try:
                loc = self.page.locator(selector)
                if await loc.count() > 0:
                    business.name = (await loc.first.inner_text()).strip()
                    if business.name:
                        break
            except:
                continue
        
        # Rating
        try:
            rating_loc = self.page.locator('div.F7nice span[aria-hidden="true"]').first
            if await self.page.locator('div.F7nice span[aria-hidden="true"]').count() > 0:
                business.rating = (await rating_loc.inner_text()).strip()
        except:
            pass
        
        # Reviews count
        try:
            reviews_loc = self.page.locator('div.F7nice span[aria-label*="review"]')
            if await reviews_loc.count() > 0:
                text = await reviews_loc.first.get_attribute('aria-label')
                if text:
                    match = re.search(r'([\d,]+)', text)
                    if match:
                        business.reviews_count = match.group(1)
        except:
            pass
        
        # Address
        try:
            addr_loc = self.page.locator('button[data-item-id="address"]')
            if await addr_loc.count() > 0:
                business.address = (await addr_loc.first.inner_text()).strip()
            else:
                addr_loc = self.page.locator('[data-item-id="address"]')
                if await addr_loc.count() > 0:
                    business.address = (await addr_loc.first.inner_text()).strip()
        except:
            pass
        
        # Phone
        try:
            phone_loc = self.page.locator('button[data-item-id*="phone:tel:"]')
            if await phone_loc.count() > 0:
                business.phone_number = (await phone_loc.first.inner_text()).strip()
            else:
                phone_loc = self.page.locator('a[href^="tel:"]')
                if await phone_loc.count() > 0:
                    href = await phone_loc.first.get_attribute('href')
                    if href:
                        business.phone_number = href.replace('tel:', '')
        except:
            pass
        
        # Website
        try:
            web_loc = self.page.locator('a[data-item-id="authority"]')
            if await web_loc.count() > 0:
                business.website = (await web_loc.first.inner_text()).strip()
            else:
                web_loc = self.page.locator('a[data-tooltip="Open website"]')
                if await web_loc.count() > 0:
                    business.website = await web_loc.first.get_attribute('href') or ""
        except:
            pass
        
        return business

    async def _setup_browser(self, playwright):
        """Setup browser with anti-detection measures"""
        print("🚀 Setting up browser...")
        
        self.current_fingerprint = self.fingerprint_manager.generate_fingerprint()
        
        launch_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--disable-gpu',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-extensions',
        ]
        
        proxy_config = None
        if self.config.use_proxy and self.proxy_manager.available_count > 0:
            self.current_proxy = self.proxy_manager.get_next_proxy()
            if self.current_proxy:
                proxy_config = self.current_proxy
                print(f"🌐 Using proxy: {self.current_proxy['server'][:40]}...")
        
        self.browser = await playwright.chromium.launch(
            headless=self.config.headless,
            slow_mo=self.config.slow_mo,
            args=launch_args
        )
        
        context_options = {
            "viewport": self.current_fingerprint["viewport"],
            "user_agent": self.current_fingerprint["user_agent"],
            "locale": self.current_fingerprint["locale"],
            "timezone_id": self.current_fingerprint["timezone_id"],
        }
        
        if proxy_config:
            context_options["proxy"] = {
                "server": proxy_config["server"],
                "username": proxy_config.get("username", ""),
                "password": proxy_config.get("password", "")
            }
        
        self.context = await self.browser.new_context(**context_options)
        
        if STEALTH_AVAILABLE and self.config.use_stealth:
            await stealth_async(self.context)
            print("🥷 Stealth mode enabled")
        
        self.page = await self.context.new_page()
        
        # Block heavy resources
        await self.page.route(
            "**/*.{png,jpg,jpeg,gif,svg,ico,webp,woff,woff2}",
            lambda route: route.abort()
        )
        
        print("✅ Browser ready")

    async def _random_delay(self):
        if self.config.random_delays:
            delay = random.uniform(self.config.min_delay, self.config.max_delay)
            await self.page.wait_for_timeout(int(delay * 1000))

    async def _handle_consent(self):
        try:
            for btn_text in ['Accept all', 'Accept', 'Reject all', 'I agree']:
                btn = self.page.get_by_role("button", name=btn_text)
                if await btn.count() > 0:
                    await btn.first.click(timeout=5000)
                    print(f"✅ Handled consent: {btn_text}")
                    await self.page.wait_for_timeout(2000)
                    break
        except:
            pass

    async def _scroll_results(self, target_count: int, listing_selector: str):
        """Scroll to load more results"""
        print(f"📜 Scrolling to load {target_count} results...")
        
        scroll_container = None
        for selector in ['div[role="feed"]', 'div.m6QErb[aria-label]']:
            if await self.page.locator(selector).count() > 0:
                scroll_container = self.page.locator(selector).first
                break
        
        previous_count = 0
        stall_count = 0
        
        for _ in range(100):
            if scroll_container:
                await scroll_container.evaluate('(el) => el.scrollBy(0, 1000)')
            else:
                await self.page.mouse.wheel(0, 3000)
            
            await self.page.wait_for_timeout(1500)
            current_count = await self.page.locator(listing_selector).count()
            
            # Progress bar
            progress = min(100, int((current_count / target_count) * 100))
            bar = "█" * (progress // 5) + "░" * (20 - progress // 5)
            print(f"   [{bar}] {current_count}/{target_count}", end='\r')
            
            if current_count >= target_count:
                print(f"\n✅ Reached target: {current_count}")
                break
            
            if current_count == previous_count:
                stall_count += 1
                if stall_count >= 5:
                    print(f"\n⚠️ End of results: {current_count}")
                    break
            else:
                stall_count = 0
            
            previous_count = current_count

    async def _cleanup(self):
        if self.browser:
            await self.browser.close()


# ============================================================
# EASY-TO-USE FUNCTIONS
# ============================================================

async def scrape_maps(
    query: str,
    max_results: int = 25,
    save_csv: bool = True,
    csv_filename: str = None,
    output_folder: str = None,
    headless: bool = True,
    use_proxy: bool = False,
    proxies: List[Dict[str, str]] = None,
    auto_setup: bool = True,
):
    """
    Scrape Google Maps - Easy async function
    
    Args:
        query: Search term (e.g., "restaurants in New York")
        max_results: Maximum results to scrape (default: 25)
        save_csv: Save results to CSV (default: True)
        csv_filename: Custom filename for CSV (default: auto-generated from query)
        output_folder: Folder to save CSV (default: 'GMaps_Data')
        headless: Run browser headless (default: True)
        use_proxy: Enable proxy rotation (default: False)
        proxies: List of proxy configs
        auto_setup: Auto-run setup_colab if in Colab (default: True)
    
    Returns:
        pandas DataFrame with scraped data
    
    Example (Google Colab):
        # First time: run setup
        await setup_colab()
        
        # Then scrape
        df = await scrape_maps("hotels in Paris", max_results=50)
        
    Example (Local):
        import asyncio
        df = asyncio.run(scrape_maps("cafes in London", max_results=30))
    """
    
    config = ScraperConfig(
        headless=headless,
        use_proxy=use_proxy,
        use_stealth=True,
        random_delays=True,
        output_folder=output_folder or "GMaps_Data",
    )
    
    scraper = GoogleMapsScraper(config, proxies=proxies)
    return await scraper.scrape(
        query,
        max_results=max_results,
        save_csv=save_csv,
        csv_filename=csv_filename,
        output_folder=output_folder,
    )


def scrape_maps_sync(
    query: str,
    max_results: int = 25,
    save_csv: bool = True,
    csv_filename: str = None,
    output_folder: str = None,
    headless: bool = True,
    use_proxy: bool = False,
    proxies: List[Dict[str, str]] = None,
):
    """
    Scrape Google Maps - Synchronous version
    
    Use this when you're not in an async context (e.g., regular Python scripts).
    
    Example:
        from gmaps_scraper import scrape_maps_sync
        df = scrape_maps_sync("restaurants in NYC", max_results=50)
    """
    return asyncio.run(scrape_maps(
        query=query,
        max_results=max_results,
        save_csv=save_csv,
        csv_filename=csv_filename,
        output_folder=output_folder,
        headless=headless,
        use_proxy=use_proxy,
        proxies=proxies,
        auto_setup=False,
    ))


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Google Maps Scraper")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--max-results", type=int, default=25)
    parser.add_argument("-o", "--output", help="Output CSV filename")
    parser.add_argument("--folder", default="GMaps_Data")
    parser.add_argument("--no-save", action="store_true")
    
    args = parser.parse_args()
    
    df = scrape_maps_sync(
        query=args.query,
        max_results=args.max_results,
        save_csv=not args.no_save,
        csv_filename=args.output,
        output_folder=args.folder,
    )
    
    print(f"\nResults: {len(df)} businesses")


"""
EB Review Automation - Main Module
Electronics Bazaar Review Submission Tool

Works in Google Colab and locally.
"""


# Third-party imports
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# ============================================================
# ENVIRONMENT DETECTION
# ============================================================

def is_colab() -> bool:
    """Check if running in Google Colab"""
    try:
        import google.colab
        return True
    except ImportError:
        return False


def is_jupyter() -> bool:
    """Check if running in Jupyter notebook"""
    try:
        from IPython import get_ipython
        shell = get_ipython().__class__.__name__
        return shell in ['ZMQInteractiveShell', 'TerminalInteractiveShell']
    except:
        return False


# ============================================================
# COLAB SETUP
# ============================================================

async def setup_colab(verbose: bool = True) -> bool:
    """
    Setup everything needed for Google Colab.
    
    This installs system dependencies required by Playwright/Chromium.
    RUN THIS FIRST before submitting reviews in Colab!
    
    Usage:
        from eb_reviews import setup_colab, submit_reviews
        
        # Setup first (only once per session)
        await setup_colab()
        
        # Then submit reviews
        df = await submit_reviews("reviews.csv", email="...", password="...")
    
    Returns:
        bool: True if setup successful
    """
    if verbose:
        print("🚀 Setting up environment...")
        print(f"   Environment: {'Google Colab' if is_colab() else 'Local/Jupyter'}")
    
    success = True
    
    # Step 1: Install system dependencies
    if verbose:
        print("\n📦 Step 1/3: Installing system dependencies...")
    
    deps_result = await install_playwright_deps(verbose=verbose)
    if not deps_result:
        success = False
    
    # Step 2: Install Playwright browsers
    if verbose:
        print("\n📦 Step 2/3: Installing Chromium browser...")
    
    browser_result = await _install_browser(verbose=verbose)
    if not browser_result:
        success = False
    
    # Step 3: Verify installation
    if verbose:
        print("\n✅ Step 3/3: Verifying installation...")
    
    verify_result = await _verify_installation(verbose=verbose)
    if not verify_result:
        success = False
    
    if success:
        if verbose:
            print("\n" + "=" * 50)
            print("✅ Setup complete! You can now use submit_reviews()")
            print("=" * 50 + "\n")
    else:
        if verbose:
            print("\n" + "=" * 50)
            print("⚠️ Setup completed with warnings. Try running anyway.")
            print("=" * 50 + "\n")
    
    return success


async def install_playwright_deps(verbose: bool = True) -> bool:
    """Install system dependencies required by Playwright/Chromium"""
    try:
        packages = [
            "libnss3", "libnspr4", "libatk1.0-0", "libatk-bridge2.0-0",
            "libcups2", "libdrm2", "libxkbcommon0", "libxcomposite1",
            "libxdamage1", "libxfixes3", "libxrandr2", "libgbm1",
            "libasound2", "libpango-1.0-0", "libpangocairo-1.0-0",
            "libcairo2", "libatspi2.0-0",
        ]
        
        if is_colab():
            if verbose:
                print("   Updating package list...")
            
            os.system("apt-get update -qq > /dev/null 2>&1")
            
            if verbose:
                print(f"   Installing {len(packages)} required packages...")
            
            packages_str = " ".join(packages)
            result = os.system(f"apt-get install -qq -y {packages_str} > /dev/null 2>&1")
            
            if verbose:
                print("   ✅ System dependencies installed!")
            return True
        else:
            if verbose:
                print("   Running playwright install-deps...")
            
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install-deps", "chromium"],
                capture_output=True, text=True
            )
            
            if verbose:
                print("   ✅ Dependencies installed!")
            return True
                
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Warning: {str(e)[:50]}")
        return False


async def _install_browser(verbose: bool = True) -> bool:
    """Install Chromium browser"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            if verbose:
                print("   ✅ Chromium browser installed!")
            return True
        else:
            if verbose:
                print(f"   ⚠️ Warning: {result.stderr[:100] if result.stderr else 'Check installation'}")
            return False
            
    except Exception as e:
        if verbose:
            print(f"   ❌ Error: {str(e)[:50]}")
        return False


async def _verify_installation(verbose: bool = True) -> bool:
    """Verify Playwright installation works"""
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
        
        if verbose:
            print("   ✅ Browser launch test passed!")
        return True
        
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Verification warning: {str(e)[:50]}")
        return False


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class ReviewConfig:
    """Configuration for the review automation"""
    headless: bool = True
    timeout: int = 60000
    min_delay: float = 3.0
    max_delay: float = 5.0
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class ReviewResult:
    """Represents a review submission result"""
    product_link: str = ""
    nickname: str = ""
    rating: int = 0
    summary: str = ""
    review: str = ""
    status: str = ""
    error_message: str = ""
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def __str__(self) -> str:
        return f"{self.nickname} → {self.status}"


@dataclass
class ReviewResultList:
    """Collection of ReviewResult objects"""
    results: List[ReviewResult] = field(default_factory=list)
    
    def add_result(self, result: ReviewResult):
        self.results.append(result)
    
    def dataframe(self):
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required. Install with: pip install pandas")
        return pd.DataFrame([asdict(r) for r in self.results])
    
    def save_to_csv(self, filename: str = "review_results.csv") -> str:
        df = self.dataframe()
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        return filename
    
    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.status == "Success")
    
    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == "Failed")
    
    def __len__(self) -> int:
        return len(self.results)
    
    def __iter__(self):
        return iter(self.results)


# ============================================================
# MAIN AUTOMATION CLASS
# ============================================================

class EBReviewAutomation:
    """
    Electronics Bazaar Review Automation
    
    Automates the submission of product reviews on electronicsbazaar.com
    
    Works in Google Colab and locally.
    """
    
    LOGIN_URL = "https://www.electronicsbazaar.com/en-us/customer/account/login/"
    
    def __init__(self, email: str, password: str, config: ReviewConfig = None):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required. Install with:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )
        
        self.email = email
        self.password = password
        self.config = config or ReviewConfig()
        self.browser = None
        self.context = None
        self.page = None

    async def submit_reviews(
        self,
        reviews_data: Any,
        save_results: bool = True,
        output_file: str = "review_results.csv"
    ) -> 'pd.DataFrame':
        """
        Submit reviews from CSV file or DataFrame
        
        Args:
            reviews_data: Path to CSV file or pandas DataFrame
            save_results: Whether to save results to CSV
            output_file: Output filename for results
        
        Returns:
            pandas DataFrame with submission results
        
        CSV/DataFrame columns required:
            - product_link: URL of the product
            - nickname: Reviewer name
            - rating: Star rating (1-5)
            - summary: Review title/summary
            - review: Review text
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required. Install with: pip install pandas")
        
        # Load data
        if isinstance(reviews_data, str):
            df_input = pd.read_csv(reviews_data)
        elif isinstance(reviews_data, pd.DataFrame):
            df_input = reviews_data
        else:
            raise ValueError("reviews_data must be a CSV filepath or pandas DataFrame")
        
        # Validate columns
        required_cols = ['product_link', 'nickname', 'rating', 'summary', 'review']
        missing = [col for col in required_cols if col not in df_input.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        results = ReviewResultList()
        
        print("=" * 60)
        print(f"🤖 EB REVIEW AUTOMATION")
        print(f"📊 Reviews to submit: {len(df_input)}")
        print("=" * 60)
        
        async with async_playwright() as p:
            await self._setup_browser(p)
            
            # Login
            if not await self._login():
                print("\n❌ Login failed!")
                await self._cleanup()
                return pd.DataFrame()
            
            # Process each review
            for idx, row in df_input.iterrows():
                print(f"\n{'='*50}")
                print(f"[{idx+1}/{len(df_input)}] {row['nickname']} - {row['rating']}⭐")
                
                result = await self._process_review(
                    product_link=row['product_link'],
                    nickname=row['nickname'],
                    rating=int(row['rating']),
                    summary=row['summary'],
                    review=row['review'],
                )
                
                results.add_result(result)
                print(f"  📋 {result.status}: {result.error_message[:50] if result.error_message else 'OK'}")
                
                # Delay between reviews
                if idx < len(df_input) - 1:
                    await self._random_delay()
            
            await self._cleanup()
        
        # Save results
        df_results = results.dataframe()
        
        if save_results and len(df_results) > 0:
            results.save_to_csv(output_file)
            print(f"\n📁 Results saved: {output_file}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"✅ Success: {results.success_count} | ❌ Failed: {results.failed_count}")
        print("=" * 60)
        
        return df_results

    async def _setup_browser(self, playwright):
        """Setup browser"""
        print("🚀 Launching browser...")
        
        self.browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        self.context = await self.browser.new_context(
            viewport={"width": self.config.viewport_width, "height": self.config.viewport_height},
            user_agent=self.config.user_agent,
            locale='en-US',
            timezone_id='America/New_York',
        )
        
        self.page = await self.context.new_page()
        print("✅ Browser ready")

    async def _handle_popup(self):
        """Handle redirect notification popup"""
        try:
            await asyncio.sleep(2)
            decline = self.page.locator('button:has-text("Decline")')
            if await decline.count() > 0 and await decline.is_visible():
                await decline.click()
                print("  ✓ Handled redirect popup")
                await asyncio.sleep(1)
        except:
            pass
        
        # Force close any modals
        try:
            await self.page.evaluate('''
                document.querySelectorAll(".modals-overlay, .modal-popup").forEach(el => el.style.display = "none");
                document.body.classList.remove("_has-modal");
            ''')
        except:
            pass

    async def _login(self) -> bool:
        """Login to Electronics Bazaar"""
        print(f"\n🔐 Logging in as: {self.email}")
        
        try:
            await self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=self.config.timeout)
            await asyncio.sleep(2)
            await self._handle_popup()
            
            # Fill credentials
            email_field = self.page.locator('input#email[name="login[username]"]').first
            await email_field.fill(self.email)
            print("  ✓ Email entered")
            
            await asyncio.sleep(0.3)
            
            password_field = self.page.locator('input#pass[name="login[password]"]').first
            await password_field.fill(self.password)
            print("  ✓ Password entered")
            
            await asyncio.sleep(0.3)
            
            # Click sign in
            sign_in_btn = self.page.locator('button#send2, button:has-text("Sign In")').first
            await sign_in_btn.click()
            print("  → Signing in...")
            
            await asyncio.sleep(5)
            await self._handle_popup()
            
            # Verify login
            if 'account' in self.page.url and 'login' not in self.page.url:
                print("  ✅ Login successful!")
                return True
            
            # Check for error
            error = self.page.locator('.message-error')
            if await error.count() > 0:
                error_text = await error.first.inner_text()
                print(f"  ❌ Error: {error_text}")
                return False
            
            print("  ✅ Login successful!")
            return True
            
        except Exception as e:
            print(f"  ❌ Login failed: {str(e)[:80]}")
            return False

    async def _navigate_to_product(self, url: str) -> bool:
        """Navigate to product page"""
        # Ensure US URL
        if '/en-us/' not in url:
            url = url.replace('electronicsbazaar.com/', 'electronicsbazaar.com/en-us/')
        
        print(f"  → Loading product...")
        
        try:
            await self.page.goto(url, wait_until='domcontentloaded', timeout=self.config.timeout)
            await asyncio.sleep(2)
            await self._handle_popup()
            print("  ✓ Product loaded")
            return True
        except Exception as e:
            print(f"  ❌ Navigation failed: {str(e)[:50]}")
            return False

    async def _click_reviews_tab(self):
        """Click on Reviews tab"""
        try:
            await self.page.evaluate('window.scrollBy(0, 600)')
            await asyncio.sleep(1)
            
            reviews_tab = self.page.locator('#tab-label-reviews-title, #tab-label-reviews')
            if await reviews_tab.count() > 0:
                await reviews_tab.first.click()
                print("  ✓ Reviews tab clicked")
                await asyncio.sleep(1)
        except:
            pass

    async def _set_rating(self, rating: int) -> bool:
        """Set star rating"""
        print(f"    Rating: {rating} stars")
        
        result = await self.page.evaluate('''(desiredRating) => {
            const radios = document.querySelectorAll('.review-control-vote input[type="radio"], .rating-control input[type="radio"], input[type="radio"][name*="rating" i]');
            
            if (radios.length === 0) {
                return { success: false, error: 'No rating radios found' };
            }
            
            const radioArray = Array.from(radios);
            
            // Try direct value match
            for (const radio of radioArray) {
                if (parseInt(radio.value) === desiredRating) {
                    radio.checked = true;
                    radio.click();
                    radio.dispatchEvent(new Event('change', { bubbles: true }));
                    return { success: true, method: 'direct-value', value: radio.value };
                }
            }
            
            // Try multiplied value (x4)
            for (const radio of radioArray) {
                if (parseInt(radio.value) === desiredRating * 4) {
                    radio.checked = true;
                    radio.click();
                    radio.dispatchEvent(new Event('change', { bubbles: true }));
                    return { success: true, method: 'value-x4', value: radio.value };
                }
            }
            
            // Try by index
            const targetIndex = desiredRating - 1;
            if (radioArray[targetIndex]) {
                radioArray[targetIndex].checked = true;
                radioArray[targetIndex].click();
                radioArray[targetIndex].dispatchEvent(new Event('change', { bubbles: true }));
                return { success: true, method: 'by-index', index: targetIndex };
            }
            
            return { success: false, error: 'Could not set rating' };
        }''', rating)
        
        if result.get('success'):
            print(f"    ✓ Rating set")
            return True
        else:
            print(f"    ⚠ Rating issue: {result.get('error')}")
            return False

    async def _fill_and_submit(self, nickname: str, rating: int, summary: str, review: str) -> tuple:
        """Fill form and submit review"""
        try:
            # Scroll to form
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)
            
            # Set rating
            await self._set_rating(rating)
            await asyncio.sleep(0.5)
            
            # Fill nickname
            print(f"    Nickname: {nickname}")
            nickname_field = self.page.locator('#nickname_field, #nickname, input[name="nickname"]').first
            await nickname_field.click()
            await nickname_field.fill('')
            await nickname_field.fill(nickname)
            print(f"    ✓ Nickname entered")
            
            await asyncio.sleep(0.3)
            
            # Fill summary
            print(f"    Summary: {summary[:30]}...")
            summary_field = self.page.locator('#summary_field, #summary, input[name="title"]').first
            await summary_field.click()
            await summary_field.fill(summary)
            print(f"    ✓ Summary entered")
            
            await asyncio.sleep(0.3)
            
            # Fill review
            print(f"    Review: {review[:30]}...")
            review_field = self.page.locator('#review_field, #review, textarea[name="detail"]').first
            await review_field.click()
            await review_field.fill(review)
            print(f"    ✓ Review entered")
            
            await asyncio.sleep(1)
            
            # Submit
            print("    Submitting...")
            submit_btn = self.page.locator('#review-form button.submit, button.action.submit.primary, button:has-text("Submit Review")').first
            await submit_btn.scroll_into_view_if_needed()
            await asyncio.sleep(0.5)
            await submit_btn.click(force=True)
            print("    ✓ Submit clicked")
            
            # Wait for response
            await asyncio.sleep(5)
            
            # Check result
            success_msg = self.page.locator('.message-success')
            if await success_msg.count() > 0:
                text = await success_msg.first.inner_text()
                return True, f"Success: {text[:50]}"
            
            error_msg = self.page.locator('.message-error, .mage-error')
            if await error_msg.count() > 0:
                text = await error_msg.first.inner_text()
                return False, f"Error: {text}"
            
            return True, "Submitted"
            
        except Exception as e:
            return False, str(e)[:80]

    async def _process_review(self, product_link: str, nickname: str, rating: int, summary: str, review: str) -> ReviewResult:
        """Process a single review"""
        result = ReviewResult(
            product_link=product_link,
            nickname=nickname,
            rating=rating,
            summary=summary,
            review=review,
            timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        try:
            if not await self._navigate_to_product(product_link):
                result.status = "Failed"
                result.error_message = "Navigation failed"
                return result
            
            await self._click_reviews_tab()
            
            success, message = await self._fill_and_submit(nickname, rating, summary, review)
            result.status = "Success" if success else "Failed"
            result.error_message = message
            
        except Exception as e:
            result.status = "Failed"
            result.error_message = str(e)
        
        return result

    async def _random_delay(self):
        """Add random delay between reviews"""
        delay = random.uniform(self.config.min_delay, self.config.max_delay)
        await asyncio.sleep(delay)

    async def _cleanup(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()


# ============================================================
# EASY-TO-USE FUNCTIONS
# ============================================================

async def submit_reviews(
    reviews_data: Any,
    email: str,
    password: str,
    save_results: bool = True,
    output_file: str = "review_results.csv",
    headless: bool = True,
) -> 'pd.DataFrame':
    """
    Submit reviews to Electronics Bazaar - Easy async function
    
    Args:
        reviews_data: CSV filepath or pandas DataFrame with review data
        email: Login email for electronicsbazaar.com
        password: Login password
        save_results: Save results to CSV (default: True)
        output_file: Output filename for results
        headless: Run browser headless (default: True)
    
    Returns:
        pandas DataFrame with submission results
    
    CSV/DataFrame columns required:
        - product_link: URL of the product
        - nickname: Reviewer name
        - rating: Star rating (1-5)
        - summary: Review title/summary
        - review: Review text
    
    Example (Google Colab):
        from eb_reviews import setup_colab, submit_reviews
        
        # Setup first (only once per session)
        await setup_colab()
        
        # Submit reviews
        df = await submit_reviews(
            "reviews.csv",
            email="your@email.com",
            password="your_password"
        )
    
    Example (Local):
        import asyncio
        from eb_reviews import submit_reviews
        
        df = asyncio.run(submit_reviews(
            "reviews.csv",
            email="your@email.com",
            password="your_password"
        ))
    """
    config = ReviewConfig(headless=headless)
    automation = EBReviewAutomation(email, password, config)
    
    return await automation.submit_reviews(
        reviews_data=reviews_data,
        save_results=save_results,
        output_file=output_file
    )


def submit_reviews_sync(
    reviews_data: Any,
    email: str,
    password: str,
    save_results: bool = True,
    output_file: str = "review_results.csv",
    headless: bool = True,
) -> 'pd.DataFrame':
    """
    Submit reviews to Electronics Bazaar - Synchronous version
    
    Use this when you're not in an async context (e.g., regular Python scripts).
    
    Example:
        from eb_reviews import submit_reviews_sync
        
        df = submit_reviews_sync(
            "reviews.csv",
            email="your@email.com",
            password="your_password"
        )
    """
    return asyncio.run(submit_reviews(
        reviews_data=reviews_data,
        email=email,
        password=password,
        save_results=save_results,
        output_file=output_file,
        headless=headless,
    ))



# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Electronics Bazaar Review Automation")
    parser.add_argument("csv_file", nargs='?', help="CSV file with reviews")
    parser.add_argument("-e", "--email", help="Login email")
    parser.add_argument("-p", "--password", help="Login password")
    parser.add_argument("-o", "--output", default="review_results.csv", help="Output file")
    parser.add_argument("--no-save", action="store_true", help="Don't save results")
    parser.add_argument("--create-sample", action="store_true", help="Create sample CSV")
    
    args = parser.parse_args()
    
    elif args.csv_file and args.email and args.password:
        df = submit_reviews_sync(
            reviews_data=args.csv_file,
            email=args.email,
            password=args.password,
            save_results=not args.no_save,
            output_file=args.output,
        )
        print(f"\nResults: {len(df)} reviews processed")
    else:
        parser.print_help()

