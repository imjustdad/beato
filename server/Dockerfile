# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Llama.cpp (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY . .

# Set environment variable for unbuffered logging
ENV PYTHONUNBUFFERED=1

# Expose FastAPI port
EXPOSE 8000

# Default command
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]