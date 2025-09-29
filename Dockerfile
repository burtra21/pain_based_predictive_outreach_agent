FROM python:3.13-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
