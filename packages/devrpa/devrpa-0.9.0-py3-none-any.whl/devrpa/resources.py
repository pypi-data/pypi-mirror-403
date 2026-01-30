
import asyncio
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser

class ResourcePool:
    def __init__(self, browser_count: int = 1):
        self.browser_count = browser_count
        self._browsers: List[Browser] = []
        self._playwright = None
        self._browser_sem = None # Semaphore to limit usage
        self._active_browsers = [] # Stack of available browsers

    async def initialize(self):
        if self.browser_count > 0:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser_sem = asyncio.Semaphore(self.browser_count)
            # Create browsers? Or lazy load?
            # Let's simple lazy load/pool limit mechanism.
            # We don't necessarily keep 5 browsers open, we just limit CONCURRENT browsers.
            # But the prompt said "Reuse Playwright browser instances".
            # So we should create them and keep them open.
            
            for _ in range(self.browser_count):
                b = await self._playwright.chromium.launch(headless=True, args=["--no-sandbox"])
                self._browsers.append(b)
                self._active_browsers.append(b)
    
    async def cleanup(self):
        for b in self._browsers:
            await b.close()
        if self._playwright:
            await self._playwright.stop()

    @asynccontextmanager
    async def get_browser(self) -> Browser:
        # Simple pool: Pop from list, yield, push back
        if not self._browser_sem:
            yield None # No pool initialized?
            return

        async with self._browser_sem:
            browser = self._active_browsers.pop()
            try:
                yield browser
            finally:
                self._active_browsers.append(browser)
