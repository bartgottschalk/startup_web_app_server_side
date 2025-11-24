# Project History & Development Timeline

> **For installation, setup, and getting started**, see the [main README](../README.md)

This document tracks the complete development history and modernization effort for the StartupWebApp project. For detailed information about specific phases, see the individual milestone documents linked below.

## Project Timeline

### Phase 1: Establish Baseline & User App Testing (Completed)
- [✅ 2025-10-31: Baseline Established](milestones/2025-10-31-baseline-established.md) - Python 3.12 compatibility, Docker containerization
- [✅ 2025-10-31: Phase 1.1 - Validator Tests](milestones/2025-10-31-phase-1-1-validators.md) - 99% validator coverage, email validation bug fix
- [✅ 2025-11-02: Phase 1.2 - Authentication Tests](milestones/2025-11-02-phase-1-2-authentication-tests.md) - Login, logout, forgot username
- [✅ 2025-11-02: Phase 1.3 - Password Management Tests](milestones/2025-11-02-phase-1-3-password-management-tests.md) - Change password, reset password flows
- [✅ 2025-11-02: Phase 1.4 - Email Verification Tests](milestones/2025-11-02-phase-1-4-email-verification-tests.md) - Email verification endpoints
- [✅ 2025-11-02: Phase 1.5 - Account Management Tests](milestones/2025-11-02-phase-1-5-account-management-tests.md) - Account info, communication preferences
- [✅ 2025-11-02: Phase 1.6 - Email Unsubscribe Tests](milestones/2025-11-02-phase-1-6-email-unsubscribe-tests.md) - Unsubscribe flows
- [✅ 2025-11-02: Phase 1.7 - Terms of Use Tests](milestones/2025-11-02-phase-1-7-terms-of-use-tests.md) - Terms agreement endpoints
- [✅ 2025-11-03: Phase 1.8 - Chat Lead Capture Tests](milestones/2025-11-03-phase-1-8-chat-lead-capture-tests.md) - PythonABot messaging
- [✅ 2025-11-03: Phase 1.9 - Logged In Tests](milestones/2025-11-03-phase-1-9-logged-in-tests.md) - Session state endpoints
- [✅ 2025-11-03: Phase 1.10 - Model & Migration Tests](milestones/2025-11-03-phase-1-10-model-migration-tests.md) - User models, constraints, migrations

### Phase 2: ClientEvent & Order App Testing (Completed)
- [✅ 2025-11-03: Phase 2.1 - ClientEvent Tests](milestones/2025-11-03-phase-2-1-clientevent-tests.md) - Analytics event tracking (51 tests)
- [✅ 2025-11-03: Phase 2.2 - Order Tests](milestones/2025-11-03-phase-2-2-order-tests.md) - E-commerce functionality (239 tests)

### Current Status: 740 Tests Passing ✅ (100% Pass Rate with PostgreSQL!)
- **User App**: 296 tests
- **Order App**: 315 tests (+19 DecimalField precision tests)
- **ClientEvent App**: 51 tests
- **Validators**: 50 tests
- **Total Unit Tests**: 712 tests
- **Functional Tests**: 28 Selenium tests (full user journey testing) - 100% reliable
- **Database**: PostgreSQL 16 (multi-tenant architecture, local + AWS RDS ready)
- **AWS Infrastructure**: Deployed (VPC, RDS, Secrets Manager, CloudWatch) - $29/month
- **Production Settings**: Django configured for AWS deployment with Secrets Manager integration
- **Code Quality**: Zero linting errors (backend + frontend), zero ESLint warnings

### Phase 3: Functional Test Infrastructure & Additional Coverage (Completed - 2025-11-07)
- ✅ Fixed boto3 import error in functional test utilities
- ✅ Added Firefox ESR and geckodriver to Docker container
- ✅ Fixed Selenium/urllib3 compatibility (pinned urllib3<2.0.0)
- ✅ Removed obsolete Docker Compose version field
- ✅ All 28 functional tests passing (100%)
- ✅ Added 53 additional unit tests (679 total, up from 626)
- ✅ Fixed critical bug: user/views.py checkout_allowed NameError
- ✅ Improved coverage: order/views.py (88%→99%), order_utils.py (84%→96%), user/views.py (82%→89%)

