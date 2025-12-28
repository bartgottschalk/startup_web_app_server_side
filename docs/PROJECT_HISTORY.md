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

### Current Status: 819 Tests Passing ✅ (100% Pass Rate with PostgreSQL!)
- **Backend Unit Tests**: 693 tests
  - User App: 299 tests (authentication, profiles, email management, admin actions)
  - Order App: 325 tests (products, cart, Stripe Checkout Sessions, webhooks, payments)
  - ClientEvent App: 51 tests (analytics event tracking)
  - Validators: 50 tests (input validation)
- **Backend Functional Tests**: 37 Selenium 4 tests (checkout flow, user journeys, Django Admin) - 100% reliable
- **Frontend Unit Tests**: 88 QUnit tests (Stripe Checkout Sessions + utilities)
- **Total Tests**: 818 tests (693 backend unit + 37 backend functional + 88 frontend unit)
- **Database**: PostgreSQL 16 (multi-tenant architecture, local + AWS RDS production)
- **AWS Infrastructure**: Deployed (VPC, RDS, Secrets Manager, CloudWatch, ECS Fargate, ALB) - ~$98/month
- **Production Settings**: Django configured for AWS deployment with Secrets Manager integration
- **Code Quality**: Zero linting errors (backend Flake8 + frontend ESLint), automated PR validation on both repos
- **CI/CD**: Automated PR validation on backend (693 unit + 38 functional) and frontend (88 tests + ESLint)
- **Payment Processing**: Stripe Checkout Sessions (modern API, production ready)

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

#### Phase 5.14: ECS Infrastructure, CI/CD, and RDS Migrations (Completed - November 26, 2025)

**Status**: ✅ COMPLETE - All Core Steps Finished (8/8)
**Branch**: `master` (All steps merged)

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

---

**Step 4: ECS Task Definition** ✅ (Completed - November 24, 2025)

- ✅ Created infrastructure scripts with full lifecycle management
- ✅ Task definition registered: `startupwebapp-migration-task:2` (0.25 vCPU, 512 MB RAM)
- ✅ Fargate launch type configured with awsvpc networking mode
- ✅ Command set to: `python manage.py migrate`
- ✅ AWS Secrets Manager integration configured:
  - DATABASE_PASSWORD, DATABASE_USER, DATABASE_HOST, DATABASE_PORT pulled from secret
  - Secret: `rds/startupwebapp/multi-tenant/master`
- ✅ Environment variables configured:
  - DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production
  - AWS_REGION=us-east-1
  - DB_SECRET_NAME=rds/startupwebapp/multi-tenant/master
- ✅ CloudWatch logging configured: `/ecs/startupwebapp-migrations` log group
- ✅ Production Docker image built and pushed to ECR:
  - Image: `853463362083.dkr.ecr.us-east-1.amazonaws.com/startupwebapp-backend:latest`
  - Size: 157 MB (compressed)
  - Built from multi-stage Dockerfile production target
- ✅ Full lifecycle testing: create → destroy → recreate validated successfully
- ✅ Updated aws-resources.env.template with 3 task definition fields
- ✅ Updated status.sh with task definition status checking
- ✅ Updated show-resources.sh with task definition display (CPU, memory, status)
- ✅ Updated scripts/infra/README.md with comprehensive documentation
- ✅ Cost: $0 for task definition (tasks cost ~$0.001 per 5-minute migration run)

**Files Created**:
- `scripts/infra/create-ecs-task-definition.sh` - Task definition creation (tested)
- `scripts/infra/destroy-ecs-task-definition.sh` - Task definition deregistration (tested)

**Files Modified**:
- `scripts/infra/aws-resources.env.template` - Added 3 task definition fields
- `scripts/infra/aws-resources.env` - Populated with task definition ARN and revision
- `scripts/infra/status.sh` - Added task definition status section with live AWS checks
- `scripts/infra/show-resources.sh` - Added task definition display with CPU/memory details
- `scripts/infra/README.md` - Added comprehensive task definition documentation

**Resources Created**:
- ECS Task Definition: `startupwebapp-migration-task:2` (ARN: arn:aws:ecs:us-east-1:853463362083:task-definition/startupwebapp-migration-task:2)
- Docker Image: `startupwebapp-backend:latest` in ECR (157 MB compressed)

**Test Results**:
- Create: Task definition revision 1 registered successfully ✅
- Destroy: Task definition deregistered, aws-resources.env cleared ✅
- Recreate: Task definition revision 2 created (AWS auto-increments revisions) ✅
- Status scripts: Accurately reflect task definition state ✅

---

**Step 5: GitHub Actions CI/CD Workflow** ✅ (Completed - November 25, 2025)

- ✅ Created comprehensive GitHub Actions workflow: `.github/workflows/run-migrations.yml`
- ✅ Manual trigger with database selection dropdown (startupwebapp_prod, healthtech_experiment, fintech_experiment)
- ✅ Fully documented workflow with 200+ inline comments explaining every step
- ✅ Four-job pipeline architecture:
  - **Job 1: Test Suite** (~5-7 min)
    - PostgreSQL 16 service container
    - Python 3.12 with dependency caching
    - Flake8 linting (code quality check)
    - 712 unit tests (parallel execution)
    - Firefox ESR + geckodriver setup
    - 28 functional tests (Selenium)
  - **Job 2: Build & Push** (~3-5 min)
    - Multi-stage Docker build (production target)
    - Tag with git commit SHA for traceability
    - Push to AWS ECR with both commit SHA and 'latest' tags
    - Output image URI for migration job
  - **Job 3: Run Migrations** (~2-5 min)
    - Configure AWS credentials from GitHub Secrets
    - Get existing ECS task definition
    - Update with new image and DATABASE_NAME environment variable
    - Register new task definition revision
    - Launch ECS Fargate task in private subnets
    - Wait for task completion (up to 10 minutes)
    - Fetch CloudWatch logs for review
    - Verify exit code (0 = success)
  - **Job 4: Summary** (~10 sec)
    - Display results of all jobs
    - Report success/failure status
- ✅ Security features:
  - AWS credentials stored as encrypted GitHub Secrets
  - No hardcoded credentials in workflow file
  - Proper IAM role usage for ECS tasks
- ✅ Safety features:
  - Manual trigger only (no automatic migrations on push)
  - Optional "skip tests" checkbox for emergencies
  - Confirmation required in GitHub UI before execution
  - Full CloudWatch logs captured for audit trail
- ✅ Created comprehensive guide: `docs/GITHUB_ACTIONS_GUIDE.md`
  - Step-by-step instructions for setting up GitHub Secrets
  - How to run migrations manually
  - Reading workflow results
  - Troubleshooting common issues
  - Cost breakdown
- ✅ Total pipeline duration: ~10-17 minutes per database
- ✅ Cost: Negligible (~$0.10/month for ~100 migration runs)

**Files Created**:
- `.github/workflows/run-migrations.yml` - GitHub Actions workflow (fully documented)
- `docs/GITHUB_ACTIONS_GUIDE.md` - Complete user guide with screenshots and examples

**Workflow Capabilities**:
- ✅ Prevents broken code from reaching production (test-first approach)
- ✅ Traceable deployments (git commit SHA tags)
- ✅ Real-time progress monitoring in GitHub UI
- ✅ CloudWatch log integration for debugging
- ✅ Multi-database support (3 RDS databases)
- ✅ Parallel test execution for speed
- ✅ Production-ready error handling

---

**Step 6: Configure GitHub Secrets & Workflow Debugging** ✅ COMPLETE (November 25, 2025)

- ✅ Created IAM user for GitHub Actions CI/CD
  - User: `github-actions-startupwebapp`
  - Policies: AmazonEC2ContainerRegistryPowerUser, AmazonECS_FullAccess, CloudWatchLogsReadOnlyAccess
  - Generated AWS access keys for programmatic access
- ✅ Added 3 GitHub repository secrets:
  - AWS_ACCESS_KEY_ID (IAM user access key)
  - AWS_SECRET_ACCESS_KEY (IAM user secret key)
  - AWS_REGION (us-east-1)
- ✅ Workflow debugging and fixes (7 iterations, ~3 hours):
  1. Fixed skip_tests boolean logic (string vs boolean comparison)
  2. Excluded migrations from flake8 linting (auto-generated files)
  3. Generated settings_secret.py for CI environment
  4. Fixed Stripe setting names (matched template structure)
  5. Fixed Firefox installation (snap for Ubuntu 24.04 vs firefox-esr)
  6. Added /etc/hosts entries for functional test hostnames
  7. Set DOCKER_ENV variable (skip frontend server, use backend directly)
- ✅ All 740 tests now pass in CI/CD (712 unit + 28 functional)
- ✅ Created comprehensive debugging documentation

**Files Modified**:
- `.github/workflows/run-migrations.yml` - 7 bug fixes applied
- All fixes committed to master (commits: 1168c38, c17734f, 8cda567, 953fad9, 62d9274, 71109c4, c74899e)

**Lessons Learned**:
- GitHub Actions inputs are strings, not booleans (even when declared as boolean)
- Environment differences require iterative testing (Docker vs GitHub Actions)
- Functional tests valuable but complex (browser, hostname resolution, server architecture)
- Template consistency critical (settings_secret.py structure)
- Ubuntu 24.04 ships Firefox as snap, not apt package

**Documentation Created**:
- `docs/technical-notes/2025-11-25-phase-5-14-step-6-github-actions-debugging.md`

---

**Step 7a: NAT Gateway Infrastructure** ✅ COMPLETE (November 26, 2025)

