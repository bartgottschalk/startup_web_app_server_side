# AWS RDS Django Integration - Phase 8

**Date**: November 20, 2025
**Status**: ✅ Complete - Django Production Settings Created
**Branch**: `feature/aws-rds-django-deployment`

## Executive Summary

Created Django production settings module and enhanced infrastructure tooling to enable secure deployment to AWS RDS PostgreSQL. All production secrets (database, Django SECRET_KEY, Stripe, Email) are now managed via AWS Secrets Manager, eliminating hardcoded credentials from the codebase.

## Changes Implemented

### 1. Production Settings Module (`settings_production.py`)

Created a new Django settings module for production deployment that:
- Retrieves ALL secrets from AWS Secrets Manager (not just database credentials)
- Supports multi-tenant database configuration via `DATABASE_NAME` environment variable
- Enforces production security settings (HTTPS, HSTS, secure cookies)
- Provides graceful fallback to environment variables for local testing
- Properly handles module-level imports after secret retrieval

**Secrets Retrieved from AWS Secrets Manager:**
- Database credentials (host, port, username, password)
- Django SECRET_KEY (50-character auto-generated)
- Stripe API keys (secret_key, publishable_key)
- Email SMTP credentials (host, port, user, password)

**File**: `StartupWebApp/StartupWebApp/settings_production.py` (233 lines)

**Usage:**
```bash
export DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production
export DATABASE_NAME=startupwebapp_prod
export DB_SECRET_NAME=rds/startupwebapp/multi-tenant/master
export AWS_REGION=us-east-1
export ALLOWED_HOSTS=www.mosaicmeshai.com
python manage.py migrate
```

### 2. Updated Infrastructure Scripts

**`scripts/infra/create-secrets.sh`:**
- Expanded to create ALL production secrets in single AWS Secrets Manager secret
- Auto-generates secure Django SECRET_KEY (50 characters)
- Creates placeholder values for Stripe and Email (must be updated manually)
- Clear documentation about what's auto-generated vs. what needs manual updates
- **Tested**: Successfully creates expanded secret structure

**`scripts/infra/destroy-secrets.sh`:**
- Updated documentation to reflect it destroys ALL production secrets
- Enhanced warning messages: "Database, Django SECRET_KEY, Stripe, Email credentials"
- **Tested**: Warning messages display correctly, 30-day recovery window works

**`scripts/infra/test-rds-connection.py`:**
- New deployment validation tool for testing AWS RDS connectivity
- Tests: Secrets Manager access, database configuration, connection, queries, Django apps
- Provides clear error messages and troubleshooting guidance
- Located in `scripts/infra/` (co-located with other infrastructure tools)
- **File**: 235 lines

### 3. Dependencies

**`requirements.txt`:**
- Added `boto3==1.35.76` for AWS SDK (Secrets Manager, S3, etc.)

### 4. Documentation Updates

**`docs/SESSION_START_PROMPT.md`:**
- Clarified Python linting workflow (Django apps only, not infrastructure scripts)
- Documented that infrastructure scripts in `scripts/infra/` are not mounted in Docker

## Security Improvements

### Before
- Database credentials in `settings_secret.py` (gitignored)
- Django SECRET_KEY in `settings_secret.py` (gitignored)
- Stripe keys in `settings_secret.py` (gitignored)
- Email credentials in `settings_secret.py` (gitignored)
- **Problem**: Secrets managed manually, no centralized secret rotation

### After
- ALL secrets retrieved from AWS Secrets Manager at runtime
- Zero hardcoded credentials in codebase or environment files
- Centralized secret management with AWS IAM permissions
- Secrets can be rotated via AWS Console or CLI without code changes
- Production settings module can be committed safely to Git

## Testing & Validation

### Unit Tests
**Status**: ✅ All 712 tests passing
```bash
docker-compose exec backend python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests --parallel=4
# Result: Ran 712 tests in 22.758s - OK
```

