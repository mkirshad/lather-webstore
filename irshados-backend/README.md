# IrshadOS Backend

The IrshadOS backend is a Django 5 + Django REST Framework service that powers the ERP/RMS experience for retail and restaurant tenants. It provides multi-tenant aware APIs, authentication, and the domain modules outlined in the IrshadOS roadmap (inventory, purchasing, sales, POS, restaurant pack, and more).

## Table of Contents
- [Tech Stack](#tech-stack)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Quality & Tooling](#quality--tooling)
- [Next Steps](#next-steps)

## Tech Stack
- Python 3.11+
- Django 5
- Django REST Framework
- drf-spectacular (OpenAPI generation)
- django-cors-headers
- Postgres (local via Docker, managed in cloud)

## Local Development

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Update DATABASE_URL or other secrets as needed

# 4. Run migrations & start the server
python manage.py migrate
python manage.py createsuperuser  # optional, for admin access
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/` with browsable Swagger docs at `/api/docs/` and the admin console at `/admin/`.

### Running with Postgres (optional)

A sample `docker-compose` definition is provided in the repository root. After starting the service (`docker compose up -d`), configure `DATABASE_URL` to point at the container (e.g., `postgresql://irshad:devpass@localhost:5432/irshados`).

## Environment Variables

Create an `.env` file from `.env.example` and set the following values:

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Secret key for Django. |
| `DEBUG` | Set to `True` locally, `False` in production. |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts. |
| `DATABASE_URL` | Connection string for Postgres or SQLite. |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF protection. |
|> **Reminder:** The values in `.env.example` are placeholders only. Replace `change-me`, database defaults, and any other sample tokens with strong secrets stored outside of git-tracked files before running in shared or production environments.

 `SENTRY_DSN` | Optional Sentry DSN for observability. |

Additional variables for email (SendGrid), object storage (S3/GCS), and third-party integrations will be introduced as the project progresses through the implementation phases.

## Project Structure

```
irshados-backend/
├─ api/                 # Domain apps (tenants, users, inventory, sales, POS, etc.)
│  ├─ __init__.py
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations/
│  ├─ models.py
│  ├─ serializers.py
│  ├─ urls.py
│  └─ views.py
├─ config/              # Django project configuration
│  ├─ __init__.py
│  ├─ asgi.py
│  ├─ settings.py
│  ├─ urls.py
│  └─ wsgi.py
├─ manage.py
├─ requirements.txt
└─ README.md (this file)
```

As the implementation matures, expect additional Django apps under `api/` for modules like purchasing, sales, POS, restaurant pack, and reporting. Each app will include serializers, viewsets, permission classes, and Celery tasks.

## Quality & Tooling

Recommended tooling aligned with the project checklist:

- **Code style**: `black`, `isort`, and `ruff`
- **Static analysis**: `mypy`
- **Pre-commit**: configure `.pre-commit-config.yaml` to run formatting and linters
- **Testing**: `pytest` with `pytest-django` and `factory-boy`
- **Async jobs**: Celery + Redis (for invites, emails, stock valuation)
- **Observability**: Sentry SDK + structured logging

Run quality checks locally once the tooling is configured:

```bash
black .
isort .
ruff check .
mypy .
pytest
```

## Next Steps

The backend will progressively deliver the capabilities defined in the IrshadOS master checklist:

1. Implement tenant/user/role models with Postgres row-level security.
2. Add JWT authentication (SimpleJWT) with invite flows.
3. Build core ERP APIs for masters, inventory, purchasing, sales, and POS.
4. Extend with restaurant pack features (menu, modifiers, KOT/KDS).
5. Integrate payment gateways, messaging providers, and observability hooks.

Keep this README updated as modules and tooling evolve.

## Authentication & Tenant Bootstrap

The initial multi-tenant authentication flow is live. The `api` app now provides:

- `User` — custom Django user model with email as the username field.
- `Organization` — represents a tenant (slug + optional domain).
- `OrganizationMembership` — links users to organizations with a role (`owner`, `admin`, `member`).

### Endpoints

| URL | Method | Description |
|-----|--------|-------------|
| `/api/sign-up` | `POST` | Create a user and either bootstrap a new organization or join an existing slug. |
| `/api/sign-in` | `POST` | Exchange email/password + organization slug for an API token. |
| `/api/sign-out` | `POST` | Stateless sign out (requires `Authorization: Token <key>` header). |

Both sign-up and sign-in return:

```json
{
  "token": "<api-token>",
  "user": {
    "userId": "<uuid>",
    "userName": "Consultant Name",
    "email": "consultant@example.com",
    "authority": ["member"],
    "activeOrganization": {
      "organizationId": "<uuid>",
      "organizationSlug": "retail-one",
      "organizationName": "Retail One",
      "role": "member"
    },
    "organizations": [
      {
        "organizationId": "<uuid>",
        "organizationSlug": "retail-one",
        "organizationName": "Retail One",
        "role": "member"
      }
    ]
  }
}
```

### Sample Requests

Create a tenant and owner in a single call:

```bash
curl -X POST http://127.0.0.1:8000/api/sign-up \
  -H 'Content-Type: application/json' \
  -d '{
        "userName": "Irshad Owner",
        "email": "owner@example.com",
        "password": "SecurePass123",
        "organizationMode": "new",
        "organizationName": "Irshad HQ"
      }'
```

Add an existing consultant to another tenant:

```bash
curl -X POST http://127.0.0.1:8000/api/sign-up \
  -H 'Content-Type: application/json' \
  -d '{
        "userName": "Consultant",
        "email": "consultant@example.com",
        "password": "SecurePass123",
        "organizationMode": "existing",
        "organizationSlug": "retail-one",
        "role": "admin"
      }'
```

Sign in to a specific organization:

```bash
curl -X POST http://127.0.0.1:8000/api/sign-in \
  -H 'Content-Type: application/json' \
  -d '{
        "email": "consultant@example.com",
        "password": "SecurePass123",
        "organizationSlug": "retail-one"
      }'
```



