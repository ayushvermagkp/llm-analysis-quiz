from bs4 import BeautifulSoup
import re
import base64

async def process_quiz_page(html):
    """
    Parses the rendered quiz page and extracts:
    - Quiz instructions
    - Submit URL
    - Answer (if detectable)
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Decode Base64 quiz content inside <script>
    decoded = extract_and_decode_base64(html)
    if decoded:
        text += " " + decoded

    submit_url = extract_submit_url(text)
    if not submit_url:
        return None, None

    lower = text.lower()

    # Example quiz type handling
    if "sum of" in lower and "value" in lower:
        # TODO: implement real logic
        answer = 123
        return answer, submit_url

    return None, submit_url


def extract_and_decode_base64(html):
    """
    Searches for atob(`...`) containing base64-encoded content.
    """
    pattern = r"atob\(`([^`]+)`\)"
    match = re.search(pattern, html)
    if not match:
        return None

    b64_text = match.group(1).strip()

    try:
        decoded = base64.b64decode(b64_text).decode("utf-8", errors="ignore")
        return decoded
    except:
        return None


def extract_submit_url(text):
    """
    Find the submit URL in the decoded quiz text.
    """
    pattern = r"https?://[^\s'\"]*submit[^\s'\"]*"
    match = re.search(pattern, text)
    return match.group(0) if match else None
