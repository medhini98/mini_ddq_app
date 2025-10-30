# Mini DDQ API – Design Document

---

## 1. Introduction

The **Mini DDQ API** is a lightweight, multi-tenant backend system for managing Due Diligence Questionnaires (DDQs).  
It allows multiple organizations (tenants) to securely manage questions, responses, and imports within isolated data spaces.

The system is built using **FastAPI**, **SQLAlchemy**, and **PostgreSQL**, ensuring modular design, high test coverage, and clear tenant separation.

---

## 2. System Goals

- JWT-based authentication and session management  
- Role-based authorization (admin, analyst, viewer)  
- Tenant data isolation via `tenant_id` scoping  
- Bulk import functionality (CSV/JSON) with async background processing  
- ≥80% test coverage for reliability  
- Performance validation via benchmark scripts  

---

## 3. Architecture Overview

The Mini DDQ API follows a **modular, layered architecture** that separates concerns between authentication, routing, data access, and storage.

### Layered Architecture Diagram

                ┌────────────────────────────────────────────┐
                │                 Client UI                  │
                │            (Swagger - Frontend App)        │
                └────────────────────────────────────────────┘
                                   │
                                   ▼
                ┌────────────────────────────────────────────┐
                │              API Layer (FastAPI)            │
                │   ├── auth.py        → JWT login endpoint   │
                │   ├── questions.py   → CRUD operations      │
                │   ├── responses.py   → Upsert responses     │
                │   ├── search.py      → Tenant-aware search  │
                │   └── imports.py     → Bulk import (async)  │
                └────────────────────────────────────────────┘
                                   │
                                   ▼
                ┌────────────────────────────────────────────┐
                │         Dependency Layer (deps.py)          │
                │   ├── get_current_user()                    │
                │   ├── require_role()                        │
                │   └── Validates JWT + enforces roles        │
                └────────────────────────────────────────────┘
                                   │
                                   ▼
                ┌────────────────────────────────────────────┐
                │           Auth Layer (auth/)                │
                │   ├── hashing.py → bcrypt password hashing  │
                │   └── jwt.py     → token issue + verify     │
                └────────────────────────────────────────────┘
                                   │
                                   ▼
                ┌────────────────────────────────────────────┐
                │         Data Layer (models/)                │
                │   ├── Tenant, User, Questionnaire, etc.     │
                │   ├── tenant_id used for isolation          │
                │   └── SQLAlchemy ORM models                 │
                └────────────────────────────────────────────┘
                                   │
                                   ▼
                ┌────────────────────────────────────────────┐
                │         Database Layer (PostgreSQL)         │
                │   ├── Alembic migrations                    │
                │   ├── Indexes on tenant_id                  │
                │   └── Enforces schema integrity             │
                └────────────────────────────────────────────┘

---

## 4. Data Model

| Entity | Key Fields | Relationships |
|---------|-------------|---------------|
| **Tenant** | id, name | 1–M User |
| **User** | id, tenant_id, role, email, password_hash | belongs to Tenant |
| **Questionnaire** | id, tenant_id, title | has many Questions |
| **Question** | id, questionnaire_id, tenant_id, question_text | has one Response |
| **Response** | id, question_id, tenant_id, answer, status | 1:1 with Question |


Note:
- Each model includes a `tenant_id` column for strict tenant-level isolation.
- Each Questionnaire row is unique by:
    - PK: id (UUID).
    - Business key (per tenant): UNIQUE(tenant_id, name, version) via uq_questionnaires_name_version.
- Question - Response relationship:
    - Enfore  "one Response per Question (per tenant)" at the database level using a unique constraint on (tenant_id, question_id):
    ```python
    __table_args__ = (
        UniqueConstraint("tenant_id", "question_id", name="uq_responses_one_per_question"),
    )
    ```
    - Because responses.question_id references questions.id (a PK), this constraint guarantees there can be at most one responses row for a given question_id within the same tenant_id.
---

## 5. Authentication & Authorization