- ✅ Created infrastructure scripts following established patterns
  - `scripts/infra/create-nat-gateway.sh` - Creates NAT Gateway with full configuration
  - `scripts/infra/destroy-nat-gateway.sh` - Safely destroys NAT Gateway
- ✅ NAT Gateway created: `nat-06ecd81baab45cf4a` (available)
- ✅ Elastic IP allocated: `52.206.125.11` (eipalloc-062ed4f41e4c172b1)
- ✅ Private subnet route table updated: 0.0.0.0/0 → NAT Gateway
- ✅ Full lifecycle validated: create → destroy → recreate tested successfully
- ✅ Updated status.sh with NAT Gateway status section (shows state, explains requirement)
- ✅ Updated show-resources.sh with NAT Gateway display (shows public IP, live state)
- ✅ Updated scripts/infra/README.md with comprehensive NAT Gateway documentation
- ✅ Cost: +$32/month (~$68/month total infrastructure)

**Why Required:**
- ECS tasks in private subnets need outbound internet access for:
  - Pulling Docker images from ECR
  - Fetching secrets from AWS Secrets Manager
  - Writing logs to CloudWatch Logs
  - Calling external APIs (Stripe, email services, etc.)
- NAT Gateway provides secure one-way internet access (outbound only, no inbound)
- Industry-standard pattern for production workloads

**Files Created:**
- `scripts/infra/create-nat-gateway.sh` - NAT Gateway creation (idempotent, tested)
- `scripts/infra/destroy-nat-gateway.sh` - NAT Gateway destruction (with confirmation, tested)

**Files Modified:**
- `scripts/infra/aws-resources.env.template` - NAT Gateway fields already present (no changes needed)
- `scripts/infra/aws-resources.env` - Populated with NAT Gateway ID and Elastic IP allocation ID
- `scripts/infra/status.sh` - Added NAT Gateway status section with live AWS state checking
- `scripts/infra/show-resources.sh` - Enhanced NAT Gateway display with public IP and state
- `scripts/infra/README.md` - Updated status, costs, deployment order, added detailed NAT Gateway documentation

**Resources Created:**
- NAT Gateway: `nat-06ecd81baab45cf4a` (state: available)
- Elastic IP: `52.206.125.11` (allocation: eipalloc-062ed4f41e4c172b1)
- Route: 0.0.0.0/0 → nat-06ecd81baab45cf4a in private route table (rtb-0085e608db16a80ca)

**Test Results:**
- Create: NAT Gateway created successfully, route added, ~2-3 min wait time ✅
- Destroy: Route deleted, NAT Gateway deleted, Elastic IP released cleanly ✅
- Recreate: New NAT Gateway with different ID/IP, all configurations correct ✅
- aws-resources.env: Properly cleared on destroy, repopulated on recreate ✅
- Status scripts: Accurately show NAT Gateway state and requirements ✅

**Network Flow Enabled:**
```
ECS Task (private subnet) → NAT Gateway → Internet Gateway → Internet
                         ← (translates IPs) ← Internet Gateway ← (responses)
```

**Security:**
- NAT Gateway only allows outbound connections (one-way)
- Inbound connections from internet are blocked
- Private resources never get public IP addresses
- All connections appear to come from NAT Gateway's Elastic IP (52.206.125.11)

---

**Step 7b: Test Workflow & Run Migrations** ✅ COMPLETE (November 26, 2025)

**Previously Step 7 - BLOCKER RESOLVED & MIGRATIONS SUCCESSFUL**

- ✅ **Additional Functional Test Fixes** (4 additional commits):
  1. Fixed CSRF_COOKIE_DOMAIN = ".startupwebapp.com" (enable cookie sharing across subdomains)
  2. Added port numbers to CSRF_TRUSTED_ORIGINS (Django 4.x requires explicit ports)
  3. Added frontend origins to CORS_ORIGIN_WHITELIST (enable AJAX with credentials)
  4. Added Orderconfiguration test fixtures (eliminate 500 errors for /order/checkout-allowed)
  5. Fixed AWS ECS wait command syntax (removed unsupported --max-attempts/--delay flags)
  6. Removed skip_unit_tests debugging option (no longer needed)
- ✅ **All 740 tests passing in CI/CD** (712 unit + 28 functional)
- ✅ **Clean logs** (no 500 errors)
- ✅ **Docker environment drift fixed** (removed manually created Orderconfiguration objects)
- ✅ **BLOCKER RESOLVED**: NAT Gateway created in Step 7a
  - **Previous Error**: "unable to pull secrets or registry auth... context deadline exceeded"
  - **Root Cause**: ECS tasks in private subnets couldn't reach AWS services (Secrets Manager, ECR)
  - **Solution**: Created NAT Gateway for private subnet internet access (Step 7a)
  - **Cost Impact**: +$32/month (total: ~$68/month)
- ✅ **Fixed Dual settings_secret Imports**:
  - **Error**: "ModuleNotFoundError: No module named 'StartupWebApp.settings_secret'"
  - **Root Cause**: settings.py imports settings_secret.py twice (lines 19 and 37)
  - **Fix**: Wrapped both imports in try/except ImportError blocks
  - **Why**: Production Docker image excludes settings_secret.py (.dockerignore), uses AWS Secrets Manager instead
- ✅ **Workflow Optimization During Debugging**:
  - Temporarily disabled test job (if: false) for faster debugging cycles
  - Re-enabled build-and-push job with dynamic image reference
  - Added explicit if condition to run-migrations: `if: always() && needs.build-and-push.result == 'success'`
  - Test job re-enabled after successful migration (commit: ca0c4d2)
- ✅ **MIGRATIONS SUCCESSFUL**:
  - Workflow run: 19711045190
  - Exit code: 0 (SUCCESS)
  - Database: startupwebapp_prod (57 tables created)
  - Duration: Build ~4 min, Migrations ~2.5 min, Total ~2m31s
  - ECS task successfully pulled image from ECR
  - ECS task fetched secrets from Secrets Manager
  - CloudWatch logs captured (log stream: migration/migration/{task-id})
  - All Django migrations applied cleanly

**Files Modified**:
- `.github/workflows/run-migrations.yml` - Fixed AWS wait command, added exit code validation, temporarily disabled test job for debugging, re-enabled test job after success (commits: 92000bf, dd1b282, 1df9d94, ca0c4d2)
- `StartupWebApp/StartupWebApp/settings.py` - Wrapped dual settings_secret imports in try/except blocks (lines 19 and 37)
- `StartupWebApp/functional_tests/base_functional_test.py` - Added Orderconfiguration fixtures

