
from typing import Any, List, Callable, Optional, Union
from ..workflow import Step
from ..core import StepResult, ExecutionContext
import asyncio

# Action takes (page, context)
# Since actions are likely modifying page state, they should be async or we run them in executor?
# Playwright objects are async in async mode. So actions MUST be async functions.
Action = Callable[[Any, ExecutionContext], Any] # Awaitable

class WebStep(Step):
    def __init__(
        self, 
        name: str, 
        headless: bool = True,
        max_retries: int = 2,
        retry_backoff_seconds: float = 2.0,
        timeout_seconds: Optional[float] = 30.0
    ):
        super().__init__(name=name, max_retries=max_retries, retry_backoff_seconds=retry_backoff_seconds, timeout_seconds=timeout_seconds)
        self.headless = headless
        
        self.actions: List[Callable] = []
        self.actions: List[Action] = []
        self._browser_context_args = {}

    def goto(self, url: str) -> "WebStep":
        async def _act(page, ctx):
            resolved_url = ctx.resolve(url)
            await page.goto(resolved_url)
        self.actions.append(_act)
        return self

    def click(self, selector: str) -> "WebStep":
        async def _act(page, ctx):
            await page.click(selector)
        self.actions.append(_act)
        return self

    def type(self, selector: str, text: str) -> "WebStep":
        async def _act(page, ctx):
            resolved_text = ctx.resolve(text)
            await page.fill(selector, resolved_text)
        self.actions.append(_act)
        return self

    def wait_for_text(self, text: str, timeout_ms: int = 10000) -> "WebStep":
        async def _act(page, ctx):
            resolved_text = ctx.resolve(text)
            await page.wait_for_selector(f"text={resolved_text}", timeout=timeout_ms)
        self.actions.append(_act)
        return self
    
    def trigger_download(self, selector: str, save_as: str) -> "WebStep":
        async def _act(page, ctx):
            filename = ctx.resolve(save_as)
            save_path = ctx.artifacts_dir / filename
            
            async with page.expect_download() as download_info:
                await page.click(selector)
            
            download = await download_info.value
            await download.save_as(str(save_path))
            ctx.data[f"{self.name}_download_path"] = str(save_path)
        self.actions.append(_act)
        return self
    
    async def execute(self, context: ExecutionContext) -> StepResult:
        from playwright.async_api import async_playwright
        
        data = {}
        error = None
        
        # Function to capture failure needs to be robust (might not have page if fail early)
        async def capture_failure(page):
            try:
                fail_dir = context.artifacts_dir / "failures"
                fail_dir.mkdir(parents=True, exist_ok=True)
                path = fail_dir / f"{self.name}_failure.png"
                await page.screenshot(path=str(path))
            except Exception:
                pass

        async def run_actions(browser):
            browser_ctx = await browser.new_context(**self._browser_context_args)
            page = await browser_ctx.new_page()
            
            if self.timeout_seconds:
                page.set_default_timeout(self.timeout_seconds * 1000)
            
            try:
                for act in self.actions:
                    await act(page, context)
            except Exception as e:
                await capture_failure(page)
                raise e
            finally:
                await page.close()
                await browser_ctx.close()

        # Check for ResourcePool
        if context.resources and hasattr(context.resources, "get_browser"):
            async with context.resources.get_browser() as pooled_browser:
                if pooled_browser:
                    try:
                        await run_actions(pooled_browser)
                        return StepResult(name=self.name, success=True, data=data)
                    except Exception as e:
                        return StepResult(name=self.name, success=False, error=e, data=data)

        # Fallback: Launch own
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless, 
                args=["--no-sandbox"]
            )
            try:
                await run_actions(browser)
                return StepResult(name=self.name, success=True, data=data)
            except Exception as e:
                return StepResult(name=self.name, success=False, error=e)
            finally:
                await browser.close()