### Phase 4: Django Upgrade to 4.2 LTS (Completed - 2025-11-06)
- ✅ Successfully upgraded Django 2.2.28 → 4.2.16 LTS (incremental 6-step process)
- ✅ All 679 unit tests passing (100% pass rate maintained)
- ✅ All 28 functional tests passing (100% pass rate maintained)
- ✅ Zero test regressions during upgrade
- ✅ Minimal code changes (1 backward-compatible CSRF_TRUSTED_ORIGINS fix)
- ✅ Resolved Python deprecation warnings (cgi, locale, datetime.utcnow)
- ✅ Security support extended until April 2026
- ✅ Django 5.0 upgrade path established

### Phase 4.5: Stripe Error Handling Refactor (Completed - 2025-11-08)
- ✅ Fixed critical bug: unhandled Stripe API errors could crash endpoints with 500 errors
- ✅ Applied Test-Driven Development (TDD) methodology
- ✅ Added 10 new unit tests covering Stripe error scenarios
- ✅ Refactored to centralize error handling in utility functions (maintainable design)
- ✅ Created new `retrieve_stripe_customer()` wrapper with error handling
- ✅ Updated 4 existing utility functions with error handling
- ✅ All 689 unit tests + 28 functional tests passing (717 total)
- ✅ Documented TDD as standard practice in SESSION_START_PROMPT.md
- ✅ See [Technical Note](technical-notes/2025-11-08-stripe-error-handling-refactor.md) for details

### Phase 5: Production Deployment Preparation (In Progress)

#### Phase 5.1: Code Linting Analysis (Completed - 2025-11-09)
- ✅ Installed and configured linting tools (pylint, flake8, ESLint)
- ✅ Installed Node.js 25.1.0 on Mac host for JavaScript linting
- ✅ Analyzed 9,313 code quality issues across backend and frontend
- ✅ Identified 1 critical bug (SMTPDataError undefined in user/admin.py)
- ✅ Created comprehensive findings report with prioritized recommendations
- ✅ Added linting to development workflow in SESSION_START_PROMPT.md
- ✅ All 717 tests still passing (no regressions from analysis)
- ✅ See [Technical Note](technical-notes/2025-11-09-code-linting-analysis.md) for details

#### Phase 5.1.1: Critical Bug Fix - SMTPDataError Import (Completed - 2025-11-09)
- ✅ Fixed critical bug found during linting: SMTPDataError undefined in user/admin.py
- ✅ Applied TDD methodology: wrote 4 tests first, verified failure, then fixed
- ✅ Added missing import: `from smtplib import SMTPDataError`
- ✅ Created comprehensive test coverage for admin email actions
- ✅ All 721 tests passing (693 unit + 28 functional, +4 new tests)
- ✅ Flake8 verification: F821 errors eliminated
- ✅ Prevents runtime crashes during admin email operations
- ✅ See [Technical Note](technical-notes/2025-11-09-code-linting-analysis.md) for full details

#### Phase 5.2: Code Linting Phase 1 - Backend High Priority (Completed - 2025-11-10)
- ✅ Removed 217 unused imports (F401 errors eliminated)
- ✅ Removed 14 unused variables (F841 errors reduced)
- ✅ Fixed 12 star import issues with noqa comments (F403/F405/F811)
- ✅ Fixed 48 comparison issues (E711/E712)
- ✅ Protected 7 validation comparisons from autopep8 with explanatory comments
- ✅ Reduced flake8 issues from 3,941 to 3,669 (272 issues fixed, 6.9% reduction)
- ✅ 51 files modified, 70 net lines removed
- ✅ All 721 tests passing (100% pass rate maintained)
- ✅ Zero regressions, validation logic protected and documented
- ✅ See [Technical Note](technical-notes/2025-11-10-linting-phase1-backend-high-priority.md) for details

