# Use the latest Playwright image with browsers
FROM mcr.microsoft.com/playwright/python:v1.56.0-jammy

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
