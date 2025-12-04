# Production Admin Commands

**Date**: December 4, 2025
**Status**: Planning
**Phase**: Post Phase 5.15 (Production Operational)

## Overview

This document describes the approach for running Django admin commands (like `createsuperuser`) in production. The goal is to create a documented, repeatable, and secure process for administrative operations.

## Problem Statement

After deploying the application to production (Phase 5.15), we discovered that no superuser exists in the production database. This means:
- No access to Django Admin interface (`/admin/`)
- No ability to manage users, orders, or other data via the admin UI
- No way to perform administrative tasks that require staff/superuser privileges

We need a way to:
1. Create a superuser in production
2. Make this process repeatable (for future environments, disaster recovery)
3. Document it for future reference
4. Keep it secure

## Options Considered

### Option 1: Direct SQL via Bastion Host

**Approach**: Connect to RDS via bastion host and INSERT directly into `auth_user` table.

**Pros**:
- Quick one-time operation
- Only people with AWS access can run it

**Cons**:
- Requires manually hashing the password with Django's algorithm
- Error-prone (easy to miss required fields)
- Not easily repeatable
- Bypasses Django's user creation logic

**Verdict**: Not recommended - too manual and error-prone.

### Option 2: One-off ECS Task (Manual)

**Approach**: Manually run an ECS task that executes `createsuperuser`.

**Pros**:
- Uses Django's proper user creation
- Can be run from AWS Console or CLI

**Cons**:
- Requires knowledge of ECS task configuration
- Not documented in code
- Hard to reproduce exact steps

**Verdict**: Possible but not ideal for repeatability.

### Option 3: GitHub Actions Workflow (Recommended)

**Approach**: Create a GitHub Actions workflow that runs admin commands via ECS tasks.

**Pros**:
- Documented in code (the workflow file itself)
- Repeatable (run anytime from GitHub Actions UI)
- Secure (credentials from AWS Secrets Manager)
- Auditable (GitHub Actions logs show who ran what and when)
- Extensible (can add other admin commands later)
- Consistent with existing CI/CD patterns (migrations workflow)

**Cons**:
- Anyone with repo write access can trigger it
- Requires workflow setup

**Verdict**: Recommended - best balance of security, repeatability, and documentation.

## Security Considerations

### Access Control

With a small team (currently solo developer), the security model is:
- **GitHub repo access ≈ AWS access** - Same person(s) control both
- **Credentials in Secrets Manager** - Not hardcoded, not in repo
- **Audit trail** - GitHub Actions logs every workflow run

For larger teams, consider:
- GitHub Environment protection rules (require approval)
- Separate workflows with different permission requirements
- AWS IAM restrictions on who can run ECS tasks

### Credential Management

Superuser credentials will be stored in AWS Secrets Manager:
- Extend existing secret: `rds/startupwebapp/multi-tenant/master`
- Add fields: `superuser_username`, `superuser_email`, `superuser_password`
- Password should be strong (generated, 20+ characters)

The workflow will:
1. Retrieve credentials from Secrets Manager
2. Pass them as environment variables to the ECS task
3. Django's `createsuperuser --noinput` reads from env vars

### Password Security

Django's `createsuperuser --noinput` requires these environment variables:
- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

The password is:
- Never logged (GitHub Actions masks secrets)
- Never stored in code or workflow files
- Only exists in Secrets Manager and ECS task environment (ephemeral)

## Implementation Plan

### Phase 1: Testing (TDD Approach)

**Step 1.1: Write unit test for superuser creation**

Create a test that verifies:
- Superuser can be created via environment variables
- User has `is_superuser=True` and `is_staff=True`
- User can authenticate with the provided password

```python
# user/tests/test_superuser_creation.py
class SuperuserCreationTests(TestCase):
    def test_createsuperuser_via_env_vars(self):
        """Test that createsuperuser works with environment variables"""
        # This tests the mechanism Django uses
        ...
```

**Step 1.2: Test manually in Docker**

```bash
docker-compose exec \
  -e DJANGO_SUPERUSER_USERNAME=testadmin \
  -e DJANGO_SUPERUSER_EMAIL=test@example.com \
  -e DJANGO_SUPERUSER_PASSWORD=TestPass123! \
  backend python manage.py createsuperuser --noinput

# Verify
docker-compose exec backend python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='testadmin')
print(f'is_superuser: {u.is_superuser}, is_staff: {u.is_staff}')
print(f'can authenticate: {u.check_password(\"TestPass123!\")}')"
```

**Step 1.3: Test on non-production database**

