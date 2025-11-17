# Database Migration Planning: SQLite to PostgreSQL (Multi-Tenant Strategy)

**Date**: November 17, 2025
**Status**: 📋 PLANNING PHASE
**Priority**: HIGH - Critical blocker for AWS production deployment

## Executive Summary

This document outlines the comprehensive plan to migrate StartupWebApp from SQLite (development database) to PostgreSQL (production database) with a **multi-tenant architecture** that allows multiple forked applications to share a single RDS instance cost-effectively.

**Recommendation**: PostgreSQL 16.x on AWS RDS with separate databases per fork
**Multi-Tenant Strategy**: Separate databases on shared RDS instance (~$26/month total)
**Estimated Timeline**: 3-5 days
**Risk Level**: Low (no advanced database features currently in use)
**Testing Requirements**: All 721 tests must pass (693 unit + 28 functional)

## Multi-Tenant Architecture Strategy

### Business Use Case

You plan to fork StartupWebApp to experiment with multiple business ideas, each with minimal initial data. Rather than paying $26/month per experiment, you'll share a single RDS instance across all forks.

**Cost Efficiency Example:**
- **Without Multi-Tenant**: 5 experiments × $26/month = $130/month
- **With Multi-Tenant**: 1 instance at $26/month (or $52 for larger instance) = $26-52/month
- **Savings**: 80-90% reduction in database costs during experimentation phase

### Architecture Options Analysis

#### Option 1: Separate Databases (RECOMMENDED) ✅

**Structure:**
```
RDS Instance (db.t4g.small)
├── startupwebapp_prod      (main production app)
├── healthtech_experiment   (fork #1)
├── fintech_experiment      (fork #2)
├── edtech_experiment       (fork #3)
└── saas_experiment         (fork #4)
```

**Pros:**
- **Complete data isolation**: Each fork has its own database namespace
- **Zero collision risk**: Tables, constraints, indexes are independent
- **Easy backup/restore**: Can backup individual databases
- **Simple migration**: Just change database NAME in settings
- **Clean separation**: Delete entire database when experiment fails
- **Django-native**: No code changes required
- **Permission control**: Can grant different users access to different DBs

**Cons:**
- Resource sharing (CPU, memory, connections) across databases
- Must manage multiple database names

**Resource Limits:**
- db.t4g.small: 2 vCPU, 2 GB RAM, 100 connections
- Typical Django app uses 5-20 connections (with connection pooling)
- Can support 5-10 low-traffic applications comfortably

#### Option 2: Shared Database with Schema Prefixes

**Structure:**
```
Database: startupwebapp_multi
├── startupwebapp_user_member
├── startupwebapp_user_prospect
├── startupwebapp_order_cart
├── healthtech_user_member
├── healthtech_user_prospect
├── healthtech_order_cart
├── fintech_user_member
...
```

**Pros:**
- Single database to manage
- Shared connection pool

**Cons:**
- ❌ Requires custom Django database router
- ❌ Complex Meta.db_table modifications for every model
- ❌ Higher collision risk if naming conflicts
- ❌ Cannot easily delete one app's data
- ❌ Backup/restore is all-or-nothing
- ❌ More complex permission management

**Verdict**: Not recommended (too complex)

#### Option 3: PostgreSQL Schemas (Namespaces)

**Structure:**
```
Database: startupwebapp_multi
├── Schema: startupwebapp
│   ├── user_member
│   ├── order_cart
├── Schema: healthtech
│   ├── user_member
│   ├── order_cart
├── Schema: fintech
    ├── user_member
    ├── order_cart
```

**Pros:**
- True namespace isolation within single database
- PostgreSQL-native feature
- Can set search_path per connection

**Cons:**
- ❌ Django doesn't natively support PostgreSQL schemas well
- ❌ Requires custom database backend or third-party package
- ❌ Complex migration management
- ❌ Testing complexity increases

**Verdict**: Overly complex for this use case

### Recommended Approach: Option 1 (Separate Databases)

**Implementation:**
- Single RDS PostgreSQL instance
- One database per forked application
- Each fork configured via environment variable: `DATABASE_NAME`
- Shared credentials (or separate users for security)
- Django settings read database name from environment

**Example Configuration:**

```python
# settings_secret.py or environment variables
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'startupwebapp_prod'),
        'USER': os.environ.get('DATABASE_USER', 'django_app'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'secret'),
        'HOST': os.environ.get('DATABASE_HOST', 'your-rds-instance.us-east-1.rds.amazonaws.com'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}
```

**Per-Fork Configuration:**
- startupwebapp: `DATABASE_NAME=startupwebapp_prod`
- healthtech fork: `DATABASE_NAME=healthtech_experiment`
- fintech fork: `DATABASE_NAME=fintech_experiment`

**Scaling Strategy:**
- Start: 3-5 experiments on db.t4g.small ($26/month)
- Grow: 5-10 experiments on db.t4g.medium ($52/month)
- Mature: Graduate successful experiments to dedicated instances

## Current State Analysis

### Database Configuration

