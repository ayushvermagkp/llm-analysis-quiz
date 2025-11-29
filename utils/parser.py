from bs4 import BeautifulSoup
from dataclasses import dataclass
import base64
import json
import re
from typing import Any, Optional


@dataclass
class QuizInterpretation:
    """Represents what we understood from a single quiz page."""
    submit_url: Optional[str]
    answer: Any
    summary: str


async def interpret_quiz_page(html: str, quiz_url: str) -> QuizInterpretation:
    """
    Takes the rendered HTML (after JS execution) and tries to:
    - Decode any base64-encoded quiz instructions.
    - Extract the submit URL.
    - Infer the answer if the question is simple enough.
    """

    soup = BeautifulSoup(html, "html.parser")
    visible_text = soup.get_text(" ", strip=True)

    # Try to decode any atob(`...`) blocks we see in the raw HTML.
    decoded_blocks = _decode_atob_blocks(html)

    combined_text = visible_text + " " + " ".join(decoded_blocks)
    combined_lower = combined_text.lower()

    submit_url = _find_submit_url(combined_text)
    summary = combined_text[:800]  # keep a short snippet for debugging

    # Default: we don't know the answer yet.
    answer: Any = None

    # ---------------------------------------------------------
    # Simple heuristic: look for an "answer" field in a JSON
    # snippet inside the decoded block, or patterns like:
    # "answer": 12345
    # ---------------------------------------------------------
    json_answer = _extract_answer_from_json_block(decoded_blocks)
    if json_answer is not None:
        answer = json_answer
        return QuizInterpretation(submit_url=submit_url, answer=answer, summary=summary)

    # Example heuristic for questions like:
    # "What is the sum of the 'value' column in ..."
    if "sum of" in combined_lower and "value" in combined_lower:
        # At this point, a full implementation would:
        # - Download the linked file (e.g., PDF/CSV)
        # - Extract the relevant data
        # - Compute the aggregation
        #
        # For now, we leave answer=None so that the quiz server
        # can tell us if the missing answer is wrong.
        answer = None
        return QuizInterpretation(submit_url=submit_url, answer=answer, summary=summary)

    # Fallback: we don't know the answer yet, but we at least return submit URL
    return QuizInterpretation(submit_url=submit_url, answer=answer, summary=summary)


# --------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------

def _decode_atob_blocks(html: str) -> list[str]:
    """
    Finds JavaScript atob(`...`) blocks in the HTML and decodes each one.
    Returns a list of decoded text blocks.
    """
    pattern = r"atob\(`([^`]+)`\)"
    blocks = re.findall(pattern, html)
    decoded: list[str] = []

    for b64_chunk in blocks:
        try:
            decoded_text = base64.b64decode(b64_chunk).decode("utf-8", errors="ignore")
            decoded.append(decoded_text)
        except Exception:
            # Ignore chunks that fail to decode
            continue

    return decoded


def _find_submit_url(text: str) -> Optional[str]:
    """
    Extracts the submit URL from text of the form:
    'Post your answer to https://example.com/submit ...'
    """
    pattern = r"https?://[^\s'\"<>]+submit[^\s'\"<>]*"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def _extract_answer_from_json_block(decoded_blocks: list[str]) -> Optional[Any]:
    """
    If any decoded block contains a JSON blob with an "answer" field,
    pull it out. This works nicely with the sample structure in the spec.
    """
    for block in decoded_blocks:
        # Try to find a JSON object in <pre>...</pre> or similar
        # For example:
        # {
        #   "email": "...",
        #   "secret": "...",
        #   "url": "...",
        #   "answer": 12345
        # }
        json_like = _extract_braced_json(block)
        for candidate in json_like:
            try:
                data = json.loads(candidate)
                if "answer" in data:
                    return data["answer"]
            except Exception:
                continue
    return None


def _extract_braced_json(text: str) -> list[str]:
    """
    Very lightweight brace-matching to pull out JSON-like substrings.
    Not perfect, but good enough for the demo/test.
    """
    results: list[str] = []
    stack = []
    start_idx = None

    for i, ch in enumerate(text):
        if ch == "{":
            if not stack:
                start_idx = i
            stack.append(ch)
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack and start_idx is not None:
                    results.append(text[start_idx: i + 1])
                    start_idx = None

    return results
