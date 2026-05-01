# Deployment Guide - Security Updates

## Pre-Deployment Checklist

### 1. Local Testing (Development Machine)
```bash
# Step 1: Install dependencies
pip install -r requirements.txt

# Step 2: Create environment file
cp .env.example .env

# Step 3: (If you have existing database with plain-text passwords)
python migrate_passwords.py

# Step 4: Run the application
python app.py

# Step 5: Test all login flows
# - Visit http://localhost:5000/login/Admin
# - Visit http://localhost:5000/login/Guide
# - Visit http://localhost:5000/login/Student
# - Verify you can login with existing credentials
```

### 2. Verify All Changes
```bash
# Check that .env is in .gitignore
cat .gitignore | grep ".env"

# Verify bcrypt is imported
grep "from flask_bcrypt import Bcrypt" app.py

# Verify environment variables are loaded
grep "load_dotenv()" app.py

# Verify password hashing methods exist
grep "def set_password" app.py
grep "def check_password" app.py
```

---

## Staging Deployment

### Pre-Staging Checklist
- [ ] All local tests pass
- [ ] Migration script runs successfully
- [ ] .env file created and configured
- [ ] No sensitive data in git history

### Deploy to Staging
```bash
# 1. Clone/pull latest code
git pull origin main  # or your branch

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env from .env.example
cp .env.example .env
# Edit .env with staging values

# 4. Database migration (if applicable)
python migrate_passwords.py

# 5. Start services
# (Docker, systemd, or your container orchestration)

# 6. Run smoke tests
python -c "from app import app; print('Import successful')"

# 7. Test login endpoints
curl -X POST http://staging-url/login/Admin \
  -d "email=admin@gmail.com&password=admin123"

# 8. Monitor logs for errors
tail -f /var/log/app.log
```

---

## Production Deployment

### 1. Backup Database
```bash
# SQLite
cp database.db database.db.backup.$(date +%Y%m%d_%H%M%S)

# PostgreSQL
pg_dump mydb > mydb.backup.$(date +%Y%m%d_%H%M%S).sql

# MySQL
mysqldump -u user -p database > database.backup.$(date +%Y%m%d_%H%M%S).sql
```

### 2. Prepare Environment
```bash
# Generate a strong secret key
python -c "import secrets; print(secrets.token_hex(32))"
# Output example: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# Create .env.prod with production values
cat > .env.prod << EOF
SECRET_KEY=<your_strong_secret_key_here>
DATABASE_URL=<your_production_database_url>
ADMIN_EMAIL=<your_production_admin_email>
ADMIN_PASSWORD=<your_production_admin_password>
FLASK_ENV=production
EOF

# Set proper permissions
chmod 600 .env.prod
```

### 3. Deploy Code
```bash
# Option A: Using Docker
docker build -t spark-app:latest .
docker push spark-app:latest
docker-compose -f docker-compose.prod.yml up -d

# Option B: Using systemd
systemctl stop spark-app
git pull origin main
pip install -r requirements.txt
systemctl start spark-app

# Option C: Using Kubernetes
kubectl set image deployment/spark-app spark-app=spark-app:latest
kubectl rollout status deployment/spark-app
```

### 4. Database Migration
```bash
# SSH into production server
ssh user@production-server

# Activate virtual environment
source /path/to/venv/bin/activate

# Set environment variables
export $(cat .env.prod | xargs)

# Run migration script
python migrate_passwords.py

# Verify database integrity
python -c "from app import app, db, Guide; \
  with app.app_context(): \
    guides = Guide.query.all(); \
    print(f'Total guides: {len(guides)}'); \
    hashed = sum(1 for g in guides if g.password.startswith('\$2')); \
    print(f'Hashed passwords: {hashed}')"
```

### 5. Post-Deployment Verification
```bash
# Health check
curl -s http://production-url/ | grep "<title>"

# Login test
curl -X POST http://production-url/login/Admin \
  -d "email=$(grep ADMIN_EMAIL .env.prod | cut -d= -f2)&password=test"

# Database check
mysql> SELECT COUNT(*) FROM guide WHERE password LIKE '$2%';
SELECT COUNT(*) FROM Student_login WHERE password LIKE '$2%';

# Index verification
SHOW INDEX FROM guide;
SHOW INDEX FROM project;
SHOW INDEX FROM Student_login;

# Monitor logs
tail -f /var/log/flask_app.log | grep -i error
```

---

## Rolling Back (If Issues Occur)

