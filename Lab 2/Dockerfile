# syntax=docker/dockerfile:1
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN useradd -m appuser
WORKDIR /app

# Copy app
COPY app /app/app
COPY client /app/client
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt || true

# Document root inside container
RUN mkdir -p /srv/www && chown -R appuser:appuser /srv/www

EXPOSE 8000
USER appuser

ENV SERVER_PORT=8000 \
    DOC_ROOT=/srv/www \
    HANDLER_DELAY=1.0 \
    COUNTER_MODE=locked \
    RATE_LIMIT_RPS=5.0 \
    RATE_LIMIT_BURST=10 \
    SERVER_TYPE=threaded

CMD ["python", "-m", "app.server"]
