FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .

# Run as a non-root user
RUN useradd --system --uid 10001 appuser
USER 10001

ARG VERSION=dev
ENV APP_VERSION=$VERSION

EXPOSE 8000
# One worker keeps Prometheus metrics consistent; threads handle concurrency
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", \
     "--access-logfile", "-", "main:app"]
