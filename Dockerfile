# Dockerfile - stable Playwright image (contains browsers)
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

WORKDIR /app

# Copy project
COPY . .

# Upgrade pip and install requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port (Railway will override PORT env)
EXPOSE 8000

# Start app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
