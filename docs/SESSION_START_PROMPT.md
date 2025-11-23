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

**Project Status:** Production-ready infrastructure deployed, ready for Django migrations on AWS RDS

- ✅ Django 4.2.16 LTS upgrade complete
- ✅ Code linting complete (zero errors)
- ✅ PostgreSQL migration complete (local Docker + AWS RDS)
- ✅ AWS Infrastructure 100% deployed (7/7 steps, $36/month)
- ✅ Multi-tenant databases created (startupwebapp_prod, healthtech_experiment, fintech_experiment)
- ✅ Bastion host with SSM access
- ✅ Separate master/application database passwords (security best practice)
- ✅ All 740 tests passing (712 unit + 28 functional)
- 📍 **Next**: Phase 10 - Run Django migrations on AWS RDS

**Recent Milestones:**
- PR #32: PostgreSQL migration (Phases 1-6) - November 19, 2025
- PR #36: Phase 9 - Bastion host & separate passwords - November 22, 2025
- PR #37: Bugfix - RDS secret preservation - November 22, 2025

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

## Next Steps (Phase 10)

**Current Focus**: Django Migrations & Production Deployment

1. **Run Django migrations on AWS RDS**
   - Connect to RDS via bastion or local machine
   - Run migrations on all 3 databases
   - Verify tables created successfully

2. **Update production credentials**
   - Add real Stripe API keys to Secrets Manager
   - Add real Email SMTP credentials to Secrets Manager

3. **Test Django application against AWS RDS**
   - Configure Django to use AWS RDS
   - Test all endpoints and functionality
   - Verify Stripe and email integrations

4. **Deploy backend to AWS**
   - Containerize Django for production
   - Choose deployment platform (ECS, EC2, or other)
   - Deploy with proper security and scaling

**Other planned work:**
- Consider Stripe library upgrade (optional)
- Consider Selenium 4 upgrade (optional)
- Setup CI/CD pipeline

## Key Documentation

- **Project History**: `docs/PROJECT_HISTORY.md`
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

**Ready to start?** Ask me what you'd like to work on, or I can propose starting Phase 10 (Django migrations on AWS RDS).
