FROM python:3.12-slim

# Prevents .pyc files from being generated and ensures that output is flushed immediately
ENV PYTHONDONTWRITEBYTECODE=1
# For structlog so that logs are not buffered and appear in real-time
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
