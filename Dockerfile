# Use a stable Playwright image with browsers included
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip

# IMPORTANT: Install matching Playwright version
RUN pip install playwright==1.45.0

# Install remaining dependencies
RUN pip install -r requirements.txt

# Expose port (Railway will set PORT env variable)
EXPOSE 8000

# Start FastAPI server using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