#### Phase 5.3: Code Linting Phase 2 - Backend Style/Formatting (Completed - 2025-11-10)
- ✅ Fixed 175 trailing whitespace issues (W291 eliminated)
- ✅ Fixed 301 blank line issues (E301/E302/E305/W391)
- ✅ Fixed 589 whitespace after comma issues (E231 eliminated)
- ✅ Fixed 32 whitespace before colon issues (E203 reduced)
- ✅ Fixed 15 blank line whitespace issues (W293 eliminated)
- ✅ Reduced flake8 issues from 3,669 to 2,490 (1,179 issues fixed, 32.1% reduction)
- ✅ Cumulative reduction: 3,941 → 2,490 (1,451 total fixed, 36.8% total reduction)
- ✅ 23 files modified, net +319 lines (blank lines for PEP 8 compliance)
- ✅ All 721 tests passing, zero regressions
- ✅ Fully automated with autopep8
- ✅ See [Technical Note](technical-notes/2025-11-10-linting-phase2-backend-style-formatting.md) for details

#### Phase 5.4: Code Linting Phase 3 - Backend Critical Issues (Completed - 2025-11-10)
- ✅ Removed 47 semicolons (E703 eliminated)
- ✅ Fixed 30 comparison issues (E712: 37 → 7, 81% reduction)
- ✅ Refactored isUserNameAvailable() to use .filter().exists() pattern
- ✅ Protected 6 validator pattern comparisons with noqa comments
- ✅ Reduced flake8 issues from 2,490 to 2,405 (85 issues fixed, 3.4% reduction)
- ✅ Cumulative reduction: 3,941 → 2,405 (1,536 total fixed, 39.0% total reduction)
- ✅ 6 files modified, net +19 lines (comments and clarifications)
- ✅ All 721 tests passing, zero regressions
- ✅ Addressed all critical code correctness issues
- ✅ See [Technical Note](technical-notes/2025-11-10-linting-phase3-backend-critical.md) for details

#### Phase 5.5: Frontend JavaScript Linting (Completed - 2025-11-11)
- ✅ Fixed all 5,333 ESLint issues (441 errors + 4,892 warnings → 0 errors + 0 warnings)
- ✅ 100% reduction achieved across all 19 JavaScript files
- ✅ Automated fixes: 4,674 issues (87.6% - indentation, quotes, semicolons)
- ✅ Manual fixes: 659 issues (12.4% - undefined vars, missing declarations, unused vars)
- ✅ Added 100+ global function declarations to eslint.config.js
- ✅ Fixed 20+ missing var declarations preventing global scope pollution
- ✅ Created TDD test for display_errors to prevent regression
- ✅ All QUnit tests passing, All 721 backend tests passing
- ✅ See [Technical Note](technical-notes/2025-11-11-frontend-javascript-linting-complete.md) for details

#### Phase 5.6: Replace print() with Django Logging (Completed - 2025-11-12)
- ✅ Configured comprehensive Django logging framework in settings.py
- ✅ Replaced 106 print() statements with appropriate logging calls
- ✅ Deleted 101 commented print() statements (technical debt cleanup)
- ✅ Updated 8 production files with logging (user, order, clientevent, validators, utilities)
- ✅ Created rotating file handler: logs/django.log (10 MB max, 5 backups)
- ✅ Environment-aware: DEBUG level in development, INFO in production
- ✅ All 721 tests passing (693 unit + 28 functional), zero regressions
- ✅ Production-ready: persistent logs, severity levels, full context (timestamps, module/function names)
- ✅ Integration-ready: can connect to Sentry, CloudWatch, ELK stack
- ✅ See [Technical Note](technical-notes/2025-11-12-replace-print-with-logging.md) for details

#### Phase 5.7: Backend Linting Phase 4-6 Complete - Zero Errors Achieved (Completed - 2025-11-13)
- ✅ **ZERO linting errors achieved** (2,286 → 0 issues, 100% reduction)
- ✅ Phase 4: Refactored identifier.py (14 issues fixed, 33% LOC reduction)
  - Migrated from while/try/except to .filter().exists() pattern
  - Fixed 7 E712 + 7 F841 + 1 F401 errors
- ✅ Phase 5: Applied autopep8 automated fixes (1,907 issues fixed, 83.9% reduction)
  - Whitespace, blank lines, import formatting
  - Fully automated, zero manual intervention
- ✅ Phase 6: Manual resolution of remaining 365 issues
  - Raised max-line-length to 120 (198 issues resolved)
  - Fixed 55 F841 unused variables (exception handlers, DB writes, test fixtures)
  - Fixed 7 critical issues (3 E999 SyntaxErrors + 4 F821 undefined names)
  - Fixed 4 minor issues (3 E203 whitespace + 1 E402 import)
  - Fixed 33 E501 long lines (email strings, test assertions, commented code)
  - Added 6 noqa comments for intentional E712 validator pattern
