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

**Project Status:** ✅ Phase 5.15 Complete - Full Production Deployment Live

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
- ✅ All 740 tests passing locally (712 unit + 28 functional)

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

### Current Branch

📍 **master** (Phase 5.15 complete, auto-deploy enabled)

**For detailed history**, see: `docs/PROJECT_HISTORY.md`

## ⚠️ CRITICAL: Auto-Deploy on Master Branch

**🚨 AUTOMATIC DEPLOYMENT TO PRODUCTION IS ENABLED 🚨**

- **Merging to `master` automatically deploys to production**
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
- ✅ CloudFront: `E1HZ3V09L2NDK1` / `d34ongxkfo84gr.cloudfront.net`
- ✅ DNS: `startupwebapp.mosaicmeshai.com` → CloudFront

**CI/CD:**
- ✅ PR validation: All 740 tests run on PRs
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

## Next Steps

**Phase 5.15 is complete.** The full-stack application is deployed to production with continuous deployment.

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

**Phase 5.16: Production Hardening** (Optional)
- AWS WAF for security
- Enhanced CloudWatch monitoring
- Load testing and performance optimization

**Other Work:**
- Stripe library upgrade
- Selenium 4 upgrade
- Feature development

## Key Documentation

- **Project History**: `docs/PROJECT_HISTORY.md`
- **Phase 5.15 (Complete)**: `docs/technical-notes/2025-11-26-phase-5-15-production-deployment.md`
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
