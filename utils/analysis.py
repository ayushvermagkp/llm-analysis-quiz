import httpx

async def submit_answer(email, secret, url, submit_url, answer):
    payload = {
        "email": email,
        "secret": secret,
        "url": url,
        "answer": answer
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(submit_url, json=payload)
        return r.json()