**Key Learnings**:
- CSRF/CORS configuration critical for cross-subdomain AJAX in tests
- Django 4.x requires explicit port numbers in CSRF_TRUSTED_ORIGINS
- Test fixtures should be self-contained (don't rely on manual database setup)
- AWS Fargate tasks in private subnets require NAT Gateway for internet/AWS service access
- Environment drift (Docker vs production) can hide infrastructure requirements
- Docker bind mounts overlay host files at runtime; production images only contain files from build context
- Must search entire file for all occurrences of problematic imports (settings.py had TWO settings_secret imports)
- GitHub Actions job dependencies require explicit `if: always()` conditions when upstream jobs are disabled

---

**Step 8: Run Migrations on All Databases** ✅ COMPLETE (November 26, 2025)

- ✅ **Critical Bug Discovered**: DATABASE_NAME not in base task definition
  - **Investigation**: Checked CloudWatch logs, saw "No migrations to apply" for healthtech/fintech
  - **Verification via Bastion**: Connected to RDS, found 0 tables in healthtech_experiment and fintech_experiment
  - **Root Cause Analysis**:
    - Base ECS task definition had no DATABASE_NAME environment variable
    - Workflow jq command only updated existing variables: `map(if .name == "DATABASE_NAME" then...)`
    - All 3 workflow runs defaulted to startupwebapp_prod (settings_production.py default)
    - First run (startupwebapp_prod): Connected correctly, ran migrations ✅
    - Second run (healthtech_experiment): Connected to startupwebapp_prod, saw migrations done, skipped ❌
    - Third run (fintech_experiment): Connected to startupwebapp_prod, saw migrations done, skipped ❌
- ✅ **Bug Fix Applied** (commit: f6de4fc)
  - Updated workflow jq logic to ADD DATABASE_NAME if missing:
    ```jq
    .containerDefinitions[0].environment |= (
      if any(.[]; .name == "DATABASE_NAME") then
        map(if .name == "DATABASE_NAME" then .value = $DB_NAME else . end)
      else
        . + [{"name": "DATABASE_NAME", "value": $DB_NAME}]
      end
    )
    ```
  - Changed from map() (update only) to conditional (update OR add)
- ✅ **Re-ran Migrations** (tests skipped for speed)
  - healthtech_experiment: Workflow run successful, migrations applied
  - fintech_experiment: Workflow run successful, migrations applied
  - CloudWatch logs confirmed: "Running migrations..." with "... OK" for all migrations
  - Duration: ~5-10 minutes per database (vs ~10-17 with tests)
- ✅ **Verification Complete**
  - Connected to RDS via bastion host
  - Ran `\dt` count on all 3 databases
  - **Results**: All 3 databases have 57 tables ✅
    - startupwebapp_prod: 57 tables
    - healthtech_experiment: 57 tables
    - fintech_experiment: 57 tables
  - Multi-tenant RDS fully operational for production and future forks

**Files Modified**:
- `.github/workflows/run-migrations.yml` - Fixed jq logic to add DATABASE_NAME (commit: f6de4fc)

**Key Learnings**:
- jq `map()` only updates existing array elements, doesn't add new ones
- Always verify task definition environment variables contain required fields
- "No migrations to apply" doesn't always mean success - verify which database connected to
- GitHub Actions input.skip_tests very useful for debugging iterations
- Multi-tenant requires explicit database selection, no safe defaults

---

**Phase 5.14 Summary** ✅ COMPLETE (November 26, 2025)

**Status**: 8/8 Core Steps Complete (Steps 9-10 are verification/completion)

**What Was Built:**
1. ✅ Multi-stage Dockerfile (development + production, 59% size reduction)
2. ✅ AWS ECR repository (startupwebapp-backend, image scanning enabled)
3. ✅ ECS Fargate cluster (startupwebapp-cluster, serverless containers)
4. ✅ ECS IAM roles (task execution + task roles with Secrets Manager access)
5. ✅ ECS task definition (startupwebapp-migration-task, 0.25 vCPU, 512MB)
6. ✅ GitHub Actions CI/CD workflow (test → build → push → migrate)
7. ✅ NAT Gateway (enables private subnet internet access, +$32/month)
8. ✅ Multi-tenant migrations (57 tables in all 3 databases)

**Key Achievements:**
- ✅ **CI/CD Pipeline Operational**: Fully automated deployment from GitHub to AWS ECS
- ✅ **Multi-Tenant RDS**: 3 databases successfully migrated (startupwebapp_prod, healthtech_experiment, fintech_experiment)
- ✅ **Infrastructure as Code**: All resources have create/destroy scripts (tested)
- ✅ **Security**: Private subnets, IAM roles, Secrets Manager, encrypted images
- ✅ **740 Tests in CI**: All tests pass before any deployment
- ✅ **CloudWatch Integration**: Full logging and monitoring

**Critical Bugs Found & Fixed:**
1. **Dual settings_secret imports** (Step 7b): settings.py imported settings_secret twice (lines 19 and 37) - fixed both
2. **DATABASE_NAME not added** (Step 8): Workflow jq only updated existing variables - fixed to add if missing

**Timeline:**
- Started: November 23, 2025
- Completed: November 26, 2025
- Duration: 4 days (multiple debugging iterations)
- Estimated: 6-7 hours → Actual: ~12-15 hours (due to debugging)

**Infrastructure Cost:**
- Base infrastructure (Phase 5.13): $36/month
- NAT Gateway: +$32/month
- ECR Storage: +$0.10/month
- **Total: ~$68/month**

**Success Metrics:**
- ✅ 16/16 Must-Have criteria complete
- ✅ 6/6 Should-Have criteria complete
- ✅ All 740 tests passing in CI
- ✅ All 3 databases have 57 tables
- ✅ Zero linting errors
- ✅ Zero security vulnerabilities

**Next Phase:**
- Phase 5.15: Full production deployment (ECS service, ALB, auto-scaling)
- Phase 5.16: Production hardening (WAF, monitoring, load testing)

---

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

#### Phase 5.15: Full Production Deployment (Complete - November 27 - December 4, 2025)

**Status**: ✅ COMPLETE - Full-stack production deployment live
**Branch**: `master` (auto-deploy enabled)

**Step 1: Application Load Balancer (ALB)** ✅ (November 27, 2025)
- ✅ Created `scripts/infra/create-alb.sh` and `destroy-alb.sh`
- ✅ ALB Security Group: `startupwebapp-alb-sg` (allows HTTP/HTTPS from internet)
- ✅ Target Group: `startupwebapp-tg` (port 8000, health check `/health`)
- ✅ Application Load Balancer: `startupwebapp-alb` (internet-facing)
- ✅ HTTP Listener: Port 80 → redirect to HTTPS (HTTP 301)
- ✅ Backend Security Group updated: Allow port 8000 from ALB
- ✅ Cost: ~$16/month (ALB fixed) + traffic-based charges

**Step 2: ACM Certificate** ✅ (November 27, 2025)
- ✅ Created `scripts/infra/create-acm-certificate.sh` and `destroy-acm-certificate.sh`
- ✅ Requested wildcard certificate: `*.mosaicmeshai.com`
- ✅ DNS validation via CNAME record in Namecheap
- ✅ Certificate status: ISSUED
- ✅ Cost: $0 (ACM certificates are free for AWS services)

**Step 3: HTTPS Listener** ✅ (November 28, 2025)
- ✅ Created `scripts/infra/create-alb-https-listener.sh` and `destroy-alb-https-listener.sh`
- ✅ HTTPS Listener on port 443 with TLS 1.2/1.3 termination
- ✅ SSL Policy: ELBSecurityPolicy-TLS13-1-2-2021-06
- ✅ Routes to target group on port 8000
- ✅ Full destroy/recreate cycle tested successfully

**Step 4: DNS Configuration** ✅ (November 28, 2025)
- ✅ Configured Namecheap CNAME: `startupwebapp-api` → ALB DNS name
- ✅ TTL: Automatic
- ✅ Verified via nslookup: `startupwebapp-api.mosaicmeshai.com` resolves to ALB

**Step 5: ECS Service Task Definition** ✅ (November 28, 2025)
- ✅ Created `scripts/infra/create-ecs-service-task-definition.sh` and `destroy-ecs-service-task-definition.sh`
- ✅ Task family: `startupwebapp-service-task`
- ✅ Configuration: 0.5 vCPU, 1 GB memory, port 8000
- ✅ Command: gunicorn with 3 workers, 30s timeout
- ✅ Health check: `curl -f http://localhost:8000/health`
- ✅ Secrets from AWS Secrets Manager (DATABASE_PASSWORD, DATABASE_USER, DATABASE_HOST, DATABASE_PORT)
- ✅ CloudWatch log group: `/ecs/startupwebapp-service`
- ✅ Full destroy/recreate cycle tested successfully
- ✅ Cost: ~$0.027/hour per task (~$39/month for 2 tasks)

**Files Created (Phase 5.15 Steps 1-5)**:
- `scripts/infra/create-alb.sh` - ALB, target group, HTTP listener, security groups
- `scripts/infra/destroy-alb.sh` - Clean teardown of ALB resources
- `scripts/infra/create-acm-certificate.sh` - Request ACM certificate with DNS validation
- `scripts/infra/destroy-acm-certificate.sh` - Delete ACM certificate
- `scripts/infra/create-alb-https-listener.sh` - HTTPS listener with TLS termination
- `scripts/infra/destroy-alb-https-listener.sh` - Remove HTTPS listener
- `scripts/infra/create-ecs-service-task-definition.sh` - Service task definition for gunicorn
- `scripts/infra/destroy-ecs-service-task-definition.sh` - Deregister service task definition

**Files Modified**:
- `scripts/infra/aws-resources.env.template` - Added ALB, ACM, service task definition fields
- `scripts/infra/status.sh` - Added Phase 5.15 status sections
- `scripts/infra/show-resources.sh` - Added ALB, ACM, service task definition display
- `scripts/infra/README.md` - Updated with Phase 5.15 progress and new script documentation

**Resources Created**:
- ALB: `startupwebapp-alb` (DNS: startupwebapp-alb-978036304.us-east-1.elb.amazonaws.com)
- ALB Security Group: `sg-07bb8f82ec378f6d4`
- Target Group: `startupwebapp-tg`
- ACM Certificate: `*.mosaicmeshai.com` (arn:aws:acm:us-east-1:853463362083:certificate/51913dd1-b907-49cd-bd0e-4b04218c4d30)
- Service Task Definition: `startupwebapp-service-task:2`
- CloudWatch Log Group: `/ecs/startupwebapp-service`

**Infrastructure Cost Update**:
- Previous (Phase 5.14): $68/month
- ALB: +$16/month
- **Current Total: ~$84/month**

**Step 6: Create ECS Service** ✅ (November 28, 2025 - December 3, 2025)
- ✅ Created `scripts/infra/create-ecs-service.sh` and `destroy-ecs-service.sh`
- ✅ Deployed 2 Fargate tasks across 2 AZs for high availability
- ✅ Connected to ALB target group
- ✅ Created PR validation workflow (`.github/workflows/pr-validation.yml`)
- ✅ Created production deployment workflow (`.github/workflows/deploy-production.yml`)

**Step 6b: ALB Health Check Debugging & Fixes** ✅ (December 2-3, 2025)

**Initial Deployment Issues** (December 2, 2025):
- Health checks failing with 301 redirect and 400 errors
- Required destroy/recreate cycle to apply Django fixes

**PR #40: ALB Health Check Fixes** ✅ (December 3, 2025)
- Created bugfix branch, identified 3 root causes, merged to master
- **Root Cause 1**: Missing `SECURE_PROXY_SSL_HEADER` - Django didn't trust ALB's X-Forwarded-Proto header
  - Fix: Added `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` to settings_production.py
- **Root Cause 2**: `ALLOWED_HOSTS` didn't include container IPs - ALB health checks use private IP as Host header
  - Fix: Added ECS metadata IP fetching function to dynamically add container IP to ALLOWED_HOSTS
- **Root Cause 3**: Health check path missing trailing slash - `/order/products` vs `/order/products/`
  - Fix: Updated all infra scripts to use `/order/products/` with trailing slash

**Infrastructure Recreated** (December 3, 2025):
- Destroyed ALB, ECS service, task definition (kept ACM certificate, ECR, ECS cluster, RDS)
- Merged PR #40 to master (auto-deploy built new Docker image with fixes)
- Recreated: ALB, HTTPS listener, service task definition, ECS service
- New ALB DNS: `startupwebapp-alb-102070760.us-east-1.elb.amazonaws.com`
- Updated Namecheap DNS CNAME

**Health Check Still Failing - Additional Fixes Required** (December 3, 2025):

**Root Cause 4: SSL Redirect on Health Checks** (Fixed)
- After infrastructure recreation, health checks returned 301 redirects
- ALB health checks bypass HTTPS listener entirely
  - User traffic: User → ALB (443) → Container (8000) with `X-Forwarded-Proto: https` header
  - Health checks: ALB → Container (8000) directly over HTTP, NO `X-Forwarded-Proto` header
  - Django's `SECURE_SSL_REDIRECT` redirects health check requests to HTTPS
- **Fix Applied**: Added `SECURE_REDIRECT_EXEMPT` to settings_production.py

**Root Cause 5: Trailing Slash Mismatch** (Fixed)
- After SSL redirect fix deployed, health checks returned 404 errors
- Investigation revealed Django URL pattern mismatch:
  - URL pattern in `order/urls.py`: `path('products', ...)` - NO trailing slash
  - Health check path: `/order/products/` - WITH trailing slash
  - Django's `APPEND_SLASH` only redirects if URL WITH slash exists (it doesn't)
