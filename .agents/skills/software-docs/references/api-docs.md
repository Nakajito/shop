# API Documentation Reference

Use this guide when writing REST or GraphQL API documentation for any project type.

---

## REST API Structure

### Overview Section

Start every API doc with:
- Base URL and versioning scheme (`https://api.example.com/v1`)
- Authentication method summary
- Rate limiting policy
- Common response formats and conventions

### Endpoint Index Table

```markdown
## Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/users` | List all users | ✅ Bearer |
| POST | `/users` | Create a new user | ✅ Bearer |
| GET | `/users/:id` | Get user by ID | ✅ Bearer |
| PUT | `/users/:id` | Update user | ✅ Bearer |
| DELETE | `/users/:id` | Delete user | ✅ Bearer Admin |
```

### Per-Endpoint Block Template

```markdown
## POST /users

Creates a new user account.

**Auth required:** Bearer token (scope: `users:write`)

### Request

\`\`\`http
POST /api/v1/users
Content-Type: application/json
Authorization: Bearer <token>
\`\`\`

\`\`\`json
{
  "name": "Ana López",
  "email": "ana@example.com",
  "role": "admin"
}
\`\`\`

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Full name, 2–100 chars |
| `email` | string | ✅ | Valid email address |
| `role` | string | ❌ | `admin` or `user` (default: `user`) |

### Response — 201 Created

\`\`\`json
{
  "id": "usr_abc123",
  "name": "Ana López",
  "email": "ana@example.com",
  "role": "admin",
  "createdAt": "2024-01-15T10:30:00Z"
}
\`\`\`

### Error Responses

| Code | Reason |
|------|--------|
| 400 | Missing or invalid required fields |
| 409 | Email already registered |
| 422 | Validation failed |
| 401 | Invalid or expired token |
| 403 | Insufficient permissions |
| 500 | Internal server error |
```

---

## Authentication Section

Always include a dedicated auth section:

```markdown
## Authentication

This API uses **JWT Bearer tokens**.

### Obtain a Token

\`\`\`http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret"
}
\`\`\`

Response:
\`\`\`json
{
  "token": "eyJhbGci...",
  "expiresIn": 3600,
  "refreshToken": "rft_xyz..."
}
\`\`\`

### Use the Token

Include in every request header:
\`\`\`
Authorization: Bearer eyJhbGci...
\`\`\`

### Token Refresh

\`\`\`http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
\`\`\`

Tokens expire after **1 hour**. Use the refresh token to obtain a new access token without re-logging in.
```

---

## Error Conventions

Document the standard error envelope used by the API:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The 'email' field is required.",
    "details": [
      { "field": "email", "issue": "required" }
    ]
  }
}
```

Include a global error code table covering 4xx and 5xx scenarios.

---

## GraphQL APIs

For GraphQL, document:

### Schema Types

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  role: UserRole!
  createdAt: DateTime!
}

enum UserRole {
  ADMIN
  USER
}
```

### Queries

```graphql
# Get a user by ID
query GetUser($id: ID!) {
  user(id: $id) {
    id
    name
    email
  }
}
```

### Mutations

```graphql
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    id
    name
  }
}
```

### Variables Example

```json
{
  "input": {
    "name": "Ana López",
    "email": "ana@example.com"
  }
}
```

---

## Pagination

Document pagination conventions used across the API:

```markdown
## Pagination

All list endpoints support cursor-based pagination.

### Parameters

| Param | Type | Description |
|-------|------|-------------|
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Items per page (default: 20, max: 100) |
| `cursor` | string | Cursor for cursor-based pagination |

### Response Envelope

\`\`\`json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "page": 1,
    "limit": 20,
    "hasNext": true,
    "nextCursor": "cur_abc"
  }
}
\`\`\`
```

---

## Versioning

Note deprecated endpoints clearly:

> ⚠️ **Deprecated in v2**: `GET /users/list` — use `GET /users` instead. Will be removed in v3.

---

## Tooling Recommendations

Suggest based on project needs:
- **Swagger/OpenAPI 3.0** — industry standard for REST, generates interactive docs
- **Redoc** — clean rendering of OpenAPI specs
- **Postman Collections** — shareable, executable examples
- **GraphQL Playground / Apollo Studio** — for GraphQL
- **Scalar** — modern OpenAPI UI alternative to Swagger UI
