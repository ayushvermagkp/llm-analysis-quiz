LLM Analysis Quiz – Automated Quiz Solver

This project implements an automated pipeline that solves multi-step data analysis quizzes issued by the IITM BS Program's LLM Analysis Quiz evaluation system.

The server exposes a single POST endpoint that:

Validates the student's secret

Loads the quiz page (including JavaScript rendering)

Extracts instructions from Base64-encoded HTML

Identifies the submit URL

Computes the required answer

Submits solutions within 3 minutes

Automatically continues to next quiz until completion

🚀 Features

FastAPI backend

Fully asynchronous pipeline

JavaScript rendering using Playwright

Automatic Base64 decoding

Dynamic quiz text interpretation

URL extraction and normalization

Multi-step quiz solving

Automatic resubmission for wrong answers

Error-handling for all edge cases

Clean and modular code architecture

📡 API Endpoint
POST /api/quiz
Request JSON:
{
  "email": "your_email@example.com",
  "secret": "your_secret",
  "url": "https://example.com/quiz-123"
}

Behaviour:

Validates secret

Loads quiz page

Detects instructions

Computes answer (placeholder logic for demo)

Extracts submit URL

Submits answer

Continues until no next quiz

📁 Project Structure
│── main.py
│── requirements.txt
│── Dockerfile
│── railway.toml
│── utils/
│    ├── scraper.py
│    ├── parser.py
│    └── analysis.py

main.py

Handles:

Request validation

Time limit enforcement

Quiz iteration loop

scraper.py

Handles:

Full JavaScript rendering

Returning HTML

parser.py

Handles:

Base64 decoding

Instruction extraction

Submit URL detection

Preliminary question parsing

analysis.py

Handles:

Answer submission

Response normalization

🐳 Docker Usage

The project includes a Dockerfile for deployment.
Railway uses this Dockerfile directly—no manual build needed.

🧪 Testing

Send POST request (Postman / cURL):

{
  "email": "your_email@example.com",
  "secret": "your_secret",
  "url": "https://tds-llm-analysis.s-anand.net/demo"
}


Expected (demo URL is closed):

{
  "done": true,
  "correct": false,
  "server_response": {
    "error": "Deadline exceeded. Project closed"
  }
}

📝 License

MIT License (required for IITM evaluation).

👤 Author

Ayush Verma
IIT Madras BS Degree Program