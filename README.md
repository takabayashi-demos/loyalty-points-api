# loyalty-points-api

Customer loyalty program and rewards API

## Tech Stack
- **Language**: java
- **Team**: customer
- **Platform**: Walmart Global K8s

## Quick Start
```bash
docker build -t loyalty-points-api:latest .
docker run -p 8080:8080 loyalty-points-api:latest
curl http://localhost:8080/health
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /ready | Readiness probe |
| GET | /metrics | Prometheus metrics |
# PR 2 - 2026-04-15T18:50:05
