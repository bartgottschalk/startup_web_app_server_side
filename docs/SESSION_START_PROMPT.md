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

## Tech Stack

- **Backend**: Django 4.2.16 (4.2 LTS), Python 3.12.12, PostgreSQL 16-alpine (multi-tenant), Stripe integration
- **Frontend**: jQuery 3.7.1, nginx:alpine
- **Infrastructure**: Docker Compose with custom bridge network "startupwebapp"
- **Testing**: Selenium 4.27.1 with Firefox ESR (headless mode), 731/731 tests passing (693 unit + 38 functional)
- **Code Quality**: Zero linting errors (flake8, ESLint)
- **AWS Production**: RDS PostgreSQL 16, VPC, Secrets Manager, CloudWatch monitoring, ECS Fargate, ECR

## Current State

**Project Status:** ✅ Phase 5.16 Session 11 Complete - Functional Test Development

**Latest Milestone (December 27, 2025):**
- ✅ 6 new PRE-STRIPE functional tests implemented (32 → 38 functional tests)
- ✅ All automation debt from Session 8 addressed
- ✅ Fixed all pre-existing linting errors in base_functional_test.py (124 errors → 0)
- ✅ Fixed CI race condition in test_checkout_confirm_page_structure()
- ✅ Documented POST-STRIPE functional test decision (not implemented - see technical notes)
- ✅ 731 total tests passing (693 unit + 38 functional)
- 📍 **Next**: TBD - Phase 5.16 Stripe upgrade work or other priorities

### Phase 5.15 Completion (December 4, 2025)

