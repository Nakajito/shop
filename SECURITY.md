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
   can grant it, via the Django admin. The entire `ADMIN_URL` prefix
   (including the login form itself) 404s for anyone who isn't already an
   authenticated, active staff user (`myshop/middleware.py:AdminAccessMiddleware`)
   — an anonymous visitor can't tell the admin exists there at all, let
   alone see a login screen to attack. Staff authenticate via the normal
   site login (`accounts:login`) first; once that session is staff, `/admin/`
   (or whatever `ADMIN_URL` is set to) works normally. See that file's
   docstring for a subtle ordering requirement: this middleware must run
   *before* `LocaleMiddleware`, or Django's i18n-redirect-on-404 logic
   quietly turns the 404 into a redirect toward a matching (and unrelated)
   catch-all route instead.
2. **A02 Security Misconfiguration** — `SECRET_KEY`/`ALLOWED_HOSTS`/etc. fail
   closed in `myshop/settings/production.py` (no insecure defaults); security
   headers (HSTS, `X_FRAME_OPTIONS`, `SECURE_REFERRER_POLICY`) set there and
   in `base.py`; `manage.py check --deploy` runs in CI (`.github/workflows/ci.yml`)
   so a regression here fails the build, not a production incident. The
   container drops root before running the app (`Dockerfile`, `appuser`
   uid 1000), but `/app/media` is a Coolify-managed volume mounted at
   container start — outside the image, so the build-time `chown` never
   reaches it. `entrypoint.sh` starts as root specifically to reconcile that
   volume's ownership on every boot before dropping to `appuser` via `gosu`,
   so a volume that predates this non-root setup (or gets recreated by
   Coolify) doesn't silently break every media upload again — it did once,
   caught via a user report of profile pictures not saving, root-caused to
   `MEDIA_ROOT` still owned by `uid 0`.
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
6. **A06 Insecure Design** — this document, plus a Content-Security-Policy in
   Report-Only mode (`myshop/settings/base.py` `CONTENT_SECURITY_POLICY_REPORT_ONLY`,
   `CSPMiddleware`) targeting the strict end-state (nonce-based `script-src`,
   no blanket `'unsafe-inline'` for scripts) so the violation reports collected
   during rollout — logged via `myshop.views.csp_report` — show exactly what's
   left before it's safe to enforce. Walk new features against this list
   before writing code, not after a review flags it.
7. **A07 Authentication Failures** — `django-axes` locks out repeated failed
   logins on both `/accounts/login/` and the Django admin (`AXES_FAILURE_LIMIT`
   in `myshop/settings/base.py`). TOTP-based MFA for staff/admin
   (`django-otp`): self-service enrollment at `accounts:mfa_setup`
   (`accounts/views.py`), `/admin/` itself gated behind a verified device via
   `django_otp.admin.OTPAdminSite` once `MFA_ENFORCE_STAFF=True` — see
   "Known risks" for why that flag defaults to off and stays staff-only.
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
  **`MFA_ENFORCE_STAFF` defaults to `False`** (settings/base.py): staff can
  self-enroll a device at `/accounts/mfa/setup/` at any time regardless of
  this flag, but `/admin/` itself only requires a verified device once the
  flag is flipped to `True`. This is deliberate, not a gap: django-otp's
  `OTPAdminSite` has **no bypass** for a staff account with zero enrolled
  devices — its admin login form always requires an OTP token once active,
  so flipping the flag before every staff/superuser account has enrolled
  would lock them out of `/admin/` with no self-service recovery path
  (verified locally: an unenrolled staff account hitting the gated admin
  login gets a clean "please enter your OTP token" validation error it can
  never satisfy, not a crash — but also no way through). Sequence: (1) staff
  enrolls via the setup page, (2) confirm enrollment works, (3) only then
  set `MFA_ENFORCE_STAFF=True` in the environment and redeploy. Recovery if
  a device is lost: the MFA gate only covers `/admin/`, not the regular site
  login — the affected account can log in normally at `/accounts/login/` and
  disable MFA at `/accounts/mfa/disable/` (password-confirmed) to re-enroll.
- **CSP is deployed in Report-Only mode, not enforced yet** (Phase 2,
  `security/owasp2025-csp-rollout`). `script-src` uses a per-request nonce;
  every inline `<script>` block carries `nonce="{{ request.csp_nonce }}"`,
  and every inline `onclick=`/`onload=` attribute site-wide has been
  refactored to delegated `addEventListener` handlers (see `js-go-back`,
  `js-remove-parent`, `js-copy-tracking` in `shop/templates/shop/base.html`
  and the per-page `extra_js` blocks) — so `script-src` carries **no**
  `'unsafe-inline'`. One casualty: the font `<link rel="preload">`+`onload=""`
  swap trick (non-blocking font load) can't be done CSP-safely without the
  inline attribute — moving the swap into a nonce'd `<script>` reintroduces
  the exact race it was designed to avoid (confirmed locally: the `load`
  event can fire, for a cached response, before that script runs, leaving
  the stylesheet permanently stuck at `rel="preload"`). Simplified to a
  plain synchronous `<link rel="stylesheet">` instead — correct over clever.
  `style-src` deliberately keeps `'unsafe-inline'` (~40 `style=""` attributes
  across ~17 templates; low risk, high refactor cost — a conscious
  trade-off, not an oversight). Bootstrap 5 and Bootstrap Icons are vendored
  locally under `static/vendor/` (no longer loaded from `cdn.jsdelivr.net`)
  specifically so the policy doesn't need a CDN exception. Violation reports
  land in the `security` logger via `myshop.views.csp_report`
  (`POST /csp-report/`). What's left before flipping
  `CONTENT_SECURITY_POLICY_REPORT_ONLY` to `CONTENT_SECURITY_POLICY` to
  actually enforce: a monitoring period against real production traffic
  (local smoke-testing can't cover every code path — every product, every
  order state, every blog post with a video embed, etc.).
- **`wholesaler` is currently just a flag** — no differentiated pricing or
  catalog logic reads it yet. Self-escalation to it is blocked (A01 above),
  but if/when pricing logic is built on top of it, re-review this doc.

## Threat modeling for new features

Before shipping anything that touches auth, payments, user data, or admin
capabilities, walk it against the 10 categories above. In particular: does a
new view need an object-level ownership check (A01)? Does a new setting need
to fail closed (A02)? Does a new error path leak internals (A10)?
