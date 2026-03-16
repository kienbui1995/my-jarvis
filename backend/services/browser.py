"""Browser automation — Playwright headless for web browsing tasks."""
import asyncio
import base64
import logging
import re

logger = logging.getLogger(__name__)

# Reuse a single browser instance across requests
_browser = None
_lock = asyncio.Lock()

MAX_PAGE_TEXT = 5000
NAVIGATION_TIMEOUT = 15000  # 15s


async def _get_browser():
    global _browser
    async with _lock:
        if _browser and _browser.is_connected():
            return _browser
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()
        _browser = await pw.chromium.launch(headless=True)
        logger.info("Playwright browser launched")
        return _browser


async def navigate_and_extract(url: str) -> dict:
    """Navigate to URL, extract text content and take screenshot.

    Returns {"text": str, "title": str, "screenshot_b64": str, "url": str}
    """
    browser = await _get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
        title = await page.title()
        # Extract readable text
        text = await page.evaluate("""() => {
            const sel = document.querySelectorAll('article, main, .content, #content, body');
            const el = sel[0] || document.body;
            return el.innerText || el.textContent || '';
        }""")
        text = re.sub(r'\n{3,}', '\n\n', text or "").strip()[:MAX_PAGE_TEXT]
        # Screenshot
        screenshot = await page.screenshot(type="png", full_page=False)
        return {
            "text": text,
            "title": title,
            "screenshot_b64": base64.b64encode(screenshot).decode(),
            "url": page.url,
        }
    finally:
        await page.close()


async def click_and_extract(url: str, selector: str) -> dict:
    """Navigate to URL, click element, then extract resulting page."""
    browser = await _get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
        await page.click(selector, timeout=5000)
        await page.wait_for_load_state("domcontentloaded", timeout=10000)
        title = await page.title()
        text = await page.evaluate("""() => {
            const sel = document.querySelectorAll('article, main, .content, #content, body');
            const el = sel[0] || document.body;
            return el.innerText || el.textContent || '';
        }""")
        text = re.sub(r'\n{3,}', '\n\n', text or "").strip()[:MAX_PAGE_TEXT]
        return {"text": text, "title": title, "url": page.url}
    finally:
        await page.close()


async def fill_and_submit(url: str, fields: dict[str, str], submit_selector: str = "") -> dict:
    """Navigate to URL, fill form fields, optionally submit."""
    browser = await _get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
        for selector, value in fields.items():
            await page.fill(selector, value, timeout=5000)
        if submit_selector:
            await page.click(submit_selector, timeout=5000)
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
        title = await page.title()
        text = await page.evaluate("""() => {
            const sel = document.querySelectorAll('article, main, .content, #content, body');
            const el = sel[0] || document.body;
            return el.innerText || el.textContent || '';
        }""")
        text = re.sub(r'\n{3,}', '\n\n', text or "").strip()[:MAX_PAGE_TEXT]
        return {"text": text, "title": title, "url": page.url}
    finally:
        await page.close()


async def screenshot_page(url: str, full_page: bool = False) -> str:
    """Take a screenshot of a URL. Returns base64-encoded PNG."""
    browser = await _get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
        data = await page.screenshot(type="png", full_page=full_page)
        return base64.b64encode(data).decode()
    finally:
        await page.close()
