# Session Starting Prompt

Use this prompt to start new Claude Code sessions for this project.

---

Hi Claude. I want to continue working on these two repositories together:
  - Backend: https://github.com/bartgottschalk/startup_web_app_server_side
  - Frontend: https://github.com/bartgottschalk/startup_web_app_client_side

  ## Repository Context

  **Tech Stack:**
  - Backend: Django 4.2.16 (4.2 LTS), Python 3.12.12, SQLite, Stripe integration
  - Frontend: jQuery 3.7.1, nginx:alpine
  - Infrastructure: Docker Compose with custom bridge network "startupwebapp"
  - Testing: Selenium 3.141.0 with Firefox ESR (headless mode)
  - Code Quality: pylint 4.0.2, flake8 7.3.0, ESLint 9.39.1, Node.js 25.1.0

  **Current State:**
  - Django upgrade: ✅ Completed (2.2.28 → 4.2.16 LTS) - November 6, 2025
  - Post-upgrade documentation: ✅ Completed - November 7, 2025
  - Code linting: ✅ Completed - Zero errors (backend + frontend) - November 13, 2025
  - CSRF token bug fix: ✅ Completed - 100% test pass rate - November 16, 2025
  - Test suite: 721/721 tests passing (693 unit + 28 functional) - 100% pass rate
  - Master branch is clean and up-to-date
  - Both repositories cloned to: ~/Projects/startup_web_app_server_side and ~/Projects/startup_web_app_client_side

  **Recent Completed Work:**
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
  - Unit tests: `docker-compose exec backend python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests` (693 tests)
  - **Functional tests: MUST run hosts setup first, then tests:**
    ```bash
    docker-compose exec backend bash /app/setup_docker_test_hosts.sh
    docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests
    ```
  - IMPORTANT: All functional tests MUST use HEADLESS=TRUE environment variable
  - If documentation contradicts HEADLESS=TRUE requirement, flag it for correction
  - Coverage analysis: `coverage run --source='.' manage.py test && coverage report`

  **Code Quality (Linting) - Run before committing:**
  - Backend Python linting:
    ```bash
    docker-compose exec backend flake8 user order clientevent StartupWebApp --max-line-length=120 --statistics
    ```
  - Frontend JavaScript linting (requires Node.js on host):
    ```bash
    cd ~/Projects/startup_web_app_client_side
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
  - Database files: db.sqlite3
  - Static file collections, media uploads
  - Environment files: .env, venv/

  **Key Configuration Files:**
  - requirements.txt - Python dependencies (Django, Stripe, Selenium, etc.)
  - docker-compose.yml - Service orchestration
  - nginx.conf - Frontend server configuration (important for extensionless URLs)
  - settings.py & settings_secret.py - Django configuration

  **Code Patterns to Follow:**
  - Mock Stripe API in tests: @patch('stripe.Customer.retrieve')
  - Validate responses: unittest_utilities.validate_response_is_OK_and_JSON()
  - Handle both Member and Prospect models for users
  - Cart operations support both authenticated and anonymous users
  - Use TimestampSigner for secure tokens (email verification, unsubscribe)

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
     - ⏳ **Next Options**:
       - Expand test coverage (currently only 3/19 JavaScript files tested, ~16% coverage)
       - Database migration planning (SQLite → PostgreSQL/MySQL for AWS deployment)

  2. **✅ Replace print statements with proper logging (COMPLETED - November 12, 2025)**
     - ✅ Converted 106 print() statements to proper logging calls
     - ✅ Set up Django logging configuration in settings.py
     - ✅ Rotating file handler: logs/django.log (10 MB max, 5 backups)
     - ✅ Environment-aware: DEBUG in dev, INFO in production
     - ✅ Production-ready: persistent logs, severity levels, full context

  3. **Migrate from SQLite to production database**
     - Critical for production deployment
     - Evaluate AWS database options:
       - Amazon RDS PostgreSQL (most popular Django choice)
       - Amazon RDS MySQL (compatible, widely supported)
       - Amazon Aurora PostgreSQL (AWS-optimized, auto-scaling)
       - Amazon Aurora MySQL (AWS-optimized)
     - Consider factors: cost, performance, backup/restore, scaling needs
     - Update Django settings.py database configuration
     - Install appropriate database driver (psycopg2 for PostgreSQL, mysqlclient for MySQL)
     - Test all 689 unit tests against new database
     - Test all 28 functional tests against new database
     - Verify Stripe integration works with new database
     - Document migration process and rollback procedure
     - Update requirements.txt with database driver dependencies
     - Must complete before AWS deployment (task #6)

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

  **Current Focus**: Database migration for production readiness
  1. ✅ Completed Backend Phase 1: High priority (272 issues fixed)
  2. ✅ Completed Backend Phase 2: Style/formatting (1,179 issues fixed)
  3. ✅ Completed Backend Phase 3: Critical issues (85 issues fixed)
  4. ✅ Completed Frontend Phase 1: Complete cleanup (5,333 issues fixed - 100% reduction)
  5. ✅ Completed Logging: Replace print() with Django logging (106 replaced, 101 deleted)
  6. ✅ Completed Backend Phase 4-6: Zero linting errors (2,286 → 0, 100% reduction)
  7. ✅ Completed CSRF Token Bug Fix: 100% test pass rate (26 instances fixed, 20 files)
  8. **🔄 NEXT: Database migration from SQLite to PostgreSQL/MySQL (Planned Work Item #3)**
     - Critical blocker for AWS production deployment
     - Evaluate database options (RDS PostgreSQL, RDS MySQL, Aurora)
     - Update Django settings and install database driver
     - Verify all 733 tests pass against new database
     - Document migration process and rollback procedure
  9. ⏳ Future: Expand test coverage (3/19 JavaScript files tested, 16% coverage)
