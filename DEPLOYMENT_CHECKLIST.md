# PostgreSQL Migration Deployment Checklist

## Pre-Deployment (1-2 days before)

### Infrastructure Setup
- [ ] Create Render PostgreSQL database (via render.yaml deployment)
- [ ] Verify database connection string is available in Render dashboard
- [ ] Configure database plan (Starter recommended for production: $7/month)
- [ ] Set up automated backups (Render default: 7 days)

### Code Preparation
- [ ] All migration files updated for PostgreSQL compatibility
- [ ] `db.py` updated with connection pooling and retry logic
- [ ] `config.py` updated with `SQLALCHEMY_ENGINE_OPTIONS`
- [ ] `render.yaml` updated with database service and env vars
- [ ] `.env.example` updated with PostgreSQL example

### Backup Strategy
- [ ] Export SQLite database: `sqlite3 instance/app.db ".backup 'pre_migration_backup.db'"`
- [ ] Export schema: `sqlite3 instance/app.db ".schema" > schema_backup.sql`
- [ ] Export data: `sqlite3 instance/app.db ".dump" > data_backup.sql`
- [ ] Store backups in secure location (S3, GCS, or local)
- [ ] Verify backup integrity by restoring to test database

### Testing
- [ ] Run full test suite locally with PostgreSQL (Docker)
- [ ] Deploy to staging environment
- [ ] Run migration script on staging
- [ ] Verify all features work on staging:
  - [ ] User registration
  - [ ] User login/logout
  - [ ] Session persistence
  - [ ] Community posts/replies
  - [ ] Community votes
  - [ ] Saved mod lists
  - [ ] API key management
  - [ ] Password reset
- [ ] Load test with Locust (simulate expected traffic)
- [ ] Verify no connection pool exhaustion

---

## Deployment Day

### Step 1: Final Pre-Checks (30 minutes before)
- [ ] Confirm low-traffic period (check analytics)
- [ ] Notify team of deployment
- [ ] Have rollback plan ready
- [ ] Ensure all team members are available for support

### Step 2: Create Final Backup (T-15 minutes)
```bash
# Export current SQLite database
sqlite3 instance/app.db ".backup 'final_backup_$(date +%Y%m%d_%H%M%S).db'"

# Verify backup
sqlite3 final_backup_*.db "SELECT COUNT(*) FROM users;"
```

### Step 3: Deploy to Render (T=0)
```bash
# Push changes to Render
git add .
git commit -m "Migrate to PostgreSQL for persistent storage"
git push render main

# Monitor deployment in Render dashboard
# Expected duration: 5-10 minutes
```

### Step 4: Run Migrations (T+10 minutes)
```bash
# SSH into Render instance or use Render web console
# Run Alembic migrations
alembic upgrade head

# Verify tables created
psql $DATABASE_URL -c "\dt"
```

### Step 5: Migrate Data (if needed) (T+20 minutes)
```bash
# Upload SQLite backup to Render
# Or use local migration script
export SQLITE_DB_PATH="final_backup_*.db"
export DATABASE_URL="<from Render dashboard>"

python migrations/migrate_sqlite_to_postgres.py

# Verify row counts
psql $DATABASE_URL -c "SELECT 'users', COUNT(*) FROM users UNION ALL SELECT 'sessions', COUNT(*) FROM user_sessions;"
```

### Step 6: Verify Deployment (T+30 minutes)
- [ ] Health check passes: `curl https://skymodderai.com/healthz`
- [ ] Application logs show no errors
- [ ] Database connections are healthy
- [ ] Connection pool metrics are normal

### Step 7: Functional Testing (T+45 minutes)
- [ ] Register new user account
- [ ] Login with new account
- [ ] Create community post
- [ ] Reply to post
- [ ] Vote on post
- [ ] Save mod list
- [ ] Logout and login again (verify session persistence)
- [ ] Test password reset flow
- [ ] Test OAuth login (Google/GitHub if configured)

### Step 8: Performance Verification (T+60 minutes)
- [ ] Check response times (<500ms for most requests)
- [ ] Monitor connection pool usage (<80% capacity)
- [ ] Verify no timeout errors in logs
- [ ] Check database CPU/memory usage

---

## Post-Deployment (First 24 hours)

### Immediate (First 2 hours)
- [ ] Monitor error rates (Sentry/logs)
- [ ] Watch database connection metrics
- [ ] Respond to any user reports of issues
- [ ] Keep team on standby

### Short-term (First 24 hours)
- [ ] Review error logs every 4 hours
- [ ] Check database performance metrics
- [ ] Verify automated backups are running
- [ ] Document any issues and resolutions

### Long-term (First week)
- [ ] Daily review of database metrics
- [ ] Weekly backup verification (test restore)
- [ ] Monitor cost vs. budget
- [ ] Plan capacity scaling if needed

---

## Rollback Procedure (If Needed)

### Decision Criteria
Rollback if any of these occur:
- Critical data loss detected
- >10% error rate for >15 minutes
- Database connection failures
- Session/authentication failures affecting users

### Rollback Steps
```bash
# 1. Stop current deployment (Render dashboard)

# 2. Revert code changes
git revert HEAD
git push render main

# 3. Restore SQLite database
cp final_backup_*.db instance/app.db

# 4. Verify application works with SQLite

# 5. Investigate issues before re-attempting migration
```

### Rollback Verification
- [ ] Application responds correctly
- [ ] Users can login
- [ ] Data is intact from backup
- [ ] All critical features work

---

## Success Criteria

Migration is successful when:
- [ ] Zero data loss verified
- [ ] All features working correctly
- [ ] Error rate <1% (same as pre-migration)
- [ ] Response times within acceptable range
- [ ] Sessions persist across restarts
- [ ] No connection pool exhaustion
- [ ] Automated backups confirmed working
- [ ] Team signs off on migration

---

## Contact List

| Role | Name | Contact |
|------|------|---------|
| Development Lead | | |
| Operations Lead | | |
| On-call Engineer | | |
| Database Admin | | |

---

## Sign-off

- [ ] All pre-deployment tasks completed
- [ ] Deployment completed successfully
- [ ] Post-deployment verification passed
- [ ] Migration declared successful

**Deployment Date:** _______________
**Deployed By:** _______________
**Sign-off Time:** _______________

---

*Document Version: 1.0*
*Last Updated: February 19, 2026*
