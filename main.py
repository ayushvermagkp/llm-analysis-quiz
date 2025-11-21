from fastapi import FastAPI, Request
import time

from utils.scraper import fetch_quiz_page
from utils.parser import process_quiz_page
from utils.analysis import submit_answer

app = FastAPI()

SECRET = "ayush$23f1001266@123"  # your secret


@app.get("/")
def root():
    return {"status": "ok", "message": "LLM Quiz API running"}


@app.post("/api/quiz")
async def quiz_endpoint(request: Request):
    # Parse input JSON
    try:
        payload = await request.json()
    except:
        return {"error": "Invalid JSON"}, 400

    # Validate secret
    if payload.get("secret") != SECRET:
        return {"error": "Forbidden"}, 403

    email = payload.get("email")
    url = payload.get("url")

    if not email or not url:
        return {"error": "Missing email or url"}, 400

    start_time = time.time()

    # Solve multi-step quiz
    while True:

        # 3-minute timeout
        if time.time() - start_time > 180:
            return {"error": "Time exceeded"}

        # 1. Fetch quiz page using Playwright
        html = await fetch_quiz_page(url)

        # 2. Parse quiz page for submit URL + answer
        answer, submit_url = await process_quiz_page(html)

        if not submit_url:
            return {
                "error": "Submit URL missing",
                "reason": "parser_failed",
                "debug_sample": html[:1500]
            }

        # 3. Submit answer
        result = await submit_answer(email, SECRET, url, submit_url, answer)

        # If correct and no next URL → quiz finished
        if result.get("correct") and not result.get("url"):
            return {
                "done": "Quiz ended",
                "answer_submitted": answer,
                "final_response": result
            }

        # If next URL → move to next quiz
        if result.get("url"):
            url = result["url"]
            continue

        # Otherwise retry same quiz
        continue
