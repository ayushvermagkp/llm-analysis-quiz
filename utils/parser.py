# utils/parser.py
from dataclasses import dataclass
from typing import Any, Optional
from bs4 import BeautifulSoup
import base64
import re
from urllib.parse import urljoin

@dataclass
class QuizInterpretation:
    submit_url: Optional[str]
    answer: Any
    summary: str


async def interpret_quiz_page(html: str, base_url: str) -> QuizInterpretation:
    """
    Robust interpretation:
      - parse rendered HTML
      - decode atob(`...`) Base64 blocks (many quizzes hide content this way)
      - attempt to extract JSON block answer or simple heuristics
      - robustly extract submit URL (handles spaces/newlines/broken formatting)
    """
    # 1) plain visible text
    soup = BeautifulSoup(html, "html.parser")
    visible_text = soup.get_text(" ", strip=True)

    # 2) decode any atob(`...`) blocks and join
    decoded_blocks = _decode_atob_blocks(html)
    decoded_text = " ".join(decoded_blocks) if decoded_blocks else ""

    # 3) combined text for searching
    combined = " ".join([visible_text, decoded_text]).strip()
    combined_clean = _normalize_whitespace(combined)

    # 4) find submit url (robust)
    submit_url = _extract_submit_url(combined_clean)

    # if submit_url is a relative path (starts with '/'), make absolute
    if submit_url and submit_url.startswith("/"):
        submit_url = urljoin(base_url, submit_url)

    # 5) try to extract an "answer" from any JSON block in decoded content
    answer = _extract_answer_from_decoded(decoded_blocks)

    # 6) fallback heuristics: detect simple "sum of ... value" questions (demo)
    lower = combined_clean.lower()
    if answer is None:
        if "sum of" in lower and "value" in lower:
            # We don't implement full PDF/table extraction in this function.
            # Returning None allows the remote server to judge; you can implement
            # file download+parsing in a later step if required by the quiz.
            answer = None

    # 7) Return a short summary for debugging as well
    summary = combined_clean[:1600]
    return QuizInterpretation(submit_url=submit_url, answer=answer, summary=summary)


# -------------------------
# Helpers
# -------------------------
def _normalize_whitespace(s: str) -> str:
    # Remove zero-width and control characters, collapse whitespace
    s = re.sub(r"[\u200B\u200C\u200D\uFEFF]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _decode_atob_blocks(html: str):
    """
    Find atob(`...`) occurrences and decode base64 inside.
    Accept multiple patterns and ignore decode failures.
    """
    # pattern captures content inside atob(`...`) or atob("...") forms
    patterns = [
        r"atob\(\s*`([^`]+)`\s*\)",
        r"atob\(\s*\"([^\"]+)\"\s*\)",
        r"atob\(\s*'([^']+)'\s*\)",
    ]
    decoded = []
    for pat in patterns:
        for m in re.findall(pat, html, flags=re.DOTALL):
            b64 = m.strip()
            # Remove spaces/newlines inside base64 block that may have been wrapped
            b64 = re.sub(r"\s+", "", b64)
            try:
                txt = base64.b64decode(b64).decode("utf-8", errors="ignore")
                decoded.append(txt)
            except Exception:
                # ignore decode failures
                continue
    return decoded


def _extract_submit_url(text: str) -> Optional[str]:
    """
    Robustly extract '.../submit' URLs even when broken by spaces or newlines.
    Steps:
      - normalize newlines
      - fix 'http : //', 'https : //' broken protocol spaces
      - remove spaces around slashes and dots in domain when likely broken
      - then run a simple regex that searches for 'submit' in URL
    """
    if not text:
        return None

    t = text.replace("\r", " ").replace("\n", " ")
    # fix protocol breaks: "https : //"
    t = re.sub(r"https?\s*:\s*//", lambda m: m.group(0).replace(" ", ""), t, flags=re.IGNORECASE)

    # fix common broken patterns: "domain . com" => "domain.com", " /submit" => "/submit"
    # be conservative: only remove spaces around dots/slashes when adjacent to alnum
    t = re.sub(r"(?<=\w)\s+/\s*(?=submit)", "/", t, flags=re.IGNORECASE)
    t = re.sub(r"(?<=\w)\s+\.\s+(?=\w)", ".", t)

    # collapse multiple spaces
    t = " ".join(t.split())

    # final regex to match URL that contains 'submit' word
    pattern = r"https?://[^\s'\"<>]*submit[^\s'\"<>]*"
    m = re.search(pattern, t, flags=re.IGNORECASE)
    if m:
        return m.group(0)

    # If not absolute URL, try to find relative "/submit" pattern and return that
    rel = re.search(r"(/[\w\-/]*submit[^\s'\"<>]*)", t, flags=re.IGNORECASE)
    if rel:
        return rel.group(1)

    return None


def _extract_answer_from_decoded(blocks):
    """
    Look for JSON-like blocks that include an "answer" field.
    If found and parseable, return that answer.
    """
    if not blocks:
        return None

    for block in blocks:
        # naive brace-based extraction of JSON substrings
        candidates = _extract_braced_json(block)
        for cand in candidates:
            try:
                import json
                data = json.loads(cand)
                if "answer" in data:
                    return data["answer"]
            except Exception:
                continue
    return None


def _extract_braced_json(text: str):
    results = []
    stack = []
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if not stack:
                start = i
            stack.append("{")
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack and start is not None:
                    results.append(text[start: i+1])
                    start = None
    return results
