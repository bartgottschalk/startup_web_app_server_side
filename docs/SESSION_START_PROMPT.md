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
- **AWS Production**: RDS PostgreSQL 16, VPC, Secrets Manager, CloudWatch monitoring

## Current State

**Project Status:** 🚧 Phase 5.14 - Step 3/9: AWS ECS Cluster (NEXT)

- ✅ Django 4.2.16 LTS upgrade complete
- ✅ Code linting complete (zero errors)
- ✅ PostgreSQL migration complete (local Docker + AWS RDS)
- ✅ AWS Infrastructure deployed (Phase 5.13/Phase 9: VPC, RDS, Secrets Manager, Bastion)
- ✅ Multi-tenant databases created (startupwebapp_prod, healthtech_experiment, fintech_experiment)
- ✅ All 740 tests passing locally (712 unit + 28 functional)
- ✅ **Step 1 Complete**: Multi-Stage Dockerfile (November 23, 2025)
  - Development image: 1.69 GB with Firefox/geckodriver for tests
  - Production image: 692 MB with gunicorn (59% smaller)
  - Files: Dockerfile, requirements.txt, .dockerignore updated and tested
- ✅ **Step 2 Complete**: AWS ECR Repository (November 24, 2025)
  - Repository: startupwebapp-backend
  - URI: 853463362083.dkr.ecr.us-east-1.amazonaws.com/startupwebapp-backend
  - Image scanning enabled, lifecycle policy configured (keep 10 images)
  - Infrastructure scripts: create-ecr.sh, destroy-ecr.sh (fully tested)
  - Cost: ~$0.10-$0.20/month
- 🚧 **Step 3 Next**: Create AWS ECS Cluster (Fargate infrastructure)
- 📍 **Current Branch**: `feature/phase-5-14-ecs-cicd-migrations`

**Phase 5.14 Goals:**
1. Create multi-stage Dockerfile (development + production targets)
2. Set up AWS ECS Fargate infrastructure (cluster, task definitions, IAM roles)
3. Create AWS ECR for Docker image registry
4. Build GitHub Actions CI/CD pipeline (test → build → deploy)
5. Run Django migrations on RDS via automated pipeline
6. Validate 57 tables created on all 3 production databases

**Recent Milestones:**
- PR #32: PostgreSQL migration (Phases 1-6) - November 19, 2025
- PR #36: Phase 9 - Bastion host & separate passwords - November 22, 2025
- PR #37: Bugfix - RDS secret preservation - November 22, 2025
- Phase 5.14 Started: November 23, 2025 - ECS/CI/CD deployment infrastructure

**For detailed history**, see: `docs/PROJECT_HISTORY.md`

## Pre-Session Checklist

Before starting work:
1. **HUMAN: START DOCKER DESKTOP FIRST!** - Required for docker-compose commands
2. Verify on master branch with clean working tree
3. Read `docs/PROJECT_HISTORY.md` for recent changes
4. Review relevant technical notes in `docs/technical-notes/`

## Development Workflow

### Branch Strategy
- All changes in feature/bugfix branches (never directly on master)
- Branch naming: `feature/descriptive-name` or `bugfix/descriptive-name`
- Run full test suite before committing
- Create PR after pushing, wait for approval before merging

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
- RDS: startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com:5432
- Bastion: i-0d8d746dd8059de2c (connect: `aws ssm start-session --target i-0d8d746dd8059de2c`)
- Secrets: rds/startupwebapp/multi-tenant/master
- Monitoring: CloudWatch dashboard + 4 alarms

**Cost**: $36/month running ($30/month with bastion stopped)

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

## Next Steps (Phase 5.14 - IN PROGRESS)

**Current Focus**: ECS Infrastructure, GitHub Actions CI/CD, and RDS Migrations

**Phase 5.14 Implementation Steps** (6-7 hours estimated):

1. ✅ **Create Multi-Stage Dockerfile** (45 min) - COMPLETE
   - Development target: includes test dependencies (Firefox, geckodriver)
   - Production target: minimal, optimized for deployment
   - Shared base layer for efficiency
   - Result: Dev 1.69 GB, Prod 692 MB (59% smaller)

2. 🚧 **Create AWS ECR Repository** (20 min) - NEXT
   - Docker image registry in AWS
   - Image scanning and lifecycle policies
   - Infrastructure script: `scripts/infra/create-ecr.sh`

3. **Create ECS Infrastructure** (45 min)
   - ECS Fargate cluster (serverless containers)
   - IAM roles for task execution (pull images, read secrets)
   - Security groups (allow ECS → RDS access)
   - Infrastructure scripts: `scripts/infra/create-ecs-*.sh`

4. **Create ECS Task Definition** (30 min)
   - Migration task: runs `python manage.py migrate`
   - 0.25 vCPU, 0.5 GB RAM
   - Pulls credentials from AWS Secrets Manager

5. **Set Up GitHub Actions CI/CD** (60 min)
   - Workflow: `.github/workflows/run-migrations.yml`
   - Pipeline: Test (740 tests) → Build → Push to ECR → Run ECS task
   - Manual trigger with database selection dropdown

6. **Configure GitHub Secrets** (10 min)
   - Add AWS credentials to GitHub repository secrets
   - Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

7. **Run Migrations via Pipeline** (45 min)
   - Trigger GitHub Actions for each database
   - Monitor CloudWatch logs
   - Verify 57 tables created on each database

8. **Verification & Documentation** (50 min)
   - Confirm all migrations successful
   - Update PROJECT_HISTORY.md
   - Update documentation

**After Phase 5.14**:
- Phase 5.15: Full production deployment (ECS service, ALB, auto-scaling)
- Phase 5.16: Production hardening (WAF, monitoring, load testing)

**Other Planned Work**:
- Consider Stripe library upgrade (optional)
- Consider Selenium 4 upgrade (optional)

## Key Documentation

- **Project History**: `docs/PROJECT_HISTORY.md`
- **Phase 5.14 Plan (Current)**: `docs/technical-notes/2025-11-23-phase-5-14-ecs-cicd-migrations.md`
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

**Ready to start?** Ask me what you'd like to work on, or I can propose continuing Phase 5.14 (ECS Infrastructure, CI/CD, and RDS Migrations).