### Rollback Plan
```bash
# Stop current version
systemctl stop spark-app

# Restore database backup
cp database.db.backup database.db
# OR for PostgreSQL:
# psql mydb < mydb.backup.sql

# Checkout previous code version
git checkout <previous_commit_hash>

# Start previous version
systemctl start spark-app

# Verify functionality
curl http://production-url/login/Guide

# Investigate issue
cat /var/log/flask_app.log | grep -i error
```

### When to Rollback
- ⚠️ Widespread login failures
- ⚠️ Database connectivity issues
- ⚠️ Critical application errors in logs
- ⚠️ Performance degradation (> 100ms response time)

---

## Docker Deployment Example

### Dockerfile (if not using python app directly)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

# Run the app
CMD ["python", "app.py"]
```

### docker-compose.yml for Production
```yaml
version: '3.8'

services:
  app:
    image: spark-app:latest
    container_name: spark-flask-app
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - ADMIN_EMAIL=${ADMIN_EMAIL}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - FLASK_ENV=production
    volumes:
      - ./instance:/app/instance
      - ./static/uploads:/app/static/uploads
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: PostgreSQL database
  db:
    image: postgres:15-alpine
    container_name: spark-postgres
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

volumes:
  postgres_data:
```

---

## Monitoring Post-Deployment

### 1. Application Metrics
```bash
# Log all authentication attempts
tail -f /var/log/flask_app.log | grep "login\|Invalid Credentials"

# Monitor errors
tail -f /var/log/flask_app.log | grep -i error

# Performance monitoring
# Monitor response times for /student/dashboard
# Should not exceed 100ms with indexes
```

### 2. Database Monitoring
```sql
-- Check for slow queries (MySQL)
SHOW VARIABLES LIKE 'slow_query%';
SELECT * FROM mysql.slow_log;

-- Check index usage
SELECT * FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA != 'mysql' AND COUNT_STAR > 0;

-- PostgreSQL: Check index usage
SELECT * FROM pg_stat_user_indexes;
```

### 3. Security Monitoring
```bash
# Monitor failed login attempts
grep "Invalid Credentials" /var/log/flask_app.log | wc -l

# Check for brute force attacks (same IP multiple failures)
grep "Invalid Credentials" /var/log/flask_app.log | \
  sed -n "s/.*from \([0-9.]*\).*/\1/p" | sort | uniq -c | sort -rn

# Monitor for database errors
grep -i "database\|sql\|integrity" /var/log/flask_app.log
```

---

## Common Deployment Issues

### Issue: "Secret key not found"
```bash
# Solution: Ensure .env exists with SECRET_KEY
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" >> .env
```

### Issue: "Password hashing failed"
```bash
# Solution: Ensure Flask-Bcrypt is installed
pip install Flask-Bcrypt
python -c "from flask_bcrypt import Bcrypt; print('OK')"
```

### Issue: "Database indexes not created"
```bash
# Solution: Run create_all()
python -c "from app import app, db; \
  with app.app_context(): db.create_all()"
```

### Issue: "Old passwords still work"
```bash
# Solution: Run migration script
python migrate_passwords.py
```

---

## Maintenance Schedule

### Daily
- Monitor error logs
- Check failed login attempts
- Monitor response times

### Weekly
- Review database size (especially uploads folder)
- Verify backup completion
- Check index fragmentation (if applicable)

### Monthly
- Performance analysis
- Security audit logs
- Update dependencies

### Quarterly
- Major backup restore test (non-production)
- Security vulnerability scan
- Database optimization (VACUUM, ANALYZE)

---

## Success Metrics

After deployment, verify:
- ✅ All users can login successfully
- ✅ Search response time < 100ms
- ✅ No password hashing errors in logs
- ✅ Zero "Invalid Credentials" false negatives
- ✅ Database indexes created and used
- ✅ All files upload/download working
- ✅ Admin dashboard loads < 500ms

---

## Support & Troubleshooting

For issues, check in this order:
1. Application logs: `/var/log/flask_app.log`
2. Database logs: Check database-specific logs
3. System resources: `free -h`, `df -h`
4. Network connectivity: `ping`, `curl` endpoints
5. Configuration: Verify `.env` values

If stuck:
- Review `SECURITY_AND_PERFORMANCE_IMPROVEMENTS.md`
- Review `IMPLEMENTATION_SUMMARY.md`
- Check GitHub issues for similar problems
- Enable Flask debug mode (dev only): `app.run(debug=True)`

---

**Deployment Status**: ✅ Ready for production
**Last Updated**: 2026-05-01
**Version**: 1.0