- **Original assumption was wrong**: We added trailing slash thinking `APPEND_SLASH` would redirect, but 301s were actually from `SECURE_SSL_REDIRECT`, not `APPEND_SLASH`
- **Fix Applied**:
  - Changed health check path to `/order/products` (no trailing slash)
  - Updated `SECURE_REDIRECT_EXEMPT` regex to `r'^order/products$'`
  - Updated all infra scripts for consistency

**Also Fixed**: AWS CLI tags syntax in `create-ecs-service-task-definition.sh`
- Tags must be comma-separated, not space-separated
- Changed from `--tags Key1=Val1 Key2=Val2` to `--tags "Key1=Val1,Key2=Val2"`

**Commits**:
- PR #40 merge: `e35ed31` - Initial health check fixes (root causes 1-3)
- Direct to master: `21f53ca` - SECURE_REDIRECT_EXEMPT fix (root cause 4)
- Direct to master: `2f36dcd` - Trailing slash fix (root cause 5)

**Production Verified Working** (December 3, 2025):
- `https://startupwebapp-api.mosaicmeshai.com/order/products` returns HTTP 200
- 4 healthy ECS tasks across 2 AZs (us-east-1a, us-east-1b)
- ALB DNS: `startupwebapp-alb-1304349275.us-east-1.elb.amazonaws.com`
- Namecheap CNAME configured for `startupwebapp-api.mosaicmeshai.com`

**Step 6b: ECS Auto-Scaling** ✅ (December 3, 2025)
- ✅ Created `scripts/infra/create-ecs-autoscaling.sh` and `destroy-ecs-autoscaling.sh`
- ✅ Registered ECS service as scalable target with Application Auto Scaling
- ✅ Configuration:
  - Minimum tasks: 1 (cost optimization for low traffic)
  - Maximum tasks: 4 (handle traffic spikes)
  - CPU target: 70% utilization (scale out when exceeded)
  - Memory target: 80% utilization (scale out when exceeded)
  - Scale-out cooldown: 60 seconds (respond quickly to load)
  - Scale-in cooldown: 300 seconds (prevent flapping)
- ✅ CloudWatch alarms auto-created for target tracking:
  - AlarmHigh: Triggers scale-out when metric exceeds target
  - AlarmLow: Triggers scale-in when metric below target for sustained period
- ✅ Full destroy/recreate cycle tested successfully
- ✅ Auto-scaling already active: scaled from 2 → 1 task due to low traffic
- ✅ Cost impact: $20-78/month depending on traffic (vs fixed $78/month for 4 tasks)

**Files Created**:
- `scripts/infra/create-ecs-autoscaling.sh` - Register scalable target, create CPU/memory policies
- `scripts/infra/destroy-ecs-autoscaling.sh` - Delete policies, deregister scalable target

**Files Modified**:
- `scripts/infra/aws-resources.env.template` - Added auto-scaling fields
- `scripts/infra/status.sh` - Added auto-scaling status section
- `scripts/infra/show-resources.sh` - Added auto-scaling display with recent activity

**Steps 8-10 Complete**:
- Step 8: Health endpoint using `/order/products` (validates Django + database)
- Step 9: CI/CD workflows created (pr-validation.yml, deploy-production.yml, rollback-production.yml)
- Step 10: Django production settings configured (settings_production.py)

**Step 7: S3 + CloudFront Frontend Hosting** ✅ (December 3-4, 2025)
- ✅ Created `scripts/infra/create-frontend-hosting.sh` and `destroy-frontend-hosting.sh`
- ✅ S3 bucket created: `startupwebapp-frontend-production`
- ✅ CloudFront distribution created: `E1HZ3V09L2NDK1`
- ✅ CloudFront domain: `d34ongxkfo84gr.cloudfront.net`
- ✅ Origin Access Control (OAC) configured for secure S3 access
- ✅ DNS CNAME configured in Namecheap: `startupwebapp` → CloudFront
- ✅ Frontend deploy workflow created: `.github/workflows/deploy-production.yml` (client-side repo)
- ✅ Frontend deployment tested via manual workflow trigger
- ✅ Frontend loads at `https://startupwebapp.mosaicmeshai.com`
- ✅ **CORS fix deployed** - PR #41 merged December 4, 2025

