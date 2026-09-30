# AI-Powered DevOps Assistant

A low-cost DevOps project: a K3s cluster monitored by Prometheus and Loki, with an
AI assistant that analyzes alerts, logs and metrics and suggests root causes.

## Architecture

    GitHub  ->  GitHub Actions (test, build, push to ghcr.io, deploy over SSH)
                        |
                        v
                  K3s (single node)
                 /                \
      Prometheus + Alertmanager   Loki + Alloy
                 \                /
                  AI DevOps Assistant  ->  LLM  ->  notification

## Components

- `demo-app/` - Flask app with Prometheus metrics and endpoints that deliberately
  fail: `/error` (500), `/slow` (2-5s latency), `/leak` (memory leak -> OOMKilled),
  `/crash` (process exits).
- `.github/workflows/demo-app.yaml` - CI/CD pipeline.
