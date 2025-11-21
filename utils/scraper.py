from playwright.async_api import async_playwright

async def fetch_quiz_page(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        html = await page.content()  # rendered HTML after JS executes
        await browser.close()
        return html
