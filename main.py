# main.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Any, Optional
import time
import os

from utils.scraper import fetch_quiz_page
from utils.parser import interpret_quiz_page, QuizInterpretation
from utils.analysis import post_answer

# Config: read secret from environment if set (safer)
SECRET = os.getenv("QUIZ_SECRET", "ayush$23f1001266@123")
TIME_LIMIT_SECONDS = int(os.getenv("QUIZ_TIME_LIMIT_SECONDS", 3 * 60))

app = FastAPI(title="LLM Analysis Quiz Solver")


class QuizRequest(BaseModel):
    email: EmailStr
    secret: str
    url: HttpUrl


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "LLM Analysis Quiz API is running"}


@app.post("/api/quiz")
async def quiz_endpoint(request: Request):
    # 1) Parse JSON payload safely
    try:
        payload = await request.json()
    except Exception:
        # Spec: 400 for invalid JSON
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 2) Validate request body with Pydantic (raises detailed errors -> 400)
    try:
        req = QuizRequest(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bad request: {e}")

    # 3) Secret check: 403 if mismatch
    if req.secret != SECRET:
        raise HTTPException(status_code=403, detail="Forbidden: invalid secret")

    start_time = time.monotonic()
    current_url: str = str(req.url)
    last_submission_result: Optional[dict[str, Any]] = None

    # Main solving loop: must finish within TIME_LIMIT_SECONDS
    while True:
        elapsed = time.monotonic() - start_time
        if elapsed > TIME_LIMIT_SECONDS:
            return {
                "error": "Time exceeded",
                "seconds_elapsed": elapsed,
                "last_submission_result": last_submission_result,
            }

        # 1) Fetch the page (Playwright rendering)
        try:
            html = await fetch_quiz_page(current_url)
        except Exception as e:
            # don't crash: return informative payload
            return {"error": "Failed to fetch quiz page", "detail": str(e)}

        # 2) Interpret page (Base64 decode, find submit URL, attempt to find answer)
        try:
            interpretation: QuizInterpretation = await interpret_quiz_page(html, current_url)
        except Exception as e:
            return {"error": "Parser exception", "detail": str(e)}

        # submit_url is mandatory to proceed
        if not interpretation.submit_url:
            # return useful debugging info but as 200 JSON per spec
            return {
                "error": "Failed to detect submit URL",
                "reason": "parser_failed",
                "quiz_url": current_url,
                "debug": {"summary": interpretation.summary[:1200]},
            }

        # 3) Prepare payload and submit (answer may be None)
        submission_payload = {
            "email": req.email,
            "secret": req.secret,
            "url": current_url,
            "answer": interpretation.answer,
        }

        try:
            submission_response = await post_answer(
                submit_url=interpretation.submit_url, payload=submission_payload, base_url=current_url
            )
        except Exception as e:
            last_submission_result = {"error": str(e)}
            # If submit fails, we retry the same page until time runs out.
            # Return helpful info so grader/debugging can follow.
            return {"error": "Submission failed", "detail": str(e)}

        last_submission_result = submission_response

        # 4) Decide next-step based on response
        # If server returns a `url`, follow it
        next_url = submission_response.get("url")
        correct_flag = bool(submission_response.get("correct", False))

        if next_url:
            # move to next quiz
            current_url = next_url
            continue

        # No next url => final response, either correct true/false
        return {
            "done": True,
            "correct": correct_flag,
            "final_quiz_url": current_url,
            "answer_submitted": interpretation.answer,
            "server_response": submission_response,
        }