- ✅ All 693 unit tests passing (verified 3 times throughout process)
- ✅ 27/28 functional tests passing (1 unrelated flaky chat test)
- ✅ Updated SESSION_START_PROMPT.md with max-line-length=120 standard
- ✅ Black code formatter integrated for ongoing code quality
- ✅ See [Technical Note](technical-notes/2025-11-13-backend-linting-phase4-phase5-phase6.md) for full details

#### Phase 5.8: CSRF Token Bug Fix - Complete Resolution (Completed - 2025-11-16)
- ✅ **Fixed critical CSRF token stale variable bug** affecting all AJAX POST requests
- ✅ Root Cause: JavaScript global variable cached token once, but Django rotated tokens causing mismatches
- ✅ Systematic debugging: production code → test analysis → manual browser testing → root cause → fix
- ✅ Solution: Changed 26 instances across 20 JavaScript files from stale variable to dynamic cookie reads
- ✅ Pattern: `csrftoken` → `$.getCookie('csrftoken')` in all AJAX `beforeSend` headers
- ✅ Code cleanup: Removed unused global variable, simplified redundant if/else fallback logic
- ✅ Manual testing: Chat submission now returns 200 OK (previously 403 Forbidden)
- ✅ **Functional test validation: 100% pass rate** (10/10 runs, 28 tests each)
  - Previous: 50% pass rate (test workarounds improved to 80-90%)
  - Current: 100% pass rate with production code fix
- ✅ Impact: Eliminated intermittent form submission failures affecting all user flows
  - Chat messages, cart operations, account updates, checkout confirmation
  - Terms acceptance, password changes, email preferences, account creation
- ✅ All 721 tests passing, zero ESLint errors/warnings maintained
- ✅ See [Technical Note](technical-notes/2025-11-16-csrf-token-stale-variable-bug-fix.md) for complete details

#### Phase 5.9: PostgreSQL Migration - Phase 1: FloatField→DecimalField (Completed - 2025-11-17)
- ✅ **Converted 12 currency FloatField instances to DecimalField** for financial precision
- ✅ Applied TDD methodology: wrote 19 tests first, verified failures, implemented fix
- ✅ Configuration: `max_digits=10, decimal_places=2` (supports up to $99,999,999.99)
- ✅ Fixed business logic in `order_utils.py` to handle Decimal types
- ✅ Updated 11 test assertions to expect string values in JSON (DecimalField serialization)
- ✅ Created Django migration: `0003_alter_discountcode_discount_amount_and_more.py`
- ✅ **All 740 tests passing** (712 unit + 28 functional) - 100% pass rate
- ✅ Zero linting errors (28 E501 in auto-generated migrations only)
- ✅ Benefits: Exact decimal arithmetic, no floating-point errors, PostgreSQL compatibility
- ✅ Example: `0.1 + 0.2 = Decimal('0.30')` (was `0.30000000000000004` with float)
- ✅ See [Technical Note](technical-notes/2025-11-17-floatfield-to-decimalfield-conversion.md) for details

#### Phase 5.10: PostgreSQL Migration - Phases 2-5 Complete (Completed - 2025-11-18)
- ✅ **Phase 2: Docker PostgreSQL Setup**
  - Added PostgreSQL 16-alpine service to docker-compose.yml
  - Created multi-database initialization script (`scripts/init-multi-db.sh`)
  - Added psycopg2-binary==2.9.9 to requirements.txt
  - Created 3 databases: startupwebapp_dev, healthtech_dev, fintech_dev
- ✅ **Phase 3: Django Configuration**
  - Updated settings_secret.py for environment-based PostgreSQL config
  - Configured multi-tenant database routing via DATABASE_NAME env var
  - Connection pooling: CONN_MAX_AGE=600 (10 minute reuse)
  - Backend depends_on db service with health check
- ✅ **Phase 4: Database Migration**
  - All 57 tables created successfully via migrations
  - Fresh PostgreSQL database (no data migration needed)
  - All Django migrations applied cleanly
