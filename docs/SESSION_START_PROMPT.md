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
- **Testing**: Selenium 3.141.0 with Firefox ESR (headless mode), 740/740 tests passing
- **Code Quality**: Zero linting errors (pylint, flake8, ESLint)
- **AWS Production**: RDS PostgreSQL 16, VPC, Secrets Manager, CloudWatch monitoring, ECS Fargate, ECR

## Current State

**Project Status:** 🚧 Phase 5.15 In Progress - Health Check Fix Complete, Remaining Steps Pending

### Current Work: Phase 5.15 (December 3, 2025)

**ALB Health Check Fix - COMPLETE:**
- ✅ All 5 root causes identified and fixed
- ✅ Infrastructure recreated with correct health check path
- ✅ Health checks passing

**All 5 Root Causes Fixed:**
1. **`SECURE_PROXY_SSL_HEADER`** - Trust ALB's X-Forwarded-Proto header
2. **`ALLOWED_HOSTS` container IPs** - ECS metadata IP fetching
3. **`SECURE_REDIRECT_EXEMPT`** - Exempt health check from SSL redirect
4. **Health check path** - `/order/products` (no trailing slash to match Django URL pattern)
5. **Trailing slash mismatch** - Django URL has no slash, health check must match

**Key Commits:**
- `e35ed31` - PR #40: Initial fixes (root causes 1-3)
- `21f53ca` - SECURE_REDIRECT_EXEMPT (root cause 4)
- `2f36dcd` - Trailing slash fix (root cause 5)

**Infrastructure Status:**
- ALB: ✓ Running (health check path: `/order/products`)
- ECS Service: ✓ Running (2 tasks across 2 AZs)
- ACM Certificate: ✓ Exists (`*.mosaicmeshai.com`)
- ECR Repository: ✓ Exists
- ECS Cluster: ✓ Exists
- RDS Database: ✓ Exists

**Future Task:** Standardize all Django URL patterns to use trailing slashes (codebase-wide refactor)

**PR Validation Workflow Added**
- Created `.github/workflows/pr-validation.yml`
- Runs on all PRs to master: flake8 linting + unit tests + functional tests
- Catches issues before merge (prevents broken code reaching master)

**Health Check Endpoint Rationale:**
- `/order/products/` validates Django is running
- Validates database connectivity (queries Product table)
- Does NOT require authentication
- Lightweight query suitable for frequent health checks (every 30s)

**FRONTEND_REPO_TOKEN** - Still needs fix (separate issue):
- Fine-grained PAT needs **Contents: Read and write** permission
- Go to: https://github.com/settings/tokens?type=beta

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
- ✅ All 740 tests passing locally (712 unit + 28 functional)

### Recent Milestones

- PR #32: PostgreSQL migration (Phases 1-6) - November 19, 2025
- PR #36: Phase 9 - Bastion host & separate passwords - November 22, 2025
- PR #37: Bugfix - RDS secret preservation - November 22, 2025
- **Phase 5.14 Complete**: ECS/CI/CD deployment infrastructure - November 26, 2025
- **PR #40**: ALB health check fixes + PR validation workflow - December 3, 2025

### Current Branch

📍 **master** (Phase 5.15 in progress, auto-deploy enabled)

**For detailed history**, see: `docs/PROJECT_HISTORY.md`

## ⚠️ CRITICAL: Auto-Deploy on Master Branch

**🚨 AUTOMATIC DEPLOYMENT TO PRODUCTION IS ENABLED 🚨**

- **Merging to `master` automatically deploys to production** (after Phase 5.15)
- **ALL work MUST be done in feature/bugfix branches** - NEVER commit directly to master
- **All 740 tests MUST pass** before merging to master
- **Breaking production = test failure** - If something breaks in production, the tests need improvement
- **This is intentional** - Continuous deployment enforces a high bar for test quality
- **PR review is your last checkpoint** - Review code and test results carefully before merging

**Branch Strategy (MANDATORY):**
1. Create feature branch: `git checkout -b feature/descriptive-name`
2. Make changes, commit, push: `git push -u origin feature/descriptive-name`
3. Create PR and verify all 740 tests pass in GitHub Actions
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
- Run full test suite (all 740 tests) before committing
- Verify zero linting errors before committing
- Create PR after pushing, verify all tests pass in GitHub Actions
- Review code carefully - PR approval is the last checkpoint before production
- **After merge to master**: Automatic deployment begins (tests → build → deploy)

### Testing Requirements

**Unit Tests (PostgreSQL):**
```bash
docker-compose exec backend python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests --parallel=4
```