Before running on `startupwebapp_prod`, test on `healthtech_experiment` or `fintech_experiment`.

### Phase 2: Secrets Manager Update

**Step 2.1: Add superuser credentials to existing secret**

```bash
# Get current secret
aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --query 'SecretString' --output text | jq . > /tmp/secret.json

# Add new fields (edit /tmp/secret.json):
# "superuser_username": "admin",
# "superuser_email": "admin@yourdomain.com",
# "superuser_password": "<strong-generated-password>"

# Update secret
aws secretsmanager put-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --secret-string file:///tmp/secret.json

# Clean up
rm /tmp/secret.json
```

**Step 2.2: Generate strong password**

```bash
# Generate a 24-character password
openssl rand -base64 18
```

### Phase 3: GitHub Actions Workflow

**Step 3.1: Create workflow file**

Create `.github/workflows/run-admin-command.yml`:

```yaml
name: Run Admin Command

on:
  workflow_dispatch:
    inputs:
      command:
        description: 'Admin command to run'
        required: true
        type: choice
        options:
          - createsuperuser
          - collectstatic
      database:
        description: 'Target database'
        required: true
        type: choice
        options:
          - startupwebapp_prod
          - healthtech_experiment
          - fintech_experiment

# ... (full workflow implementation)
```

**Step 3.2: Workflow implementation details**

The workflow will:
1. Configure AWS credentials
2. Fetch secrets from Secrets Manager
3. Create ECS task definition with environment variables
4. Run ECS task
5. Wait for completion
6. Fetch and display CloudWatch logs
7. Report success/failure

### Phase 4: Execution

**Step 4.1: Test on non-production**

1. Run workflow with `database: healthtech_experiment`
2. Verify via bastion: `SELECT * FROM auth_user WHERE is_superuser = true;`
3. Test login at admin URL (if accessible)

**Step 4.2: Run on production**

1. Run workflow with `database: startupwebapp_prod`
2. Verify via bastion
3. Test Django Admin login

### Phase 5: Documentation Updates

**Step 5.1: Update README.md**

Add section under "Production" about admin commands.

**Step 5.2: Update SESSION_START_PROMPT.md**

Add workflow to CI/CD section.

**Step 5.3: Update GITHUB_ACTIONS_GUIDE.md**

Add detailed instructions for running admin commands.

## Workflow File Structure

```
.github/workflows/
├── pr-validation.yml          # Run tests on PRs
├── deploy-production.yml      # Deploy backend to ECS
├── run-migrations.yml         # Run Django migrations
├── run-admin-command.yml      # NEW: Run admin commands
└── rollback-production.yml    # Rollback to previous version
```

## Future Extensibility

The admin command workflow can be extended to support:
- `collectstatic` - Collect static files (if needed)
- `clearsessions` - Clear expired sessions
- `flush` - Clear database (DANGEROUS - add confirmation)
- Custom management commands

Each command should be:
1. Added to the workflow dropdown
2. Documented in this technical note
3. Tested on non-production first

## Rollback / Recovery

If superuser creation fails or creates incorrect user:

**Via Bastion**:
```sql
-- Delete incorrectly created user
DELETE FROM auth_user WHERE username = 'admin';

-- Or update existing user
UPDATE auth_user SET is_superuser = true, is_staff = true WHERE username = 'admin';
```

**Via Workflow**:
- The workflow is idempotent for `createsuperuser` - running it again will fail if user exists
- To recreate, first delete via bastion, then run workflow again

## Checklist

- [ ] Write unit test for superuser creation via env vars
- [ ] Test `createsuperuser --noinput` in Docker locally
- [ ] Add superuser credentials to AWS Secrets Manager
- [ ] Create `run-admin-command.yml` workflow
- [ ] Test workflow on `healthtech_experiment` database
- [ ] Verify superuser via bastion query
- [ ] Run workflow on `startupwebapp_prod` database
- [ ] Verify production superuser via bastion
- [ ] Test Django Admin login in production
- [ ] Update README.md
- [ ] Update SESSION_START_PROMPT.md
- [ ] Update GITHUB_ACTIONS_GUIDE.md (or create if doesn't exist)

## References

- [Django createsuperuser documentation](https://docs.djangoproject.com/en/4.2/ref/django-admin/#createsuperuser)
- [Django DJANGO_SUPERUSER_* environment variables](https://docs.djangoproject.com/en/4.2/ref/django-admin/#envvar-DJANGO_SUPERUSER_PASSWORD)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
- [GitHub Actions workflow_dispatch](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch)
- Existing workflow: `.github/workflows/run-migrations.yml`
