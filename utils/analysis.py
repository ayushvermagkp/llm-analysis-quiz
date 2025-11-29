import httpx
from typing import Any, Dict


async def post_answer(submit_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends the answer JSON to the quiz's submit URL and returns
    the parsed JSON response from the server.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(submit_url, json=payload)

    try:
        return resp.json()
    except Exception:
        # If server responds with non-JSON, wrap it in a dict for safety
        return {
            "correct": False,
            "error": "Non-JSON response from submit endpoint",
            "status_code": resp.status_code,
            "text": resp.text[:500],
        }
