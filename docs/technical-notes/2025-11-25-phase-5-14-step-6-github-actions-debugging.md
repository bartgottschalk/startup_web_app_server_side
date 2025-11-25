# Phase 5.14 Step 6: GitHub Actions Workflow Debugging & Fixes

**Date**: November 25, 2025
**Status**: ✅ Complete
**Branch**: `master` (PR #38 merged)
**Duration**: ~3 hours (7 iterations)

## Overview

This document details the debugging process for the GitHub Actions CI/CD workflow created in Phase 5.14 Step 5. While the workflow file was created successfully, it required 7 iterations of testing and fixes to resolve all compatibility issues between the local Docker development environment and the GitHub Actions CI/CD environment.

## Initial Setup

### IAM User Creation

**Created**: `github-actions-startupwebapp`

**Policies Attached**:
- `AmazonEC2ContainerRegistryPowerUser` - For pushing/pulling Docker images to/from ECR
- `AmazonECS_FullAccess` - For running ECS tasks and updating task definitions
- `CloudWatchLogsReadOnlyAccess` - For fetching migration logs from CloudWatch

**Access Keys**: Generated for programmatic access (stored in GitHub Secrets)

### GitHub Secrets Added

Three repository secrets configured in GitHub:
1. `AWS_ACCESS_KEY_ID` - IAM user access key (starts with AKIA)
2. `AWS_SECRET_ACCESS_KEY` - IAM user secret access key
3. `AWS_REGION` - us-east-1

**Location**: GitHub repo → Settings → Secrets and variables → Actions

**Security**: All secrets encrypted by GitHub, never exposed in workflow logs

---

## Debugging Iterations

### Iteration 1: skip_tests Boolean Logic Error

**Problem**: Tests were being skipped even when `skip_tests` checkbox was unchecked.

**Root Cause**:
```yaml
if: ${{ !github.event.inputs.skip_tests }}
```

GitHub Actions workflow inputs are **strings**, not booleans:
- When unchecked: `skip_tests = "false"` (string)
- Condition `!"false"` evaluates to `false` (non-empty string is truthy)
- Tests skipped incorrectly

**Fix**:
```yaml
if: ${{ github.event.inputs.skip_tests != 'true' }}
```

**Commit**: `1168c38` - "Fix GitHub Actions workflow: correct skip_tests boolean condition"

---

### Iteration 2: Flake8 Linting Failed on Migrations

**Problem**: Flake8 linting failed with 28 E501 errors (line too long) in Django migration files.

**Error**:
```
clientevent/migrations/0001_initial.py:38:121: E501 line too long (130 > 120 characters)
order/migrations/0001_initial.py:267:121: E501 line too long (155 > 120 characters)
...28 total errors
```

**Root Cause**: Migration files are **auto-generated** by Django and shouldn't be manually edited or linted. They often contain long database field definitions.

**Fix**: Added `--exclude=*/migrations/*` flag to flake8 command:
```yaml
flake8 user order clientevent StartupWebApp --max-line-length=120 --exclude=*/migrations/* --statistics
```

**Standard Practice**: Most Django projects exclude migrations from linting.

**Commit**: `c17734f` - "Fix: Exclude Django migrations from flake8 linting"

---

### Iteration 3: Missing settings_secret.py

**Problem**: Tests failed with `ModuleNotFoundError: No module named 'StartupWebApp.settings_secret'`

**Root Cause**:
- `settings.py` imports `settings_secret.py`
- `settings_secret.py` is gitignored (contains local secrets)
- File doesn't exist in GitHub Actions environment

**Fix**: Generate a minimal `settings_secret.py` during workflow run before tests:

```yaml
- name: Create settings_secret.py for CI
  run: |
    cat > StartupWebApp/StartupWebApp/settings_secret.py << 'EOF'
    # CI/CD Test Settings (auto-generated)
    import os

    SECRET_KEY = 'test-secret-key-for-ci-only-not-secure'
    ALLOWED_HOSTS = ['localhost', 'backend', 'testserver']

    # Database from environment variables
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DATABASE_NAME', 'startupwebapp_test'),
            'USER': os.environ.get('DATABASE_USER', 'postgres'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
            'PORT': os.environ.get('DATABASE_PORT', '5432'),
            'CONN_MAX_AGE': 600,
        }
    }

    # ... additional settings ...
    EOF
```

**Commit**: `8cda567` - "Fix: Create settings_secret.py for CI/CD environment"

---

### Iteration 4: Stripe Setting Name Mismatch

**Problem**: Tests failed with `AttributeError: 'Settings' object has no attribute 'STRIPE_SERVER_SECRET_KEY'`

**Root Cause**: Generated `settings_secret.py` used incorrect setting names:
- Generated: `STRIPE_SECRET_KEY`
- Expected (in template): `STRIPE_SERVER_SECRET_KEY`

**Template Structure** (`settings_secret.py.template` line 80-81):
```python
STRIPE_SERVER_SECRET_KEY = 'sk_test_secret_key'
STRIPE_PUBLISHABLE_SECRET_KEY = 'pk_test_secret_key'
```

**Fix**: Updated generated file to match template exactly with all required settings:
- `STRIPE_SERVER_SECRET_KEY` (not `STRIPE_SECRET_KEY`)
- `STRIPE_PUBLISHABLE_SECRET_KEY` (not `STRIPE_PUBLISHABLE_KEY`)
- Added missing: `STRIPE_LOG_LEVEL`, `SESSION_COOKIE_*`, `CSRF_*`, `EMAIL_*`, etc.

**Commit**: `953fad9` - "Fix: Match settings_secret.py structure to template"

---

### Iteration 5: Firefox ESR Not Available

**Problem**: Functional tests failed during Firefox installation step:

```
E: Package 'firefox-esr' has no installation candidate
```

**Root Cause**:
- GitHub Actions runs on Ubuntu 24.04 (noble)
- `firefox-esr` package not available in Ubuntu 24.04 repos
- Ubuntu 24.04 ships Firefox as snap, not apt package

**Fix**: Use Firefox snap instead of firefox-esr:
```yaml
- name: Set up Firefox
  run: |
    # Firefox pre-installed as snap on GitHub Actions Ubuntu 24.04
    firefox --version || sudo snap install firefox
    firefox --version
```

**Why Keep Functional Tests**:
- Critical for full-stack integration testing
- Test real HTTP requests/responses
- Verify CSRF, sessions, database transactions work end-to-end
- 28 tests provide important coverage beyond 712 unit tests

**Commit**: `62d9274` - "Fix: Use Firefox snap instead of firefox-esr for Ubuntu 24.04"

---

### Iteration 6: DNS Not Resolving for Functional Tests

**Problem**: Functional tests failed with `dnsNotFound` errors:

```
selenium.common.exceptions.WebDriverException: Message: Reached error page: about:neterror?e=dnsNotFound
...localliveservertestcase.startupwebapp.com
```

**Root Cause**:
- Tests access `localliveservertestcase.startupwebapp.com`
- In Docker: `/app/setup_docker_test_hosts.sh` adds entries to `/etc/hosts`
- In CI: Script doesn't exist, hostnames don't resolve

**Fix**: Add hostname entries to `/etc/hosts` before running functional tests:
```yaml
- name: Run functional tests
  run: |
    # Setup /etc/hosts for functional tests
    echo "127.0.0.1    localliveservertestcase.startupwebapp.com" | sudo tee -a /etc/hosts
    echo "127.0.0.1    localliveservertestcaseapi.startupwebapp.com" | sudo tee -a /etc/hosts

    cd StartupWebApp
    python manage.py test functional_tests
```

**Commit**: `71109c4` - "Fix: Setup /etc/hosts for functional tests in CI"

---

### Iteration 7: Connection Failure to Port 8080

**Problem**: Tests resolved DNS but failed to connect:

```
selenium.common.exceptions.WebDriverException: Message: Reached error page: about:neterror?e=connectionFailure
...localliveservertestcase.startupwebapp.com:8080
```

**Root Cause Analysis**:

From `base_functional_test.py`:
```python
# Line 24: Django test server runs on port 60767 (hardcoded)
port = 60767

# Line 29: Frontend URL depends on environment
static_home_page_url = "http://localliveservertestcase.startupwebapp.com/" if os.environ.get('DOCKER_ENV') \
                       else "http://localliveservertestcase.startupwebapp.com:8080/"
```

**Docker Setup**:
- Frontend server on port 8080 (serves static files)
- Backend Django test server on port 60767 (API)
- Tests access frontend at `:8080` → proxies to backend `:60767`

**CI Setup**:
- No frontend server on port 8080
- Only Django LiveServerTestCase on port 60767
- Tests try `:8080` → nothing listening → connectionFailure

**Fix**: Set `DOCKER_ENV=true` to skip port 8080, use backend directly:
```yaml
- name: Run functional tests
  env:
    DOCKER_ENV: "true"  # Tell tests to use backend directly (no :8080)
  run: |
    # ... rest of test setup
```

With `DOCKER_ENV=true`:
- `static_home_page_url = "http://localliveservertestcase.startupwebapp.com/"`
- Tests connect to Django LiveServerTestCase on port 60767
- No separate frontend server needed

**Commit**: `c74899e` - "Fix: Set DOCKER_ENV to skip frontend server in functional tests"

---

## Summary of Fixes

| Issue | Root Cause | Fix | Commit |
|-------|-----------|-----|--------|
| Tests skipped | Boolean string comparison | Change to `!= 'true'` | 1168c38 |
| Flake8 failures | Linting migrations | Add `--exclude=*/migrations/*` | c17734f |
| Missing settings_secret | Gitignored file | Generate during workflow | 8cda567 |
| Stripe setting names | Incorrect names | Match template structure | 953fad9 |
| Firefox not found | Ubuntu 24.04 incompatibility | Use Firefox snap | 62d9274 |
| DNS not resolving | Missing /etc/hosts | Add hostname entries | 71109c4 |
| Port 8080 connection | No frontend server | Set DOCKER_ENV=true | c74899e |

**Total Iterations**: 7
**Total Time**: ~3 hours
**Status**: All 740 tests now pass in CI/CD

---

## Key Learnings

### 1. Environment Differences

Local Docker environment ≠ GitHub Actions environment:
- Different OS (custom Docker image vs Ubuntu 24.04)
- Different package availability (firefox-esr vs snap)
- Different architecture (multi-container vs single VM)
- Different file availability (gitignored files)

### 2. Testing Strategy

**Always test CI/CD workflows early** - Don't wait until everything is "perfect"
- Each iteration revealed a new issue
- Issues couldn't be predicted without running
- Rapid iteration was faster than trying to anticipate all problems

### 3. String vs Boolean in GitHub Actions

GitHub Actions workflow inputs are **always strings**:
```yaml
inputs:
  skip_tests:
    type: boolean
    default: false
```

Even though declared as `boolean`, the value is a string:
- `"true"` when checked
- `"false"` when unchecked

**Correct comparison**: `${{ inputs.value != 'true' }}`
**Incorrect comparison**: `${{ !inputs.value }}`

### 4. Functional Test Complexity

Functional tests are valuable but complex in CI:
- Require browser (Firefox/Chrome)
- Require Selenium + geckodriver
- Require hostname resolution
- Require understanding of test architecture
- **Worth the effort** for integration coverage

### 5. Template Consistency

When generating config files dynamically:
- **Always match existing templates exactly**
- Compare field-by-field with production template
- Small name differences cause hard-to-debug errors
- Document any intentional differences

---

## Current Workflow Status

**File**: `.github/workflows/run-migrations.yml`
**Size**: 523 lines (200+ lines of comments)
**Jobs**: 4 (Test, Build, Migrate, Summary)
**Duration**: ~10-17 minutes per database
**Tests**: 740 total (712 unit + 28 functional)

**Success Criteria**:
- ✅ All 740 tests pass in CI environment
- ✅ Docker image builds and pushes to ECR
- ✅ ECS task launches and runs migrations
- ✅ CloudWatch logs retrieved and displayed

**Next Step**: Test the complete workflow end-to-end (Step 7)

---

## References

- Workflow file: `.github/workflows/run-migrations.yml`
- User guide: `docs/GITHUB_ACTIONS_GUIDE.md`
- Base test class: `StartupWebApp/functional_tests/base_functional_test.py`
- Settings template: `StartupWebApp/StartupWebApp/settings_secret.py.template`
- Phase 5.14 plan: `docs/technical-notes/2025-11-23-phase-5-14-ecs-cicd-migrations.md`
