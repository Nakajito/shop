# Technical Documentation Reference

Use sections of this file when generating developer-facing documentation.

---

## Architecture Document (SAD — Software Architecture Document)

### Structure

```markdown
# Architecture Document — [Project Name]

**Version:** 1.0  
**Date:** YYYY-MM-DD  
**Authors:** [Names]  
**Status:** Draft / Approved

---

## 1. Overview

Brief description of the system's purpose, business context, and main users.

## 2. Tech Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Frontend | React | 18.x | Component-based UI, large ecosystem |
| Backend | Node.js + Express | 20.x | Team expertise, fast I/O |
| Database | PostgreSQL | 15 | Relational integrity, JSONB support |
| Cache | Redis | 7 | Session storage, rate limiting |
| Infrastructure | AWS (EC2, RDS, S3) | — | Scalability, managed services |

## 3. System Architecture

[Mermaid diagram here]

\`\`\`mermaid
graph TD
  Browser --> CDN
  CDN --> LoadBalancer
  LoadBalancer --> AppServer1
  LoadBalancer --> AppServer2
  AppServer1 --> DB[(PostgreSQL)]
  AppServer1 --> Cache[(Redis)]
  AppServer1 --> S3[(S3 Storage)]
\`\`\`

## 4. Component Descriptions

### Frontend
- Framework: React 18
- State management: Zustand
- Routing: React Router v6
- Bundler: Vite

### Backend
- REST API with Express
- JWT-based authentication
- Validation: Zod
- ORM: Prisma

### Database
- Primary: PostgreSQL (structured data, transactions)
- Cache: Redis (sessions, queue jobs)
- File storage: S3 (uploads, media)

## 5. Design Patterns

| Pattern | Where applied | Why |
|---------|--------------|-----|
| Repository | Data access layer | Decouples business logic from DB |
| Factory | Service instantiation | Flexible dependency injection |
| Observer | Event system | Loose coupling between modules |
| CQRS | Read/write paths | Optimized query performance |

## 6. Communication Between Components

Describe sync (HTTP, gRPC) vs async (queues, events) communication.

## 7. Security Architecture

- Auth: JWT with refresh tokens
- Transport: HTTPS / TLS 1.3
- Secrets: Environment variables (never hardcoded)
- Permissions: Role-based access control (RBAC)

## 8. Deployment Architecture

[Mermaid deployment diagram]

## 9. Non-Functional Requirements

| NFR | Target | How achieved |
|-----|--------|-------------|
| Availability | 99.9% uptime | Multi-AZ deployment |
| Performance | < 200ms p95 | CDN, caching, DB indexes |
| Scalability | 10k concurrent users | Horizontal scaling |

## 10. Architecture Decisions (ADRs)

Brief log of key decisions and their rationale.

| Decision | Options considered | Chosen | Reason |
|---|---|---|---|
| Database | MySQL vs PostgreSQL | PostgreSQL | Better JSON support, full-text search |
```

---

## Data Dictionary / Database Model

### Structure

```markdown
# Data Dictionary — [Project Name]

**Database:** PostgreSQL 15  
**ORM:** Prisma / TypeORM / SQLAlchemy

---

## Entity Relationship Diagram

\`\`\`mermaid
erDiagram
  USER ||--o{ ORDER : places
  ORDER ||--|{ ORDER_ITEM : contains
  PRODUCT ||--o{ ORDER_ITEM : referenced_in
  PRODUCT }|--|| CATEGORY : belongs_to
\`\`\`

---

## Table: users

**Description:** Registered user accounts.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK, NOT NULL | Unique identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User's email address |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt hash, never plain text |
| `role` | ENUM | NOT NULL, default 'user' | `admin` or `user` |
| `created_at` | TIMESTAMP | NOT NULL, default NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |
| `deleted_at` | TIMESTAMP | NULLABLE | Soft delete timestamp |

**Indexes:**
- `idx_users_email` — UNIQUE on `email`

**Relations:**
- `users.id` → `orders.user_id` (one-to-many)
```

Repeat this block for every significant table in the schema. Group tables by domain (auth, catalog, orders, payments, etc.).

---

## Contribution Guide

### Structure

```markdown
# Contributing to [Project Name]

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USER/project.git`
3. Add upstream: `git remote add upstream https://github.com/org/project.git`
4. Install dependencies: `npm install`
5. Copy env file: `cp .env.example .env`
6. Start dev server: `npm run dev`

## Branching Strategy

We use **GitHub Flow**:

- `main` — production-ready code, protected
- `feature/description` — new features
- `fix/description` — bug fixes
- `chore/description` — maintenance, deps updates

## Commit Messages

Follow **Conventional Commits**:

\`\`\`
type(scope): short description

feat(auth): add OAuth2 Google login
fix(cart): resolve quantity rounding error
docs(api): update authentication section
chore(deps): upgrade eslint to v9
\`\`\`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Code Style

- Linter: ESLint (`npm run lint`)
- Formatter: Prettier (`npm run format`)
- Pre-commit hooks: Husky runs lint + format automatically

## Pull Request Process

1. Update docs if you changed behavior
2. Add/update tests for your change
3. Ensure `npm test` passes
4. Open a PR with a clear description
5. Link to the related issue: `Closes #123`
6. Request at least one review

## Tests

\`\`\`bash
npm test              # run all tests
npm run test:unit     # unit tests only
npm run test:e2e      # end-to-end tests
npm run test:coverage # coverage report
\`\`\`
```

---

## Inline Code Documentation

### JavaScript / TypeScript — JSDoc

```javascript
/**
 * Creates a new user account.
 *
 * @param {Object} userData - User creation payload
 * @param {string} userData.email - Valid email address
 * @param {string} userData.password - Plain text password (will be hashed)
 * @param {'admin'|'user'} [userData.role='user'] - User role
 * @returns {Promise<User>} The created user object (without password)
 * @throws {ConflictError} If email is already registered
 *
 * @example
 * const user = await createUser({ email: 'ana@example.com', password: 'secret' });
 */
async function createUser(userData) { ... }
```

### Python — Docstrings (Google style)

```python
def create_user(email: str, password: str, role: str = "user") -> User:
    """Create a new user account.

    Args:
        email: Valid email address for the account.
        password: Plain text password — will be hashed before storage.
        role: User role, either 'admin' or 'user'. Defaults to 'user'.

    Returns:
        The created User object (password field excluded).

    Raises:
        ConflictError: If the email is already registered.

    Example:
        >>> user = create_user("ana@example.com", "secret")
        >>> user.email
        'ana@example.com'
    """
```

### General Guidelines for Inline Docs

- Document **why**, not **what** — the code shows what; comments explain the reasoning
- Every public function/method should have a docstring
- Document non-obvious side effects, performance implications, and external dependencies
- Keep comments up to date — outdated comments are worse than no comments
