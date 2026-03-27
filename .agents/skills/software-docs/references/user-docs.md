# User & Functional Documentation Reference

Use sections of this file when generating documentation for end users, administrators, or clients.

---

## User Manual / Admin Guide

### Structure

```markdown
# [Project Name] — User Manual

**Version:** 1.0  
**Audience:** End users / Administrators  
**Last updated:** YYYY-MM-DD

---

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Main Features](#main-features)
4. [Frequently Asked Questions](#faq)
5. [Glossary](#glossary)

---

## 1. Introduction

Brief, plain-language description of what the system does and who it's for. Avoid all technical jargon.

## 2. Getting Started

### Creating an Account

1. Go to [https://app.example.com](https://app.example.com)
2. Click **Sign Up** in the top right corner
3. Enter your email and choose a password
4. Check your inbox for a confirmation email
5. Click the link in the email to activate your account

> 💡 **Tip:** Use your work email to access team features automatically.

### Logging In

1. Go to the login page
2. Enter your email and password
3. Click **Log In**

> ⚠️ **Note:** After 5 failed login attempts, your account will be locked for 30 minutes.

## 3. Main Features

Organize by role or workflow. Use numbered steps for processes. Include screenshots or diagrams when available.

### For Administrators: Managing Products

1. Go to **Dashboard → Products**
2. Click **+ Add Product**
3. Fill in the required fields:
   - Product name
   - Price
   - Stock quantity
   - Category
4. Upload at least one product image
5. Click **Save** to publish, or **Save as Draft** to review later

### For Users: Placing an Order

...
```

### Tone Guidelines for User Docs

- Use "you" to address the reader directly
- Use imperative for steps: "Click Save", not "The user should click Save"
- Avoid acronyms without defining them first
- Keep sentences short — one action per step
- Add ⚠️ warnings for irreversible actions and 💡 tips for shortcuts

---

## User Stories / Use Cases

### User Story Format (Agile)

```markdown
## US-001: User Registration

**As a** new visitor,  
**I want to** create an account with my email and password,  
**So that** I can access my personal dashboard and order history.

### Acceptance Criteria

- [ ] User can register with a unique email address
- [ ] Password must be at least 8 characters with one uppercase and one number
- [ ] User receives a confirmation email after registration
- [ ] User cannot log in until email is confirmed
- [ ] Duplicate emails show a clear error message

**Priority:** High  
**Status:** ✅ Completed  
**Sprint:** 2
```

### Use Case Format (Traditional)

```markdown
## UC-003: Process Payment

**Actor:** Authenticated customer  
**Preconditions:** Cart has at least one item; user is logged in  
**Trigger:** User clicks "Proceed to Checkout"

### Main Flow

1. System displays order summary with total price
2. User selects payment method (card, PayPal, etc.)
3. User enters payment details
4. System validates card details with payment gateway
5. Payment gateway returns authorization
6. System creates order record and sends confirmation email
7. System reduces inventory stock

### Alternative Flows

- **4a. Payment declined:** System shows error message; user may retry or use a different method
- **4b. Gateway timeout:** System retries once after 5 seconds; if still failing, shows error and cancels transaction

**Postconditions:** Order created, payment captured, inventory updated
```

---

## Glossary of Terms

Include domain-specific terms, system-specific concepts, and any acronyms used.

```markdown
# Glossary of Terms — [Project Name]

| Term | Definition |
|------|-----------|
| **SKU** | Stock Keeping Unit. A unique code assigned to each product variant (size, color, etc.) used for inventory tracking. |
| **Fulfillment** | The process of picking, packing, and shipping an order after it has been placed. |
| **Payment Gateway** | A third-party service (e.g., Stripe, PayPal) that securely processes credit card transactions. |
| **Stock** | The quantity of a product currently available for sale. When stock reaches 0, the product is marked as Out of Stock. |
| **Order Status** | The current state of an order: Pending → Processing → Shipped → Delivered → Cancelled |
| **UAT** | User Acceptance Testing. The final testing phase where the client validates that the system meets their requirements. |
| **SLA** | Service Level Agreement. A contract specifying the minimum standards for system availability and response times. |
| **RBAC** | Role-Based Access Control. A system where user permissions are determined by their assigned role. |
```

Adapt the glossary to the project domain — an e-commerce system will have different terms than a healthcare platform or a logistics SaaS.

---

## Changelog / Release Notes

```markdown
# Changelog

All notable changes to this project are documented here.
Format: [Semantic Versioning](https://semver.org/)

---

## [2.1.0] — 2024-06-10

### Added
- Bulk product import via CSV
- Multi-currency support (USD, MXN, EUR)
- Email notifications for low stock alerts

### Changed
- Checkout flow redesigned — reduced steps from 5 to 3
- Product search now includes tags and descriptions

### Fixed
- Cart total rounding error with discount codes
- Mobile layout broken on iPhone SE

---

## [2.0.0] — 2024-03-01

### Breaking Changes
- API v1 endpoints removed — use v2
- `user.username` field replaced by `user.displayName`

### Added
- Admin dashboard with analytics
- OAuth2 login (Google, GitHub)
```
