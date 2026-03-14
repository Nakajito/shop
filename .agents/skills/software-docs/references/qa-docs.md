# Quality & Testing Documentation Reference

Use sections of this file when generating QA, testing, or security documentation.

---

## Test Plan & Report

### Test Plan Structure

```markdown
# Test Plan — [Project Name] v[X.X]

**Prepared by:** [QA Lead]  
**Date:** YYYY-MM-DD  
**Project phase:** Pre-release / UAT / Regression

---

## 1. Scope

What is being tested and what is explicitly out of scope.

**In scope:**
- User registration and authentication flows
- Product catalog and search
- Shopping cart and checkout
- Payment processing (Stripe integration)
- Admin dashboard

**Out of scope:**
- Third-party payment gateway internals
- Mobile native apps (web responsive only)

---

## 2. Test Types

| Type | Description | Tool | Coverage Target |
|------|-------------|------|----------------|
| Unit | Individual functions and components | Jest / Pytest | 80%+ |
| Integration | Service-to-service communication | Supertest / Postman | Critical paths |
| End-to-End (E2E) | Full user workflows | Playwright / Cypress | Happy paths + key errors |
| UAT | Client validates functional requirements | Manual | 100% of requirements |
| Performance | Load and stress testing | k6 / JMeter | 1000 concurrent users |
| Security | OWASP Top 10 checklist | OWASP ZAP / manual | Critical endpoints |

---

## 3. Test Environment

| Environment | URL | Purpose |
|---|---|---|
| Development | http://localhost:3000 | Active development |
| Staging | https://staging.example.com | Pre-release testing |
| Production | https://app.example.com | Live — no destructive tests |

---

## 4. Test Cases Summary

| ID | Module | Scenario | Type | Status |
|----|--------|----------|------|--------|
| TC-001 | Auth | User registers with valid email | Unit | ✅ Pass |
| TC-002 | Auth | Login with wrong password shows error | Integration | ✅ Pass |
| TC-003 | Cart | Adding out-of-stock item blocked | E2E | ✅ Pass |
| TC-004 | Payment | Declined card shows user-friendly error | Integration | ✅ Pass |
| TC-005 | Admin | Bulk import CSV with 1000 products | Performance | ⚠️ Slow |

---

## 5. Test Report Summary

**Total test cases:** 87  
**Passed:** 83 (95.4%)  
**Failed:** 2 (2.3%)  
**Blocked:** 2 (2.3%)

### Failed Tests

| ID | Test | Failure Description | Severity | Resolution |
|----|------|---------------------|----------|-----------|
| TC-058 | Bulk CSV import >1000 rows | Timeout after 30s | Medium | Pagination fix scheduled for v2.1 |
| TC-072 | Safari mobile checkout | Layout breaks on iOS 16 | Low | CSS fix in next patch |
```

---

## Vulnerability / Security Report

```markdown
# Security Assessment Report — [Project Name]

**Date:** YYYY-MM-DD  
**Methodology:** OWASP Top 10 (2021)  
**Tools used:** OWASP ZAP, manual penetration testing, npm audit

---

## Executive Summary

Overall security posture: **ACCEPTABLE** with two medium-severity findings requiring remediation before production.

---

## OWASP Top 10 Coverage

| # | Vulnerability | Status | Notes |
|---|--------------|--------|-------|
| A01 | Broken Access Control | ✅ Mitigated | RBAC enforced on all routes |
| A02 | Cryptographic Failures | ✅ Mitigated | HTTPS enforced, bcrypt for passwords |
| A03 | Injection (SQL, NoSQL) | ✅ Mitigated | ORM with parameterized queries |
| A04 | Insecure Design | ⚠️ Partial | See finding SEC-002 |
| A05 | Security Misconfiguration | ✅ Mitigated | Security headers configured |
| A06 | Vulnerable Components | ✅ Mitigated | npm audit clean, no critical deps |
| A07 | Auth & Session Failures | ✅ Mitigated | JWT, refresh tokens, rate limiting |
| A08 | Data Integrity Failures | ✅ Mitigated | Input validation via Zod |
| A09 | Logging & Monitoring Failures | ⚠️ Partial | Logs exist; alerting not configured |
| A10 | Server-Side Request Forgery | ✅ N/A | No user-initiated server requests |

---

## Findings

### SEC-001 — Rate Limiting Missing on Password Reset [MEDIUM]

**Description:** The `/auth/reset-password` endpoint has no rate limiting, allowing unlimited requests.  
**Risk:** Brute-force enumeration of valid emails.  
**Recommendation:** Apply rate limiting (5 requests/hour per IP).  
**Status:** 🔴 Open — scheduled for v2.0.1

### SEC-002 — Missing Account Lockout After Failed Logins [MEDIUM]

**Description:** Login endpoint allows unlimited attempts without lockout.  
**Risk:** Credential stuffing attacks.  
**Recommendation:** Lock account after 5 failed attempts for 30 minutes.  
**Status:** ✅ Fixed in commit `a3f2c1b`
```

---

## Traceability Matrix

Maps each business requirement to its feature implementation and test case — confirms complete delivery.

```markdown
# Requirements Traceability Matrix — [Project Name]

| Req ID | Requirement Description | Feature / Module | Test Case(s) | Status |
|--------|------------------------|-----------------|-------------|--------|
| REQ-001 | User can register with email/password | `AuthService.register()` | TC-001, TC-002 | ✅ Done |
| REQ-002 | Products are searchable by name and category | `ProductSearch` component | TC-020, TC-021 | ✅ Done |
| REQ-003 | Cart persists across sessions | `CartContext` + localStorage | TC-035 | ✅ Done |
| REQ-004 | Admin can export orders to CSV | `OrderExport` service | TC-060 | ✅ Done |
| REQ-005 | System supports PayPal and Stripe | `PaymentGateway` abstraction | TC-070, TC-071 | ⚠️ PayPal pending |
| REQ-006 | All pages load in < 3 seconds | CDN + lazy loading | PERF-001 | ✅ Done |

**Coverage:** 5/6 requirements fully implemented and tested (83.3%)  
**Open items:** REQ-005 PayPal integration deferred to v2.1
```
