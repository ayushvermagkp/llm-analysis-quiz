from playwright.async_api import async_playwright


async def fetch_quiz_page(url: str) -> str:
    """
    Uses Playwright to open the quiz URL in a headless Chromium browser
    and returns the fully rendered HTML (after JavaScript execution).
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        html = await page.content()
        await browser.close()
        return html