**Current Setup:**
- **Database**: SQLite 3.x
- **Location**: `/app/data/rg_unittest` (Docker volume mount)
- **Configuration**: `StartupWebApp/StartupWebApp/settings_secret.py`
- **Engine**: `django.db.backends.sqlite3`

**Usage Patterns:**
- 3 Django apps: user, order, clientevent
- 40+ database tables with explicit table names
- 40+ CASCADE foreign key relationships
- Multiple unique constraints (single and composite)
- No PostgreSQL-specific features (JSONField, ArrayField, etc.)

### Database Schema Complexity

**Models Summary:**
- **User App**: Member, Prospect, Email, Chat, TermsOfUse, etc. (14+ models)
- **Order App**: Cart, Order, Product, SKU, Discount, Shipping (25+ models)
- **ClientEvent App**: PageView, PageElement, Registration, etc. (6+ models)

**Field Types Used:**
- CharField, IntegerField, FloatField, BooleanField, DateTimeField
- ForeignKey, OneToOneField relationships
- All standard Django field types (highly portable)

**Critical Findings:**
1. ✅ No PostgreSQL-specific features (easy migration)
2. ⚠️ FloatField used for currency (should be DecimalField)
3. ⚠️ Nullable unique constraints (behavior differs between databases)
4. ✅ Explicit table names preserved (no migration issues)
5. ✅ No custom SQL in models (pure Django ORM)

## Database Selection Analysis

### Option 1: AWS RDS PostgreSQL (RECOMMENDED)

**Pros:**
- Industry standard for Django production deployments
- Full Django feature support (JSONField, full-text search, etc.)
- Excellent ACID compliance and transaction handling
- Superior query optimizer for complex joins
- Better performance with subqueries and aggregations
- Native support for advanced data types (JSON, arrays, hstore)
- Strong community support and Django developer preference
- Future-proof for advanced features

**Cons:**
- 20% higher cost than MySQL for equivalent instance size
- Slightly steeper learning curve if team only knows MySQL

**Cost (us-east-1, 2025 estimates):**
- db.t4g.micro (2 vCPU, 1 GB RAM): ~$13/month
- db.t4g.small (2 vCPU, 2 GB RAM): ~$26/month
- db.t4g.medium (2 vCPU, 4 GB RAM): ~$52/month
- Includes: 20 GB storage, automated backups, Multi-AZ optional

**Recommendation**: Start with db.t4g.small for low-traffic production

### Option 2: AWS RDS MySQL

**Pros:**
- Lower cost (20% cheaper than PostgreSQL)
- Widely known and supported
- Compatible with all current Django field types
- Good performance for standard operations

**Cons:**
- Limited support for advanced Django features
- Less robust query optimizer
- Requires careful configuration (utf8mb4, strict mode)
- Not preferred by Django community

**Cost (us-east-1):**
- ~20% cheaper than PostgreSQL equivalent instances

### Option 3: AWS Aurora PostgreSQL

**Pros:**
- 3x throughput compared to standard PostgreSQL
- Auto-scaling storage (10 GB to 128 TB)
- Up to 15 read replicas for horizontal scaling
- Superior high-availability and failover
- I/O-optimized pricing can save 40% at high volume

**Cons:**
- 20% more expensive than RDS PostgreSQL
- Overkill for current traffic levels
- More complex configuration

**Cost (us-east-1):**
- db.t4g.medium: ~$62/month (vs $52 for RDS)
- Better value at high transaction volumes (10M+ I/O per month)

**Recommendation**: Consider Aurora after 6-12 months if traffic scales significantly

### Option 4: AWS Aurora Serverless v2

**Pros:**
- Auto-scales capacity based on load (0.5 to 128 ACUs)
- Pay only for capacity used
- Perfect for variable workloads
- Near-instant scaling

**Cons:**
- Complex pricing model (ACU-based)
- Minimum charge even when idle
- May be more expensive for steady workloads

**Recommendation**: Consider for staging/development environments

## Final Recommendation: AWS RDS PostgreSQL 16.x

**Rationale:**
1. **Django Community Standard**: PostgreSQL is the de facto production database for Django
2. **Future-Proof**: Supports advanced features if needed later (JSON, full-text search, arrays)
3. **Cost-Effective**: Reasonable pricing for startup budget (~$26/month for db.t4g.small)
4. **Performance**: Superior query optimization and transaction handling
5. **Reliability**: Proven track record with Django applications
6. **Migration Path**: Clear upgrade path to Aurora if scaling needs increase

## Implementation Plan

### Phase 1: Pre-Migration Improvements (Optional but Recommended)

**Priority: HIGH - Fix before migration to avoid double work**

1. **Replace FloatField with DecimalField for Currency**
   - Files affected: order/models.py (Price, DiscountAmount, SalesTaxAmt, etc.)
   - Pattern: `FloatField()` → `DecimalField(max_digits=10, decimal_places=2)`
   - Reason: Prevents rounding errors in financial calculations
   - Impact: Requires Django migration, may affect existing data
   - Estimated time: 4-6 hours (TDD, tests, validation)

