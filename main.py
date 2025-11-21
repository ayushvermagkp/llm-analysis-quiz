from fastapi import FastAPI, Request
import httpx, time

from utils.scraper import fetch_quiz_page
from utils.parser import process_quiz_page
from utils.analysis import submit_answer

app = FastAPI()

SECRET = "ayush$23f1001266@123"  # Change this


@app.post("/api/quiz")
async def quiz_endpoint(request: Request):
    try:
        payload = await request.json()
    except:
        return {"error": "Invalid JSON"}

    if payload.get("secret") != SECRET:
        return {"error": "Forbidden"}, 403

    email = payload["email"]
    url = payload["url"]

    start_time = time.time()

    while True:
        if time.time() - start_time > 180:  # 3 minutes
            return {"error": "Time exceeded"}

        html = await fetch_quiz_page(url)
        answer, submit_url = await process_quiz_page(html)

        result = await submit_answer(email, SECRET, url, submit_url, answer)

        if result.get("correct") and not result.get("url"):
            return {"done": "Quiz ended", "answer": answer}

        if result.get("url"):
            url = result["url"]  # Move to next quiz
        else:
            continue  # retry same quiz
