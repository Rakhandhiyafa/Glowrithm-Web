# Build from the repository root:  docker build -f backend/Dockerfile -t glowrithm-api .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 TF_CPP_MIN_LOG_LEVEL=2
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
RUN pip install "tensorflow-cpu>=2.16,<3"
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt
COPY ml/pyproject.toml ml/pyproject.toml
COPY ml/glowrithm_ml ml/glowrithm_ml
RUN pip install ./ml
COPY backend/app backend/app
COPY backend/models backend/models
COPY web web

RUN useradd --create-home --uid 10001 glowrithm
USER glowrithm
WORKDIR /srv/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=4)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
