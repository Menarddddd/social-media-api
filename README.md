# Social Media API 🚀

A production-ready RESTful API for a social media platform built with FastAPI, PostgreSQL, and Redis.

🌐 **Live Demo:** [API Documentation](https://social-media-api-z06j.onrender.com/docs)

---

## Features

### 👤 User Management
- User registration with input validation
- Secure login with OAuth2 (username & password)
- JWT access tokens (30 min) + refresh token rotation (7 days)
- Profile update (name, username, email)
- Password change with current password verification
- Soft delete with 30-day recovery period
- Account recovery via email

### 📝 Posts
- Create, read, update, and delete posts
- Cursor-based pagination for efficient data loading
- View personal posts and public feed
- Only post owners can edit/delete their posts

### 💬 Comments
- Create, read, update, and delete comments on posts
- Cursor-based pagination
- Only comment owners can edit/delete their comments

### 🔐 Authentication & Authorization
- OAuth2 with password flow
- JWT access token + refresh token rotation
- Hashed refresh tokens stored in database
- Token revocation on use (prevents replay attacks)
- Role-based access control (User / Admin)

### 👑 Admin Panel
- Promote users to admin
- Delete any user account with reason
- Delete any post or comment
- View user deletion records

### 📧 Account Recovery
- Email-based account recovery using Resend
- Background email jobs with Redis (ARQ)
- Secure recovery tokens with expiration
- Rate limiting on recovery attempts

### 🛡️ Error Handling
- Custom exception classes (DuplicateEntry, NotFound, BadRequest, Credentials)
- Database-agnostic error parsing (PostgreSQL + SQLite)
- Consistent JSON error responses with proper HTTP status codes

### 📝 Logging
- Structured logging across all services
- Logs user actions (login, signup, updates, deletions)
- Warning logs for failed attempts and suspicious activity
- Console + file output

### 🧪 Testing
- 13 integration tests
- Async test client with HTTPX
- In-memory SQLite for test isolation
- Helper functions for clean, reusable test code
- Tests cover users, posts, and comments

---

## Tech Stack

| Category | Technology |
|----------|------------|
| **Framework** | FastAPI |
| **Language** | Python 3.12 |
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy (async) |
| **Migrations** | Alembic |
| **Async Driver** | asyncpg |
| **Auth** | OAuth2 + JWT (PyJWT) |
| **Password Hashing** | Argon2 (pwdlib) |
| **Redis Client** | Upstash Redis (REST) |
| **Background Jobs** | ARQ |
| **Email** | Resend |
| **Validation** | Pydantic v2 |
| **Testing** | Pytest + HTTPX |
| **Containerization** | Docker + Docker Compose |
| **Deployment** | Render |

---

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis (or Upstash account)
- Git
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/Menarddddd/social-media-api.git
cd social-media-api

# Install uv (if not installed)
pip install uv

# Install project dependencies
uv sync

### 2. Set up environment variables

# Database
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_NAME=your_db_name
DATABASE_URL=postgresql+asyncpg://your_db_user:your_db_password@localhost:5432/your_db_name

# Redis (Upstash)
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_upstash_token

# JWT
ACCESS_SECRET_KEY=your_access_secret_key
ACCESS_MINUTES_EXPIRE=30
REFRESH_SECRET_KEY=your_refresh_secret_key
REFRESH_DAYS_EXPIRE=7
ALGORITHM=HS256

# Admin Account (created on first startup)
ADMIN_FIRST_NAME=ADMIN
ADMIN_LAST_NAME=ADMIN
ADMIN_USERNAME=ADMIN
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your_admin_password

# Other
SOFT_DELETE_RETENTION_DAYS=30

# Email (Resend)
RESEND_API_KEY=your_resend_api_key
RECOVERY_SECRET_KEY=your_recovery_secret_key
RECOVERY_MINUTES=30


### Set up your postgresql

# Create database
createdb your_db_name

# Or using psql
psql -U postgres
CREATE DATABASE your_db_name;

### 4. RUN THE APPLICATION

uv run uvicorn app.main:app --reload

The API will be available at: http://127.0.0.1:8000

API Documentation: http://127.0.0.1:8000/docs

API Status: http://127.0.0.1:8000/healthy


### Running with docker using docker compose

# Start all services (PostgreSQL + Redis + App)
docker compose up --build

# Start in background
docker compose up -d --build

# Stop all services
docker compose down

# Stop and remove data
docker compose down -v

The API will be available at: http://127.0.0.1:8000

API Documentation: http://127.0.0.1:8000/docs

API Status: http://127.0.0.1:8000/healthy

### Running tests

# Run all tests
uv run pytest -v

# Run with output
uv run pytest -v -s

# Run specific test file
uv run pytest test/test_user.py -v

# Run specific test
uv run pytest test/test_user.py::test_login -v
