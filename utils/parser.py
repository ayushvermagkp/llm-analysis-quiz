from bs4 import BeautifulSoup

async def process_quiz_page(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text().lower()

    # Example detection logic
    if "sum of the" in text and "value" in text:
        # Example answer
        answer = 123  # You will improve later
        submit_url = extract_submit_url(text)
        return answer, submit_url

    return "unknown", extract_submit_url(text)


def extract_submit_url(text):
    import re
    pattern = r"https?://[^\s\"]+submit[^\s\"]*"
    match = re.search(pattern, text)
    return match.group(0) if match else None

