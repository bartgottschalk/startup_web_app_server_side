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

  **Current State:**
  - Django upgrade: ✅ Completed (2.2.28 → 4.2.16 LTS) - November 6, 2025
  - Post-upgrade documentation: ✅ Completed - November 7, 2025
  - Test suite: 707/707 tests passing (679 unit + 28 functional)
  - Master branch is clean and up-to-date
  - Both repositories cloned to: ~/Projects/startup_web_app_server_side and ~/Projects/startup_web_app_client_side

  **Recent Completed Work:**
  - **Phase 4 (November 6, 2025)**: Django 2.2.28 → 4.2.16 LTS upgrade
    - Incremental 6-step upgrade completed in 3.8 hours
    - Zero test regressions, minimal code changes
    - Security support extended until April 2026
  - **Phase 3 (November 7, 2025)**: Additional test coverage
    - Added 53 new unit tests (626→679 total)
    - Fixed critical production bug: checkout_allowed NameError in user/views.py:1057,1060
    - Achieved 100% functional test pass rate (was 24/28, now 28/28)
    - Coverage improvements: order/views.py (99%), order_utils.py (96%), user/views.py (89%)

  ## Pre-Session Checklist

  Before starting work:
  1. Verify both repos are on master branch with no uncommitted changes
  2. Verify no pending branches with changes
  3. Read key documentation files:
     - `docs/PROJECT_HISTORY.md` - Project timeline and current status
     - `KNOWN_ISSUES.md` - Current priorities and blockers
     - `docs/milestones/2025-11-06-phase-4-django-upgrade-to-4-2-lts.md` - Most recent work
  4. Review full gitignore files in both projects and respect them
  5. Flag any new files/extensions that should be added to gitignore

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
  - Unit tests: `docker-compose exec backend python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests` (679 tests)
  - **Functional tests: MUST run hosts setup first, then tests:**
    ```bash
    docker-compose exec backend bash /app/setup_docker_test_hosts.sh
    docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests
    ```
  - IMPORTANT: All functional tests MUST use HEADLESS=TRUE environment variable
  - If documentation contradicts HEADLESS=TRUE requirement, flag it for correction
  - Coverage analysis: `coverage run --source='.' manage.py test && coverage report`

  **Docker Environment:**
  - Backend API: http://localhost:8000
  - Frontend: http://localhost:8080
  - Start services: `docker-compose up -d`
  - Backend server: `docker-compose exec -d backend python manage.py runserver 0.0.0.0:8000`
  - Custom bridge network: "startupwebapp" (enables inter-service communication)

  **Documentation Requirements:**
  - Every commit MUST include updated documentation
  - Key doc files: `docs/PROJECT_HISTORY.md`, `README.md`, `KNOWN_ISSUES.md`
  - Key doc directories: `docs/milestones/`, `docs/technical-notes/`
  - Create new milestone docs for significant work (follow existing naming: YYYY-MM-DD-phase-description.md)
  - Update test counts and coverage stats when changed
  - Document all bugs found and fixed

  **Testing Conventions:**
  - Use unittest.mock for external API calls (especially Stripe)
  - Test both authenticated (Member) and anonymous (Prospect) user flows
  - Include edge cases and error handling scenarios
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

  1. **Address Known Issues List**
     - Review and prioritize items in KNOWN_ISSUES.md
     - Identify urgent production bugs vs. enhancements
     - Triage and fix documented issues in priority order
     - Update KNOWN_ISSUES.md as items are resolved

  2. **Fix Stripe Errors on Account Page**
     - Investigate and resolve Stripe-related errors on account page
     - May already be documented in Known Issues List
     - Add tests to prevent regression
     - User-facing issue requiring prompt resolution

  3. **Linting**
     - Run code linters (pylint, flake8, or similar for Python; ESLint for JavaScript)
     - Address style and quality issues
     - Enforce consistent code standards across both repos
     - May reveal hidden bugs (unused imports, undefined variables, etc.)
     - Establishes baseline before making more changes

  4. **Replace print statements with proper logging**
     - Convert print() to logging.debug(), logging.warning(), logging.error()
     - Set up proper logging configuration in settings.py
     - Improves production debugging and monitoring
     - Makes debugging easier for deployment

  5. **Migrate from SQLite to production database**
     - Critical for production deployment
     - Evaluate AWS database options:
       - Amazon RDS PostgreSQL (most popular Django choice)
       - Amazon RDS MySQL (compatible, widely supported)
       - Amazon Aurora PostgreSQL (AWS-optimized, auto-scaling)
       - Amazon Aurora MySQL (AWS-optimized)
     - Consider factors: cost, performance, backup/restore, scaling needs
     - Update Django settings.py database configuration
     - Install appropriate database driver (psycopg2 for PostgreSQL, mysqlclient for MySQL)
     - Test all 679 unit tests against new database
     - Test all 28 functional tests against new database
     - Verify Stripe integration works with new database
     - Document migration process and rollback procedure
     - Update requirements.txt with database driver dependencies
     - Must complete before AWS deployment (task #8)

  6. **Consider Stripe library upgrade (optional)**
     - Current: stripe==5.5.0
     - Evaluate upgrade path and breaking changes
     - Review Stripe API changelog for new features and deprecations
     - Test thoroughly with existing payment flows (especially after fixing task #2)
     - Only proceed if benefits outweigh risks

  7. **Consider Selenium 4 upgrade (optional)**
     - Current: Selenium 3.141.0
     - Evaluate benefits (better waits, modern WebDriver API, improved stability)
     - May require functional test refactoring
     - All 28 tests currently passing - low priority
     - Consider during major test infrastructure updates

  8. **Prepare containers for deployment to AWS for "production"**
     - Configure production-ready Docker images (security, optimization)
     - Set up environment variable management for secrets (AWS Secrets Manager or Parameter Store)
     - Configure production database connection (from task #5)
     - Set up S3 for static files and media storage
     - Configure CloudFront CDN for frontend
     - Implement health checks and monitoring
     - Security hardening (disable DEBUG, set ALLOWED_HOSTS, configure HTTPS)
     - Review and configure AWS security groups, IAM roles
     - Depends on task #5 (database migration)

  9. **Setup CI/CD pipeline**
     - Configure GitHub Actions or AWS CodePipeline
     - Automated testing on push:
       - Run all 679 unit tests
       - Run all 28 functional tests (with HEADLESS=TRUE)
       - Fail pipeline if any tests fail
     - Trigger deployment on successful test run:
       - Deploy to AWS when master is updated
       - Consider staging environment for feature/bugfix branches
     - Configure deployment to AWS (ECS, EKS, or Elastic Beanstalk)
     - Set up rollback mechanism for failed deployments
     - Configure deployment notifications (Slack, email, etc.)
     - Depends on task #8 (AWS infrastructure ready)

  ## Next Steps

  Please review all documentation (especially `docs/PROJECT_HISTORY.md` and `KNOWN_ISSUES.md`) and propose next steps based on the Planned Work Items above, starting with #1: Address Known Issues List.
