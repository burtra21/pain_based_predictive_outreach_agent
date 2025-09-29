FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and update pip
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements-simple.txt .
RUN pip install --no-cache-dir -r requirements-simple.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Expose port
EXPOSE 8002

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PORT=8002

# Command to run the enhanced API
CMD ["python", "-c", "import sys; sys.path.append('src'); from api.enriched_company_api import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8002)"]