2. **Document Nullable Unique Constraint Behavior**
   - SQLite allows only one NULL in unique fields
   - PostgreSQL/MySQL allow multiple NULLs in unique fields
   - Review: email_unsubscribe_string, mb_cd, pr_cd, stripe_customer_token
   - Action: Verify business logic handles multiple NULLs or add constraints
   - Estimated time: 2-3 hours (analysis + tests)

**Decision Required**: Should we fix FloatField→DecimalField before or after migration?
- **Option A (Recommended)**: Fix before migration (cleaner, safer)
- **Option B**: Migrate first, fix later (faster to production)

### Phase 2: Local Development Environment Setup (Multi-Tenant Ready)

**Objective**: Configure PostgreSQL in Docker for local development with multi-database support

**Steps:**

1. **Update docker-compose.yml**
   - Add PostgreSQL service container (postgres:16-alpine)
   - Configure persistent volume for database data
   - Set up environment variables for credentials
   - Connect to "startupwebapp" network
   - Expose port 5432 for local access

   ```yaml
   db:
     image: postgres:16-alpine
     container_name: startupwebapp-db-dev
     environment:
       POSTGRES_USER: django_app
       POSTGRES_PASSWORD: dev_password_change_in_prod
       POSTGRES_MULTIPLE_DATABASES: startupwebapp_dev,healthtech_dev,fintech_dev
     volumes:
       - postgres_data:/var/lib/postgresql/data
       - ./init-multi-db.sh:/docker-entrypoint-initdb.d/init-multi-db.sh
     ports:
       - "5432:5432"
     networks:
       - startupwebapp
   ```

2. **Create multi-database initialization script**
   - `init-multi-db.sh`: Creates multiple databases from POSTGRES_MULTIPLE_DATABASES
   - Sets up proper permissions and encoding (UTF8) for each database
   - Enables required PostgreSQL extensions (if needed)
   - Creates shared user with access to all databases

   ```bash
   #!/bin/bash
   set -e

   # Parse comma-separated database names
   IFS=',' read -ra DATABASES <<< "$POSTGRES_MULTIPLE_DATABASES"

   for db in "${DATABASES[@]}"; do
       echo "Creating database: $db"
       psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
           CREATE DATABASE $db;
           GRANT ALL PRIVILEGES ON DATABASE $db TO $POSTGRES_USER;
       EOSQL
   done
   ```

3. **Install PostgreSQL client (psycopg2) dependency**
   - Update requirements.txt: `psycopg2-binary==2.9.9`
   - Rebuild Docker image with new dependency

4. **Test Docker Compose startup with multiple databases**
   - Verify backend and database containers start successfully
   - Test connection from backend to each database
   - Verify volume persistence across restarts
   - Test database switching via DATABASE_NAME environment variable

**Multi-Tenant Testing:**
```bash
# Test connection to different databases
docker-compose exec db psql -U django_app -d startupwebapp_dev -c "\dt"
docker-compose exec db psql -U django_app -d healthtech_dev -c "\dt"
docker-compose exec db psql -U django_app -d fintech_dev -c "\dt"
```

**Estimated Time**: 4-5 hours (includes multi-database setup and testing)

### Phase 3: Django Configuration (Environment-Based Multi-Tenant)

**Objective**: Update Django settings to support PostgreSQL with environment-based database selection

**Steps:**

1. **Update settings_secret.py.template for multi-tenant**
   - Add PostgreSQL configuration with environment variables
   - Document DATABASE_NAME for fork selection
   - Provide examples for local, staging, production
   - Add comments explaining multi-tenant approach

   ```python
   # Multi-Tenant PostgreSQL Configuration
   # Each forked application uses a different DATABASE_NAME
   # All forks share the same RDS instance (cost savings)

   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.environ.get('DATABASE_NAME', 'startupwebapp_dev'),
           'USER': os.environ.get('DATABASE_USER', 'django_app'),
           'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'dev_password'),
           'HOST': os.environ.get('DATABASE_HOST', 'db'),  # 'db' for Docker, RDS endpoint for AWS
           'PORT': os.environ.get('DATABASE_PORT', '5432'),
           'CONN_MAX_AGE': 600,  # Connection pooling (10 minutes)
       }
   }

   # Example environment configurations:
   # StartupWebApp (main):     DATABASE_NAME=startupwebapp_prod
   # HealthTech fork:          DATABASE_NAME=healthtech_experiment
   # FinTech fork:             DATABASE_NAME=fintech_experiment
   # EdTech fork:              DATABASE_NAME=edtech_experiment
   ```

2. **Create settings_secret.py for local PostgreSQL**
   - Copy template and configure for local Docker PostgreSQL
   - Set HOST to 'db' (Docker service name)
   - Set DATABASE_NAME to 'startupwebapp_dev'
   - Configure proper credentials

3. **Update docker-compose.yml backend service with environment variable**
   ```yaml
   backend:
     environment:
       - DATABASE_NAME=startupwebapp_dev  # Default for main app
       - DATABASE_USER=django_app
       - DATABASE_PASSWORD=dev_password_change_in_prod
       - DATABASE_HOST=db
       - DATABASE_PORT=5432
   ```