### Code Quality
**Status**: ✅ Zero linting errors
```bash
docker-compose exec backend flake8 StartupWebApp/settings_production.py --max-line-length=120 --statistics
# Result: 0 errors
```

### Infrastructure Validation
**Status**: ✅ Full destroy → create cycle tested

**Test Sequence:**
1. ✅ `destroy-monitoring.sh` - Cleaned up alarms, SNS, dashboard
2. ✅ `destroy-rds.sh` - Deleted RDS without snapshot
3. ✅ `destroy-secrets.sh` - **NEW expanded warnings displayed correctly**
4. ✅ `create-secrets.sh` - **NEW expanded secret structure created**
   - Auto-generated: DB password (32 chars) + Django SECRET_KEY (50 chars)
   - Placeholders: Stripe keys + Email credentials
5. ✅ `create-rds.sh` - Used new password, updated secret with endpoint
6. ✅ `create-monitoring.sh` - Recreated all monitoring
7. ✅ `show-resources.sh` - Verified all resources

**Result**: Infrastructure at 71% complete (5/7 steps), $29/month cost

### Files Modified/Created
- ✅ `StartupWebApp/StartupWebApp/settings_production.py` (new, 233 lines)
- ✅ `requirements.txt` (added boto3)
- ✅ `scripts/infra/create-secrets.sh` (updated with expanded secret structure)
- ✅ `scripts/infra/destroy-secrets.sh` (updated warnings and documentation)
- ✅ `scripts/infra/test-rds-connection.py` (new, 235 lines)
- ✅ `docs/SESSION_START_PROMPT.md` (clarified linting workflow)

## Deployment Workflow

### Prerequisites (Already Complete)
- ✅ VPC and networking infrastructure
- ✅ Security groups configured
- ✅ AWS Secrets Manager secret with expanded structure
- ✅ RDS PostgreSQL 16 instance (available)
- ✅ CloudWatch monitoring and alarms

### Step 1: Update Production Secrets (Manual)
```bash
# Update Stripe keys via AWS Console or CLI
aws secretsmanager update-secret --secret-id rds/startupwebapp/multi-tenant/master \
  --secret-string file://updated-secret.json

# Example updated-secret.json:
{
  "engine": "postgresql",
  "host": "startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com",
  "port": 5432,
  "username": "django_app",
  "password": "EXISTING_AUTO_GENERATED_PASSWORD",
  "django_secret_key": "EXISTING_AUTO_GENERATED_KEY",
  "stripe_secret_key": "sk_live_REAL_KEY",
  "stripe_publishable_key": "pk_live_REAL_KEY",
  "email_host": "smtp.gmail.com",
  "email_port": 587,
  "email_user": "notifications@mosaicmeshai.com",
  "email_password": "REAL_SMTP_PASSWORD"
}
```

### Step 2: Create Multi-Tenant Databases (Manual)
```bash
# Generate SQL
./scripts/infra/create-databases.sh

# Execute SQL via bastion host or SSH tunnel
psql -h startupwebapp-multi-tenant-prod.xxx.rds.amazonaws.com \
     -U postgres -d postgres -f /tmp/create-databases-*.sql
```

### Step 3: Test RDS Connection
```bash
cd StartupWebApp
export DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production
export DATABASE_NAME=startupwebapp_prod
python ../scripts/infra/test-rds-connection.py
```

### Step 4: Run Django Migrations
```bash
# Set environment variables
export DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production
export DATABASE_NAME=startupwebapp_prod
export DB_SECRET_NAME=rds/startupwebapp/multi-tenant/master
export AWS_REGION=us-east-1
export ALLOWED_HOSTS=www.mosaicmeshai.com

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py load_sample_data
```

## Configuration Reference

### Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DJANGO_SETTINGS_MODULE` | Yes | - | Must be `StartupWebApp.settings_production` |
| `DATABASE_NAME` | Yes | `startupwebapp_prod` | Multi-tenant database name |
| `DB_SECRET_NAME` | No | `rds/startupwebapp/multi-tenant/master` | AWS Secrets Manager secret name |
| `AWS_REGION` | No | `us-east-1` | AWS region for Secrets Manager |
| `ALLOWED_HOSTS` | No | `www.mosaicmeshai.com` | Comma-separated list of allowed hosts |
| `LOG_LEVEL` | No | `INFO` | Django logging level |

### AWS Secrets Manager Structure
```json
{
  "engine": "postgresql",
  "host": "startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com",
  "port": 5432,
  "username": "django_app",
  "password": "AUTO_GENERATED_32_CHARS",
  "django_secret_key": "AUTO_GENERATED_50_CHARS",
  "stripe_secret_key": "sk_live_MANUAL_UPDATE_REQUIRED",
  "stripe_publishable_key": "pk_live_MANUAL_UPDATE_REQUIRED",
  "email_host": "smtp.example.com",
  "email_port": 587,
  "email_user": "MANUAL_UPDATE_REQUIRED",
  "email_password": "MANUAL_UPDATE_REQUIRED"
}
```

## Next Steps (Phase 9+)

### Immediate Tasks
1. **Update Stripe Keys**: Add production Stripe keys to AWS Secrets Manager
2. **Update Email Credentials**: Add SMTP credentials to AWS Secrets Manager
3. **Create Databases**: Run `create-databases.sh` and execute SQL manually
4. **Run Migrations**: Deploy Django schema to AWS RDS
5. **Test Full Stack**: Verify application works against AWS RDS

### Future Enhancements
1. **S3 Integration**: Configure S3 for static/media files
2. **Container Deployment**: Set up Docker on ECS or EC2
3. **CI/CD Pipeline**: Automate testing and deployment
4. **CloudWatch Logging**: Integrate Django logs with CloudWatch
5. **Database Backups**: Configure automated RDS snapshots

## Lessons Learned

### 1. Module-Level Logging Issue
**Problem**: Initial attempt to call `logger.info()` at module level caused syntax errors.
**Solution**: Settings modules should avoid side effects during import. Replaced logger calls with comments.

### 2. Linting Workflow Clarity
**Problem**: Confusion about whether infrastructure scripts need linting.
**Solution**: Documented in `SESSION_START_PROMPT.md` that `scripts/infra/` are not mounted in Docker and don't require container-based linting.

### 3. Secret Management Pattern
**Insight**: Consolidating ALL secrets in a single AWS Secrets Manager secret:
- Simplifies configuration (one secret to manage)
- Reduces API calls during application startup
- Makes secret rotation easier (update one place)

### 4. Graceful Fallback Pattern
**Insight**: Providing environment variable fallbacks for secret retrieval:
- Makes local testing easier (no AWS credentials needed)
- Provides clear error messages when secrets fail
- Maintains production security while enabling development flexibility

### 5. Infrastructure Script Idempotency
**Issue**: `create-secrets.sh` exits if secret already exists (not idempotent).
**Impact**: Requires force-delete when secret is scheduled for deletion (30-day recovery window).
**Workaround**: Use `aws secretsmanager delete-secret --force-delete-without-recovery` before recreating.

## Cost Analysis

**Monthly Infrastructure Cost**: $29
- RDS db.t4g.small: ~$26/month
- Enhanced Monitoring: ~$2/month
- CloudWatch/SNS: ~$1/month
- NAT Gateway: $0 (not created - saved $32/month)

**Total Savings**: $32/month (52% reduction) by skipping NAT Gateway

## References

- AWS RDS Deployment Plan: `docs/technical-notes/2025-11-19-aws-rds-deployment-plan.md`
- PostgreSQL Migration: `docs/technical-notes/2025-11-18-postgresql-migration-phases-2-5-complete.md`
- Django Settings Documentation: https://docs.djangoproject.com/en/4.2/topics/settings/
- AWS Secrets Manager: https://docs.aws.amazon.com/secretsmanager/
- boto3 Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
