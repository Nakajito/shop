# Operational & Support Documentation Reference

Use sections of this file when generating IT operations, DevOps, or infrastructure documentation.

---

## Backup & Recovery Protocol

```markdown
# Backup & Recovery Protocol — [Project Name]

**Version:** 1.0  
**Owner:** DevOps / IT Operations  
**Last reviewed:** YYYY-MM-DD

---

## Backup Schedule

| Asset | Frequency | Retention | Method | Location |
|-------|-----------|-----------|--------|----------|
| PostgreSQL DB | Every 6 hours | 30 days | pg_dump → S3 | `s3://backups/db/` |
| Media files (S3) | Daily | 90 days | S3 versioning | Same bucket, versioned |
| Application config | On every deploy | Indefinite | Git repository | GitHub |
| Redis cache | Not backed up | — | Rebuilt on restart | — |

> ⚠️ **Critical:** Database backups are the most important asset. Verify the automated schedule is running weekly using the monitoring dashboard.

---

## Backup Verification

Run a test restoration monthly:

\`\`\`bash
# 1. List available backups
aws s3 ls s3://backups/db/ --recursive | tail -20

# 2. Download latest backup
aws s3 cp s3://backups/db/latest.dump /tmp/restore_test.dump

# 3. Restore to test database
pg_restore -h localhost -U postgres -d db_test /tmp/restore_test.dump

# 4. Verify row counts match production
psql -h localhost -U postgres -d db_test -c "SELECT COUNT(*) FROM users;"
\`\`\`

---

## Disaster Recovery Steps

**Scenario:** Production database is corrupted or accidentally deleted.

1. **Immediately notify** the tech lead and client
2. **Scale down** the application to prevent further writes
   ```bash
   kubectl scale deployment app --replicas=0
   ```
3. **Identify** the most recent clean backup
   ```bash
   aws s3 ls s3://backups/db/ --recursive | sort | tail -5
   ```
4. **Provision** a new database instance (RDS or local)
5. **Restore** from backup (see verification steps above)
6. **Update** the `DATABASE_URL` environment variable
7. **Scale up** the application
8. **Verify** basic functionality (login, data reads)
9. **Document** the incident in the incident log

**Expected RTO (Recovery Time Objective):** < 2 hours  
**Expected RPO (Recovery Point Objective):** < 6 hours (last backup)
```

---

## Infrastructure Configuration

```markdown
# Infrastructure Configuration — [Project Name]

**Environment:** Production  
**Last updated:** YYYY-MM-DD  
**Cloud provider:** AWS / GCP / Azure / DigitalOcean

---

## Architecture Overview

\`\`\`mermaid
graph TD
  DNS[Route 53 / Cloudflare] --> LB[Load Balancer]
  LB --> App1[App Server 1]
  LB --> App2[App Server 2]
  App1 --> DB[(RDS PostgreSQL)]
  App1 --> Cache[(ElastiCache Redis)]
  App1 --> Storage[(S3 Bucket)]
  App1 --> Queue[(SQS Queue)]
\`\`\`

---

## Server Inventory

| Server | Provider | Size | Region | Purpose |
|--------|---------|------|--------|---------|
| app-prod-01 | AWS EC2 | t3.medium | us-east-1 | App server (primary) |
| app-prod-02 | AWS EC2 | t3.medium | us-east-1 | App server (secondary) |
| db-prod | AWS RDS | db.t3.large | us-east-1 | PostgreSQL 15 |
| cache-prod | AWS ElastiCache | cache.t3.micro | us-east-1 | Redis 7 |

---

## Domain & SSL

| Domain | DNS Provider | SSL Certificate | Expires | Auto-renew |
|--------|-------------|----------------|---------|-----------|
| app.example.com | Cloudflare | Let's Encrypt | 2025-03-15 | ✅ Yes |
| api.example.com | Cloudflare | Let's Encrypt | 2025-03-15 | ✅ Yes |
| admin.example.com | Cloudflare | Let's Encrypt | 2025-03-15 | ✅ Yes |

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379` |
| `JWT_SECRET` | JWT signing secret (min 32 chars) | Stored in AWS Secrets Manager |
| `STRIPE_SECRET_KEY` | Stripe API key | Stored in AWS Secrets Manager |
| `S3_BUCKET` | Media storage bucket name | `myapp-prod-media` |
| `SMTP_HOST` | Email server | `smtp.sendgrid.net` |

> 🔐 **Security:** Sensitive values are stored in AWS Secrets Manager, not in `.env` files in production.

---

## CI/CD Pipeline

| Stage | Tool | Trigger | Duration |
|-------|------|---------|---------|
| Test | GitHub Actions | Every PR | ~3 min |
| Build | GitHub Actions | Push to `main` | ~5 min |
| Deploy staging | GitHub Actions | Push to `main` | ~2 min |
| Deploy production | GitHub Actions (manual) | Manual approval | ~3 min |
```

---

## Known Issues Log

```markdown
# Known Issues Log — [Project Name]

Last updated: YYYY-MM-DD

| ID | Description | Severity | Status | Workaround | Fix planned |
|----|-------------|---------|--------|-----------|-------------|
| KI-001 | Bulk CSV import fails for files > 5MB | Medium | Open | Split file into chunks < 5MB | v2.1 |
| KI-002 | Password reset email delayed up to 5 min during peak hours | Low | Open | Inform user to check spam | v2.2 |
| KI-003 | Safari iOS 15 checkout layout misaligned | Low | Open | Use Chrome or Firefox on mobile | v2.0.1 |
| KI-004 | Admin export to CSV truncates descriptions > 500 chars | Low | Fixed (v2.0.2) | — | — |
```

---

## Runbook / Incident Response

```markdown
# Runbook — [Project Name]

Quick reference for common incidents and on-call procedures.

---

## Application is Down (500 errors)

1. Check application logs:
   ```bash
   kubectl logs -l app=myapp --tail=100
   ```
2. Check database connectivity:
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```
3. Restart application pods:
   ```bash
   kubectl rollout restart deployment/myapp
   ```
4. If not resolved → escalate to senior engineer

---

## Database Connection Pool Exhausted

**Symptoms:** `connection timeout` errors, slow responses

1. Check current connections:
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```
2. Kill idle connections older than 10 min:
   ```sql
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle' AND query_start < NOW() - INTERVAL '10 minutes';
   ```
3. Review and adjust `DB_POOL_MAX` env var if this recurs

---

## High Memory / CPU Alert

1. Identify heavy processes:
   ```bash
   top -o %MEM
   ```
2. Check for memory leak in recent deploys
3. Scale up horizontally if needed:
   ```bash
   kubectl scale deployment myapp --replicas=4
   ```

---

## SSL Certificate Expired

1. If using Let's Encrypt with Certbot:
   ```bash
   certbot renew --force-renewal
   systemctl reload nginx
   ```
2. Verify: `curl -vI https://app.example.com 2>&1 | grep -i expire`

---

## On-Call Contacts

| Role | Name | Contact |
|------|------|---------|
| Primary on-call | [Name] | +52 55 0000 0000 |
| Secondary on-call | [Name] | +52 55 0000 0001 |
| DB specialist | [Name] | Slack: @username |
| Cloud/Infra | [Name] | Slack: @username |
```
