# utils/analysis.py
import httpx
from typing import Any, Dict
from urllib.parse import urljoin
import asyncio

async def post_answer(submit_url: str, payload: Dict[str, Any], base_url: str = None) -> Dict[str, Any]:
    """
    Submits the answer to submit_url.
    If submit_url is relative (starts with '/'), join with base_url.
    Returns parsed JSON response or a safe dict describing failure.
    """
    if not submit_url:
        raise ValueError("submit_url is required")

    # Make absolute if relative path and base_url provided
    if submit_url.startswith("/") and base_url:
        submit_url = urljoin(base_url, submit_url)

    # Defensive: if submit_url seems malformed (contains spaces), sanitize
    submit_url = submit_url.strip().replace(" ", "")

    timeout = httpx.Timeout(30.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(submit_url, json=payload)
        except httpx.RequestError as exc:
            return {"correct": False, "error": f"Request error: {str(exc)}"}
        except asyncio.TimeoutError:
            return {"correct": False, "error": "Timeout while posting answer"}

    # Try to parse JSON
    try:
        return resp.json()
    except Exception:
        # If not JSON, return some helpful fields
        return {
            "correct": False,
            "status_code": resp.status_code,
            "text_preview": resp.text[:1000]
        }