- ✅ **Phase 5: Test Compatibility - Major Achievement!**
  - **Problem**: PostgreSQL sequence management differs from SQLite (explicit IDs cause conflicts)
  - **Solution**: Created PostgreSQLTestCase base class (TransactionTestCase + reset_sequences=True)
  - Fixed data migration to skip during PostgreSQL test runs (check for `test_` prefix)
  - Created automated migration script with dry-run validation
  - **Updated 138 test classes across 43 test files** (proof-of-concept → automation → success)
  - Trade-off: TransactionTestCase 20-30% slower but necessary for correctness
- ✅ **All 740 tests passing** (712 unit + 28 functional) - 100% pass rate with PostgreSQL!
- ✅ Linting: Zero functional code errors (28 E501 in migrations only - acceptable)
- ✅ Multi-tenant architecture: Separate databases per fork on shared instance (75% cost savings)
- ✅ Production-ready for AWS RDS deployment
- ✅ Timeline: 8 hours end-to-end (including discovery, implementation, documentation)
- ✅ See [Technical Note](technical-notes/2025-11-18-postgresql-migration-phases-2-5-complete.md) for comprehensive details

#### Phase 5.11: AWS RDS Infrastructure Setup - Phase 7 (Completed - 2025-11-19)
- ✅ **21 Infrastructure as Code Scripts Created** for AWS deployment
- ✅ **VPC & Networking**: Custom VPC with public/private subnets across 2 AZs
- ✅ **Security**: RDS in private subnets, proper security groups, deletion protection
- ✅ **Secrets Manager**: Database credentials stored securely, no hardcoded passwords
- ✅ **RDS PostgreSQL 16**: db.t4g.small instance with multi-tenant support
- ✅ **CloudWatch Monitoring**: 4 alarms (CPU, connections, storage, memory) + SNS email alerts
- ✅ **Cost Optimization**: Skipped NAT Gateway (saved $32/month, 52% reduction)
- ✅ **Monthly Cost**: $29/month (RDS $26 + monitoring $3)
- ✅ **Deployment Status**: 5/7 steps complete (71%) - Ready for database creation
- ✅ All scripts tested with create→destroy→create cycles (idempotent and reliable)
- ✅ See [Technical Note](technical-notes/2025-11-19-aws-rds-deployment-plan.md) for architecture details

#### Phase 5.12: AWS RDS Django Integration - Phase 8 (Completed - 2025-11-20)
- ✅ **Production Settings Module Created** (`settings_production.py`)
  - Retrieves ALL secrets from AWS Secrets Manager (not just database)
  - Database credentials + Django SECRET_KEY + Stripe keys + Email SMTP
  - Multi-tenant database support via DATABASE_NAME environment variable
  - Enforces production security (HTTPS, HSTS, secure cookies)
  - Graceful fallback to environment variables for local testing
- ✅ **Enhanced Infrastructure Scripts**
  - Updated `create-secrets.sh`: Auto-generates Django SECRET_KEY (50 chars)
  - Updated `create-secrets.sh`: Creates placeholders for Stripe/Email credentials
  - Updated `destroy-secrets.sh`: Enhanced warnings for expanded secret structure
  - Created `test-rds-connection.py`: Validates AWS RDS connectivity (5 tests)
- ✅ **Infrastructure Validation**: Full destroy→create cycle tested successfully
  - Tested: destroy-monitoring, destroy-rds, destroy-secrets (with new warnings)
  - Tested: create-secrets (expanded structure), create-rds, create-monitoring
  - Result: Infrastructure at 71% (5/7 steps), $29/month cost confirmed
- ✅ **Dependencies**: Added boto3==1.35.76 for AWS SDK integration
- ✅ **All 712 unit tests passing** (100% pass rate maintained)
- ✅ **Zero linting errors** (settings_production.py validated)
- ✅ **Security**: Zero hardcoded credentials, all secrets in AWS Secrets Manager
- ✅ See [Technical Note](technical-notes/2025-11-20-aws-rds-django-integration.md) for deployment guide

