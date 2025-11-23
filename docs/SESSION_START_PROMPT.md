# Session Starting Prompt

Use this prompt to start new Claude Code sessions for this project.

---

Hi Claude. I want to continue working on these two repositories together:
  - Backend: https://github.com/bartgottschalk/startup_web_app_server_side
  - Frontend: https://github.com/bartgottschalk/startup_web_app_client_side

  ## Repository Location

  - Projects directory: `~/Projects/WebApps/`
  - This directory contains multiple projects:
    - `StartUpWebApp/` - This project (startup_web_app_server_side and startup_web_app_client_side)
    - `RefrigeratorGames/` - Separate project
  - Current working directory: `~/Projects/WebApps/StartUpWebApp/startup_web_app_server_side`

  ## Repository Context

  **Tech Stack:**
  - Backend: Django 4.2.16 (4.2 LTS), Python 3.12.12, PostgreSQL 16-alpine (multi-tenant), Stripe integration
  - Frontend: jQuery 3.7.1, nginx:alpine
  - Infrastructure: Docker Compose with custom bridge network "startupwebapp"
  - Database: PostgreSQL 16 with multi-database support (startupwebapp_dev, healthtech_dev, fintech_dev)
  - Testing: Selenium 3.141.0 with Firefox ESR (headless mode)
  - Code Quality: pylint 4.0.2, flake8 7.3.0, ESLint 9.39.1, Node.js 25.1.0

  **Current State:**
  - Django upgrade: ✅ Completed (2.2.28 → 4.2.16 LTS) - November 6, 2025
  - Post-upgrade documentation: ✅ Completed - November 7, 2025
  - Code linting: ✅ Completed - Zero errors (backend + frontend) - November 13, 2025
  - CSRF token bug fix: ✅ Completed - 100% test pass rate - November 16, 2025
  - PostgreSQL migration Phase 1: ✅ Completed - FloatField→DecimalField conversion - November 17, 2025
  - PostgreSQL migration Phases 2-5: ✅ Completed - Multi-tenant Docker setup - November 18, 2025
  - AWS RDS Infrastructure Phase 7: ✅ Completed - VPC, RDS, Secrets Manager, CloudWatch - November 19, 2025
  - AWS RDS Django Integration Phase 8: ✅ Completed - Production settings with Secrets Manager - November 20, 2025
  - AWS RDS Database Creation Phase 9: ✅ In Progress - Bastion host + multi-tenant databases - November 22, 2025
  - Test suite: 740/740 tests passing (712 unit + 28 functional) with PostgreSQL - 100% pass rate
  - AWS Infrastructure: Deployed (86% complete, 6/7 steps) - $36/month ($30 with bastion stopped)
  - PostgreSQL migration fully merged to master (PR #32) - November 19, 2025
  - Branch: feature/phase-9-aws-rds-deployment (security improvements in progress)
  - Both repositories cloned to: ~/Projects/WebApps/StartUpWebApp/startup_web_app_server_side and ~/Projects/WebApps/StartUpWebApp/startup_web_app_client_side

  **Recent Completed Work:**
  - **AWS RDS Database Creation Phase 9 (November 22, 2025)**: Bastion Host & Multi-Tenant Databases
    - Created bastion host infrastructure scripts (create-bastion.sh, destroy-bastion.sh)
    - Root caused SSM connection issue: Missing public IP address on bastion instance
    - Fixed create-bastion.sh: Added --associate-public-ip-address flag
    - Successfully deployed bastion host (i-0d8d746dd8059de2c) with SSM access
    - Created 3 multi-tenant databases on AWS RDS: startupwebapp_prod, healthtech_experiment, fintech_experiment
    - Verified django_app user can connect to all databases
    - Updated infrastructure scripts: status.sh and show-resources.sh with bastion support
    - Deployment progress: 6/7 steps complete (86%)
    - Cost: $36/month with bastion running, $30/month with bastion stopped
    - Security improvements: Implemented separate master and application database passwords (principle of least privilege)
    - Technical documentation: docs/technical-notes/2025-11-22-phase-9-bastion-troubleshooting.md
  - **AWS RDS Django Integration Phase 8 (November 20, 2025)**: Production Settings with Secrets Manager
    - Created settings_production.py: Retrieves ALL secrets from AWS Secrets Manager
    - Database credentials + Django SECRET_KEY + Stripe keys + Email SMTP
    - Updated create-secrets.sh: Auto-generates separate master and application passwords (32 chars each) + Django SECRET_KEY (50 chars)
    - Security architecture: Separate passwords for master (postgres admin) and application (django_app) users
    - Updated destroy-secrets.sh: Enhanced warnings for expanded secret structure
    - Created test-rds-connection.py: AWS RDS connectivity validation
    - Added boto3==1.35.76 for AWS SDK integration
    - Infrastructure tested: Full destroy→create cycle successful
    - All 712 unit tests passing, zero linting errors
    - Security: Zero hardcoded credentials, all secrets in AWS Secrets Manager, principle of least privilege
    - Technical documentation: docs/technical-notes/2025-11-20-aws-rds-django-integration.md
  - **AWS RDS Infrastructure Phase 7 (November 19, 2025)**: Infrastructure as Code Complete
    - Created 21 AWS infrastructure scripts for deployment automation
    - VPC with public/private subnets, security groups, RDS PostgreSQL 16
    - AWS Secrets Manager for credential management
    - CloudWatch monitoring with 4 alarms + SNS email alerts
    - Cost optimization: $29/month (saved $32/month by skipping NAT Gateway)
    - Deployment status: 71% complete (5/7 steps), ready for database creation
    - Technical documentation: docs/technical-notes/2025-11-19-aws-rds-deployment-plan.md
  - **PostgreSQL Migration Phases 2-5 (November 18, 2025)**: Multi-Tenant Docker Setup - Production Ready
    - Phase 2: Docker PostgreSQL 16-alpine with multi-database support (startupwebapp_dev, healthtech_dev, fintech_dev)
    - Phase 3: Environment-based database selection with connection pooling (CONN_MAX_AGE=600)
    - Phase 4: Fresh PostgreSQL migrations (all 57 tables created successfully)
    - Phase 5: Fixed PostgreSQL sequence issues in tests (138 test classes updated to PostgreSQLTestCase)
    - Created PostgreSQLTestCase base class (TransactionTestCase with reset_sequences=True)
    - Fixed data migration to skip during test runs (detect test_ prefix)
    - Automated test file updates with dry-run validation (scripts/update_test_base_class.py)
    - All 740 tests passing (712 unit + 28 functional) with PostgreSQL - 100% pass rate
    - Zero functional code linting errors (28 E501 in auto-generated migrations only)
    - Multi-tenant architecture: separate databases per fork on shared instance (75% cost savings)
    - Technical documentation: docs/technical-notes/2025-11-18-postgresql-migration-phases-2-5-complete.md
  - **PostgreSQL Migration Phase 1 (November 17, 2025)**: FloatField→DecimalField Conversion
    - Converted all 12 currency FloatField instances to DecimalField (max_digits=10, decimal_places=2)
    - Created 19 new TDD tests for DecimalField precision validation
    - Fixed business logic in order_utils.py to handle Decimal types
    - Updated 11 test assertions to expect string values in JSON (DecimalField serialization)
    - Created Django migration: 0003_alter_discountcode_discount_amount_and_more.py
    - All 740 tests passing (712 unit + 28 functional), 100% pass rate
    - Zero linting errors (28 E501 in auto-generated migrations only)
    - Ensures precise currency calculations, PostgreSQL compatibility
    - Technical documentation: docs/technical-notes/2025-11-17-floatfield-to-decimalfield-conversion.md
  - **Phase 5.8 (November 16, 2025)**: CSRF Token Bug Fix - Complete Resolution
    - Fixed critical CSRF token stale variable bug affecting all AJAX POST requests
    - Changed 26 instances across 20 JavaScript files from stale global variable to dynamic cookie reads
    - Removed unused global variable and redundant fallback logic
    - Manual browser testing confirmed fix (200 OK vs previous 403 Forbidden)
    - Functional test validation: 100% pass rate (10/10 runs, 28 tests each)
    - Previous state: 80-90% pass rate with test-side workarounds
    - Production impact: Eliminated intermittent form submission failures for users
    - All 721 tests passing, zero ESLint errors/warnings
    - Technical documentation: docs/technical-notes/2025-11-16-csrf-token-stale-variable-bug-fix.md
  - **Phase 5.7 (November 13, 2025)**: Backend Linting Phase 4-6 Complete - Zero Errors
    - Achieved ZERO linting errors (2,286 → 0 issues, 100% reduction)
    - Phase 4: Refactored identifier.py (14 issues, .filter().exists() pattern)
    - Phase 5: autopep8 automated fixes (1,907 issues, 83.9% reduction)
    - Phase 6: Manual fixes (365 issues) - max-line-length 120, F841, E999, F821, E203, E402, E501
    - Integrated black code formatter for ongoing quality
    - All 693 unit tests + 27/28 functional tests passing
    - Production-ready codebase with 100% PEP 8 compliance
  - **Phase 5.6 (November 12, 2025)**: Replace print() with Django logging
    - Configured comprehensive logging framework in settings.py
    - Replaced 106 print() statements with appropriate logging
    - Deleted 101 commented print() statements (technical debt cleanup)
    - Created rotating file handler: logs/django.log (10 MB max, 5 backups)
    - Environment-aware: DEBUG level in dev, INFO in production
    - All 721 tests passing, zero regressions
    - Production-ready with persistent logs, severity levels, full context
  - **Phase 5.5 (November 11, 2025)**: Code linting Phase 1 - Frontend JavaScript
    - Fixed all 5,333 ESLint issues (441 errors + 4,892 warnings → 0 errors + 0 warnings)
    - 100% reduction achieved across all 19 JavaScript files
    - Automated fixes: 4,674 issues (indentation, quotes, semicolons)
    - Manual fixes: 659 issues (undefined vars, missing var declarations, unused variables)
    - Added 100+ global function declarations to eslint.config.js
    - Fixed 20+ missing var declarations preventing global scope pollution
    - Created TDD test for display_errors to prevent regression
    - Identified test coverage gap: only 3/19 files tested (~16% coverage)
    - All QUnit tests passing, zero regressions
    - All 721 backend tests passing, zero regressions
    - Manual full-stack testing validated
  - **Phase 5.4 (November 10, 2025)**: Code linting Phase 3 - Backend critical issues
    - Removed 47 semicolons (E703 eliminated)
    - Fixed 30 comparison issues (E712: 37 → 7, 81% reduction)
    - Refactored isUserNameAvailable() to .filter().exists() pattern
    - Protected 6 validator comparisons with noqa comments
    - Reduced flake8 issues: 2,490 → 2,405 (85 fixed, 3.4% reduction)
    - Cumulative: 3,941 → 2,405 (1,536 total fixed, 39.0% total reduction)
    - All 721 tests passing, zero regressions
    - Addressed all critical code correctness issues
  - **Phase 5.3 (November 10, 2025)**: Code linting Phase 2 - Backend style/formatting
    - Fixed 1,179 style issues: whitespace, blank lines, formatting (autopep8)
    - Reduced flake8 issues: 3,669 → 2,490 (1,179 fixed, 32.1% reduction)
    - Cumulative: 3,941 → 2,490 (1,451 total fixed, 36.8% total reduction)
    - All 721 tests passing, zero regressions
    - Fully automated, PEP 8 compliant formatting
  - **Phase 5.2 (November 10, 2025)**: Code linting Phase 1 - Backend high priority
    - Removed 217 unused imports, 14 unused variables (autoflake)
    - Fixed 12 star import issues, 48 comparison issues (autopep8)
    - Protected 7 validation comparisons with explanatory comments
    - Reduced flake8 issues: 3,941 → 3,669 (272 fixed, 6.9% reduction)
    - All 721 tests passing, zero regressions
    - Documented validator pattern (returns True or error array)
  - **Phase 5.1.1 (November 9, 2025)**: Critical bug fix - SMTPDataError import
    - Fixed critical bug found during linting: SMTPDataError undefined in user/admin.py
    - Applied TDD methodology: wrote 4 tests first, verified failure, then fixed
    - Added missing import: from smtplib import SMTPDataError
    - All 721 tests passing (693 unit + 28 functional, +4 new tests)
    - Prevents runtime crashes during admin email operations
  - **Phase 5.1 (November 9, 2025)**: Code linting analysis
    - Installed linting tools: pylint, flake8, ESLint, Node.js 25.1.0
    - Analyzed 9,313 code quality issues (3,978 Python + 5,335 JavaScript)
    - Identified 1 critical bug: SMTPDataError undefined in user/admin.py
    - Created comprehensive findings report with prioritized recommendations
    - Added linting to development workflow (run before commits)
  - **Phase 4.5 (November 8, 2025)**: Stripe error handling refactor
    - Fixed critical bug: unhandled Stripe API errors could crash endpoints
    - Added 10 new unit tests (679→689 total) using TDD methodology
    - Centralized error handling in utility functions
  - **Phase 4 (November 6, 2025)**: Django 2.2.28 → 4.2.16 LTS upgrade
    - Incremental 6-step upgrade completed in 3.8 hours
    - Zero test regressions, minimal code changes
    - Security support extended until April 2026

  ## Pre-Session Checklist

  Before starting work:
  1. **HUMAN: START DOCKER DESKTOP FIRST!** - You need to manually start Docker before Claude can run any docker-compose commands
  2. Verify both repos are on master branch with no uncommitted changes
  3. Verify no pending branches with changes
  4. Read key documentation files:
     - `docs/PROJECT_HISTORY.md` - Project timeline and current status
     - `docs/technical-notes/2025-11-08-stripe-error-handling-refactor.md` - Most recent work
  5. Review full gitignore files in both projects and respect them
  6. Flag any new files/extensions that should be added to gitignore

  ## Development Workflow Requirements

  **Branch Strategy:**
  - All code changes in feature branches (never directly on master)
  - Branch naming: `feature/descriptive-name` or `bugfix/descriptive-name`
  - Run full test suite before committing
  - Perform manual browser testing for UI changes
  - Create PR after pushing branch to remote
  - Wait for my approval and merge confirmation
  - Clean up local and remote branches after merge

  **Testing Requirements:**
  - Unit tests (PostgreSQL backend): `docker-compose exec backend python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests --parallel=4` (712 tests)
  - **Functional tests: MUST run hosts setup first, then tests:**
    ```bash
    docker-compose exec backend bash /app/setup_docker_test_hosts.sh
    docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests
    ```
  - IMPORTANT: All functional tests MUST use HEADLESS=TRUE environment variable
  - If documentation contradicts HEADLESS=TRUE requirement, flag it for correction
  - PostgreSQL note: Tests use PostgreSQLTestCase (TransactionTestCase with reset_sequences=True)
  - Coverage analysis: `coverage run --source='.' manage.py test && coverage report`

  **Code Quality (Linting) - Run before committing:**
  - Backend Python linting (Django apps and StartupWebApp directory):
    ```bash
    docker-compose exec backend flake8 user order clientevent StartupWebApp --max-line-length=120 --statistics
    ```
  - **Note**: Infrastructure scripts in `scripts/infra/` are NOT mounted in Docker and don't need linting (they're deployment tools, not app code)
  - Frontend JavaScript linting (requires Node.js on host):
    ```bash
    cd ~/Projects/WebApps/StartUpWebApp/startup_web_app_client_side
    npx eslint js/**/*.js --ignore-pattern "js/jquery/**"
    ```
  - IMPORTANT: Run linting alongside unit and functional tests to catch code quality issues early
  - Goal: Zero new linting errors introduced (warnings acceptable for now)
  - See `docs/technical-notes/2025-11-09-code-linting-analysis.md` for baseline and priorities

  **Docker Environment:**
  - Backend API: http://localhost:8000
  - Frontend: http://localhost:8080
  - Start services: `docker-compose up -d`
  - Backend server: `docker-compose exec -d backend python manage.py runserver 0.0.0.0:8000`
  - Custom bridge network: "startupwebapp" (enables inter-service communication)

  **AWS Infrastructure Management:**
  - **CRITICAL WORKFLOW RULE**: All AWS infrastructure scripts (`scripts/infra/*.sh`) will be executed manually in separate terminal windows
  - **DO NOT run infrastructure scripts within Claude Code chat sessions**
  - Infrastructure scripts directory: `scripts/infra/`
  - Scripts are idempotent and safe to run multiple times
  - Naming convention: `create-*.sh` for provisioning, `destroy-*.sh` for teardown
  - Resource IDs tracked in: `scripts/infra/aws-resources.env`
  - AWS CLI configured (region: us-east-1, IAM user: startupwebapp-admin)

  **Documentation Requirements:**
  - Every commit MUST include updated documentation
  - Key doc files: `docs/PROJECT_HISTORY.md`, `README.md`
  - Key doc directories: `docs/milestones/`, `docs/technical-notes/`
  - Create new milestone docs for significant work (follow existing naming: YYYY-MM-DD-phase-description.md)
  - Create technical notes for bug fixes and refactorings (follow existing naming: YYYY-MM-DD-description.md)
  - Update test counts and coverage stats when changed
  - Document all bugs found and fixed in technical notes

  **Testing Conventions:**
  - **Test-Driven Development (TDD)**: ALWAYS write tests first before implementing code changes
    - Write tests that demonstrate the bug or desired feature
    - Run tests to verify they fail (proving the issue exists)
    - Implement the minimum code needed to make tests pass
    - Refactor while keeping all tests passing
    - This approach maintains high code coverage and prevents regressions
  - Use unittest.mock for external API calls (especially Stripe)
  - Test both authenticated (Member) and anonymous (Prospect) user flows
  - Include edge cases and error handling scenarios (InvalidRequestError, AuthenticationError, APIConnectionError)
  - Target 90%+ coverage for critical payment/order/auth paths
  - Follow existing test patterns in codebase

  ## Critical Files & Patterns

  **Gitignored (never commit):**
  - settings_secret.py - Contains API keys, database passwords, CORS config
  - *.pyc, __pycache__/ - Python bytecode
  - Database files: db.sqlite3 (legacy), PostgreSQL volume data
  - Static file collections, media uploads
  - Environment files: .env, venv/

  **Key Configuration Files:**
  - requirements.txt - Python dependencies (Django, Stripe, Selenium, psycopg2-binary)
  - docker-compose.yml - Service orchestration (PostgreSQL 16 + backend + frontend)
  - scripts/init-multi-db.sh - PostgreSQL multi-database initialization
  - nginx.conf - Frontend server configuration (important for extensionless URLs)
  - settings.py & settings_secret.py - Django configuration (PostgreSQL with environment variables)

  **Code Patterns to Follow:**
  - Mock Stripe API in tests: @patch('stripe.Customer.retrieve')
  - Validate responses: unittest_utilities.validate_response_is_OK_and_JSON()
  - Handle both Member and Prospect models for users
  - Cart operations support both authenticated and anonymous users
  - Use TimestampSigner for secure tokens (email verification, unsubscribe)
  - Test base class: PostgreSQLTestCase (from StartupWebApp.utilities.test_base)
  - PostgreSQL test database: Uses TransactionTestCase with reset_sequences=True

  ## Planned Work Items (Priority Order)

  1. **✅ Linting (Phase 1 Complete - November 11, 2025)**
     - ✅ Backend Phase 1: High priority (Completed - November 10, 2025)
       - ✅ Removed 217 unused imports, 14 unused variables
       - ✅ Fixed 12 star import issues, 48 comparison issues
       - ✅ Reduced flake8 issues: 3,941 → 3,669 (-272, -6.9%)
       - ✅ Protected validation comparisons with documentation
     - ✅ Backend Phase 2: Style/formatting (Completed - November 10, 2025)
       - ✅ Fixed 1,179 whitespace and formatting issues (autopep8)
       - ✅ Reduced flake8 issues: 3,669 → 2,490 (-1,179, -32.1%)
       - ✅ Cumulative: 36.8% total reduction (1,451 issues fixed)
       - ✅ Fully automated, zero regressions
     - ✅ Backend Phase 3: Critical issues (Completed - November 10, 2025)
       - ✅ Removed 47 semicolons (E703 eliminated)
       - ✅ Fixed 30 comparison issues (E712: 37 → 7, 81% reduction)
       - ✅ Refactored isUserNameAvailable() to .filter().exists()
       - ✅ Reduced flake8 issues: 2,490 → 2,405 (-85, -3.4%)
       - ✅ Cumulative: 39.0% total reduction (1,536 issues fixed)
     - ✅ Frontend Phase 1: Complete cleanup (Completed - November 11, 2025)
       - ✅ Fixed all 5,333 ESLint issues (100% reduction)
       - ✅ 87.6% automated fixes (indentation, quotes, semicolons)
       - ✅ 12.4% manual fixes (undefined vars, missing declarations, unused vars)
       - ✅ Configured eslint.config.js with 100+ global functions
       - ✅ Fixed global scope pollution bugs (20+ missing var declarations)
       - ✅ Created TDD test to prevent regressions
     - ✅ Logging setup (Completed - November 12, 2025)
       - ✅ Configured Django logging framework in settings.py
       - ✅ Replaced 106 print() statements with appropriate logging
       - ✅ Deleted 101 commented print() statements
       - ✅ Created rotating file handler with 10 MB max, 5 backups
       - ✅ All 721 tests passing, zero regressions
     - ✅ Backend Phase 4-6: Complete linting cleanup (Completed - November 13, 2025)
       - ✅ Phase 4: identifier.py refactor (14 issues fixed, .filter().exists() pattern)
       - ✅ Phase 5: autopep8 automated fixes (1,907 issues fixed, 83.9% reduction)
       - ✅ Phase 6: Manual resolution (365 issues fixed)
       - ✅ ZERO linting errors achieved (2,286 → 0, 100% reduction)
       - ✅ All 693 unit tests + 27/28 functional tests passing
     - ✅ CSRF Token Bug Fix (Completed - November 16, 2025)
       - ✅ Fixed critical bug causing 403 CSRF errors on AJAX POST requests
       - ✅ Changed 26 instances across 20 JavaScript files
       - ✅ Achieved 100% functional test pass rate (previously 80-90%)
       - ✅ Zero ESLint errors/warnings maintained
     - ✅ **PostgreSQL Migration Phase 1** (Completed - November 17, 2025)
       - ✅ Converted 12 FloatField instances to DecimalField for currency precision
       - ✅ Created 19 TDD tests for DecimalField validation
       - ✅ All 740 tests passing (712 unit + 28 functional)
       - ✅ Zero linting errors maintained
       - ✅ Technical doc: docs/technical-notes/2025-11-17-floatfield-to-decimalfield-conversion.md
     - ✅ **PostgreSQL Migration Phases 2-5** (Completed - November 18, 2025)
       - ✅ Phase 2: Docker PostgreSQL 16-alpine with multi-database support
       - ✅ Phase 3: Django environment-based database selection with connection pooling
       - ✅ Phase 4: Fresh PostgreSQL migrations (all 57 tables created)
       - ✅ Phase 5: Fixed PostgreSQL sequence issues (138 test classes updated)
       - ✅ All 740 tests passing (712 unit + 28 functional) with PostgreSQL
       - ✅ Zero functional code linting errors
       - ✅ Multi-tenant architecture: 75% cost savings on AWS RDS
       - ✅ Technical doc: docs/technical-notes/2025-11-18-postgresql-migration-phases-2-5-complete.md
     - 🔮 **Future Options**:
       - Phase 6: AWS RDS PostgreSQL deployment (when ready)
       - Expand test coverage (currently only 3/19 JavaScript files tested, ~16% coverage)

  2. **✅ Replace print statements with proper logging (COMPLETED - November 12, 2025)**
     - ✅ Converted 106 print() statements to proper logging calls
     - ✅ Set up Django logging configuration in settings.py
     - ✅ Rotating file handler: logs/django.log (10 MB max, 5 backups)
     - ✅ Environment-aware: DEBUG in dev, INFO in production
     - ✅ Production-ready: persistent logs, severity levels, full context

  3. **✅ Migrate from SQLite to PostgreSQL** (Phases 1-7 Complete - November 19, 2025)
     - **Status**: Phases 1-7 complete, infrastructure deployed to AWS RDS, ready for database setup and Django deployment
     - **Decision**: AWS RDS PostgreSQL 16.x with multi-tenant architecture
     - **Cost**: $29/month (RDS: $26, Monitoring: $2, CloudWatch: $1) - NAT Gateway skipped (saved $32/month)
     - **Architecture**: Separate databases per fork on shared RDS instance
     - **Implementation Plan** (8 phases documented):
       - ✅ Phase 1: FloatField→DecimalField conversion (COMPLETE - November 17, 2025)
         - Converted 12 currency fields to DecimalField (max_digits=10, decimal_places=2)
         - Created 19 TDD tests, all 740 tests passing
         - Technical doc: docs/technical-notes/2025-11-17-floatfield-to-decimalfield-conversion.md
       - ✅ Phase 2: Docker PostgreSQL 16-alpine with multi-database support (COMPLETE - November 18, 2025)
       - ✅ Phase 3: Django configuration with environment-based database selection (COMPLETE - November 18, 2025)
       - ✅ Phase 4: Migrations on fresh PostgreSQL database (COMPLETE - November 18, 2025)
       - ✅ Phase 5: Testing & validation - all 740 tests passing with PostgreSQL (COMPLETE - November 18, 2025)
         - Created PostgreSQLTestCase base class (TransactionTestCase with reset_sequences=True)
         - Updated 138 test classes across 43 test files
         - Fixed data migration to skip during test runs
         - Technical doc: docs/technical-notes/2025-11-18-postgresql-migration-phases-2-5-complete.md
       - ✅ Phase 6: Merged to master via PR #32 (COMPLETE - November 19, 2025)
       - ✅ Phase 7: AWS RDS Infrastructure Deployment (COMPLETE - November 19, 2025)
         - Created 21 Infrastructure as Code bash scripts (14 create + 5 destroy + 2 status)
         - Deployed VPC, Security Groups, Secrets Manager, RDS PostgreSQL 16.x, CloudWatch monitoring
         - RDS Endpoint: startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com:5432
         - Progress: 5/7 steps complete (71%) - RDS available, monitoring active
         - Tested all destroy/create cycles - all validated successfully
         - Monthly cost: $29 (saved $32/month by skipping NAT Gateway)
         - Technical doc: docs/technical-notes/2025-11-19-aws-rds-deployment-plan.md
       - ✅ Phase 8: Django Production Settings (COMPLETE - November 20, 2025)
         - Created settings_production.py with AWS Secrets Manager integration
         - All secrets retrieved from Secrets Manager (DB, Django SECRET_KEY, Stripe, Email)
         - Updated infrastructure scripts with expanded secret structure
         - Security: Separate master (postgres) and application (django_app) passwords
         - Added boto3==1.35.76 for AWS SDK
         - All 712 tests passing, zero linting errors
         - Technical doc: docs/technical-notes/2025-11-20-aws-rds-django-integration.md
       - ⏳ Phase 9: Database Creation & Django Deployment (in progress - November 22, 2025)
         - ✅ Created bastion host infrastructure scripts with SSM access
         - ✅ Implemented separate master and application database passwords (security improvement)
         - ⏳ Next: Destroy and recreate infrastructure with new password structure
         - ⏳ Next: Create 3 multi-tenant databases on AWS RDS
         - ⏳ Next: Update Stripe and Email credentials in AWS Secrets Manager
         - ⏳ Next: Run Django migrations on AWS RDS PostgreSQL
         - ⏳ Next: Test full application against AWS RDS
         - ⏳ Next: Deploy backend application to AWS (ECS or EC2)
     - **Database Naming**: Removed legacy `rg_` prefix → `startupwebapp_prod` (production)
     - **Local Setup**: 3 databases (startupwebapp_dev, healthtech_dev, fintech_dev)
     - **Production Setup**: 3 databases (startupwebapp_prod, healthtech_experiment, fintech_experiment)
     - **Alternatives Evaluated**: Lightsail, DynamoDB, Aurora Serverless v2 (all rejected)
     - **Timeline**: Phases 1-7 completed in ~15 hours over 3 days
     - **See**: docs/technical-notes/2025-11-17-database-migration-planning.md v2.2
     - **Branch**: Phases 1-6 merged to master (PR #32), Phase 7 on feature/aws-infrastructure-setup

  4. **Consider Stripe library upgrade (optional)**
     - Current: stripe==5.5.0
     - Evaluate upgrade path and breaking changes
     - Review Stripe API changelog for new features and deprecations
     - Test thoroughly with existing payment flows
     - Only proceed if benefits outweigh risks

  5. **Consider Selenium 4 upgrade (optional)**
     - Current: Selenium 3.141.0
     - Evaluate benefits (better waits, modern WebDriver API, improved stability)
     - May require functional test refactoring
     - All 28 tests currently passing - low priority
     - Consider during major test infrastructure updates

  6. **Prepare containers for deployment to AWS for "production"**
     - Configure production-ready Docker images (security, optimization)
     - Set up environment variable management for secrets (AWS Secrets Manager or Parameter Store)
     - Configure production database connection (from task #3)
     - Set up S3 for static files and media storage
     - Configure CloudFront CDN for frontend
     - Implement health checks and monitoring
     - Security hardening (disable DEBUG, set ALLOWED_HOSTS, configure HTTPS)
     - Review and configure AWS security groups, IAM roles
     - Depends on task #3 (database migration)

  7. **Setup CI/CD pipeline**
     - Configure GitHub Actions or AWS CodePipeline
     - Automated testing on push:
       - Run all 689 unit tests
       - Run all 28 functional tests (with HEADLESS=TRUE)
       - Fail pipeline if any tests fail
     - Trigger deployment on successful test run:
       - Deploy to AWS when master is updated
       - Consider staging environment for feature/bugfix branches
     - Configure deployment to AWS (ECS, EKS, or Elastic Beanstalk)
     - Set up rollback mechanism for failed deployments
     - Configure deployment notifications (Slack, email, etc.)
     - Depends on task #6 (AWS infrastructure ready)

  ## Next Steps

  Please review all documentation (especially `docs/PROJECT_HISTORY.md` and recent technical notes in `docs/technical-notes/`) and propose next steps based on the Planned Work Items above.

  **Current Focus**: PostgreSQL Migration Phase 7 Complete - AWS RDS Infrastructure Deployed
  1. ✅ Completed Backend Phase 1: High priority (272 issues fixed)
  2. ✅ Completed Backend Phase 2: Style/formatting (1,179 issues fixed)
  3. ✅ Completed Backend Phase 3: Critical issues (85 issues fixed)
  4. ✅ Completed Frontend Phase 1: Complete cleanup (5,333 issues fixed - 100% reduction)
  5. ✅ Completed Logging: Replace print() with Django logging (106 replaced, 101 deleted)
  6. ✅ Completed Backend Phase 4-6: Zero linting errors (2,286 → 0, 100% reduction)
  7. ✅ Completed CSRF Token Bug Fix: 100% test pass rate (26 instances fixed, 20 files)
  8. ✅ Completed PostgreSQL Migration Planning (v2.2 - comprehensive analysis, all decisions made)
  9. ✅ **COMPLETED & MERGED: PostgreSQL Migration Phases 1-6 (Planned Work Item #3)**
     - **Status**: Merged to master (PR #32) - November 19, 2025
     - **Branch**: Fully merged and cleaned up
     - **Test Results**: All 740 tests passing (712 unit + 28 functional) with PostgreSQL
     - **Achievements**:
       - ✅ Phase 1: FloatField→DecimalField conversion (November 17, 2025)
       - ✅ Phase 2: Docker PostgreSQL 16-alpine with multi-database support (November 18, 2025)
       - ✅ Phase 3: Django configuration with environment-based database selection (November 18, 2025)
       - ✅ Phase 4: Fresh PostgreSQL migrations - all 57 tables created (November 18, 2025)
       - ✅ Phase 5: Fixed PostgreSQL sequence issues - 138 test classes updated (November 18, 2025)
       - ✅ Phase 6: Merged to master via PR #32 (November 19, 2025)
     - **Architecture**: 3 local databases (startupwebapp_dev, healthtech_dev, fintech_dev)
     - **Documentation**:
       - Planning: docs/technical-notes/2025-11-17-database-migration-planning.md v2.2
       - Phase 1: docs/technical-notes/2025-11-17-floatfield-to-decimalfield-conversion.md
       - Phases 2-5: docs/technical-notes/2025-11-18-postgresql-migration-phases-2-5-complete.md
  10. ✅ **COMPLETED: PostgreSQL Migration Phase 7 - AWS RDS Infrastructure (Planned Work Item #3)**
     - **Status**: Infrastructure deployed, RDS available, monitoring active
     - **Branch**: feature/aws-infrastructure-setup (ready to merge)
     - **Progress**: 5/7 steps complete (71%)
     - **Achievements**:
       - ✅ Created 21 Infrastructure as Code bash scripts
       - ✅ Deployed VPC (10.0.0.0/16, 2 AZs, 4 subnets)
       - ✅ Deployed Security Groups (RDS, Bastion, Backend)
       - ✅ Deployed AWS Secrets Manager (32-char auto-generated password)
       - ✅ Deployed RDS PostgreSQL 16.x (db.t4g.small, 20 GB gp3)
       - ✅ Deployed CloudWatch monitoring (4 alarms, email confirmed)
       - ✅ Tested all destroy/create cycles - all validated
     - **RDS Endpoint**: startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com:5432
     - **Monthly Cost**: $29 (RDS: $26, Monitoring: $2, CloudWatch: $1)
     - **Cost Savings**: Skipped NAT Gateway (saved $32/month, 52% reduction)
     - **Timeline**: Completed in ~7 hours
     - **Documentation**: docs/technical-notes/2025-11-19-aws-rds-deployment-plan.md
     - **Next**: Phase 8 (Database setup and Django deployment)
  11. ⏳ Future: Expand test coverage (3/19 JavaScript files tested, 16% coverage)