**Functional Tests (MUST run hosts setup first):**
```bash
docker-compose exec backend bash /app/setup_docker_test_hosts.sh
docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests
```

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
- ALB: startupwebapp-alb (DNS: startupwebapp-alb-152031950.us-east-1.elb.amazonaws.com)
- ACM Certificate: *.mosaicmeshai.com (issued)
- DNS: startupwebapp-api.mosaicmeshai.com → ALB
- Secrets: rds/startupwebapp/multi-tenant/master
- Monitoring: CloudWatch dashboard + 4 alarms

**Cost**: ~$84/month running (~$78/month with bastion stopped)

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

## 🚧 Phase 5.15 IN PROGRESS - Production Deployment

**Branch**: `master` (auto-deploy enabled)
**Status**: Backend deployed, debugging health checks
**Goal**: Deploy full-stack application to production with continuous deployment

### Current Implementation Status (December 2, 2025)

**✅ Steps 1-6 Complete:**
1. ✅ **Application Load Balancer** - `startupwebapp-alb` created with HTTP→HTTPS redirect
2. ✅ **ACM Certificate** - `*.mosaicmeshai.com` wildcard certificate issued
3. ✅ **HTTPS Listener** - TLS 1.2/1.3 termination on ALB port 443
4. ✅ **DNS Configuration** - `startupwebapp-api.mosaicmeshai.com` CNAME → ALB
5. ✅ **Service Task Definition** - `startupwebapp-service-task` (0.5 vCPU, 1GB, gunicorn)
6. ✅ **ECS Service** - 2 tasks running across 2 AZs

**✅ Step 10 Complete (moved up):**
- `deploy-production.yml` - Auto-deploy on push to master (tests → migrate → deploy backend → trigger frontend)
- `rollback-production.yml` - Manual rollback workflow

**🚧 Current Issues to Fix (see "Next Steps" section for details):**
1. **Missing `SECURE_PROXY_SSL_HEADER`** - Causes 301 redirect loop
2. **`ALLOWED_HOSTS` doesn't accept VPC IPs** - Causes 400 error on health checks
3. **Health check path needs trailing slash** - `/order/products` → `/order/products/`
4. **FRONTEND_REPO_TOKEN permissions** - Need to add Contents: Read and write to fine-grained PAT

**Remaining Steps (after health checks fixed):**
7. Configure Auto-Scaling (1-4 tasks based on CPU/memory)
8. Setup S3 + CloudFront (frontend static hosting)
11. Django production settings - mostly done, may need tweaks
12. Verification and documentation

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

## Next Steps

**🚧 Phase 5.15 Remaining Steps**

### Completed (December 3, 2025)
- ✅ ALB Health Check Fix (all 5 root causes)
- ✅ PR Validation Workflow
- ✅ Production Deployment Workflow

### Remaining Phase 5.15 Steps
- Step 7: Configure Auto-Scaling (1-4 tasks based on CPU/memory)
- Step 8: Setup S3 + CloudFront (frontend static hosting)
- Step 12: Final verification and documentation

### Verify Production is Working
```bash
# Check health checks
source scripts/infra/aws-resources.env
aws elbv2 describe-target-health --target-group-arn $TARGET_GROUP_ARN

# Test endpoint
curl -I https://startupwebapp-api.mosaicmeshai.com/order/products
```

Expected: All targets healthy, HTTP 200 response

---

**Separate Issue: FRONTEND_REPO_TOKEN permissions**
- Go to: https://github.com/settings/tokens?type=beta
- Edit token for `startup_web_app_client_side`
- Add **Contents: Read and write** permission

**Remaining Phase 5.15 Steps (after health checks work):**
- Step 7: Configure Auto-Scaling (1-4 tasks based on CPU/memory)
- Step 8: Setup S3 + CloudFront (frontend)
- Step 12: Final verification and documentation

**After Phase 5.15:**
- **Phase 5.16**: Production Hardening (WAF, enhanced monitoring, load testing)
- **Other Work**: Stripe library upgrade, Selenium 4 upgrade, feature development

## Key Documentation

- **Project History**: `docs/PROJECT_HISTORY.md`
- **Phase 5.14 (Complete)**: `docs/technical-notes/2025-11-23-phase-5-14-ecs-cicd-migrations.md`
- **Phase 5.15 Plan (Next)**: `docs/technical-notes/2025-11-26-phase-5-15-production-deployment.md`
- **AWS RDS Deployment**: `docs/technical-notes/2025-11-19-aws-rds-deployment-plan.md`
- **Phase 9 Deployment Guide**: `docs/technical-notes/2025-11-21-phase-9-deployment-guide.md`
- **Bastion Troubleshooting**: `docs/technical-notes/2025-11-22-phase-9-bastion-troubleshooting.md`
- **RDS Secret Bugfix**: `docs/technical-notes/2025-11-22-rds-secret-preservation-bugfix.md`
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

**Ready to start?** Ask me what you'd like to work on, or I can propose starting Phase 5.15 (Full Production Deployment).
