# API Gateway Service

Central entry point for the **Portfolio Activity & Notification System**. Handles authentication, rate limiting, and request proxying to downstream microservices.

---

## Architecture

```
                    ┌──────────────────────┐
   Client ────────▶ │    API Gateway       │
   (REST)           │    (Port 5000)       │
                    │                      │
                    │  • JWT Validation    │
                    │  • Rate Limiting     │
                    │  • Request Proxy     │
                    │  • CORS              │
                    │  • Tracing           │
                    └──────┬───────┬───────┘
                           │       │
                    ┌──────▼──┐ ┌──▼──────────┐
                    │Portfolio│ │Notification  │
                    │Service  │ │Service       │
                    │  :5001  │ │  :5002       │
                    └─────────┘ └──────────────┘
```

## Features

- **JWT Authentication** — Validates Bearer tokens and injects user context headers (`X-User-ID`, `X-Username`, `X-Email`) for downstream services
- **Rate Limiting** — Redis-backed rate limiting via `flask-limiter` (configurable, default: 100 req/hour)
- **Request Proxying** — Transparent forwarding to Portfolio and Notification services with full header propagation
- **CORS Support** — Cross-origin requests enabled for `/api/*`
- **Distributed Tracing** — OpenTelemetry integration with Jaeger for end-to-end request tracing
- **Structured Logging** — JSON-formatted logs with request ID correlation
- **Health Check** — `/health` endpoint for monitoring and load balancers
- **Service Discovery** — `/api/services` endpoint listing downstream service URLs
- **Error Handling** — Graceful handling of 502 (service down), 504 (timeout), and 500 (internal) errors

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Auth Strategy** | JWT (HS256) | Stateless, no session store needed, lightweight for microservices |
| **Rate Limiting** | Redis-backed `flask-limiter` | Distributed rate limiting across multiple gateway instances |
| **Proxy Pattern** | Direct HTTP forwarding | Simple, transparent — no protocol translation needed |
| **User Context** | Internal headers (X-User-*) | Downstream services trust gateway; no need to re-validate JWT |

## Tradeoffs Considered

1. **Reverse proxy vs application-level proxy** — An Nginx/Kong gateway would be more performant, but a Flask-based gateway provides tighter integration with shared auth logic and is simpler for this scope.
2. **Central JWT validation vs per-service** — Centralizing auth in the gateway avoids duplicate validation but creates a single point of failure. In production, you'd add a fallback JWT validation in each service.
3. **Synchronous proxy vs async** — Using synchronous `requests` library is simpler. For high throughput, `httpx` with async support would reduce resource usage.

## Scalability Considerations

- **Horizontal scaling**: Run multiple gateway instances behind a load balancer. Rate limiting state is shared via Redis.
- **Connection pooling**: Uses `requests.Session` patterns for efficient HTTP connection reuse to downstream services.
- **Timeout configuration**: Configurable per-route timeouts (default 30s) prevent slow downstream services from blocking the gateway.

## Project Structure

```
api_gateway/
├── app.py              # Flask application factory
├── config.py           # Configuration (dev/prod/testing)
├── middleware.py        # Auth validation, error handlers, request ID
├── routes.py           # Proxy route definitions
├── wsgi.py             # Gunicorn WSGI entry point
├── Dockerfile          # Container build
├── Jenkinsfile         # CI/CD pipeline
├── requirements.txt    # Python dependencies
└── shared/             # Shared utilities
    ├── auth.py         # JWT encode/decode helpers
    ├── tracing.py      # OpenTelemetry setup
    └── logging_config.py  # Structured logging
```

## Steps to Run Locally

### Prerequisites
- Python 3.11+
- Redis (for rate limiting)
- Portfolio Service running on port 5001
- Notification Service running on port 5002

### Option 1: Docker (Recommended)
```bash
# From the project root (with docker-compose.yml)
docker-compose up --build api_gateway
```

### Option 2: Standalone
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export JWT_SECRET=your-secret-key
export REDIS_URL=redis://localhost:6379/0
export PORTFOLIO_SERVICE_URL=http://localhost:5001
export NOTIFICATION_SERVICE_URL=http://localhost:5002

# Run with Gunicorn
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 4

# Or run directly
python app.py
```

### Verify
```bash
curl http://localhost:5000/health
# {"service": "api-gateway", "status": "healthy", "version": "1.0.0"}
```

## API Routes

### Public (no auth)
| Method | Endpoint | Proxied To |
|--------|----------|------------|
| POST | `/api/auth/register` | Portfolio Service |
| POST | `/api/auth/login` | Portfolio Service |

### Protected (JWT required)
| Method | Endpoint | Proxied To |
|--------|----------|------------|
| GET | `/api/auth/me` | Portfolio Service |
| GET/POST | `/api/portfolios` | Portfolio Service |
| GET/PUT/DELETE | `/api/portfolios/:id` | Portfolio Service |
| GET | `/api/portfolios/:id/holdings` | Portfolio Service |
| GET/POST | `/api/portfolios/:id/transactions` | Portfolio Service |
| GET | `/api/notifications` | Notification Service |
| PATCH | `/api/notifications/:id/read` | Notification Service |
| PATCH | `/api/notifications/read-all` | Notification Service |
| GET/PUT | `/api/preferences` | Notification Service |
| GET/POST | `/api/rules` | Notification Service |
| PUT/DELETE | `/api/rules/:id` | Notification Service |

## CI/CD (Jenkins)

Pipeline stages: `Checkout → Install → Lint → Test → Docker Build → Deploy`

See [Jenkinsfile](./Jenkinsfile) for full pipeline definition.

## Related Services

- [Portfolio Service](https://github.com/lazuardi21/AcumenPortfolio) — User management, portfolios, transactions
- [Notification Service](https://github.com/lazuardi21/AcumenNotification) — Notifications, preferences, rules engine