4. **Add database connection validation**
   - Test script to verify database connectivity: `test_db_connection.py`
   - Include in docker-entrypoint.sh startup checks
   - Log connection status and database name for debugging
   - Verify correct database is being used

5. **Create helper script for fork development**
   - `switch-database.sh`: Easily switch between databases locally
   - Updates .env file or docker-compose.override.yml
   - Useful for testing multiple forks locally

4. **Update documentation**
   - README.md: New setup instructions for PostgreSQL
   - Document environment variable requirements
   - Add troubleshooting section for common issues

**Estimated Time**: 2-3 hours

### Phase 4: Database Migration & Data Transfer

**Objective**: Migrate schema to PostgreSQL and verify data integrity

**Steps:**

1. **Backup SQLite database**
   - Export current SQLite data: `python manage.py dumpdata > backup.json`
   - Store backup with timestamp
   - Verify JSON validity

2. **Create fresh PostgreSQL schema**
   - Run: `python manage.py migrate`
   - Verify all 40+ tables created correctly
   - Check indexes and constraints created

3. **Import data from backup (if needed)**
   - Load data: `python manage.py loaddata backup.json`
   - Verify foreign key relationships
   - Check sequence counters updated

4. **Alternative: Start with fresh database**
   - Run: `python manage.py load_sample_data` (if sample data command exists)
   - Create test users and orders manually
   - Advantage: Clean slate, no data migration issues

**Estimated Time**: 2-3 hours

### Phase 5: Testing & Validation

**Objective**: Verify all functionality works correctly with PostgreSQL

**Critical Tests:**

1. **Unit Tests (693 tests)**
   ```bash
   docker-compose exec backend python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests
   ```
   - Expected result: 693 tests passing
   - Watch for: Database-specific errors, constraint violations

2. **Functional Tests (28 tests)**
   ```bash
   docker-compose exec backend bash /app/setup_docker_test_hosts.sh
   docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests
   ```
   - Expected result: 28 tests passing
   - Watch for: CSRF token issues, session handling, cookie management

3. **Code Quality (Linting)**
   ```bash
   docker-compose exec backend flake8 user order clientevent StartupWebApp --max-line-length=120 --statistics
   ```
   - Expected result: 0 errors (maintain current standards)

**Validation Checklist:**
- ✅ All 721 tests passing (100% pass rate)
- ✅ Manual browser testing: Create account, login, add to cart, checkout
- ✅ Admin panel: Verify data access and operations
- ✅ Stripe integration: Test payment processing
- ✅ Email functionality: Verify email sending/receiving
- ✅ CSRF tokens: Verify all AJAX POST requests work
- ✅ Session management: Test login persistence across requests
- ✅ Performance: Compare query times vs SQLite (should be similar or better)

**Estimated Time**: 4-6 hours (includes multiple test runs and fixes)

### Phase 6: Production AWS RDS Setup (Multi-Tenant)

**Objective**: Configure AWS RDS PostgreSQL for production deployment with multi-tenant support

**Instance Sizing for Multi-Tenant:**
- **3-5 low-traffic forks**: db.t4g.small (2 vCPU, 2 GB RAM) @ $26/month
- **5-10 low-traffic forks**: db.t4g.medium (2 vCPU, 4 GB RAM) @ $52/month
- **10+ forks or high traffic**: db.t4g.large or scale vertically as needed

**Steps:**

