FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends poppler-utils \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt pyproject.toml README.md /app/
COPY requirements /app/requirements

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY construction_rag /app/construction_rag
COPY frontend /app/frontend

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "construction_rag.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