#### Phase 5.13: AWS RDS Database Creation & Bastion Host - Phase 9 (Complete - 2025-11-22)
- ✅ **Bastion Host Infrastructure Scripts Created**
  - Created `create-bastion.sh`: Deploys t3.micro EC2 instance with SSM access
  - Created `destroy-bastion.sh`: Clean teardown with proper dependency ordering
  - IAM role with AmazonSSMManagedInstanceCore policy (no SSH keys needed)
  - Amazon Linux 2023 with PostgreSQL 15 client pre-installed
  - User data script installs jq and creates helpful MOTD
- ✅ **Root Caused SSM Connection Issue**
  - Systematic diagnosis: SSM agent never registered (empty InstanceInformationList)
  - Found: Bastion instance had no public IP address (PublicIP: null)
  - Root cause: Missing `--associate-public-ip-address` flag in run-instances command
  - Fix applied: Added flag to create-bastion.sh line 200
- ✅ **Bastion Host Successfully Deployed**
  - Instance ID: i-0d8d746dd8059de2c (Public IP: 44.200.159.86)
  - SSM agent online and verified
  - Successfully connected via: `aws ssm start-session --target i-0d8d746dd8059de2c`
  - Cost: ~$7/month running, ~$1/month stopped (can stop when not in use)
- ✅ **Multi-Tenant Databases Created on AWS RDS**
  - Created database user: `django_app` with proper permissions
  - Created database: `startupwebapp_prod` (UTF8, en_US.UTF-8, owner: django_app)
  - Created database: `healthtech_experiment` (UTF8, en_US.UTF-8, owner: django_app)
  - Created database: `fintech_experiment` (UTF8, en_US.UTF-8, owner: django_app)
  - Verified: django_app user can connect to all databases
  - Connected via bastion host using PostgreSQL client
- ✅ **Infrastructure Scripts Enhanced**
  - Updated `status.sh`: Added optional bastion section with cost tracking
  - Updated `show-resources.sh`: Added bastion display with SSM connect command
  - Updated `aws-resources.env.template`: Added BASTION_INSTANCE_ID field
  - Generated `create-databases.sh`: SQL script generator for multi-tenant setup
- ✅ **Security Improvements: Separate Master and Application Passwords**
  - Implemented principle of least privilege for database access
  - Updated `create-secrets.sh`: Generates separate MASTER_PASSWORD and APP_PASSWORD (32 chars each)
  - Secret structure includes both `master_username/master_password` and `username/password`
  - postgres (master) and django_app (application) now have different passwords
- ✅ **Critical Bug Fix: RDS Secret Update**
  - **Problem**: `create-rds.sh` was overwriting entire secret when updating RDS endpoint
  - Lost fields: `master_password`, `django_secret_key`, Stripe keys, Email credentials
  - **Solution**: Updated script to use `jq` to update only `host` field, preserving all others
  - Fixed in PR #37, infrastructure destroyed and recreated with correct secrets
- ✅ **Deployment Progress**: 7/7 steps complete (100%)
  - Step 1: VPC and Networking ✅
  - Step 2: Security Groups ✅
  - Step 3: Secrets Manager ✅ (with separate master/app passwords)
  - Step 4: RDS PostgreSQL ✅ (using fixed create-rds.sh)
  - Step 5: Multi-Tenant Databases ✅ (using separate passwords)
  - Optional: Bastion Host ✅
  - Step 6: CloudWatch Monitoring ✅ (SNS email confirmed)
  - Step 7: Verification ✅
- ✅ **Monthly Infrastructure Cost**: $36 ($29 base + $7 bastion running)
  - Can reduce to $30/month by stopping bastion when not in use
- ✅ **Pull Requests Merged**:
  - PR #36: Phase 9 initial deployment (bastion host, separate passwords, documentation)
  - PR #37: Bugfix for secret preservation in create-rds.sh
- ✅ **Next Steps**:
  - Run Django migrations on AWS RDS from local machine or bastion
  - Update production credentials (Stripe keys, Email SMTP)
  - Test full Django application against AWS RDS
- ✅ See [Deployment Guide](technical-notes/2025-11-21-phase-9-deployment-guide.md) for step-by-step instructions
- ✅ See [Bastion Troubleshooting](technical-notes/2025-11-22-phase-9-bastion-troubleshooting.md) for SSM connection fix

#### Phase 5.14: ECS Infrastructure, CI/CD, and RDS Migrations (In Progress - November 24, 2025)