- **JWT Authentication** (`/auth/login`)  
  Verifies credentials and issues a token:
  ```json
  {
    "sub": "<user_id>",
    "tenant_id": "<tenant_id>",
    "role": "admin",
    "exp": "<expiry_timestamp>"
  }

 - Role-Based Authorization
 - Implemented via require_role("admin", "analyst") dependency.
 - Guards endpoints for question/response creation and editing.
 - View-only users (viewer) are restricted to GET endpoints.
 - Password Hashing
 - Bcrypt is used to securely store and verify passwords.
 - Plaintext passwords never touch the database.

--- 

## 6. Tenant Isolation

To ensure multi-tenant integrity:
 - Every route filters by tenant_id == current_user.tenant_id.
 - get_current_user() decodes the JWT and retrieves the active user’s tenant.
 - Queries in /questions and /responses are scoped to the current tenant.
 - Indexes on tenant_id ensure optimized lookup and no cross-tenant data access.

✅ Tenant A’s user cannot read or modify Tenant B’s questions or responses.

--- 

## 7. Bulk Import Design

Endpoint:

POST /imports/questions

Supports both sync and async modes.

| Mode                 | Behavior                                                 | Response                               |
|----------------------|----------------------------------------------------------|----------------------------------------|
| `sync=true`          | Parses, validates, and inserts all rows **before** returning | Returns summary of rows imported        |
| `sync=false` (default) | Runs import in a background task                         | Returns immediate acknowledgment        |

Batch Logic
 - CSV/JSON parsed into dicts
 - Inserts in batches of 100 rows per transaction
 - Validates questionnaire and tenant before insert

Example Response

{
  "mode": "sync",
  "format": "csv",
  "rows_total": 2000,
  "rows_ok": 2000,
  "rows_failed": 0,
  "errors": []
}


--- 

## 8. Testing Strategy

| Test Type         | Purpose                          | Example Tests                          |
|-------------------|----------------------------------|----------------------------------------|
| Unit Tests        | Validate helper logic            | bcrypt hashing, JWT decode             |
| Integration Tests | Verify end-to-end API flow       | `/auth/login`, `/questions`, `/responses` |
| Tenant Tests      | Ensure isolation between tenants | Cross-tenant access → 404              |
| Import Tests      | Validate CSV/JSON parsing        | `/imports/questions?sync=true`         |
| Search Tests      | Check text search and scoping    | `/search?q=...`                        |

Framework: pytest + TestClient
Fixtures: Pre-seeded tenants, users, and sample questions.
Coverage:

TOTAL: 650 statements, 91% covered

### What the End-to-End (E2E) Test Does

The E2E test exercises the **full request→response pipeline** of the Mini DDQ app — from an authenticated HTTP call down to database writes/reads — to prove that real user flows work as intended in a tenant-scoped system.

#### Scope (Systems Touched)
1. **Auth & RBAC**
   - Logs in via `/auth/login`, obtains a JWT, and sends it as `Authorization: Bearer <token>`.
   - Server decodes the JWT, loads the user, and attaches `tenant_id` + `role`.

2. **Tenant Scoping**
   - All subsequent requests are implicitly filtered by `tenant_id = current_user.tenant_id`.
   - Verifies that the caller only sees/acts on their tenant’s data.

3. **Functional Paths**
   - **Questions (read):** Calls `/questions` and receives a list limited to the caller’s tenant.
   - **Responses (write):** Calls `/responses` (upsert) to create/update a response for a question.
   - **Search (read):** Calls `/search?q=...` and gets tenant-scoped matches.
   - **Bulk Import (write):**
     - Uploads a CSV to `/imports/questions?sync=true` (synchronous mode).
     - Server parses, validates, and inserts rows, returning a structured summary:
       `rows_total`, `rows_ok`, `rows_failed`, `errors`.
     - Mixed-tenant CSV case confirms isolation: rows for the caller’s tenant **succeed**; cross-tenant rows **fail** with clear errors.

4. **Database Layer**
   - Uses real models & constraints (FKs, NOT NULLs, UNIQUEs).
   - Commits transactions and surfaces row-level validation failures in the response (no mocks).

#### What This Proves
- **Authentication works** (JWT issuance + verification).
- **Authorization works** (role checks via `require_role`).
- **Tenant isolation works** (no cross-tenant reads/writes).
- **Business flows work end-to-end**:
  - Reading questions, writing responses, searching, and importing questions.
- **Data integrity holds**:
  - Inserts respect schema rules, and invalid rows are rejected with actionable error messages.

#### Typical Success Signal
- Login returns `200` with a valid `access_token`.
- `/questions` returns only tenant-owned questions.
- `/responses` upsert returns `200` with the saved response.
- `/search` returns keyword matches scoped to the tenant.
- `/imports/questions?sync=true` returns:


--- 

## 9. Summary

- The Mini DDQ API delivers a complete, modular, and secure foundation for enterprise-grade multi-tenant backends.
- It implements JWT-based authentication, strong tenant isolation, efficient data imports, and 91% test coverage.

Core Achievements:
 - Authenticated multi-tenant API
 - Comprehensive unit + integration tests
 - Async bulk import functionality
 - Design document describing architecture
 - Performance benchmark for 2,000+ rows

---
