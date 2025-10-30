# Mini DDQ API

A multi-tenant **Due Diligence Questionnaire (DDQ)** backend built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**.  
It supports **JWT authentication**, **role-based authorization**, **tenant-aware CRUD**, **search**, and **bulk imports** with 91%+ test coverage.

---

## Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [Key Concepts](#-key-concepts)
- [Project Structure](#-project-structure)
- [Database Setup & Migration Steps](#-database-setup--migration-steps)
  - [1. Create the PostgreSQL Database and User](#1-create-the-postgresql-database-and-user)
  - [2. Project Initialization](#2-project-initialization)
  - [3. Models Setup](#3-models-setup)
  - [4. Initialize Alembic](#4-initialize-alembic)
  - [5. Configure Alembic](#5-configure-alembic)
  - [6. Test Models in Python Shell](#6-test-models-in-python-shell)
  - [7. Create and Apply Initial Migration](#7-create-and-apply-initial-migration)
  - [8. Add Tenant Indexes](#8-add-tenant-indexes)
- [Authentication & Authorization Setup](#-authentication--authorization-setup)
- [Auth Routes](#-auth-routes)
- [Questions Routes](#-questions-routes)
- [Responses Routes](#-responses-routes)
- [App Integration](#-integration)
- [Current Status](#-current-status)
- [Tests & Coverage](#-tests--coverage)
- [Benchmark](#-benchmark)
- [Next Steps](#-next-steps)
- [Run the App](#-run-the-app)
- [License](#-license)

---

## Overview

Mini DDQ API is a lightweight, secure backend for managing due diligence questions and responses across multiple organizations (tenants).  
Each tenant’s data is fully isolated, ensuring users can only access records belonging to their own organization.

---

## Features

- JWT-based authentication  
- Role-based authorization (admin / analyst / viewer)  
- Tenant-aware data isolation  
- CRUD APIs for Questions and Responses  
- Bulk import (CSV/JSON) with sync & async modes  
- 91% test coverage using pytest  
- SQLAlchemy ORM + Alembic migrations  
- FastAPI async architecture  

---

## Key Concepts

- **JWT (JSON Web Token):** A signed token carrying claims (`sub`, `tenant_id`, `role`, `exp`) to identify users securely.
- **Hashing:** Used for password verification during login via bcrypt.
- **Bearer Token:** The JWT sent with every request in the `Authorization` header (`Authorization: Bearer <JWT>`).
- **Authentication vs Authorization:**
  - *Authentication* → Verify identity (email + password)
  - *Authorization* → Verify permissions (role-based)
- **Upsert (PUT /responses/{question_id}):** Create a response if none exists or update the existing one.
- **Tenant Isolation:** Every query filters by `tenant_id = current_user.tenant_id`, ensuring no data leaks between organizations.

---

## Project Structure

```text
sandbox/
└── mini_ddq_app/
    ├── alembic/
    │   ├── versions/
    │   └── env.py
    ├── auth/           # password hashing + JWT helpers
    ├── models/         # ORM models: Tenant, User, Question, Response, etc.
    ├── routes/         # FastAPI routers: auth, questions, responses, search, imports
    ├── scripts/        # Utility scripts (benchmarks, seeding)
    ├── tests/          # pytest-based test suite
    ├── alembic.ini     # Alembic config used with "-c mini_ddq_app/alembic.ini"
    ├── config.py       # Environment config
    ├── db.py           # DB connection & session management
    ├── deps.py         # Auth dependencies (get_current_user, require_role)
    └── main.py         # FastAPI app entry point
```
---

## 1. Database Setup & Migration Steps

### Create the PostgreSQL Database and User
```sql
psql -U postgres
CREATE DATABASE mini_ddq;
CREATE USER ddq_user WITH PASSWORD 'ddq_pass';
GRANT ALL PRIVILEGES ON DATABASE mini_ddq TO ddq_user;
\q
```

Database URL (for .env):

DATABASE_URL=postgresql+psycopg2://ddq_user:ddq_pass@localhost:5432/mini_ddq

---
 

## 2. Project Initialization

Inside sandbox/:

```bash
mkdir mini_ddq_app
touch mini_ddq_app/{__init__.py,config.py,db.py,main.py}
```

.env file:
```python
DATABASE_URL=postgresql+psycopg2://ddq_user:ddq_pass@localhost:5432/mini_ddq
JWT_SECRET=changeme
```

--- 

## 3. Models Setup

In mini_ddq_app/models/, create:

- tenant.py
- user.py
- questionnaire.py
- question.py
- response.py

__init__.py:

- from .tenant import Tenant
- from .user import User
- from .questionnaire import Questionnaire
- from .question import Question
- from .response import Response

--- 

## 4. Initialize Alembic

```bash
cd mini_ddq_app
alembic init alembic
```

--- 

## 5. Configure Alembic

Edit mini_ddq_app/alembic/env.py:

```python
from mini_ddq_app.db import Base
from mini_ddq_app import models
from mini_ddq_app.config import settings

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
target_metadata = Base.metadata
```

--- 

## 6. Test Models in Python Shell

```python
from mini_ddq_app.db import Base
from mini_ddq_app import models
Base.metadata.tables.keys()
# Expected Output: dict_keys(['tenants','users','questionnaires','questions','responses'])
```

--- 

## 7. Create and Apply Initial Migration

```bash
alembic -c mini_ddq_app/alembic.ini revision --autogenerate -m "init schema"
alembic -c mini_ddq_app/alembic.ini upgrade head
```

Verify tables:
```bash
psql -U ddq_user -d mini_ddq -c "\dt"
```

--- 

## 8. Add Tenant Indexes

- Indexing tenant_id ensures tenant-scoped queries (WHERE tenant_id = ...) use fast index scans instead of full table scans, which is critical as data grows. 
- It also improves join performance on tenant_id across related tables, preserving multi-tenant isolation guarantees and keeping per-tenant operations consistently low-latency.

```bash
alembic -c mini_ddq_app/alembic.ini revision -m "add tenant indexes"
```

Edit version file:
```python
def upgrade():
    op.create_index("users_tenant_idx", "users", ["tenant_id"])
    op.create_index("questions_tenant_idx", "questions", ["tenant_id"])
```

Apply and verify:
```bash
alembic -c mini_ddq_app/alembic.ini upgrade head
```

Expected indexes:

users_tenant_idx      | CREATE INDEX users_tenant_idx ON public.users USING btree (tenant_id)
questions_tenant_idx  | CREATE INDEX questions_tenant_idx ON public.questions USING btree (tenant_id)

✅ Status: Database schema, models, and indexes created successfully.

--- 

## 9. Authentication & Authorization Setup

auth/
- hashing.py → bcrypt-based secure password hashing and verification.
- jwt.py → generates and validates JWT tokens.

deps.py
- get_current_user() → extracts & validates JWT, loads active user.
- require_role() → role-based guard (e.g., admin, analyst, viewer).
- Enforces tenant-aware authorization.

 

### Auth Routes
- /auth/login → Validates credentials and returns JWT.
Handles secure session management via tokens instead of plaintext passwords.


### Questions Routes
- /questions → List or create questions (tenant-aware).
- Only admins/analysts can modify questions.
- Uses Pydantic models for input validation.

 
### Responses Routes
- /responses/{question_id} → Upsert response (create/update).
- Ensures a 1:1 relationship per question within each tenant.
- Role-based access enforced (admin/analyst only).

### Role–Permission Matrix

| Endpoint / Action | Description | Admin | Analyst | Viewer |
|--------------------|-------------|:------:|:--------:|:-------:|
| **`POST /auth/login`** | Login and get JWT token | ✅ | ✅ | ✅ |
| **`GET /questions`** | View all questions for your tenant | ✅ | ✅ | ✅ |
| **`POST /questions`** | Create new question | ✅ | 🚫 | 🚫 |
| **`PUT /questions/{id}` / `DELETE /questions/{id}`** | Update or delete a question | ✅ | 🚫 | 🚫 |
| **`GET /responses`** | View all responses for your tenant | ✅ | ✅ | ✅ |
| **`GET /responses/{question_id}`** | View a single response | ✅ | ✅ | ✅ |
| **`PUT /responses/{question_id}`** | Upsert (create or update) a response | ✅ | ✅ | 🚫 |
| **`POST /imports/questions`** | Bulk import questions (CSV/JSON) | ✅ | 🚫 | 🚫 |
| **`GET /search`** | Search across questions and responses | ✅ | ✅ | ✅ |
| **Background import (async)** | Run large imports in background | ✅ | 🚫 | 🚫 |

---

**Summary:**
- **Admin** → Full access: manage questions, imports, and responses within their tenant.  
- **Analyst** → Limited write: can add/update responses but not manage questions or imports.  
- **Viewer** → Read-only: can view questions/responses and perform searches.
- All actions are **scoped by tenant** → no cross-tenant access possible.

--- 

## 10. Integration

- Including all routers in main.py wires the auth, question, response, search, and import modules into a single FastAPI app. 
- This is the integration layer that composes independent features into one cohesive API surface.

Routers included in main.py:
```python
app.include_router(auth_routes.router)
app.include_router(question_routes.router)
app.include_router(response_routes.router)
app.include_router(search_routes.router)
app.include_router(imports_routes.router)
```

--- 

Now:
- ✅ Database and migrations completed
- ✅ JWT-based authentication & role-based authorization working
- ✅ Tenant isolation confirmed
- ✅ CRUD operations tenant-scoped
- ✅ Integration tests passing (91% coverage)
- ✅ Async background import implemented

--- 

## 11. Tests & Coverage
```bash
pytest -q mini_ddq_app/tests --cov=mini_ddq_app --cov-report=term-missing
```

Coverage:

TOTAL: 650 statements, 91% covered

| File Path                                             | Stmts | Miss | Cover | Missing                                                                                  |
|--------------------------------------------------------|-------|------|--------|------------------------------------------------------------------------------------------|
| mini_ddq_app/__init__.py                               | 5     | 0    | 100%   | -                                                                                        |
| mini_ddq_app/auth/hashing.py                           | 7     | 0    | 100%   | -                                                                                        |
| mini_ddq_app/auth/jwt.py                               | 10    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/config.py                                 | 9     | 0    | 100%   | -                                                                                        |
| mini_ddq_app/db.py                                     | 11    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/deps.py                                   | 35    | 2    | 94%    | 49, 57                                                                                   |
| mini_ddq_app/models/question.py                        | 16    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/models/questionnaire.py                   | 15    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/models/response.py                        | 14    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/models/tenant.py                          | 13    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/models/user.py                            | 17    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/routes/auth.py                            | 26    | 1    | 96%    | 34                                                                                       |
| mini_ddq_app/routes/imports.py                         | 95    | 28   | 71%    | 49, 73–75, 79–81, 97–98, 108–114, 119–127, 149–150, 155, 159–161                        |
| mini_ddq_app/routes/questions.py                       | 44    | 11   | 75%    | 35–42, 57, 72–85                                                                         |
| mini_ddq_app/routes/responses.py                       | 53    | 10   | 81%    | 55–58, 79, 107–111                                                                       |
| mini_ddq_app/routes/search.py                          | 21    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/__init__.py                         | 0     | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/conftest.py                         | 93    | 1    | 99%    | 174                                                                                      |
| mini_ddq_app/tests/it_test_auth.py                     | 6     | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/it_test_imports.py                  | 11    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/it_test_questions_responses.py       | 28    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/it_test_search.py                   | 24    | 3    | 88%    | 9–10, 24                                                                                 |
| mini_ddq_app/tests/test_auth_form.py                   | 5     | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/test_auth_route.py                  | 10    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/test_db_dep.py                      | 9     | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/test_deps.py                        | 14    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/test_hashing.py                     | 14    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/test_import_utils.py                | 26    | 0    | 100%   | -                                                                                        |
| mini_ddq_app/tests/test_jwt_utils.py                   | 19    | 0    | 100%   | -                                                                                        |
| **TOTAL**                                              | **650** | **56** | **91%** | -                                                                                        |

--- 

## 12. End-to-End Testing: Benchmark

- The benchmark script acts as an end-to-end sanity and performance test.
- It spins up the real FastAPI app (via TestClient), authenticates, uploads a large CSV, and measures how long the entire flow - from request to DB insert-takes.
- This script spins up a local TestClient for the app, logs in (seeded user), auto-discovers a questionnaire_id, generates an in-memory CSV with 2,000 rows, and posts it to /imports/questions?sync=true as a multipart upload. 
- It measures end-to-end time (client → router → parsing → validation → DB insert).
- This helps confirm both correctness (no failed rows) and efficiency of the import pipeline.

```bash
python -m mini_ddq_app.scripts.bench_imports
```

Result:

```python
Status: 200 Time(ms): 585
Result: {'mode': 'sync', 'format': 'csv', 'rows_total': 2000, 'rows_ok': 2000, 'rows_failed': 0, 'errors': []}
```

✅ 2000 rows imported in ~585 ms (sync mode, local TestClient).

- Status: 200 means the endpoint accepted and processed the file successfully.
- rows_total/rows_ok/rows_failed are server-reported counters after parsing/validation.
- The ~585 ms is measured locally via TestClient (no network latency), so it reflects pure app+DB performance on the machine; real HTTP calls will be a bit slower.

### Integration & End-to-End Test Files

| File | Purpose | What It Covers |
|------|----------|----------------|
| **`it_test_auth.py`** | Tests authentication flow | Verifies login endpoint `/auth/login` → checks valid credentials produce a working JWT |
| **`it_test_questions_responses.py`** | Core end-to-end test for tenant-scoped CRUD | ✅ Authenticates a user → ✅ Creates/fetches questions → ✅ Creates/updates responses → ✅ Confirms tenant isolation (no leakage across tenants) |
| **`it_test_search.py`** | End-to-end tenant-aware search | ✅ Authenticated search → ✅ Validates results filtered by `tenant_id` |
| **`it_test_imports.py`** | Bulk import validation | ✅ Uploads CSV/JSON → ✅ Ensures server parses, inserts, and returns success JSON |

### Notes & toggles (optional but handy)
- Seed user must exist (the script expects `alice@alpha.com / alpha_admin`).  
- To test **async** path (if your endpoint supports it), call `/imports/questions?sync=false`.  
- Change dataset size via `make_csv(..., n=...)` to stress-test parsing or DB performance.

### (Reference) `bench_imports.py` summary
- **`make_csv`**: builds a CSV with headers matching your importer.  
- **`discover_questionnaire_id`**: tries to fetch one from `/questions`; otherwise you can hardcode an ID.  
- **`client.post(... files={...})`**: sends multipart form data exactly like a browser upload.  
- **Timing**: `time.perf_counter()` → simple wall-clock measurement for end-to-end duration.

### Testing Levels Overview

| Type of Test | Scope & Purpose | Example in This Project |
|---------------|----------------|--------------------------|
| **Unit Test** | Tests one small function or module in isolation (no DB, no FastAPI). Ensures individual logic works as expected. | `test_hashing.py`, `test_jwt_utils.py`, `test_import_utils.py` |
| **Integration Test** | Tests interactions between components — routes, DB, dependencies — using real app context but limited scope. | `it_test_auth.py`, `it_test_questions_responses.py`, `it_test_search.py` |
| **End-to-End (E2E) Test** | Tests the full system from API request to DB and back. Validates real authentication, business logic, and database writes in one flow. | `scripts/bench_imports.py` (auth → upload → parse → insert → measure) |

---

**Summary:**  
- Unit = *Does each part work correctly?*  
- Integration = *Do parts work together correctly?*  
- End-to-End = *Does the whole system behave correctly from the user’s perspective?*  

--- 

## 13. Run the App
```bash
uvicorn mini_ddq_app.main:app --reload
```

Open: http://localhost:8000/docs
---
 
