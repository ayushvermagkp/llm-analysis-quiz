from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, EmailStr, HttpUrl, ValidationError
from typing import Any, Optional
import time
import os

from utils.scraper import fetch_quiz_page
from utils.parser import interpret_quiz_page
from utils.analysis import post_answer

# redeploy trigger****
# ----------------------------
# Configuration
# ----------------------------

# Read secret from env if present, otherwise fall back to a default.
# Make sure the value here matches what you filled in the Google Form.
SECRET = os.getenv("QUIZ_SECRET", "ayush$23f1001266@123")

# 3-minute limit from the time their POST hits our endpoint
QUIZ_TIME_LIMIT_SECONDS = 3 * 60


# ----------------------------
# Request schema
# ----------------------------

class QuizRequest(BaseModel):
    email: EmailStr
    secret: str
    url: HttpUrl

    class Config:
        extra = "allow"  # ignore any extra fields they send


# ----------------------------
# FastAPI app
# ----------------------------

app = FastAPI(title="LLM Analysis Quiz Solver")


@app.get("/")
async def healthcheck():
    """Simple health-check for debugging / viva."""
    return {
        "status": "ok",
        "message": "LLM Analysis Quiz API is running",
    }


@app.post("/api/quiz")
async def quiz_endpoint(raw_request: Request):
    """
    Entry point for the evaluation.
    - Validates JSON payload.
    - Checks secret.
    - Visits quiz URL(s) and solves them in a loop.
    """

    # -------- 1. Parse JSON safely --------
    try:
        body = await raw_request.json()
    except Exception:
        # Spec: HTTP 400 for invalid JSON
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        req = QuizRequest(**body)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Bad request: {e.errors()}")

    # -------- 2. Verify secret --------
    if req.secret != SECRET:
        # Spec: HTTP 403 for invalid secrets
        raise HTTPException(status_code=403, detail="Invalid secret")

    # From this point on, secret is valid. We must respond 200,
    # even if something goes wrong inside the quiz logic.

    start = time.monotonic()
    current_url: str = str(req.url)
    last_result: Optional[dict[str, Any]] = None

    # -------- 3. Quiz solving loop --------
    while True:
        elapsed = time.monotonic() - start
        if elapsed > QUIZ_TIME_LIMIT_SECONDS:
            return {
                "error": "Time limit exceeded",
                "seconds": elapsed,
                "last_result": last_result,
            }

        # (a) Fetch the quiz page (JS-rendered)
        page_html = await fetch_quiz_page(current_url)

        # (b) Interpret instructions: find submit URL + answer (if possible)
        interpretation = await interpret_quiz_page(page_html, current_url)

        if interpretation.submit_url is None:
            # We cannot continue without a submit URL – return debug info instead of crashing.
            return {
                "error": "Failed to detect submit URL",
                "reason": "parser_failed",
                "quiz_url": current_url,
                "debug": {
                    "summary": interpretation.summary,
                },
            }

        # (c) Post our answer
        answer_payload = {
            "email": req.email,
            "secret": req.secret,
            "url": current_url,
            "answer": interpretation.answer,
        }

        submission_response = await post_answer(
            submit_url=interpretation.submit_url,
            payload=answer_payload,
        )
        last_result = submission_response

        # Quiz server may tell us if we were correct and give a new URL.
        next_url = submission_response.get("url")
        is_correct = bool(submission_response.get("correct", False))

        if next_url:
            # They gave us the next quiz URL – move on.
            current_url = next_url
            continue

        # No next URL → either quiz is over or we got a final failure.
        return {
            "done": True,
            "correct": is_correct,
            "final_quiz_url": current_url,
            "answer_submitted": interpretation.answer,
            "server_response": submission_response,
        }


