# Security

How this project maps to the OWASP Top 10 (2025), and a running list of
risks we've deliberately accepted (with the reasoning), so they don't get
"rediscovered" as surprise bugs later. Read this before designing a feature
that touches auth, payments, user data, or admin capabilities.

## OWASP Top 10 (2025) — where the controls live

1. **A01 Broken Access Control** — object-level ownership checks on orders
   (`orders/views/_helpers.py:get_user_order`) and payment views
   (`payment/views.py`); `user_type` is not self-assignable to `wholesaler`
   (`accounts/forms.py`, `accounts/views.py:change_user_type`) — only staff
   can grant it, via the Django admin.
2. **A02 Security Misconfiguration** — `SECRET_KEY`/`ALLOWED_HOSTS`/etc. fail
   closed in `myshop/settings/production.py` (no insecure defaults); security
   headers (HSTS, `X_FRAME_OPTIONS`, `SECURE_REFERRER_POLICY`) set there and
   in `base.py`; `manage.py check --deploy` runs in CI (`.github/workflows/ci.yml`)
   so a regression here fails the build, not a production incident.
3. **A03 Software Supply Chain Failures** — CodeQL (`.github/workflows/codeql.yml`),
   Dependabot (`.github/dependabot.yml`), GitHub Actions pinned by commit SHA,
   `pip-audit` in CI (currently informational — see "Known risks" below),
   `.github/CODEOWNERS` for required review before `main` (which Coolify
   auto-deploys on every push).
4. **A04 Cryptographic Failures** — no PANs stored (Stripe tokenization only,
   `payment/models.py`), PBKDF2 password hashing in production, TLS enforced
   via `SECURE_SSL_REDIRECT`/HSTS.
5. **A05 Injection** — no raw SQL/`eval`/`shell=True` in app code. One
   deliberate `mark_safe` (`shop/templatetags/i18n_extras.py:tr_safe`): the
   text it renders is always staff-authored CKEditor5 content (blog/product
   fields), never end-user input — same trust boundary as Django's built-in
   `|safe`. Don't reuse `tr_safe` for anything a non-staff user can write.
6. **A06 Insecure Design** — this document. Walk new features against this
   list before writing code, not after a review flags it.
7. **A07 Authentication Failures** — `django-axes` locks out repeated failed
   logins on both `/accounts/login/` and the Django admin (`AXES_FAILURE_LIMIT`
   in `myshop/settings/base.py`). MFA is staff/admin-only for now — see
   "Known risks".
8. **A08 Software or Data Integrity Failures** — Stripe webhook verifies the
   signature before processing (`payment/webhooks.py`). Merge-to-`main`
   requires review per CODEOWNERS since Coolify deploys straight from `main`.
9. **A09 Security Logging and Alerting Failures** — a dedicated `security`
   logger (`myshop/settings/base.py` `LOGGING`) records wholesaler
   self-escalation attempts, account deactivation, and blocked IDOR attempts
   in `payment/views.py`; `django-axes` logs lockouts under its own `axes`
   logger. Sentry runs with `send_default_pii=False`.
10. **A10 Mishandling of Exceptional Conditions** — `payment/views.py` never
    returns a raw exception/Stripe error message to the client; it logs the
    detail server-side and shows a generic, translated message instead.

## Known / accepted risks

- **Django is pinned to the 5.0 series (`pyproject.toml`), which is past its
  security-support window.** `pip-audit` currently flags ~11 CVEs on
  `django==5.0.14` whose fixes only ship in 5.1+/5.2/6.0 — outside the
  `<5.1` range, and 5.0.14 is already the newest available 5.0.x patch, so
  nothing in-range fixes this. Upgrading is a real, separate initiative
  (breaking-change review, full regression pass) — **not bundled into the
  `security/owasp2025-*` branches**, both because it's high-blast-radius for
  a live production app and because it's out of the scope those branches were
  scoped for. Track this as its own upgrade branch. Until it lands, the
  `pip-audit` CI step is informational (`continue-on-error`) rather than a
  hard gate, specifically because of this known baseline — flip it back to
  blocking once the Django upgrade merges.
- **MFA covers staff/admin only**, not regular customers (Phase 3 of the
  OWASP hardening work, `security/owasp2025-mfa-staff`). Extending it to
  customers is a separate UX project.
- **CSP is not enforced yet** (Phase 2, `security/owasp2025-csp-rollout`):
  Stripe.js, Google OAuth, and CKEditor5 all need an inline-script/style
  audit first; that branch starts in report-only mode before enforcing.
- **`wholesaler` is currently just a flag** — no differentiated pricing or
  catalog logic reads it yet. Self-escalation to it is blocked (A01 above),
  but if/when pricing logic is built on top of it, re-review this doc.

## Threat modeling for new features

Before shipping anything that touches auth, payments, user data, or admin
capabilities, walk it against the 10 categories above. In particular: does a
new view need an object-level ownership check (A01)? Does a new setting need
to fail closed (A02)? Does a new error path leak internals (A10)?