**Status**: 🚧 In Progress - Step 2/9 Complete
**Branch**: `feature/phase-5-14-ecs-cicd-migrations`

**Step 1: Multi-Stage Dockerfile** ✅ (Completed - November 23, 2025)
- ✅ Added gunicorn==21.2.0 to requirements.txt for production WSGI server
- ✅ Created multi-stage Dockerfile with three targets:
  - **base**: Shared layer with Python 3.12, gcc, libpq-dev, all Python dependencies
  - **development**: Includes Firefox ESR, geckodriver for Selenium tests (1.69 GB)
  - **production**: Minimal, optimized for deployment with gunicorn (692 MB, 59% smaller)
- ✅ Enhanced .dockerignore to exclude AWS/infrastructure files from build context
- ✅ Built and tested both images successfully
- ✅ Verified development image has all test dependencies (Firefox, geckodriver)
- ✅ Verified production image has gunicorn, excludes test dependencies
- ✅ Production image ready for AWS ECS deployment

**Files Modified**:
- `requirements.txt` - Added gunicorn==21.2.0
- `Dockerfile` - Complete rewrite as multi-stage build
- `.dockerignore` - Added AWS/infrastructure exclusions

**Step 2: AWS ECR Repository** ✅ (Completed - November 24, 2025)
- ✅ Created infrastructure scripts following established patterns
  - `scripts/infra/create-ecr.sh` - Creates ECR repository with full configuration
  - `scripts/infra/destroy-ecr.sh` - Safely destroys ECR repository
- ✅ ECR repository created: `startupwebapp-backend`
- ✅ Image scanning enabled (scan on push for vulnerabilities)
- ✅ Lifecycle policy configured (keep last 10 images automatically)
- ✅ AES256 encryption at rest
- ✅ Resource tracking in aws-resources.env
- ✅ Full create → destroy → recreate test cycle validated
- ✅ Updated status.sh with Phase 5.14 section and ECR status checking
- ✅ Updated show-resources.sh to display ECR repository details
- ✅ Updated scripts/infra/README.md with comprehensive ECR documentation
- ✅ Cost: ~$0.10-$0.20/month for ECR storage (1-2 images)

**Files Created**:
- `scripts/infra/create-ecr.sh` - ECR creation script (idempotent, tested)
- `scripts/infra/destroy-ecr.sh` - ECR destruction script (with confirmation)

**Files Modified**:
- `scripts/infra/aws-resources.env.template` - Added ECR_REPOSITORY_URI and ECR_REPOSITORY_NAME
- `scripts/infra/status.sh` - Added Phase 5.14 section with visual separator
- `scripts/infra/show-resources.sh` - Added ECR display with image count and quick link
- `scripts/infra/README.md` - Added ECR documentation throughout

---

**Step 3: AWS ECS Infrastructure** ✅ (Completed & Tested - November 24, 2025)

- ✅ Created 5 infrastructure scripts with full lifecycle management
- ✅ ECS Fargate cluster created: `startupwebapp-cluster`
- ✅ CloudWatch log group created: `/ecs/startupwebapp-migrations` (7-day retention)
- ✅ IAM roles created:
  - `ecsTaskExecutionRole-startupwebapp` (pull images, write logs, read secrets)
  - `ecsTaskRole-startupwebapp` (application runtime permissions)
- ✅ Security groups updated for ECS → RDS communication (port 5432) and ECR access (port 443)
- ✅ Full lifecycle testing: create → destroy → recreate validated successfully
- ✅ Updated aws-resources.env.template with 7 ECS fields
- ✅ Updated status.sh with ECS cluster and IAM role tracking
- ✅ Updated show-resources.sh with ECS resource display and live status
- ✅ Updated scripts/infra/README.md with comprehensive ECS documentation
- ✅ Cost: $0 for infrastructure (pay-per-use: ~$0.0137/hour when tasks run)

**Files Created**:
- `scripts/infra/create-ecs-cluster.sh` - ECS cluster creation (tested)
- `scripts/infra/destroy-ecs-cluster.sh` - ECS cluster destruction (tested)
- `scripts/infra/create-ecs-task-role.sh` - IAM roles creation (tested)
- `scripts/infra/destroy-ecs-task-role.sh` - IAM roles destruction (tested)
- `scripts/infra/update-security-groups-ecs.sh` - Security group updates (tested)

