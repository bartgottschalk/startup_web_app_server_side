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

**Project Status:** 🚧 Phase 5.14 - Step 7/8: Test Workflow & Run Migrations (IN PROGRESS)

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
- ✅ **Step 3 Complete**: AWS ECS Infrastructure (November 24, 2025)
  - ECS Cluster: startupwebapp-cluster (Fargate)
  - IAM Roles: ecsTaskExecutionRole-startupwebapp, ecsTaskRole-startupwebapp
  - CloudWatch log group: /ecs/startupwebapp-migrations (7-day retention)
  - Security groups updated (Backend SG → RDS + ECR)
  - Infrastructure scripts: create-ecs-cluster.sh, create-ecs-task-role.sh, update-security-groups-ecs.sh, destroy scripts
  - Full lifecycle tested (create → destroy → recreate)
  - Cost: $0 (pay-per-use for tasks: ~$0.0137/hour when running)
- ✅ **Step 4 Complete**: ECS Task Definition (November 24, 2025)
  - Task definition: startupwebapp-migration-task (revision 2)
  - Configuration: 0.25 vCPU, 512 MB RAM, Fargate launch type
  - Secrets Manager integration for DB credentials
  - Command: python manage.py migrate
  - Infrastructure scripts: create-ecs-task-definition.sh, destroy-ecs-task-definition.sh (fully tested)
  - Production Docker image pushed to ECR (157 MB compressed)
  - Full lifecycle tested (create → destroy → recreate)
  - Cost: $0 (task definition free; tasks cost ~$0.001 per 5-minute run)
- ✅ **Step 5 Complete**: GitHub Actions CI/CD Workflow (November 25, 2025)
  - Workflow file: .github/workflows/run-migrations.yml (200+ inline comments)
  - Manual trigger with database selection dropdown
  - Four-job pipeline: Test (5-7 min) → Build (3-5 min) → Migrate (2-5 min) → Summary (10 sec)
  - Job 1: Runs 740 tests (712 unit + 28 functional) with PostgreSQL 16 service container
  - Job 2: Builds production Docker image, tags with git commit SHA, pushes to ECR
  - Job 3: Updates ECS task definition, launches Fargate task, fetches CloudWatch logs
  - Job 4: Displays workflow summary and success/failure status
  - User guide: docs/GITHUB_ACTIONS_GUIDE.md (comprehensive setup and troubleshooting)
  - Total pipeline duration: ~10-17 minutes per database
  - Cost: Negligible (~$0.10/month for ~100 migration runs)
- ✅ **Step 6 Complete**: Configure GitHub Secrets (November 25, 2025)
  - Created IAM user: github-actions-startupwebapp
  - IAM policies attached: AmazonEC2ContainerRegistryPowerUser, AmazonECS_FullAccess, CloudWatchLogsReadOnlyAccess
  - Generated AWS access keys for programmatic access
  - Added 3 secrets to GitHub repository:
    - AWS_ACCESS_KEY_ID (IAM user access key)
    - AWS_SECRET_ACCESS_KEY (IAM user secret key)
    - AWS_REGION (us-east-1)
  - Workflow now has AWS credentials for ECR push, ECS task execution, CloudWatch logs
  - Security: Credentials encrypted by GitHub, never exposed in logs
  - **Workflow debugging and fixes completed**:
    - Fixed skip_tests boolean logic (string comparison issue)
    - Excluded migrations from flake8 linting (auto-generated files)
    - Created settings_secret.py for CI environment (matched template structure)
    - Fixed Stripe setting names (STRIPE_SERVER_SECRET_KEY vs STRIPE_SECRET_KEY)
    - Fixed Firefox installation (using snap for Ubuntu 24.04 instead of firefox-esr)
    - Added /etc/hosts entries for functional tests (hostname resolution)
    - Set DOCKER_ENV variable for functional tests (skip frontend server, use backend directly)
  - **7 workflow iterations** completed to debug and fix all issues
  - Workflow now ready for testing with all 740 tests
- 🚧 **Step 7 In Progress**: Test Workflow & Run Migrations (November 25, 2025)
  - Workflow triggered, currently running
  - Testing full pipeline: tests → build → push to ECR → run migrations
  - Target database: startupwebapp_prod
  - Expected: All 740 tests pass, migrations applied successfully
- 📍 **Current Branch**: `master` (PR #38 merged)

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

**Phase 5.14 Implementation Steps** (6-7 hours estimated, 6/8 steps complete, Step 7 in progress):

1. ✅ **Create Multi-Stage Dockerfile** (45 min) - COMPLETE
   - Development target: includes test dependencies (Firefox, geckodriver)
   - Production target: minimal, optimized for deployment
   - Shared base layer for efficiency
   - Result: Dev 1.69 GB, Prod 692 MB (59% smaller)

2. ✅ **Create AWS ECR Repository** (20 min) - COMPLETE
   - Docker image registry in AWS
   - Image scanning and lifecycle policies (keep 10 images)
   - Infrastructure scripts: create-ecr.sh, destroy-ecr.sh (fully tested)
   - Repository: startupwebapp-backend
   - URI: 853463362083.dkr.ecr.us-east-1.amazonaws.com/startupwebapp-backend
   - Cost: ~$0.10-$0.20/month

3. ✅ **Create ECS Infrastructure** (45 min) - COMPLETE
   - ECS Fargate cluster (serverless containers)
   - IAM roles for task execution (pull images, read secrets)
   - Security groups (allow ECS → RDS access)
   - Infrastructure scripts: create-ecs-cluster.sh, create-ecs-task-role.sh, update-security-groups-ecs.sh
   - Full lifecycle tested (create → destroy → recreate)
   - Cost: $0 (pay-per-use for tasks)

4. ✅ **Create ECS Task Definition** (30 min) - COMPLETE
   - Infrastructure scripts: create-ecs-task-definition.sh, destroy-ecs-task-definition.sh
   - Task definition: startupwebapp-migration-task (0.25 vCPU, 512 MB RAM)
   - Pulls credentials from AWS Secrets Manager
   - Full lifecycle tested (create → destroy → recreate)
   - Production Docker image pushed to ECR

5. ✅ **Set Up GitHub Actions CI/CD** (60 min) - COMPLETE
   - Workflow: `.github/workflows/run-migrations.yml` (200+ inline comments)
   - Four-job pipeline: Test (740 tests) → Build → Push to ECR → Run ECS task → Summary
   - Manual trigger with database selection dropdown
   - User guide: `docs/GITHUB_ACTIONS_GUIDE.md` (setup + troubleshooting)
   - Total duration: ~10-17 minutes per database

6. ✅ **Configure GitHub Secrets** (180 min) - COMPLETE
   - Created IAM user with programmatic access
   - Added 3 secrets to GitHub: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
   - **Workflow debugging** (7 iterations to fix all issues):
     - Fixed skip_tests boolean logic (string comparison)
     - Excluded migrations from flake8 linting
     - Generated settings_secret.py for CI (matched template)
     - Fixed Stripe setting names (SERVER_SECRET_KEY)
     - Fixed Firefox for Ubuntu 24.04 (snap vs firefox-esr)
     - Added /etc/hosts for functional tests
     - Set DOCKER_ENV for functional tests (no frontend server)
   - Note: Took significantly longer than estimated due to debugging

7. 🚧 **Run Migrations via Pipeline** (45 min) - IN PROGRESS
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