**CORS Fix Applied** (PR #41):
- File: `StartupWebApp/StartupWebApp/settings_production.py`
- Added `https://startupwebapp.mosaicmeshai.com` to `CORS_ORIGIN_WHITELIST`
- Added frontend domain to `CSRF_TRUSTED_ORIGINS`
- Added `CORS_ALLOW_CREDENTIALS = True`

**Frontend Repo Changes Made**:
- Added `.github/workflows/deploy-production.yml` - S3 deployment workflow
- Updated `js/index-0.0.2.js` - Added production API URL case
- Committed `package.json`, `package-lock.json`, `eslint.config.js` to git
- Updated `.gitignore` to track npm config files

**PR #42: Deploy Workflow Health Check Fix** ✅ (December 4, 2025)
- Fixed deploy workflow to use correct health check endpoint
- Updated documentation for Step 7 completion

**Step 11: Seed Data Migrations** ✅ (December 4, 2025)

**PR #43: Seed Data Migrations (fixes 500 error)** ✅ (December 4, 2025)
- **Root Cause**: `/user/logged-in` returning 500 because `ClientEventConfiguration.objects.get(id=1)` fails when table is empty
- **Solution**: Created data migrations to automatically seed required reference data
- **Migrations Created**:
  - `clientevent/0002_seed_configuration.py` - **CRITICAL** (fixes 500 error)
  - `user/0002_seed_user_data.py` - Auth groups, Terms of Use, Email templates
  - `order/0004_seed_order_data.py` - Order config, products, shipping methods
- **Features**:
  - Uses `get_or_create` for idempotency (safe to run multiple times)
  - Skips during test runs (tests create their own data)
  - Based on `db_inserts.sql` and `load_sample_data.py`
- **Documentation**:
  - Updated `README.md` with "Seed Data & Data Migrations" section
  - Created `docs/technical-notes/2025-12-04-seed-data-migrations.md`
- **Result**: `/user/logged-in` now returns HTTP 200

**Phase 5.15 Complete** ✅ (December 4, 2025)

---

#### Phase 5.16: Production Superuser & Django Admin (Complete - December 7, 2025)

**Status**: ✅ COMPLETE - Django Admin fully operational with CSS
**Branch**: `master` (auto-deploy enabled)
**PRs**: #45 (superuser), #46 (WhiteNoise), #47 (hotfix)

**Problem Solved**:
- No superuser existed in production database
- Could not access Django Admin interface at `/admin/`
- Django Admin lacked CSS styling when initially accessed

**Solution Implemented (TDD Approach)**:

**PR #45: Production Superuser Creation** (December 7, 2025)
- ✅ **Unit Tests** (`user/tests/test_superuser_creation.py`): 3 tests
  - Test `createsuperuser --noinput` with environment variables
  - Test idempotency (duplicate username fails gracefully)
  - Test unusable password when DJANGO_SUPERUSER_PASSWORD missing
- ✅ **Functional Tests** (`functional_tests/test_django_admin_login.py`): 3 tests
  - Test superuser can login to Django Admin
  - Test wrong password rejection
  - Test non-staff users cannot access admin
  - **Regression prevention**: Catches CSRF cookie domain issues
- ✅ **Static Files Configuration**:
  - Added `STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')`
  - Updated `.gitignore` to exclude `**/staticfiles/`
  - Fixes TypeError exceptions in functional tests
- ✅ **Infrastructure as Code**:
  - Updated `scripts/infra/create-secrets.sh` to include superuser fields
  - Prompts for username, email, password during secret creation
  - Added superuser credentials to existing AWS secret via one-time CLI script
- ✅ **GitHub Actions Workflow**: `.github/workflows/run-admin-command.yml`
  - Manual workflow for running Django admin commands
  - Supports: `createsuperuser`, `collectstatic`
  - Database selection: startupwebapp_prod, healthtech_experiment, fintech_experiment
  - Fetches credentials from AWS Secrets Manager
  - Runs as ECS Fargate task (same pattern as migrations)
  - CloudWatch logging
- ✅ **IAM Permissions**: Updated `github-actions-startupwebapp` user
  - Added `secretsmanager:GetSecretValue` permission
  - Added `secretsmanager:DescribeSecret` permission
- ✅ **Superuser Created**: `prod-admin` (bart@mosaicmeshai.com)
  - 16-character password (LastPass generated)
  - Login verified successfully

**PR #46: WhiteNoise for Django Admin Static Files** (December 7, 2025)
- ✅ **Added WhiteNoise**: Industry-standard Python static file serving
  - `requirements.txt`: whitenoise==6.7.0
  - `settings.py`: WhiteNoiseMiddleware (after SecurityMiddleware)
  - `settings.py`: CompressedManifestStaticFilesStorage (compression + caching)
  - Works with any WSGI app (not Django-specific)
  - Compression: gzip/Brotli, far-future cache headers, CDN-friendly
- ✅ **Dockerfile Updates**:
  - Set `DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production` before collectstatic
  - Run collectstatic during Docker build with DJANGO_SECRET_KEY fallback
  - Collects 129 admin static files into image
- ✅ **Workflow Updates**:
  - `pr-validation.yml`: Added collectstatic step before functional tests
  - `deploy-production.yml`: Added collectstatic step before functional tests
  - Prevents "Missing staticfiles manifest entry" errors

**Hotfixes** (December 7, 2025):
- ✅ Fixed deploy-production workflow to explicitly set `migrate` command
  - Prevents command pollution from run-admin-command workflow
  - ECS task definitions persist commands between revisions
- ✅ Fixed Dockerfile collectstatic SECRET_KEY issue
  - Settings_production.py fallback mechanism uses DJANGO_SECRET_KEY env var
  - Build-time dummy key for collectstatic only

**Production Verification**:
- ✅ Django Admin URL: https://startupwebapp-api.mosaicmeshai.com/admin/
- ✅ Login: `prod-admin` with LastPass password
- ✅ Full CSS styling present (WhiteNoise serving static files)
- ✅ All admin functionality operational
- ✅ All 746 tests passing (715 unit + 31 functional)

**Key Learnings**:
- Shell escaping: Special chars in passwords escaped via `docker-compose exec -e`
- ECS task definitions: Command persists between revisions, must set explicitly
- WhiteNoise: CompressedManifestStaticFilesStorage requires collectstatic for manifest
- CloudWatch logs: Actual stream name is `migration/migration/{TASK_ID}` (double prefix)

**Documentation**:
- Technical note: `docs/technical-notes/2025-12-04-production-admin-commands.md`
- Test coverage for Django Admin prevents future regressions

---
- All 11 steps complete
- Full-stack production deployment live and operational
- Backend: `https://startupwebapp-api.mosaicmeshai.com`
- Frontend: `https://startupwebapp.mosaicmeshai.com`

**Infrastructure Cost Update**:
- Previous (fixed 2 tasks): ~$118/month
- With auto-scaling (1 task at low traffic): ~$98/month
- Savings: ~$20/month (17% reduction) during low traffic periods

**Future Task: URL Pattern Standardization**
- All Django URL patterns should consistently use trailing slashes
- This is a codebase-wide refactor to be done separately
- Will make `APPEND_SLASH` work correctly and follow Django conventions

See [Technical Note](technical-notes/2025-11-26-phase-5-15-production-deployment.md) for full implementation plan.

#### Django 5.2 LTS Upgrade (HIGH PRIORITY - Q1 2026)

**Current**: Django 4.2.16 LTS (support ends April 2026)
**Target**: Django 5.2 LTS (released April 2, 2025, supported until April 2028)
**Timeline**: ~4 months remaining until Django 4.2 EOL

**Why Upgrade?**
- Security patches for Django 4.2 end April 2026
- Django 5.2 LTS provides 3 more years of support
- Django 6.0 is NOT LTS (skip it, wait for 8.2 LTS in ~2027)

**Recommended Approach**:
- Start planning: January 2026
- Complete upgrade: By March 2026
- Use same TDD methodology as Django 4.2 upgrade (incremental steps)
- Reference: Previous upgrade took 6 steps, well-documented process

**Priority**: HIGH - Cannot run unsupported Django in production

---

#### Phase 5.16 Stripe Upgrade - Session 2: Library Upgrade (Complete - December 11, 2025)

**Status**: ✅ COMPLETE - Stripe library upgraded successfully
**Branch**: `feature/stripe-upgrade-library`
**Session**: 2 of 10 (Stripe upgrade multi-session project)

**Changes Made**:
- ✅ **Stripe Library Upgrade**: `stripe==5.5.0` → `stripe==14.0.1` (latest stable)
  - Jumped from 2023 version to November 2025 release
  - Reviewed breaking changes (v6-v14): No code changes needed
  - Our code already uses keyword arguments (compatible with v8+ requirements)
- ✅ **Docker Configuration Fix**: Added `target: development` to docker-compose.yml
  - Issue: Multi-stage Dockerfile defaulted to production stage (no geckodriver)
  - Root cause: Configuration gap from Phase 5.14 (missed during production deployment work)
  - Fix enables functional tests to run in local development
  - Production deployment unaffected (explicitly uses `--target production`)

**Test Results**:
- ✅ **Linting**: Zero errors (excluding gitignored settings_secret.py)
- ✅ **Unit Tests**: 715/715 passed
- ✅ **Functional Tests**: 30/31 passed (1 failure unrelated to Stripe - email address from other branch)
- ✅ All Stripe-related tests passing with new library version

**Key Findings**:
- Stripe test coverage: 27 mocked Stripe API calls across 5 test files
- APIs tested: `Customer.create()`, `Customer.retrieve()`, `Customer.modify()`
- Tests use mocks, so real Stripe API validation happens in later sessions
- No deprecated API calls found in codebase (already using modern patterns)

**Files Modified**:
- `requirements.txt` (line 18)
- `docker-compose.yml` (line 13)

**Next Session**: Session 3 - Create Checkout Session endpoint

**See**: `docs/technical-notes/2025-12-11-stripe-upgrade-plan.md` for full 10-session plan

---

#### Phase 5.16 Stripe Upgrade - Session 3: Create Checkout Session Endpoint (Complete - December 12, 2025)

**Status**: ✅ COMPLETE - Backend endpoint ready for Stripe Checkout Sessions
**Branch**: `feature/stripe-checkout-session-endpoint`
**PR**: #50 (pending)
**Session**: 3 of 10 (Stripe upgrade multi-session project)

**Changes Made**:
- ✅ **New Endpoint**: `/order/create-checkout-session` (POST)
  - Creates Stripe Checkout Session with cart line items
  - Returns `session_id` and `checkout_url` for frontend redirect
  - Handles both authenticated members (with email) and anonymous users
  - Calculates line items with prices in cents (Stripe requirement)
  - Uses `ENVIRONMENT_DOMAIN` setting for success/cancel URLs
  - Comprehensive error handling (no cart, empty cart, Stripe API errors)

- ✅ **Implementation Details**:
  - Uses `stripe.checkout.Session.create()` with modern API
  - Line items include product name, description (color/size), image URL, price, quantity
  - Member emails pre-filled, anonymous users prompted by Stripe
  - Success URL: `{domain}/checkout/success?session_id={CHECKOUT_SESSION_ID}`
  - Cancel URL: `{domain}/checkout/confirm`

- ✅ **Test Coverage**: 7 new comprehensive unit tests
  - Checkout not allowed (permission check)
  - Cart not found (user has no cart)
  - Cart is empty (no items)
  - Success for authenticated member (with email pre-fill)
  - Success without email (anonymous flow)
  - Stripe API error handling
  - Multiple line items calculation

**Test Results**:
- ✅ **Unit Tests**: 722/722 passed (715 → 722, +7 new tests)
- ✅ **Test Approach**: TDD methodology (tests written first)
- ✅ All Stripe calls mocked (real API testing in Session 8)
- ✅ Zero linting errors

**Files Modified**:
- `StartupWebApp/order/views.py` - New `create_checkout_session()` function
- `StartupWebApp/order/urls.py` - Added route for new endpoint
- `StartupWebApp/order/tests/test_stripe_checkout_session.py` - New test file (7 tests)
- `docs/technical-notes/2025-12-11-stripe-upgrade-plan.md` - Added to branch

**Next Session**: Session 4 - Create success handler endpoint to process completed payments

**Note**: Functional tests deferred to Session 8 (requires frontend integration from Sessions 6-7)

**See**: `docs/technical-notes/2025-12-11-stripe-upgrade-plan.md` for full 10-session plan

---

#### Phase 5.16 Stripe Upgrade - Session 4: Checkout Session Success Handler (Complete - December 12, 2025)

**Status**: ✅ COMPLETE - Backend success handler ready for order creation
**Branch**: `feature/stripe-checkout-success-handler`
**PR**: #51 (pending)
**Session**: 4 of 10 (Stripe upgrade multi-session project)

**Changes Made**:
- ✅ **New Endpoint**: `/order/checkout-session-success` (GET)
  - Retrieves completed Stripe Checkout Session by `session_id` query parameter
  - Verifies payment status is `paid` before creating order
  - Extracts shipping and billing addresses from Stripe session
  - Creates complete Order with all related objects (OrderSku, OrderStatus, OrderShippingMethod, OrderDiscount)
  - Sends order confirmation email (member or prospect flow)
  - Deletes cart after successful order creation
  - Prevents duplicate orders using `stripe_payment_intent_id` unique constraint

- ✅ **Database Migration**: Added `stripe_payment_intent_id` field to OrderPayment model
  - Enables idempotent order creation (prevents duplicates if user refreshes page)
  - Unique constraint ensures one order per Stripe payment
  - Migration: `order/migrations/0005_orderpayment_stripe_payment_intent_id.py`

- ✅ **Updated Checkout Session Creation**: Added address collection
  - `billing_address_collection: 'required'`
  - `shipping_address_collection: {'allowed_countries': ['US', 'CA']}`
  - `phone_number_collection: {'enabled': True}`
  - Ensures Stripe collects all required data before redirecting back

- ✅ **Test Coverage**: 7 new comprehensive unit tests (TDD approach)
  - Requires `session_id` parameter
  - Handles invalid session ID
  - Requires payment completed status
  - Creates order for authenticated member
  - Creates order for anonymous prospect (with prospect creation)
  - Handles cart not found error
  - Prevents duplicate orders (idempotent behavior)

**Test Results**:
- ✅ **Unit Tests**: 729/729 passed (722 → 729, +7 new tests)
- ✅ **Test Approach**: TDD methodology (tests written first, saw them fail, then implemented)
- ✅ All Stripe `Session.retrieve()` calls mocked
- ✅ Email sending mocked to verify confirmation emails sent
- ✅ Zero linting errors

**Files Modified**:
- `StartupWebApp/order/models.py` - Added `stripe_payment_intent_id` field to Orderpayment
- `StartupWebApp/order/views.py` - New `checkout_session_success()` function (344 lines)
- `StartupWebApp/order/views.py` - Updated `create_checkout_session()` to collect addresses
- `StartupWebApp/order/urls.py` - Added route for success handler
- `StartupWebApp/order/migrations/0005_orderpayment_stripe_payment_intent_id.py` - New migration
- `StartupWebApp/order/tests/test_checkout_session_success.py` - New test file (7 tests, 417 lines)

**Implementation Highlights**:
- Complete order creation flow mirrors existing `confirm_place_order()` function
- Handles both member and prospect email confirmation flows
- Extracts customer name, email, and addresses from Stripe session objects
- Creates Prospect records automatically for anonymous checkouts
- Supports all existing order features (discounts, shipping methods, order status)

**Next Session**: Session 5 - Create webhook handler for `checkout.session.completed` events

**Note**: This endpoint will be called by frontend after Stripe redirects user with `session_id` parameter

**See**: `docs/technical-notes/2025-12-11-stripe-upgrade-plan.md` for full 10-session plan

---

#### Phase 5.16 Stripe Upgrade - Session 5: Stripe Webhook Handler (Complete - December 13, 2025)

**Status**: ✅ COMPLETE - Webhook handler provides production reliability
**Branch**: `feature/stripe-webhooks`
**PR**: #52 (pending)
**Session**: 5 of 10 (Stripe upgrade multi-session project)

**Changes Made**:
- ✅ **New Endpoint**: `/order/stripe-webhook` (POST) with `@csrf_exempt`
  - Verifies webhook signatures using `stripe.Webhook.construct_event()`
  - Handles `checkout.session.completed` event (creates orders if webhook arrives first)
  - Handles `checkout.session.expired` event (logging only)
  - Returns 200 for unknown event types (graceful handling)
  - Provides backup order creation if user closes browser before success redirect completes

- ✅ **Signature Verification**: Cryptographic security
  - Uses `STRIPE_WEBHOOK_SECRET` from settings (more secure than CSRF tokens)
  - Validates entire payload integrity
  - Returns 400 for invalid signatures or malformed JSON
  - Prevents malicious webhook injection attacks

- ✅ **Order Creation Logic**: Reuses checkout session success handler patterns
  - Idempotent: Checks for existing orders via `stripe_payment_intent_id`
  - Retrieves cart using `cart_id` from session metadata
  - Creates complete Order with all related objects
  - Sends order confirmation emails (member or prospect flow)
  - Deletes cart after successful creation
  - Helper function `send_order_confirmation_email()` extracted for reuse

- ✅ **Enhanced Checkout Session**: Added metadata for webhook handler
  - Stores `cart_id` in session metadata for webhook access
  - Enables webhook to process orders independently of browser session
  - Critical for production reliability (handles network failures, browser closes, etc.)

- ✅ **Test Coverage**: 6 new comprehensive unit tests (TDD approach)
  - Rejects invalid webhook signatures (400 error)
  - Handles malformed JSON gracefully (400 error)
  - Handles existing orders (idempotent, returns order identifier)
  - Handles expired sessions (logging only, 200 response)
  - Handles unknown event types (logging only, 200 response)
  - Creates orders for completed sessions (full order creation workflow)

**Test Results**:
- ✅ **Unit Tests**: 735/735 passed (729 → 735, +6 new webhook tests)
- ✅ **Test Approach**: TDD methodology (wrote tests first, saw failures, then implemented)
- ✅ All Stripe `Webhook.construct_event()` calls mocked with dictionary-style event objects
- ✅ Email sending mocked to verify confirmation emails sent
- ✅ Zero linting errors (fixed unused imports and variables)

**Files Modified**:
- `StartupWebApp/order/views.py` - New `stripe_webhook()`, `handle_checkout_session_completed()`, `handle_checkout_session_expired()`, `send_order_confirmation_email()` functions (~350 lines)
- `StartupWebApp/order/views.py` - Updated `create_checkout_session()` to include `cart_id` in metadata
- `StartupWebApp/order/urls.py` - Added route for webhook endpoint
- `StartupWebApp/StartupWebApp/settings_secret.py` - Added `STRIPE_WEBHOOK_SECRET` setting
- `StartupWebApp/order/tests/test_stripe_webhook.py` - New test file (6 tests, 425 lines)

**Implementation Highlights**:
- **Security**: `@csrf_exempt` required for webhooks, but signature verification provides stronger security
- **Reliability**: Webhooks ensure orders created even if user doesn't complete redirect
- **Idempotency**: Both success handler AND webhook check for existing orders (prevents duplicates)
- **Code Reuse**: Extracted email helper function used by both success handler and webhook
- **Error Handling**: Returns 500 if `STRIPE_WEBHOOK_SECRET` not configured (prevents silent failures)

**Next Session**: Session 6 - Update frontend checkout flow to use new Stripe Checkout Sessions

**Production Note**: Webhook secret will be configured in AWS Secrets Manager during Session 9

**See**: `docs/technical-notes/2025-12-11-stripe-upgrade-plan.md` for full 10-session plan

---

#### Phase 5.16 Stripe Upgrade - Session 6: Frontend Checkout Migration (Complete - December 15, 2025)

**Status**: ✅ COMPLETE - Frontend checkout fully migrated to Stripe Checkout Sessions
**Frontend Branch**: `feature/stripe-frontend-checkout`
**Backend Branch**: `feature/stripe-backend-image-url-fix`
**Frontend PR**: #12 (merged to master)
**Backend PR**: #53 (merged to master)
**Session**: 6 of 10 (Stripe upgrade multi-session project)

**Changes Made**:

**Frontend Repository (`startup_web_app_client_side`):**
- ✅ **Replaced Deprecated Stripe v2 with v3**:
  - Removed: `checkout.stripe.com/checkout.js` (deprecated)
  - Added: `js.stripe.com/v3/` (modern Stripe.js library)
  - Updated: Stripe publishable key initialization

- ✅ **New Checkout Flow Functions** (`js/checkout/confirm-0.0.1.js`):
  - `create_stripe_checkout_session()`: Calls backend `/order/create-checkout-session`
  - `handle_checkout_session_success()`: Processes Stripe redirect with `session_id`
  - Redirects to Stripe hosted checkout page (replaces inline Stripe modal)

- ✅ **Checkout Success Page** (`checkout/success`):
  - New page displays order confirmation after successful payment
  - Shows order number, items purchased, total amount, shipping address
  - Handles both member and anonymous checkout flows
  - Calls backend `/order/checkout-session-success` to retrieve order details

- ✅ **Bug Fixes**: Fixed 9 bugs discovered during testing
  1. Decimal parsing: Added `parseFloat()` on price/shipping fields (7 locations)
  2. Missing error display: Added error message div to checkout confirm page
  3. Cart quantity selector: Fixed event handler to update cart properly

- ✅ **Test Coverage**: 13 new QUnit unit tests
  - 10 Stripe tests (create session, handle success, error cases)
  - 3 decimal parsing tests (regression prevention)
  - All tests pass in headless browser

**Backend Repository (`startup_web_app_server_side`):**
- ✅ **Image URL Fix**: Added domain prefix to product image URLs for Stripe
  - Fixed: Stripe "url_invalid" error on relative URLs
  - Changed: `/img/product/...` → `https://domain.com/img/product/...`
  - Uses `ENVIRONMENT_DOMAIN` setting to construct absolute URLs
  - Product images now display correctly on Stripe checkout page

**Test Results**:
- ✅ **Frontend**: 13 QUnit tests passing, ESLint 0 errors (2 warnings acceptable)
- ✅ **Backend**: 737/737 unit tests passing (+2 new tests for image URL fix)
- ✅ **Manual Testing**: Complete checkout flow tested end-to-end in production
  - Test card (4242 4242 4242 4242) processes successfully
  - Order created correctly in database
  - Confirmation email sent
  - Success page displays order details

**Files Modified (Frontend)**:
- `checkout/confirm` - Updated to use new Stripe v3 API
- `checkout/success` - New page for order confirmation
- `js/checkout/confirm-0.0.1.js` - New checkout functions, decimal parsing fixes
- `js/checkout/success-0.0.1.js` - New success page handler
- `unittests/checkout_confirm_tests.html` - New test file
- `unittests/js/checkout_confirm_tests.js` - 13 new tests

**Files Modified (Backend)**:
- `StartupWebApp/order/views.py` - Image URL fix in `create_checkout_session()`
- `StartupWebApp/order/tests/test_stripe_checkout_session.py` - 2 new tests for absolute URLs

**Implementation Highlights**:
- **User Experience**: Clean redirect to Stripe hosted checkout (no inline modal)
- **Security**: PCI compliance simplified (Stripe handles all payment details)
- **Reliability**: Checkout tested with real Stripe test mode in production
- **Mobile Optimized**: Stripe's hosted checkout is fully responsive
- **Email Confirmation**: Works for both member and anonymous checkouts

**Known Issues Fixed During Session**:
- Decimal parsing bugs in price/shipping calculations (7 locations)
- Missing error message container on checkout page
- Cart quantity update event handler binding
- Relative image URLs causing Stripe validation errors

**Production Deployment**:
- ✅ Frontend PR #12 merged and deployed to S3/CloudFront
- ✅ Backend PR #53 merged and deployed to ECS
- ✅ End-to-end checkout tested in production with test cards
- ✅ Order confirmation emails sending correctly

**Next Session**: Session 6.5 - Add PR validation workflow to frontend repository

**Note**: This completes the core Stripe Checkout Sessions migration. Sessions 7-9 will add account payment history and production testing.

**See**: `docs/technical-notes/2025-12-11-stripe-upgrade-plan.md` for full 10-session plan

---

#### Phase 5.16 Stripe Upgrade - Session 6.5: Frontend PR Validation Workflow (Complete - December 16, 2025)

**Status**: ✅ COMPLETE - Frontend now has automated PR validation matching backend standards
**Branch**: `feature/frontend-pr-validation`
**PR**: #13 (merged to master)
**Session**: 6.5 of 10 (Stripe upgrade multi-session project)

**Context**: During Session 6 review, discovered frontend repository lacked automated PR validation. Backend has comprehensive `pr-validation.yml` workflow running 737 tests on every PR, but frontend PRs were merging without automated checks. This created inconsistency and risk.

**Changes Made**:

**Frontend Repository (`startup_web_app_client_side`):**
- ✅ **GitHub Actions Workflow** (`.github/workflows/pr-validation.yml`):
  - Runs ESLint on all JavaScript files (currently 0 errors, 2 warnings)
  - Runs 88 QUnit tests in headless Chromium browser via Playwright
  - Tests both test suites:
    - `checkout_confirm_tests.html` (19 tests)
    - `index_tests.html` (69 tests)
  - Fails PR if any linting errors or test failures occur
  - Uses Node.js 20.x (modern LTS version)
  - 10-minute timeout (tests run in ~2 seconds locally, 45 seconds in CI)

- ✅ **Playwright Test Infrastructure**:
  - `playwright.config.js`: Configuration for headless browser testing
  - `playwright-tests/qunit.spec.js`: Test runner that loads QUnit HTML pages
  - Validates QUnit results programmatically (checks for failures)
  - Provides detailed error output if tests fail
  - Uses Chromium only (sufficient for jQuery + QUnit testing)

- ✅ **Package Updates**:
  - Added `@playwright/test` (^1.48.0) for headless browser testing
  - Added `http-server` (^14.1.1) for local test server
  - New npm scripts:
    - `npm test`: Run tests in headless browser
    - `npm run test:headed`: Run with visible browser (debugging)

- ✅ **Documentation Updates**:
  - Added PR Validation workflow badge to README.md
  - Updated test counts (88 total tests: 19 checkout + 69 utility)
  - Added CI/CD testing instructions
  - Documented Playwright test commands

- ✅ **Configuration Updates**:
  - Updated `.gitignore` for Playwright artifacts (test-results/, playwright-report/)

**Test Results**:
- ✅ **PR Validation**: All checks passed on PR #13
  - ESLint: PASSED (0 errors, 2 warnings)
  - QUnit Tests: PASSED (88/88 tests)
  - Workflow runtime: 45 seconds
- ✅ **Local Testing**: All 88 tests pass in ~2 seconds

**Files Created/Modified**:
- `.github/workflows/pr-validation.yml` - New workflow (84 lines)
- `playwright.config.js` - New Playwright configuration
- `playwright-tests/qunit.spec.js` - New test runner (53 lines)
- `package.json` - Added test scripts and dependencies
- `package-lock.json` - Dependency lock file updated
- `.gitignore` - Added Playwright exclusions
- `README.md` - Added badge and testing documentation

**Implementation Highlights**:
- **Consistency**: Frontend now matches backend's automated PR validation standards
- **Quality Gates**: All future PRs must pass 88 tests + ESLint before merging
- **Modern Tooling**: Playwright chosen over Puppeteer for better reliability
- **Fast Execution**: Tests complete in under 1 minute in CI
- **Zero Disruption**: No changes to existing code, only CI/CD additions

**Comparison with Backend PR Validation**:
| Aspect | Backend | Frontend (After Session 6.5) |
|--------|---------|------------------------------|
| Workflow | `.github/workflows/pr-validation.yml` | `.github/workflows/pr-validation.yml` |
| Linting | Flake8 (Python) | ESLint (JavaScript) |
| Unit Tests | 737 tests (pytest) | 88 tests (QUnit + Playwright) |
| Functional Tests | 28 tests (Selenium + Firefox) | N/A (frontend is static) |
| Runtime | ~10-15 minutes | ~45 seconds |
| Test Coverage | 100% of code tested | ~20% of files (4/20 JS files) |

**Impact**:
- **Quality Assurance**: Prevents broken JavaScript from reaching master
- **Regression Prevention**: 88 tests catch breaking changes automatically
- **Developer Confidence**: PRs can merge knowing tests passed
- **Future Growth**: Easy to add more tests as coverage expands

**See**: `docs/technical-notes/2025-12-11-stripe-upgrade-plan.md` for full multi-session plan

---

### **Phase 5.16 - Session 8: Dead Code Cleanup + Selenium Upgrade** ✅ (December 18, 2025)

**Branch**: `feature/stripe-cleanup-dead-code` (merged to master via PR #54)
**Duration**: ~4 hours

**Milestone**: Removed all deprecated Stripe v2 code and modernized functional testing infrastructure

**What Was Accomplished:**

**Dead Code Cleanup:**
- ✅ Removed 847 lines of deprecated Stripe v2 code from backend
  - 3 deprecated view functions in `order/views.py` (609 lines)
  - 1 deprecated view function in `user/views.py` (100 lines)
  - Payment data cleanup in `user/views.py account_content()` (23 lines)
  - 6 deprecated utility functions in `order_utils.py` (115 lines)
- ✅ Removed 4 deprecated URL patterns
- ✅ Removed ~2,193 lines of obsolete tests
  - Deleted entire file: `test_process_stripe_payment_token.py`
  - Deleted 4 test classes from 3 files
  - Removed/updated 5 individual tests
- ✅ Fixed unused imports and linting issues

**Selenium 4 Upgrade (Bonus Work):**
- ✅ Upgraded `selenium==3.141.0` → `selenium==4.27.1`
- ✅ Updated `geckodriver` 0.33.0 → 0.35.0 in Dockerfile
- ✅ Migrated all 31 functional tests to Selenium 4 syntax
- ✅ Added `from selenium.webdriver.common.by import By` to test files
- ✅ Updated syntax: `find_element_by_id()` → `find_element(By.ID, ...)`
- ✅ Fixed `switch_to_window()` → `switch_to.window()`
- ✅ Added explicit geckodriver/Firefox paths for ARM64 compatibility

**New Functional Test:**
- ✅ Added `functional_tests/checkout/test_checkout_flow.py`
  - 1 working test: checkout success page error handling
  - 2 TODO tests for future session (cart & checkout page structure)

**Test Results:**
- Unit tests: 737 → 692 (-45 obsolete tests)
- Functional tests: 31 → 32 (+1 new test)
- **Total: 768 → 724 tests**
- ✅ All tests passing
- ✅ Zero linting errors

**Why This Matters:**
- Removes technical debt from deprecated Stripe v2 integration
- Modernizes testing infrastructure with Selenium 4
- Smaller, cleaner codebase (3,040 lines removed)
- Better foundation for future functional test development

**Documentation:**
- Created: `docs/technical-notes/2025-12-18-session-8-dead-code-cleanup-selenium-upgrade.md`
- Comprehensive learnings about frontend/backend architecture for future test development

**See**: `docs/technical-notes/2025-12-18-session-8-dead-code-cleanup-selenium-upgrade.md`

---

### **Phase 5.16 - Session 9: Stripe Webhook Production Configuration** ✅ (December 19, 2025)

**Branch**: `feature/stripe-webhook-production` (merged to master via PR #55)
**Duration**: ~3 hours (including troubleshooting)

**Milestone**: Activated Stripe webhook infrastructure in production for reliable payment processing

**What Was Accomplished:**

**Stripe Webhook Configuration:**
- ✅ Created webhook destination in Stripe TEST mode dashboard
  - URL: `https://startupwebapp-api.mosaicmeshai.com/order/stripe-webhook`
  - Events: `checkout.session.completed`, `checkout.session.expired`
  - Destination ID: `we_1Sg7IY1L9oz9ETFuPSIFcsem`
- ✅ Configured webhook signing secret in AWS Secrets Manager
  - Secret: `rds/startupwebapp/multi-tenant/master`
  - Key: `stripe_webhook_secret`
- ✅ Webhook delivery tested and verified working in production

**Critical Bug Fix (Backend):**
- ✅ Fixed Docker health check issue blocking deployment
  - Problem: ECS task definition used curl-based health check
  - Production image: curl not installed
  - Solution: Added curl to Dockerfile production stage (5 lines)
  - Deployment time: 20+ minutes stuck → 10 minutes successful

**Critical Bug Fix (Frontend PR #16):**
- ✅ Fixed checkout login race condition
  - Problem: Logged-in users saw login/anonymous buttons (Place Order disabled)
  - Root cause: Session 8 hotfix created race condition checking `$.user_logged_in` before API completed
  - Solution: Exposed `$.loginStatusReady` promise, checkout waits with `.then()`
  - Testing: Verified with 3-second backend delay + debug logging
- ✅ Removed deprecated "Save shipping and payment information" checkbox
  - Checkbox was misleading (Checkout Sessions don't save payment info)
  - Aligns with Session 7 decision (removed payment info from account page)
- ✅ All 88 frontend tests passing, ESLint clean

**Production Testing:**
- ✅ Completed test checkout with Stripe test card (4242...)
- ✅ Webhook received and processed successfully
- ✅ Order created via webhook: `qWUrhAgvtU`
- ✅ Idempotency verified (webhook + success handler both handled same session)
- ✅ Stripe Dashboard shows 200 OK webhook responses
- ✅ CloudWatch logs confirm successful order creation

**Reliability Benefits:**
- **Before**: Order only created if user completes redirect to success page
- **After**: Stripe webhook creates order even if browser closed
- Backup mechanism ensures no lost orders
- Production-grade payment reliability

**Test Results:**
- Backend: All 724 tests passing (692 unit + 32 functional), zero linting errors
- Frontend: All 88 tests passing (19 Checkout + 69 Index), ESLint clean
- Webhook signature verification working (secret from AWS Secrets Manager)
- Confirmation emails sending successfully
- Checkout flow working for both logged-in and anonymous users

**Why This Matters:**
- Completes core payment infrastructure from Sessions 5-9
- Provides production reliability for checkout flow
- Webhook + success handler create dual safety net
- Ready for real customer transactions (in forks with live Stripe keys)

**Documentation:**
- Created: `docs/technical-notes/2025-12-19-session-9-stripe-webhook-production.md`
- Comprehensive troubleshooting guide for deployment issues

**See**: `docs/technical-notes/2025-12-19-session-9-stripe-webhook-production.md`

---

### **Phase 5.16 - Session 10: Email Address Updates** ✅ (December 19, 2025)

**Branch**: `feature/email-address-updates` (merged to master via PR #56)
**Frontend Branch**: `bugfix/anonymous-checkout-email-prefill` (merged to master via PR #17)
**Duration**: ~4 hours

**Milestone**: Updated all email addresses and improved email presentation throughout application

**What Was Accomplished:**

**Email Address Updates (13 types total):**
- ✅ Updated 9 code-based emails (8 user + 1 admin)
- ✅ Updated 4 database email templates via migration
- ✅ Changed: `contact@startupwebapp.com` → `bart+startupwebapp@mosaicmeshai.com`
- ✅ Added professional display name: `StartUpWebApp <bart+...>`
- ✅ Removed BCC from all emails (no longer copying admin)
- ✅ Updated phone: `1-844-473-3744` → `1-800-123-4567`
- ✅ Updated signatures: `StartUpWebApp.com` → `StartUpWebApp`

**Order Email Cleanup:**
- ✅ Removed PAYMENT INFORMATION section from order confirmations
  - Was showing: `None: **** **** **** None, Exp: None/None`
  - Stripe Checkout Sessions don't save card details (Session 7 decision)
  - Order emails now cleaner and less confusing

**Critical Bugfix (Anonymous Checkout Email):**
- ✅ Fixed email pre-fill for anonymous checkout
  - Problem: Email entered on checkout/confirm ignored, Stripe showed empty field
  - User could enter different email at Stripe (bypassed validation)
  - Solution: Pass anonymous email to Stripe, pre-fill and lock field
- ✅ Frontend passes email in create_checkout_session call
- ✅ Backend sends email to Stripe as customer_email parameter
- ✅ Stripe pre-fills and makes email read-only
- ✅ Prevents validation bypass (can't use member email at Stripe)

**Display Name Enhancement:**
- ✅ Gmail shows "StartUpWebApp" instead of "bart"
- ✅ Professional appearance, prevents spam filtering
- ✅ Applied to all 13 email types

**Test Results:**
- Backend: 693 tests passing (692 + 1 new for anonymous email)
- Frontend: 88 tests passing
- Zero linting errors
- Migration reversible and idempotent

**Production Verification:**
- ✅ Order Confirmation - Anonymous: Professional sender, no payment info
- ✅ Order Confirmation - Logged In: Professional sender
- ✅ Welcome Email: Professional sender, updated contact info
- ✅ Anonymous email pre-fill: Email locked at Stripe

**Why This Matters:**
- Completes email updates deferred from Session 1
- Now that Stripe works (Sessions 2-9), all email types testable
- Order confirmation emails verified end-to-end
- Professional email presentation improves deliverability
- Anonymous checkout security improved

**Documentation:**
- Created: `docs/technical-notes/2025-12-19-session-10-email-address-updates.md`
- Comprehensive documentation of all email updates and bugfix

**See**: `docs/technical-notes/2025-12-19-session-10-email-address-updates.md`

---

### **Phase 5.16 - Session 11: Functional Test Development** ✅ (December 27, 2025)

**Goal**: Address automation debt from Session 8 by implementing comprehensive functional tests for PRE-STRIPE checkout flow

**Backend Repository - PR #57**:
- Branch: `feature/functional-test-checkout-flow`
- Merged to master and deployed

**Accomplished**:
- ✅ Implemented 6 new PRE-STRIPE functional tests for checkout flow
- ✅ Fixed ALL 124 pre-existing linting errors in `base_functional_test.py`
- ✅ Fixed CI race condition for empty cart scenarios
- ✅ Test coverage increased: 32 → 37 functional tests
- ✅ All 730 tests passing (693 unit + 37 functional)
- ✅ Zero linting errors across entire codebase

**New Tests Implemented**:
1. `test_cart_page_structure()` - Cart page loads correctly with empty cart
2. `test_checkout_confirm_page_structure()` - Confirm page loads with empty cart message
3. `test_checkout_flow_navigation()` - Basic navigation through checkout flow
4. `test_checkout_button_links_to_confirm()` - Cart → confirm navigation works
5. `test_add_product_to_cart_flow()` ⭐ - Full product-to-cart flow (most comprehensive)

**Test Strategy**: "Test Around Stripe" - Test our code thoroughly, don't test Stripe's code
- PRE-STRIPE tests provide comprehensive coverage of cart, checkout, navigation
- POST-STRIPE tests deferred (nice-to-have, not critical)

**Technical Challenges Solved**:
- Empty cart structure (different DOM for empty vs populated carts)
- Stale element references (AJAX page updates invalidate Selenium references)
- Missing test data (added `default_shipping_method` and `Productimage`)
- CI race condition (JavaScript removes elements faster in CI than local)

**Documentation**: `docs/technical-notes/2025-12-27-session-11-functional-test-checkout-flow.md`

---

### **Phase 5.16 - Session 12: Final Documentation** ✅ (December 27, 2025)

**Goal**: Complete Phase 5.16 with comprehensive documentation and cleanup

**Accomplished**:
- ✅ Created comprehensive Phase 5.16 technical note covering all 11 sessions
- ✅ Updated README.md with test counts (731 tests)
- ✅ Updated SESSION_START_PROMPT.md to mark Phase 5.16 complete
- ✅ Updated PROJECT_HISTORY.md with Phase 5.16 completion summary
- ✅ Updated stripe-upgrade-plan.md with completion status

**Documentation Created**: `docs/technical-notes/2025-12-27-phase-5-16-stripe-upgrade-complete.md`

---

### **Phase 5.16 COMPLETE** ✅ (December 11-27, 2025)

**Duration**: 11 sessions over 16 days (~30 hours)
**PRs Merged**: 14 total (9 backend + 5 frontend)
**Status**: Payment processing restored and operational in production

**Business Impact**:
- ✅ Payment processing restored (Checkout v2 was deprecated and broken)
- ✅ Modern infrastructure (Stripe's current recommended APIs)
- ✅ Production reliability (webhook backup ensures orders created)
- ✅ Email system operational (all 13 email types working)
- ✅ Future-proof (built on actively supported APIs)

**Technical Impact**:
- ✅ Test coverage: 724 → 730 tests (693 unit + 37 functional)
- ✅ Code quality: Removed 1,043 lines of deprecated code
- ✅ Infrastructure: Selenium 3 → 4, frontend PR validation automated
- ✅ Production: All 14 PRs auto-deployed successfully, zero rollbacks

**Key Milestones**:
- Session 2: Stripe library upgraded (5.5.0 → 14.0.1)
- Session 3-5: Backend Checkout Sessions API + webhooks
- Session 6: Frontend migration to Stripe.js v3
- Session 8: Dead code cleanup + Selenium 4 upgrade (bonus)
- Session 9: Production webhook configuration
- Session 10: Email address updates (all 13 types)
- Session 11: Functional test automation debt resolved

**Documentation**: `docs/technical-notes/2025-12-27-phase-5-16-stripe-upgrade-complete.md`

---

#### Phase 5.17: Production Hardening (Future)
- AWS WAF for security
- Enhanced CloudWatch monitoring
- Load testing and performance optimization
- Automated disaster recovery testing

#### Other Library Upgrades
- **Stripe**: ✅ Library upgraded to 14.0.1 (Phase 5.16) - Checkout Sessions complete
- **Selenium**: ✅ Upgraded to 4.27.1 (December 2025) - Modern API with all tests migrated

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
