from bs4 import BeautifulSoup
import re

async def process_quiz_page(html):
    """
    Parse quiz page HTML and extract:
    - The answer (if identifiable)
    - The submit URL
    """

    soup = BeautifulSoup(html, "html.parser")

    # Clean readable text from page
    text = soup.get_text(" ", strip=True)

    # Always extract submit URL (required for quiz)
    submit_url = extract_submit_url(text)
    if not submit_url:
        return None, None

    lower_text = text.lower()

    # ---------------------------
    # EXAMPLE: Identify a sum question
    # ---------------------------
    if "sum of" in lower_text and "value" in lower_text:
        # TODO: Replace this with real data extraction logic
        answer = 123  
        return answer, submit_url

    # If unable to detect quiz type yet, still return submit_url
    return None, submit_url


def extract_submit_url(text):
    """
    Extract submit URL from the quiz page text.
    The page usually contains something like:
    'Post your answer to https://example.com/submit with this JSON payload'
    """

    pattern = r"https?://[^\s'\"]*submit[^\s'\"]*"
    match = re.search(pattern, text)
    return match.group(0) if match else None
