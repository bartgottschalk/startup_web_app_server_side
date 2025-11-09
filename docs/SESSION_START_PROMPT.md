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
  - Code linting analysis: ✅ Completed - November 9, 2025
  - Test suite: 721/721 tests passing (693 unit + 28 functional)
  - Master branch is clean and up-to-date
  - Both repositories cloned to: ~/Projects/startup_web_app_server_side and ~/Projects/startup_web_app_client_side

  **Recent Completed Work:**
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
    docker-compose exec backend flake8 user order clientevent StartupWebApp --max-line-length=100 --statistics
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

  1. **✅ Linting (Completed - November 9, 2025)**
     - ✅ Installed linting tools: pylint, flake8, ESLint, Node.js 25.1.0
     - ✅ Analyzed 9,313 code quality issues across both repositories
     - ✅ Created comprehensive findings report (see technical notes)
     - ✅ Added linting to development workflow
     - ✅ Fixed critical bug: SMTPDataError import missing (user/admin.py)
     - ⏳ **Next**: Decide on strategy for remaining 9,311 linting issues

  2. **Replace print statements with proper logging**
     - Convert print() to logging.debug(), logging.warning(), logging.error()
     - Set up proper logging configuration in settings.py
     - Improves production debugging and monitoring
     - Makes debugging easier for deployment

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

  **Current Focus**: Critical linting bug fixed. Next priorities:
  1. ✅ Fixed critical SMTPDataError bug (user/admin.py) with TDD approach
  2. Decide on strategy for addressing remaining 9,311 linting issues
  3. Replace print statements with proper logging (Planned Work Item #2)
  4. Database migration planning (Planned Work Item #3)