1. **Create RDS PostgreSQL instance via AWS Console**
   - Engine: PostgreSQL 16.x (latest stable)
   - Instance class: db.t4g.small (start here, scale up as needed)
   - Storage: 20 GB SSD with auto-scaling enabled (up to 100 GB)
   - Multi-AZ: No initially (can enable later for HA when traffic grows)
   - Backup retention: 7 days (automated daily backups)
   - Maintenance window: Choose low-traffic period (e.g., Sunday 3-4 AM)
   - Initial database name: `postgres` (default, we'll create app databases separately)

2. **Configure Security Groups**
   - Create security group: `rds-startupwebapp-multi-tenant-sg`
   - Allow inbound PostgreSQL (port 5432) from backend ECS/EC2 security group only
   - Deny all public internet access (important for security)
   - Document security group IDs for future reference
   - Tag appropriately: `Environment: Production`, `Purpose: Multi-Tenant-DB`

3. **Create multiple databases for each fork**
   - Connect to RDS from bastion host, Cloud9, or local with SSH tunnel
   - Create databases for main app and initial forks:

   ```sql
   -- Connect to default postgres database first
   psql -h your-rds-endpoint.us-east-1.rds.amazonaws.com -U django_app -d postgres

   -- Create databases for each application
   CREATE DATABASE startupwebapp_prod;
   CREATE DATABASE healthtech_experiment;
   CREATE DATABASE fintech_experiment;
   -- Add more as needed for new forks

   -- Verify databases created
   \l
   ```

4. **Set up database credentials management (Multi-Tenant Aware)**
   - **Recommended: AWS Secrets Manager** (better rotation, auditing)
   - Store shared credentials (all forks use same user):
     - Secret name: `rds/startupwebapp-multi-tenant/master`
     - Keys: `host`, `port`, `username`, `password`
   - Each fork reads DATABASE_NAME from its own environment config
   - Alternative: Per-fork secrets if you want separate users/permissions

   ```json
   {
     "host": "your-rds-instance.us-east-1.rds.amazonaws.com",
     "port": "5432",
     "username": "django_app",
     "password": "strong_random_password_here"
   }
   ```

5. **Create production settings_secret.py (multi-tenant pattern)**
   - Configure to read from AWS Secrets Manager/Parameter Store
   - DATABASE_NAME comes from environment variable (fork-specific)
   - Shared credentials from Secrets Manager
   - Set DEBUG=False for all production deployments
   - Configure ALLOWED_HOSTS per fork (fork-specific domains)

   ```python
   import boto3
   import json

   # Read shared database credentials from AWS Secrets Manager
   def get_secret(secret_name):
       client = boto3.client('secretsmanager', region_name='us-east-1')
       response = client.get_secret_value(SecretId=secret_name)
       return json.loads(response['SecretString'])

   db_creds = get_secret('rds/startupwebapp-multi-tenant/master')

   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.environ.get('DATABASE_NAME'),  # Fork-specific, set in ECS task or EC2
           'USER': db_creds['username'],
           'PASSWORD': db_creds['password'],
           'HOST': db_creds['host'],
           'PORT': db_creds['port'],
           'CONN_MAX_AGE': 600,  # Connection pooling (critical for multi-tenant)
       }
   }

   # Fork-specific settings
   DEBUG = False
   ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
   ```

6. **Initialize each database (per fork)**
   - For StartupWebApp (main):
     ```bash
     export DATABASE_NAME=startupwebapp_prod
     python manage.py migrate
     python manage.py createsuperuser
     ```

   - For HealthTech fork:
     ```bash
     export DATABASE_NAME=healthtech_experiment
     python manage.py migrate
     python manage.py createsuperuser --username admin_healthtech
     ```

   - Repeat for each fork as they're deployed

7. **Configure connection pooling (CRITICAL for multi-tenant)**
   - With multiple apps sharing one instance, connection management is critical
   - **Option A**: Django CONN_MAX_AGE (already configured above, 600 seconds)
   - **Option B**: PgBouncer (if >5 apps or high connection count)
     - Deploy PgBouncer as sidecar container or separate service
     - Configure transaction pooling mode
     - Reduces connection overhead significantly

8. **Set up monitoring and alerting for multi-tenant**
   - CloudWatch metrics to monitor:
     - `DatabaseConnections`: Watch for connection limit (100 on db.t4g.small)
     - `CPUUtilization`: Alert if >70% sustained
     - `FreeableMemory`: Alert if <500 MB
     - `ReadLatency` / `WriteLatency`: Baseline and alert on spikes
   - Create alarms for each metric
   - Set up SNS topic for notifications
   - Monitor per-database activity with pg_stat_database

9. **Document database naming convention**
   - Create `DATABASE_REGISTRY.md` to track all databases:

   ```markdown
   # Multi-Tenant Database Registry

   RDS Instance: your-rds-instance.us-east-1.rds.amazonaws.com
   Instance Type: db.t4g.small

   | Database Name           | Application    | Status  | Owner | Deployed |
   |------------------------|----------------|---------|-------|----------|
   | startupwebapp_prod     | StartupWebApp  | Active  | Bart  | 2025-11-20 |
   | healthtech_experiment  | HealthTech     | Active  | Bart  | 2025-12-01 |
   | fintech_experiment     | FinTech        | Testing | Bart  | 2025-12-15 |
   ```

**Multi-Tenant Management Commands:**

```bash
# List all databases on RDS instance
psql -h <rds-endpoint> -U django_app -d postgres -c "\l"

# Check connection count per database
psql -h <rds-endpoint> -U django_app -d postgres -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Create new database for new fork
psql -h <rds-endpoint> -U django_app -d postgres -c "CREATE DATABASE newexperiment_test;"

# Drop database for failed experiment (careful!)
psql -h <rds-endpoint> -U django_app -d postgres -c "DROP DATABASE failed_experiment;"

# Backup specific database
pg_dump -h <rds-endpoint> -U django_app -d healthtech_experiment > healthtech_backup.sql

# Restore specific database
psql -h <rds-endpoint> -U django_app -d healthtech_experiment < healthtech_backup.sql
```

**Estimated Time**: 4-5 hours (includes multi-database setup and documentation)

### Phase 7: Documentation & Rollback Planning

**Objective**: Document migration process and create rollback procedures

**Documentation Required:**

1. **Migration Runbook** (this document + detailed steps)
   - Pre-migration checklist
   - Step-by-step migration commands
   - Validation procedures
   - Expected results at each step

2. **Rollback Procedure**
   - Steps to revert to SQLite if needed
   - Data backup/restore procedures
   - Configuration file changes to undo
   - Timeline for safe rollback (before data divergence)

3. **Troubleshooting Guide**
   - Common connection errors and solutions
   - Performance troubleshooting
   - Query debugging techniques
   - AWS RDS monitoring setup

4. **Update Existing Documentation**
   - README.md: PostgreSQL setup instructions
   - SESSION_START_PROMPT.md: Update database info
   - PROJECT_HISTORY.md: Document migration completion
   - Docker Compose comments: Document database service

**Estimated Time**: 2-3 hours

## Risk Assessment & Mitigation

### Low Risk Items ✅

1. **Schema Compatibility**: No PostgreSQL-specific features currently used
2. **Django ORM**: Pure Django ORM with no raw SQL in models
3. **Table Names**: Explicit table names preserved (no naming conflicts)
4. **Foreign Keys**: Standard CASCADE relationships (compatible)

### Medium Risk Items ⚠️

1. **FloatField Precision**
   - **Risk**: Rounding errors in financial calculations
   - **Mitigation**: Replace with DecimalField (Phase 1)
   - **Impact**: Requires Django migration, affects pricing calculations

2. **Nullable Unique Constraints**
   - **Risk**: PostgreSQL allows multiple NULLs (SQLite allows one)
   - **Mitigation**: Review business logic, add tests
   - **Impact**: May affect data validation logic

3. **Test Suite Compatibility**
   - **Risk**: Tests may have SQLite-specific assumptions
   - **Mitigation**: Run full test suite multiple times, fix failures
   - **Impact**: May require test updates

4. **Performance Changes**
   - **Risk**: Query performance may differ (better or worse)
   - **Mitigation**: Monitor slow queries, add indexes if needed
   - **Impact**: May require query optimization

### High Risk Items 🚨

**None Identified** - This is a relatively low-risk migration due to:
- No advanced database features in use
- Pure Django ORM (no raw SQL)
- All 721 tests provide comprehensive coverage
- Can test locally before AWS deployment

### Mitigation Strategy

1. **Backup Everything**: SQLite database, code, configuration
2. **Test Locally First**: Validate PostgreSQL works in Docker before AWS
3. **Run All Tests**: 721 tests must pass before considering migration successful
4. **Manual Testing**: Full user journey testing in local environment
5. **Staged Rollout**: Local → Staging → Production (if staging env exists)
6. **Rollback Plan**: Document exact steps to revert if critical issues found

## Timeline & Effort Estimate

### Conservative Estimate (Recommended)

| Phase | Description | Estimated Time | Dependencies |
|-------|-------------|----------------|--------------|
| Phase 1 | Pre-migration improvements (FloatField→DecimalField) | 4-6 hours | None |
| Phase 2 | Local Docker PostgreSQL setup | 3-4 hours | Phase 1 complete |
| Phase 3 | Django configuration | 2-3 hours | Phase 2 complete |
| Phase 4 | Database migration & data transfer | 2-3 hours | Phase 3 complete |
| Phase 5 | Testing & validation (multiple runs) | 4-6 hours | Phase 4 complete |
| Phase 6 | Production AWS RDS setup | 3-4 hours | Phase 5 complete |
| Phase 7 | Documentation & rollback planning | 2-3 hours | Ongoing |

**Total Estimated Time**: 20-29 hours (3-5 business days)

**Timeline Factors:**
- Assumes no major issues discovered during testing
- Includes time for multiple test runs and bug fixes
- Includes documentation and code review
- Assumes familiarity with Docker, Django, PostgreSQL, AWS

### Aggressive Estimate (Higher Risk)

Skip Phase 1 (FloatField fix), minimal testing: 10-15 hours (2-3 days)

**Not Recommended**: Increases risk of production issues

## Success Criteria

### Must Have (Blocking) ✅

1. All 721 tests passing (693 unit + 28 functional)
2. Zero linting errors maintained (flake8 + ESLint)
3. Manual browser testing completed successfully
4. Stripe payment processing works end-to-end
5. Data integrity verified (if migrating existing data)
6. Performance acceptable (similar or better than SQLite)
7. Rollback procedure documented and validated

### Should Have (Important) ⚙️

1. FloatField→DecimalField conversion completed
2. Nullable unique constraint behavior documented
3. Connection pooling configured
4. AWS RDS monitoring/alerting set up
5. Automated backup verification
6. Performance baseline established

### Nice to Have (Future Improvements) 💡

1. Query performance optimization
2. Read replica for reporting/analytics
3. Aurora PostgreSQL evaluation
4. Database connection pooling with pgBouncer
5. Advanced PostgreSQL features (full-text search, JSON queries)

## Next Steps

### Immediate Actions (Session Continuation)

1. **Decision Required**: Approve overall migration plan
2. **Decision Required**: FloatField→DecimalField before or after migration?
3. **Action**: Create feature branch `feature/postgresql-migration`
4. **Action**: Begin Phase 1 (Pre-migration improvements) or Phase 2 (Docker setup)

### Recommended Sequence

**Option A: Safer Approach (Recommended)**
1. Fix FloatField→DecimalField first (Phase 1)
2. Set up local PostgreSQL (Phase 2-4)
3. Validate with all tests (Phase 5)
4. Deploy to AWS RDS (Phase 6)
5. Document & monitor (Phase 7)

**Option B: Faster to Production**
1. Set up local PostgreSQL (Phase 2-4)
2. Validate with all tests (Phase 5)
3. Deploy to AWS RDS (Phase 6)
4. Fix FloatField→DecimalField later (Phase 1 deferred)
5. Document & monitor (Phase 7)

### Questions for Discussion

1. Should we fix FloatField→DecimalField before or after migration?
2. Do we need to migrate existing SQLite data or start fresh?
3. Should we create a staging environment first?
4. What's the target timeline for production deployment?
5. What's the budget for AWS RDS? (db.t4g.small ~$26/month shared across forks)
6. How many experimental forks do you anticipate running initially? (affects sizing)
7. Do you want separate database users per fork for better security/isolation?

## Multi-Tenant Best Practices & Considerations

### Resource Management

**Connection Limits:**
- db.t4g.small: 100 max connections
- Reserve ~10 connections for admin/monitoring
- Budget ~10-20 connections per active application
- **Capacity**: 3-5 active applications safely, 5-10 with connection pooling

**When to Scale Up:**
- Monitor `DatabaseConnections` metric in CloudWatch
- Scale from db.t4g.small → db.t4g.medium when:
  - Sustained >70 connections
  - More than 5 active forks
  - High traffic periods causing connection exhaustion
- Scale from db.t4g.medium → db.t4g.large when:
  - Sustained >150 connections
  - More than 10 active forks
  - CPU utilization consistently >70%

**Storage Considerations:**
- Start: 20 GB with auto-scaling
- Typical Django app with low traffic: 500 MB - 2 GB
- 5 forks: ~5-10 GB total (plenty of headroom)
- Auto-scaling triggers at 90% capacity
- Monitor storage growth per database

### Security Isolation

**Shared User Approach (Simpler):**
- ✅ All forks use same database user (`django_app`)
- ✅ Isolation via separate databases (can't query across databases easily)
- ✅ Simpler credential management
- ⚠️ If one fork is compromised, attacker can access other databases

**Separate User Approach (More Secure):**
- ✅ Each fork has its own database user
- ✅ Strong isolation - compromise doesn't spread
- ✅ Fine-grained permission control
- ⚠️ More complex credential management
- ⚠️ More AWS Secrets Manager secrets to manage

**Recommendation**: Start with shared user, migrate to separate users if/when forks reach production with real user data.

### Cost Optimization Strategies

**Current Plan:**
- db.t4g.small: $26/month for 3-5 forks
- **Savings**: 80-90% vs separate instances

**Further Optimization:**
1. **Reserved Instances**: Commit 1-3 years for 30-60% discount
   - db.t4g.small 1-year reserved: ~$18/month (save $8/month)
   - db.t4g.small 3-year reserved: ~$12/month (save $14/month)
   - Best when you know you'll run experiments long-term

2. **Storage Optimization**:
   - Delete databases for failed experiments promptly
   - Compress old backups
   - Use snapshot instead of backup for long-term storage

3. **Instance Right-Sizing**:
   - Start small (db.t4g.small)
   - Monitor actual usage for 1 month
   - Scale up only if needed (most experiments won't need it)

4. **Development/Staging Savings**:
   - Use same local Docker PostgreSQL for all fork development
   - Only deploy to AWS RDS when ready for production testing
   - Stop RDS instance during periods of inactivity (manual or automated)

### Fork Lifecycle Management

**Fork Stages:**

1. **Local Development** (Cost: $0)
   - Fork repo, make initial changes
   - Test locally with Docker PostgreSQL
   - All development happens locally

2. **AWS Testing** (Cost: Shared $26/month)
   - Create database on shared RDS: `CREATE DATABASE newexperiment_test;`
   - Deploy to AWS for real-world testing
   - Minimal traffic, shared resources

3. **Production (Validated)** (Cost: Shared $26/month)
   - Experiment shows promise
   - Rename database: `ALTER DATABASE newexperiment_test RENAME TO newexperiment_prod;`
   - Increase monitoring and alerting

4. **Graduation** (Cost: New dedicated instance)
   - Experiment succeeds, needs dedicated resources
   - Migrate to new RDS instance: `pg_dump` + `pg_restore`
   - Scale independently

5. **Retirement** (Cost: $0)
   - Experiment failed or completed
   - Backup database: `pg_dump > experiment_archive.sql`
   - Drop database: `DROP DATABASE failed_experiment;`
   - Archive backup to S3 for future reference

**Database Lifecycle Commands:**

```bash
# Create database for new fork
psql -h <rds> -U django_app -d postgres -c "CREATE DATABASE experiment_staging;"

# Rename database (production ready)
psql -h <rds> -U django_app -d postgres -c "ALTER DATABASE experiment_staging RENAME TO experiment_prod;"

# Archive and delete failed experiment
pg_dump -h <rds> -U django_app -d failed_experiment | gzip > failed_experiment_$(date +%Y%m%d).sql.gz
aws s3 cp failed_experiment_20251201.sql.gz s3://your-bucket/database-archives/
psql -h <rds> -U django_app -d postgres -c "DROP DATABASE failed_experiment;"
```

### Monitoring Multi-Tenant Performance

**Key Metrics Per Database:**

```sql
-- Connection count per database
SELECT datname, count(*) as connections
FROM pg_stat_activity
WHERE datname IS NOT NULL
GROUP BY datname
ORDER BY connections DESC;

-- Database size
SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datname NOT IN ('postgres', 'template0', 'template1')
ORDER BY pg_database_size(datname) DESC;

-- Active queries per database
SELECT datname, count(*) as active_queries
FROM pg_stat_activity
WHERE state = 'active' AND datname IS NOT NULL
GROUP BY datname;

-- Table count per database
SELECT schemaname, count(*) as table_count
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
GROUP BY schemaname;
```

**CloudWatch Dashboard Setup:**
- Create custom dashboard: "StartupWebApp Multi-Tenant RDS"
- Add widgets for:
  - Total connections (line graph)
  - CPU utilization (line graph)
  - Free memory (line graph)
  - Storage used (line graph)
  - Read/write latency (line graph)
- Set up alarms for critical thresholds

### Future Scaling Paths

**When to Graduate Fork to Dedicated Instance:**
- Traffic exceeds 1000 requests/day consistently
- Database size exceeds 5 GB
- Requires specialized configuration (extensions, parameters)
- Business-critical application requiring HA (Multi-AZ)
- Fork generates revenue justifying dedicated cost

**When to Migrate to Aurora:**
- Combined traffic across all forks exceeds 10,000 requests/day
- Need read replicas for reporting/analytics
- Require better high availability and failover
- Connection pooling becomes complex
- Storage exceeds 50 GB across all databases

**When to Consider Database Sharding:**
- Don't. Each fork is already isolated.
- This architecture IS horizontal scaling (separate databases)
- Add more forks without code changes

## References

### Django Documentation
- [Database Configuration](https://docs.djangoproject.com/en/4.2/ref/settings/#databases)
- [PostgreSQL Notes](https://docs.djangoproject.com/en/4.2/ref/databases/#postgresql-notes)
- [Django Migrations](https://docs.djangoproject.com/en/4.2/topics/migrations/)

### AWS Documentation
- [AWS RDS PostgreSQL](https://aws.amazon.com/rds/postgresql/)
- [RDS Pricing](https://aws.amazon.com/rds/pricing/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)

### Related Project Documentation
- `docs/SESSION_START_PROMPT.md` - Development workflow
- `docs/PROJECT_HISTORY.md` - Project timeline and status
- `docker-compose.yml` - Current infrastructure configuration
- `requirements.txt` - Python dependencies

### External Resources
- [PostgreSQL vs MySQL for Django (2025)](https://www.bytebase.com/blog/aurora-vs-rds/)
- [AWS Aurora vs RDS Comparison](https://aws.amazon.com/blogs/database/is-amazon-rds-for-postgresql-or-amazon-aurora-postgresql-a-better-choice-for-me/)
- [Django Best Practices](https://docs.djangoproject.com/en/4.2/topics/db/)

---

## Summary: Multi-Tenant Strategy Benefits

**Cost Savings:**
- Traditional: 5 experiments × $26/month = **$130/month**
- Multi-Tenant: 1 instance = **$26/month**
- **Savings: $104/month (80% reduction)**

**Technical Benefits:**
- ✅ Complete data isolation per fork (separate databases)
- ✅ Zero code changes required (environment variable configuration)
- ✅ Easy to add/remove experiments (CREATE/DROP database)
- ✅ Individual database backups (granular recovery)
- ✅ Simple credential management (shared or separate users)
- ✅ Django-native approach (no custom routers or middleware)

**Operational Benefits:**
- ✅ Single RDS instance to monitor and maintain
- ✅ Unified backup/restore procedures
- ✅ Simplified security group management
- ✅ Easy fork lifecycle (development → testing → production → graduation/retirement)
- ✅ Clear scaling path (vertical scaling → Aurora → dedicated instances)

**Risk Mitigation:**
- ⚠️ Resource contention (mitigated by connection pooling and monitoring)
- ⚠️ Security isolation (mitigated by separate databases, optional separate users)
- ⚠️ Connection limits (mitigated by CONN_MAX_AGE, scale up if needed)
- ✅ All risks are manageable with proper monitoring and scaling

**Bottom Line:**
This multi-tenant approach is ideal for experimentation phase. You can validate 3-5 business ideas simultaneously for the cost of one database instance. Successful experiments can graduate to dedicated resources when they prove viable.

---

**Document Version**: 2.0 (Multi-Tenant Strategy)
**Last Updated**: November 17, 2025
**Author**: Claude Code (AI Assistant)
**Review Status**: Awaiting human approval
