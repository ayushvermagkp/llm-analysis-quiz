# utils/scraper.py
from playwright.async_api import async_playwright, Error as PlaywrightError
import asyncio

async def fetch_quiz_page(url: str) -> str:
    """
    Launch Playwright, navigate to URL, wait for network idle, return rendered HTML.
    Defensive settings used so it runs in containerized environments.
    """
    try:
        async with async_playwright() as p:
            # headless and no-sandbox for many container hosts
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            page = await browser.new_page()
            # set a sane navigation timeout (30s)
            page.set_default_navigation_timeout(30_000)
            await page.goto(url, wait_until="networkidle")
            html = await page.content()
            await browser.close()
            return html
    except PlaywrightError as e:
        raise RuntimeError(f"Playwright error: {e}") from e
    except asyncio.TimeoutError as e:
        raise RuntimeError("Timeout while loading page") from e
    except Exception as e:
        raise RuntimeError(f"Unknown scraping error: {e}") from e