**Production Deployment - FULLY OPERATIONAL:**
- ✅ Backend API: `https://startupwebapp-api.mosaicmeshai.com` (all endpoints working)
- ✅ Frontend: `https://startupwebapp.mosaicmeshai.com` (S3 + CloudFront)
- ✅ `/user/logged-in` returns HTTP 200 (seed data deployed via PR #43)
- ✅ `/order/products` returns HTTP 200 (health check endpoint)
- ✅ Auto-scaling: 1-4 tasks (CPU 70%, Memory 80% targets)
- ✅ CI/CD: Auto-deploy on merge to master

**Key PRs (Phase 5.15):**
- PR #40: ALB health check fixes (5 root causes) - December 3
- PR #41: Auto-scaling + CORS fix - December 4
- PR #42: Deploy workflow health check fix - December 4
- PR #43: Seed data migrations (fixes 500 error) - December 4

**Infrastructure Status:**
- ALB: ✅ Running (`startupwebapp-alb-1304349275.us-east-1.elb.amazonaws.com`)
- ECS Service: ✅ Healthy tasks with auto-scaling
- ACM Certificate: ✅ Issued (`*.mosaicmeshai.com`)
- RDS Database: ✅ Running with seed data
- CloudFront: ✅ Frontend hosting active
- S3: ✅ `startupwebapp-frontend-production`

**CI/CD Workflows:**
- `.github/workflows/pr-validation.yml` - Runs on all PRs to master
- `.github/workflows/deploy-production.yml` - Auto-deploy on push to master (code changes only)
- `.github/workflows/run-admin-command.yml` - Manual admin commands (createsuperuser, collectstatic)
- `.github/workflows/rollback-production.yml` - Manual rollback workflow

**Verify Production:**
```bash
# Health check (should return 200)
curl -I https://startupwebapp-api.mosaicmeshai.com/order/products

# User endpoint (should return 200 with JSON)
curl https://startupwebapp-api.mosaicmeshai.com/user/logged-in
```

**See detailed documentation:** `docs/technical-notes/2025-11-26-phase-5-15-production-deployment.md`

### Previous: Phase 5.14 Complete (November 23-26, 2025)

- Multi-stage Dockerfile (development + production, 59% size reduction)
- AWS ECR repository with image scanning
- ECS Fargate cluster with IAM roles
- GitHub Actions CI/CD pipeline (test → build → push → migrate)
- NAT Gateway for private subnet internet access
- Multi-tenant RDS migrations (57 tables × 3 databases)

### Other Completed Phases

- ✅ Django 4.2.16 LTS upgrade complete
- ✅ Code linting complete (zero errors: backend + frontend)
- ✅ PostgreSQL migration complete (local Docker + AWS RDS)
- ✅ AWS Infrastructure deployed (VPC, RDS, Secrets Manager, Bastion, NAT Gateway)
- ✅ Multi-tenant databases created with 57 tables each
- ✅ All 768 tests passing locally (737 unit + 31 functional)

### Recent Milestones

- PR #32: PostgreSQL migration (Phases 1-6) - November 19, 2025
- PR #36: Phase 9 - Bastion host & separate passwords - November 22, 2025
- PR #37: Bugfix - RDS secret preservation - November 22, 2025
- **Phase 5.14 Complete**: ECS/CI/CD deployment infrastructure - November 26, 2025
- **PR #40**: ALB health check fixes + PR validation workflow - December 3, 2025
- **PR #41**: Auto-scaling + Frontend CORS fix - December 4, 2025
- **PR #42**: Deploy workflow health check fix - December 4, 2025
- **PR #43**: Seed data migrations (fixes 500 error) - December 4, 2025
- **Phase 5.15 Complete**: Full production deployment live - December 4, 2025
- **PR #44**: Cookie domain fix + Phase 5.15 docs - December 4, 2025
- **Client PR #11**: S3 Content-Type fix for extensionless HTML - December 4, 2025
- **PR #45**: Production superuser creation via GitHub Actions - December 7, 2025
- **PR #46**: WhiteNoise for Django Admin static files - December 7, 2025
- **PR #47**: Hotfix - collectstatic in deploy workflow - December 7, 2025
- **PR #48**: Production frontend fixes (ENVIRONMENT_DOMAIN + CloudFront Function) - December 9, 2025
- **Client PR #12**: Updated CloudFront distribution ID - December 9, 2025
- **PR #49**: Stripe library upgrade 5.5.0 → 14.0.1 (Session 2) - December 11, 2025
- **PR #50**: Stripe Checkout Session endpoint (Session 3) - December 12, 2025
- **PR #51**: Checkout session success handler (Session 4) - December 12, 2025
- **PR #52**: Stripe webhook handler (Session 5) - December 13, 2025
- **Client PR #12**: Frontend Stripe Checkout Sessions migration (Session 6) - December 15, 2025
- **PR #53**: Stripe checkout bugfixes (image URLs, shipping, API changes) (Session 6) - December 15, 2025
- **PR #54**: Stripe webhook production configuration (Session 9) - December 19, 2025
- **PR #55**: Frontend checkout login race condition fix (Session 9) - December 19, 2025
- **PR #56**: Email address updates (Session 10) - December 19, 2025
- **Client PR #17**: Email address updates (Session 10) - December 19, 2025
- **PR #57**: Functional test development + linting cleanup (Session 11) - December 27, 2025

### Current Branch

📍 **master** (Phase 5.15 complete, auto-deploy enabled)

**For detailed history**, see: `docs/PROJECT_HISTORY.md`

## ⚠️ CRITICAL: Auto-Deploy on Master Branch

**🚨 AUTOMATIC DEPLOYMENT TO PRODUCTION IS ENABLED 🚨**

- **Merging to `master` automatically deploys to production**
- **ALL work MUST be done in feature/bugfix branches** - NEVER commit directly to master
- **All 731 tests MUST pass** before merging to master
- **Breaking production = test failure** - If something breaks in production, the tests need improvement
- **This is intentional** - Continuous deployment enforces a high bar for test quality
- **PR review is your last checkpoint** - Review code and test results carefully before merging

**Branch Strategy (MANDATORY):**
1. Create feature branch: `git checkout -b feature/descriptive-name`
2. Make changes, commit, push: `git push -u origin feature/descriptive-name`
3. Create PR and verify all 731 tests pass in GitHub Actions
4. Review code and test results carefully
5. Merge to master → **automatic deployment to production**

## Pre-Session Checklist

Before starting work:
1. **HUMAN: START DOCKER DESKTOP FIRST!** - Required for docker-compose commands
2. Verify on master branch with clean working tree (then create feature branch immediately)
3. Read `docs/PROJECT_HISTORY.md` for recent changes
4. Review relevant technical notes in `docs/technical-notes/`
5. **Create feature branch before making ANY changes** - Never work directly on master

## Development Workflow

### Branch Strategy (CRITICAL - Production Auto-Deploy Enabled)

**⚠️ MANDATORY: All changes MUST be in feature/bugfix branches**

- **NEVER commit directly to master** - Merging to master triggers automatic deployment to production
- Branch naming: `feature/descriptive-name` or `bugfix/descriptive-name`
- Run full test suite (all 731 tests) before committing
- Verify zero linting errors before committing
- Create PR after pushing, verify all tests pass in GitHub Actions
- Review code carefully - PR approval is the last checkpoint before production
- **After merge to master**: Automatic deployment begins (tests → build → deploy)

### Testing Requirements

**Unit Tests (PostgreSQL):**
```bash
docker-compose exec backend python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests --parallel=4 --keepdb
```

**Functional Tests (MUST run hosts setup first):**
```bash
docker-compose exec backend bash /app/setup_docker_test_hosts.sh
docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests --keepdb
```

**Note**: Use `--keepdb` flag to reuse test database (faster). Django will automatically handle test database creation/cleanup.

**Code Quality (run before committing):**
```bash
# Backend
docker-compose exec backend flake8 user order clientevent StartupWebApp --max-line-length=120 --statistics

# Frontend (requires Node.js on host)
cd ~/Projects/WebApps/StartUpWebApp/startup_web_app_client_side
npx eslint js/**/*.js --ignore-pattern "js/jquery/**"
```

### Docker Environment
```bash
# Start services
docker-compose up -d

# Start backend server
docker-compose exec -d backend python manage.py runserver 0.0.0.0:8000

# Access
# - Backend API: http://localhost:8000
# - Frontend: http://localhost:8080
```

### AWS Infrastructure Management

**CRITICAL**: All AWS infrastructure scripts (`scripts/infra/*.sh`) must be executed manually in separate terminal windows. **DO NOT run within Claude Code sessions.**

**Scripts location**: `scripts/infra/`
- Resource tracking: `scripts/infra/aws-resources.env` (gitignored)
- Deployment status: `./scripts/infra/status.sh`
- View resources: `./scripts/infra/show-resources.sh`

**Infrastructure Deployed:**
- VPC: vpc-0df90226462f00350 (10.0.0.0/16)
- NAT Gateway: nat-06ecd81baab45cf4a (Elastic IP: 52.206.125.11)
- RDS: startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com:5432
- Bastion: i-0d8d746dd8059de2c (connect: `aws ssm start-session --target i-0d8d746dd8059de2c`)
- ECS Cluster: startupwebapp-cluster (Fargate)
- ECR Repository: startupwebapp-backend (URI: 853463362083.dkr.ecr.us-east-1.amazonaws.com/startupwebapp-backend)
- ALB: startupwebapp-alb (DNS: startupwebapp-alb-1304349275.us-east-1.elb.amazonaws.com)
- ACM Certificate: *.mosaicmeshai.com (issued)
- DNS: startupwebapp-api.mosaicmeshai.com → ALB
- Auto-Scaling: Min 1, Max 4 tasks (CPU 70%, Memory 80% targets)
- Secrets: rds/startupwebapp/multi-tenant/master
- Monitoring: CloudWatch dashboard + 4 alarms + auto-scaling alarms

**Cost**: ~$98/month running (1 task), scales to ~$156/month at max (4 tasks)

### Documentation Requirements

Every commit MUST include documentation updates:
- `docs/PROJECT_HISTORY.md` - Add milestone entries
- `README.md` - Update if user-facing changes
- Technical notes (`docs/technical-notes/YYYY-MM-DD-description.md`) for significant work

### Test-Driven Development (TDD)

**ALWAYS write tests first:**
1. Write tests demonstrating the bug or desired feature
2. Run tests to verify they fail
3. Implement minimum code to make tests pass
4. Refactor while keeping tests passing

## Key Configuration Files

**Gitignored (never commit):**
- `settings_secret.py` - API keys, database passwords, CORS config
- `*.pyc`, `__pycache__/` - Python bytecode
- Database files, static collections, media uploads
- `.env`, `venv/`

**Important configs:**
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Service orchestration
- `scripts/init-multi-db.sh` - PostgreSQL initialization
- `settings.py` & `settings_secret.py` - Django configuration

## Code Patterns

- **Tests**: Use `PostgreSQLTestCase` (from `StartupWebApp.utilities.test_base`)
- **Stripe**: Mock in tests with `@patch('stripe.Customer.retrieve')`
- **Users**: Handle both `Member` and `Prospect` models
- **Validation**: Use `unittest_utilities.validate_response_is_OK_and_JSON()`

## ✅ Phase 5.15 COMPLETE - Production Deployment

**Branch**: `master` (auto-deploy enabled)
**Status**: Full-stack deployed and operational
**Completed**: December 4, 2025

### Implementation Summary

**Backend (ECS Fargate):**
- ✅ ALB: `startupwebapp-alb-1304349275.us-east-1.elb.amazonaws.com`
- ✅ ACM Certificate: `*.mosaicmeshai.com` (wildcard)
- ✅ DNS: `startupwebapp-api.mosaicmeshai.com` → ALB
- ✅ ECS Service: Auto-scaling 1-4 tasks (CPU 70%, Memory 80%)
- ✅ Task Definition: 0.5 vCPU, 1GB, gunicorn with 3 workers

**Frontend (S3 + CloudFront):**
- ✅ S3: `startupwebapp-frontend-production`
- ✅ CloudFront: `E2IQ9KG6S4Y7R3` / `d39qs5j90scefu.cloudfront.net`
- ✅ CloudFront Function: `startupwebapp-directory-index` (rewrites `/account` → `/account/index.html`)
- ✅ DNS: `startupwebapp.mosaicmeshai.com` → CloudFront

**CI/CD:**
- ✅ PR validation: All 768 tests run on PRs
- ✅ Auto-deploy: Merges to master deploy automatically (code changes only)
- ✅ Rollback: Manual workflow available

**Data:**
- ✅ Seed data migrations deployed (PR #43)
- ✅ All endpoints operational

### Infrastructure Scripts Created (Phase 5.15)

```bash
# Step 1: ALB
./scripts/infra/create-alb.sh
./scripts/infra/destroy-alb.sh

# Step 2: ACM Certificate
./scripts/infra/create-acm-certificate.sh
./scripts/infra/destroy-acm-certificate.sh

# Step 3: HTTPS Listener
./scripts/infra/create-alb-https-listener.sh
./scripts/infra/destroy-alb-https-listener.sh

# Step 5: Service Task Definition
./scripts/infra/create-ecs-service-task-definition.sh
./scripts/infra/destroy-ecs-service-task-definition.sh

# Step 6: ECS Service
./scripts/infra/create-ecs-service.sh
./scripts/infra/destroy-ecs-service.sh

# Step 6b: Auto-Scaling
./scripts/infra/create-ecs-autoscaling.sh
./scripts/infra/destroy-ecs-autoscaling.sh

# Step 7: Frontend Hosting (S3 + CloudFront)
./scripts/infra/create-frontend-hosting.sh
./scripts/infra/destroy-frontend-hosting.sh
```

### Production Architecture Decisions

**Domain Configuration:**
- **Backend API**: `startupwebapp-api.mosaicmeshai.com` (ALB → ECS Fargate)
- **Frontend**: `startupwebapp.mosaicmeshai.com` (CloudFront → S3)
- **DNS**: Managed via Namecheap (not Route 53)
- **SSL**: ACM wildcard certificate `*.mosaicmeshai.com` (ISSUED)
- **Pattern for forks**: `{fork}-api.mosaicmeshai.com` / `{fork}.mosaicmeshai.com`

**Deployment Strategy:**
- Backend: Auto-deploy on merge to `master`
- Frontend: Backend-triggered or manual only (NO auto-deploy on frontend merge)
- Migrations: Run automatically in deploy workflow (backward compatible only)
- Default database: `startupwebapp_prod`

### Migration Development Rules (CRITICAL)

**✅ Allowed (Backward Compatible):**
- ADD COLUMN (new columns, old code ignores them)
- CREATE TABLE (new tables, old code doesn't use them)
- ADD INDEX with CONCURRENTLY (no table locks)

**❌ NOT Allowed in Phase 5.15:**
- DROP COLUMN (breaks old code during rollback)
- RENAME COLUMN (breaks old code during rollback)
- ALTER COLUMN TYPE (can break old code)

**Best Practices:**
- Keep migrations fast (<30 seconds ideally, <5 minutes max)
- Test migrations on production snapshot before merging PR
- Use `CREATE INDEX CONCURRENTLY` to avoid table locks

### Coordinated Deployment Workflow

**For changes requiring both backend + frontend updates:**

1. **Develop both PRs** (backend + frontend with same feature name)
2. **Merge frontend FIRST** to master (does NOT auto-deploy)
3. **Backend PR runs tests** against frontend master (validates compatibility)
4. **Merge backend** → auto-deploys both backend + frontend

**For backend-only changes:** Just merge backend (triggers frontend deploy anyway)

**For frontend-only changes:** Manual trigger of frontend deployment workflow

### Technical Details

See: `docs/technical-notes/2025-11-26-phase-5-15-production-deployment.md`

---

## Current Status

**Phase 5.15 Complete + Production Superuser & Django Admin** ✅

### Production Superuser (December 7, 2025) - COMPLETE ✅

**Status**: Fully operational with Django Admin access

**Implementation**: TDD approach with comprehensive testing
- **PR #45**: Production superuser creation via GitHub Actions
- **PR #46**: WhiteNoise for Django Admin static files
- **Hotfixes**: Workflow and Dockerfile fixes

**Django Admin Access:**
- **URL**: https://startupwebapp-api.mosaicmeshai.com/admin/
- **Username**: `prod-admin`
- **Email**: `bart@mosaicmeshai.com`
- **Password**: (stored in LastPass - 16 characters)
- **Status**: ✅ Login working, full CSS styling

**GitHub Actions Workflow:**
- **Workflow**: `.github/workflows/run-admin-command.yml`
- **Usage**: Actions → Run Admin Command → Select command + database
- **Supported commands**: `createsuperuser`, `collectstatic`
- **Credentials**: Fetched from AWS Secrets Manager

**Tests Added:**
- `user/tests/test_superuser_creation.py` (3 unit tests)
- `functional_tests/test_django_admin_login.py` (3 functional tests)
- **Total tests**: 746 passing (715 unit + 31 functional)

**Documentation**: `docs/technical-notes/2025-12-04-production-admin-commands.md`

## Next Steps

### Production Frontend Issues - RESOLVED ✅

**Completed**: December 9, 2025 (PR #48, Client PR #12)

**Issues Fixed**:
1. ✅ `/user/create-account` - 500 error (missing `ENVIRONMENT_DOMAIN` setting)
2. ✅ `/account` - 403 error (CloudFront Function for directory index)
3. ✅ Email configuration (Gmail SMTP for local + production)

**Details**: See `docs/technical-notes/2025-12-07-production-frontend-issues.md`

---

### High Priority Tasks

#### 1. **Stripe Integration Upgrade** (CRITICAL - In Progress)

   **Status**: Phase 5.16 multi-session project - Session 3 COMPLETE ✅

   **Problem:**
   - Current: Stripe Checkout v2 (deprecated, non-functional)
   - Library: ✅ stripe==14.0.1 (upgraded December 11, 2025)
   - Error: "Integration surface is unsupported for publishable key tokenization"
   - Impact: **Payment processing completely broken**

   **Solution:**
   - Migrate to Stripe Checkout Sessions (modern hosted checkout)
   - ✅ Upgraded stripe library to 14.0.1 (Session 2, PR #49, deployed)
   - ✅ Created checkout session endpoint (Session 3, PR #50, pending)
   - 10-session plan documented in `docs/technical-notes/2025-12-11-stripe-upgrade-plan.md`

   **Session Progress:**
   - Session 1: ✅ Planning & assessment complete (branch not merged, superseded)
   - Session 2: ✅ Library upgrade complete (PR #49, merged to master, deployed to production)
   - Session 3: ✅ Checkout session endpoint (PR #50, merged to master, deployed to production)
   - Session 4: ✅ Success handler complete (PR #51, merged to master, deployed to production)
   - Session 5: ✅ Webhook handler complete (PR #52, merged and deployed)
   - Session 6: ✅ Frontend checkout flow complete (Client PR #12, Server PR #53, merged and deployed, production tested)
   - Session 6.5: ✅ Frontend PR validation workflow (Client PR #13, merged, 88 tests + ESLint automated on all PRs)
   - Session 7: ✅ Frontend account payments complete (Client PR #14, merged and deployed)
   - Session 8: ✅ Dead code cleanup + Selenium 4 upgrade (PR #54, merged to master, deployed)
   - Session 9: ✅ Production webhook configuration (PR #55 + Client PR #16, merged and deployed)
   - Session 10: ✅ Email address updates (PR #56 + Client PR #17, merged and deployed)
   - Session 11: 📍 Functional test development (NEXT - automation debt)
   - Session 12: Final documentation

   **Core Infrastructure**: COMPLETE ✅ (Stripe payment processing + email system fully operational)
   **Remaining**: Functional tests, final documentation
   **Estimated Timeline:** 1 day (2 remaining sessions × 2-3 hours each)

   **See:** `docs/technical-notes/2025-12-11-stripe-upgrade-plan.md` for full plan

#### 2. **Email Address Updates** ✅ COMPLETE (December 19, 2025)

   **Status**: Deployed to production via PR #56 (Session 10)

   **Accomplished:**
   - ✅ Updated: `contact@startupwebapp.com` → `bart+startupwebapp@mosaicmeshai.com`
   - ✅ Added professional display name: "StartUpWebApp"
   - ✅ Removed: BCC from all emails
   - ✅ Updated: Phone to 1-800-123-4567, signature to "StartUpWebApp"
   - ✅ Updated: 13 email types (9 code-based + 4 database templates)
   - ✅ Removed PAYMENT INFORMATION from order emails
   - ✅ Fixed anonymous checkout email pre-fill bug

   **Testing:**
   - ✅ All email types tested (local + production)
   - ✅ Order confirmation emails working end-to-end
   - ✅ 693 backend tests + 88 frontend tests passing

   **See**: `docs/technical-notes/2025-12-19-session-10-email-address-updates.md`

#### 3. **Superuser Access to Customer Site** (Security/Design - Deferred)

   **Issue**: Superuser (`prod-admin`) gets 500 error on `/user/logged-in`
   **Cause**: Superuser has no `member` attribute
   **Decision needed**: Should admin users access customer-facing site?
   **Priority**: Low - defer until after Stripe upgrade

### Verify Production
```bash
# Health check (should return 200)
curl -I https://startupwebapp-api.mosaicmeshai.com/order/products

# User endpoint (should return 200 with JSON)
curl https://startupwebapp-api.mosaicmeshai.com/user/logged-in

# Frontend (should load in browser)
open https://startupwebapp.mosaicmeshai.com
```

### Future Work

**Django 5.2 LTS Upgrade** (HIGH PRIORITY - Q1 2026)
- **Current**: Django 4.2.16 LTS (support ends April 2026)
- **Target**: Django 5.2 LTS (supported until April 2028)
- **Timeline**: ~4 months remaining until 4.2 EOL
- **Recommendation**: Start planning January 2026, complete by March 2026
- **Approach**: Use same TDD methodology as 4.2 upgrade (incremental steps)
- **Skip**: Django 6.0 (not LTS, released December 2025)
- **Priority**: High - security patches end April 2026

**Phase 5.17: Production Hardening** (Optional)
- AWS WAF for security
- Enhanced CloudWatch monitoring
- Load testing and performance optimization
- Automated disaster recovery testing

**Other Library Upgrades:**
- ✅ Stripe library upgrade complete (5.5.0 → 14.0.1, Phase 5.16)
- ✅ Selenium upgrade complete (3.141.0 → 4.27.1, Session 8)

**Feature Development:**
- New business functionality as needed

## Key Documentation

- **Project History**: `docs/PROJECT_HISTORY.md`
- **Phase 5.15 (Complete)**: `docs/technical-notes/2025-11-26-phase-5-15-production-deployment.md`
- **Production Admin Commands**: `docs/technical-notes/2025-12-04-production-admin-commands.md`
- **Seed Data Migrations**: `docs/technical-notes/2025-12-04-seed-data-migrations.md`
- **Phase 5.14 (Complete)**: `docs/technical-notes/2025-11-23-phase-5-14-ecs-cicd-migrations.md`
- **AWS RDS Deployment**: `docs/technical-notes/2025-11-19-aws-rds-deployment-plan.md`
- **Infrastructure README**: `scripts/infra/README.md`

## Session Workflow

1. Read `docs/PROJECT_HISTORY.md` for context
2. Confirm task and approach with user
3. Create feature/bugfix branch if making changes
4. Use TDD methodology for all code changes
5. Run full test suite before committing
6. Update documentation
7. Create PR and wait for approval
8. Clean up branches after merge

---

**Ready to start?** Production is live. Ask me what you'd like to work on next.
