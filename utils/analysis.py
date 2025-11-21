import httpx

async def submit_answer(email, secret, quiz_url, submit_url, answer):
    payload = {
        "email": email,
        "secret": secret,
        "url": quiz_url,
        "answer": answer
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(submit_url, json=payload)

    try:
        return response.json()
    except:
        return {"correct": False, "error": "Invalid JSON from submit server"}