**Files Modified**:
- `scripts/infra/aws-resources.env.template` - Added 7 ECS resource fields
- `scripts/infra/aws-resources.env` - Populated with actual ECS resource ARNs
- `scripts/infra/status.sh` - Added ECS cluster and IAM role status checking with live AWS queries
- `scripts/infra/show-resources.sh` - Added ECS resource display with cluster status and task count
- `scripts/infra/README.md` - Added ECS deployment order and comprehensive script documentation

**Resources Created**:
- ECS Cluster: `startupwebapp-cluster` (ARN: arn:aws:ecs:us-east-1:853463362083:cluster/startupwebapp-cluster)
- Log Group: `/ecs/startupwebapp-migrations` (7-day retention)
- Task Execution Role: `ecsTaskExecutionRole-startupwebapp` (ARN: arn:aws:iam::853463362083:role/ecsTaskExecutionRole-startupwebapp)
- Task Role: `ecsTaskRole-startupwebapp` (ARN: arn:aws:iam::853463362083:role/ecsTaskRole-startupwebapp)
- Security Group Rules: Backend SG outbound to RDS (5432) and internet (443)

**Test Results**:
- Destroy: IAM roles, cluster, and log group deleted cleanly ✅
- Recreate: All resources recreated with same names and configurations ✅
- aws-resources.env: Properly cleared on destroy, repopulated on recreate ✅
- Status scripts: Accurately reflect resource state ✅
- Base infrastructure: Remained untouched (VPC, RDS, security groups, ECR) ✅

**Next Steps**:
- Step 4: Create ECS task definition for migrations (code-based)
- Step 5: Create GitHub Actions CI/CD workflow
- Step 6: Configure GitHub secrets
- Step 7: Run migrations via pipeline (3 databases)
- Step 8: Verification
- Step 9: Documentation
**Objective**: Establish production deployment infrastructure with GitHub Actions CI/CD and run Django migrations on AWS RDS

**Approach**: CI/CD-first strategy - validate deployment pipeline with low-risk database migrations before full application deployment

**Key Components**:
- Multi-stage Dockerfile (development + production targets)
- AWS ECR for Docker image registry
- AWS ECS Fargate cluster (serverless containers)
- GitHub Actions workflow (test → build → push → deploy)
- ECS task definitions for migrations
- Automated migrations on all 3 RDS databases (startupwebapp_prod, healthtech_experiment, fintech_experiment)

**Estimated Time**: 6-7 hours
**Progress**: Documentation complete, ready for implementation

**Decisions Made**:
- ✅ Multi-stage Dockerfile over separate files
- ✅ GitHub Actions over AWS CodePipeline
- ✅ CI/CD setup in Phase 5.14 (not deferred to later phase)
- ✅ Manual trigger for migrations (safety for database operations)
- ✅ Automated testing (740 tests) in pipeline before any deployment

See [Phase 5.14 Technical Note](technical-notes/2025-11-23-phase-5-14-ecs-cicd-migrations.md) for detailed implementation plan.

---

#### Phase 5.15: Full Production Deployment (Planned)
- Deploy long-running ECS service (not just one-time tasks)
- Application Load Balancer with HTTPS
- Auto-scaling policies
- Frontend deployment (S3 + CloudFront)
- Enhanced monitoring and observability

#### Phase 5.16: Production Hardening (Future)
- AWS WAF for security
- Load testing and performance optimization
- Automated disaster recovery testing

## Documentation Structure

### `/milestones`
Chronological project milestones and phase completion reports. Each milestone documents what was accomplished, why it matters, and the impact on the project.

### `/test-coverage`
Test coverage analysis and reports. Includes detailed breakdowns of coverage by module and recommendations for improvement.

### `/technical-notes`
Implementation details, bug fixes, and technical decisions. Reference material for specific problems and their solutions.

## Contributing

When adding new documentation:
- **Milestones**: Date-prefix with `YYYY-MM-DD-description.md` format
- **Test Coverage**: Update after significant coverage changes
- **Technical Notes**: Use descriptive kebab-case filenames
- Include clear headers with date and status
- Write for an external audience (open source project)
