# Django Migration Testing Guide

**Purpose**: This guide provides instructions for testing database migrations to ensure compatibility when upgrading Django versions or making schema changes.

**Created**: 2025-11-03
**Updated**: 2025-11-03

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Migration Checks](#pre-migration-checks)
3. [Migration Testing Procedures](#migration-testing-procedures)
4. [Django Version Upgrade Testing](#django-version-upgrade-testing)
5. [Troubleshooting](#troubleshooting)

---

## Overview

Migration testing ensures that:
- Database schema changes are applied correctly
- No migration conflicts exist
- Models match the database schema
- Migrations can be rolled back safely
- Django version upgrades don't break existing migrations

---

## Pre-Migration Checks

### 1. Check for Unmade Migrations

Before any Django upgrade or deployment, verify no model changes are unmigrated:

```bash
docker-compose exec backend python manage.py makemigrations --check --dry-run
```

**Expected Output**: "No changes detected"

**If Changes Detected**:
- Review the proposed changes carefully
- Create migrations: `docker-compose exec backend python manage.py makemigrations`
- Test the migrations (see below)
- Commit the migration files

### 2. Verify Migration Consistency

Check that all migrations have been applied:

```bash
docker-compose exec backend python manage.py showmigrations
```

**Expected Output**: All migrations should have `[X]` markers (applied)

**If Unapplied Migrations Exist**:
- Review the unapplied migrations
- Test in development first: `docker-compose exec backend python manage.py migrate`
- Verify all tests pass after applying

---

## Migration Testing Procedures

### Test 1: Fresh Database Migration

Tests that all migrations work from scratch (simulates initial deployment):

```bash
# Step 1: Stop containers
docker-compose down

# Step 2: Remove database volume (WARNING: destroys all data)
docker volume rm startup_web_app_server_side_postgres_data

# Step 3: Start containers (creates fresh database)
docker-compose up -d

# Step 4: Wait for database to be ready (check logs)
docker-compose logs -f postgres

# Step 5: Run all migrations
docker-compose exec backend python manage.py migrate

# Step 6: Verify migrations applied successfully
docker-compose exec backend python manage.py showmigrations

# Step 7: Run all tests to verify schema
docker-compose exec backend python manage.py test user.tests
```

**Success Criteria**:
- All migrations apply without errors
- All tests pass (236 tests for user app as of Phase 1.10)
- No warnings about conflicting migrations

### Test 2: Incremental Migration Testing

Tests new migrations on existing database (simulates production upgrade):

```bash
# Step 1: Create backup of current database
docker-compose exec postgres pg_dump -U postgres postgres > backup_before_migration.sql

# Step 2: Apply new migrations
docker-compose exec backend python manage.py migrate

# Step 3: Verify migrations
docker-compose exec backend python manage.py showmigrations

# Step 4: Run all tests
docker-compose exec backend python manage.py test

# Step 5: If tests fail, rollback to previous migration
# docker-compose exec backend python manage.py migrate <app_name> <migration_number>

# Step 6: If successful, remove backup
# rm backup_before_migration.sql
```

### Test 3: Migration Reversibility Testing

Tests that migrations can be rolled back (important for production safety):

```bash
# Step 1: Note current migration state
docker-compose exec backend python manage.py showmigrations > migrations_before.txt

# Step 2: Apply new migration
docker-compose exec backend python manage.py migrate user <new_migration_number>

# Step 3: Test with new schema
docker-compose exec backend python manage.py test user.tests

# Step 4: Rollback to previous migration
docker-compose exec backend python manage.py migrate user <previous_migration_number>

# Step 5: Test with old schema
docker-compose exec backend python manage.py test user.tests

# Step 6: Reapply new migration
docker-compose exec backend python manage.py migrate user <new_migration_number>

# Step 7: Final test
docker-compose exec backend python manage.py test user.tests
```

**Success Criteria**:
- Migration applies successfully
- Tests pass with new schema
- Migration rolls back without errors
- Tests pass with old schema
- Migration reapplies successfully

### Test 4: Fake Migration Testing

Tests that existing databases can "fake" initial migrations (for brownfield upgrades):

```bash
# This simulates adding migration tracking to existing database
docker-compose exec backend python manage.py migrate --fake-initial

# Verify migrations are marked as applied
docker-compose exec backend python manage.py showmigrations

# Run tests to ensure schema matches
docker-compose exec backend python manage.py test
```

---

## Django Version Upgrade Testing

### Pre-Upgrade Checklist

Before upgrading Django version:

1. **Review Django Release Notes**
   - Check deprecation warnings for your current version
   - Review breaking changes in target version
   - Note any model/migration changes

2. **Run Deprecation Warnings Test**
   ```bash
   # Enable Python warnings
   docker-compose exec backend python -Wd manage.py test
   ```

   Fix any DeprecationWarnings before upgrading.

3. **Backup Production Database**
   ```bash
   # On production server
   pg_dump -U postgres -d production_db > production_backup_$(date +%Y%m%d).sql
   ```

### Upgrade Testing Procedure

#### Step 1: Test in Development Environment

```bash
# 1. Create new branch for upgrade
git checkout -b upgrade/django-X.Y

# 2. Update requirements.txt
# Change Django version: Django==X.Y.Z

# 3. Rebuild Docker containers
docker-compose down
docker-compose build
docker-compose up -d

# 4. Check for migration issues
docker-compose exec backend python manage.py makemigrations --check --dry-run

# 5. Run all tests
docker-compose exec backend python manage.py test

# 6. Check for deprecation warnings
docker-compose exec backend python -Wd manage.py test
```

#### Step 2: Test Fresh Database Migration

Follow [Test 1: Fresh Database Migration](#test-1-fresh-database-migration) with new Django version.

#### Step 3: Test Incremental Migration

```bash
# 1. Start with database from OLD Django version
# (use docker volume from before upgrade)

# 2. Upgrade Django in requirements.txt

# 3. Rebuild containers
docker-compose down
docker-compose build
docker-compose up -d

# 4. Apply any new Django system migrations
docker-compose exec backend python manage.py migrate

# 5. Run all tests
docker-compose exec backend python manage.py test

# 6. Verify no migration conflicts
docker-compose exec backend python manage.py makemigrations --check --dry-run
```

#### Step 4: Test with Production Data Snapshot

```bash
# 1. Copy production database to development
# (using sanitized backup)

# 2. Apply to development database
docker-compose exec -T postgres psql -U postgres postgres < production_sanitized_backup.sql

# 3. Run migrations with new Django version
docker-compose exec backend python manage.py migrate

# 4. Run all tests
docker-compose exec backend python manage.py test

# 5. Spot-check critical functionality manually
```

---

## Troubleshooting

### Problem: "No changes detected" but models don't match database

**Solution**:
```bash
# Check what Django thinks is in database
docker-compose exec backend python manage.py inspectdb

# Compare with your models
# If inconsistent, may need to manually create migration
docker-compose exec backend python manage.py makemigrations --empty user
# Then edit the migration file manually
```

### Problem: Migration conflicts

**Solution**:
```bash
# Django will suggest merge migration
docker-compose exec backend python manage.py makemigrations --merge

# Review the merge migration carefully
# Test thoroughly before committing
```

### Problem: "Migration is already applied"

**Solution**:
```bash
# Check migration status
docker-compose exec backend python manage.py showmigrations user

# If migration is marked applied but changes not in DB:
docker-compose exec backend python manage.py migrate user <migration_number> --fake
docker-compose exec backend python manage.py migrate user
```

### Problem: Migrations work but tests fail

**Possible Causes**:
1. **Test database not migrated**: Tests create fresh database each run
2. **Model changes not reflected**: Check `makemigrations --check`
3. **Foreign key constraints**: Check test data setup
4. **Unique constraints**: Check for duplicate test data

**Solution**:
```bash
# Run single test with verbose output
docker-compose exec backend python manage.py test user.tests.test_models_extended.MemberModelTest.test_member_creation_with_user -v 2

# Check test database creation
docker-compose exec backend python manage.py test --debug-sql
```

### Problem: Django version upgrade breaks migrations

**Solution**:
```bash
# Downgrade Django to previous version
# Update requirements.txt
docker-compose down
docker-compose build
docker-compose up -d

# Review Django upgrade guide for your versions
# Check for required migration changes

# If necessary, create data migration to fix issues:
docker-compose exec backend python manage.py makemigrations --empty user
# Edit migration file to add data transformation
```

---

## Model-Specific Testing

### User App Models

The user app has comprehensive model tests as of Phase 1.10:

```bash
# Run all model tests
docker-compose exec backend python manage.py test user.tests.test_models
docker-compose exec backend python manage.py test user.tests.test_models_extended
docker-compose exec backend python manage.py test user.tests.test_model_constraints

# Test specific model
docker-compose exec backend python manage.py test user.tests.test_models_extended.MemberModelTest
docker-compose exec backend python manage.py test user.tests.test_model_constraints.MemberUniqueConstraintTest
```

**Coverage**:
- Member model: Instance creation, defaults, relationships, cascade deletes
- Prospect model: Uniqueness, nullable fields, conversions
- Termsofuse model: Versioning, agreements
- Emailunsubscribereasons model: Member/prospect associations
- Chatmessage model: Member/prospect associations
- Email models: Types, statuses, sending history
- Constraint testing: Unique fields, unique_together, foreign keys, null/blank validation

---

## Best Practices

### Before Committing Migrations

1. **Always test migrations locally first**
   ```bash
   docker-compose exec backend python manage.py migrate
   docker-compose exec backend python manage.py test
   ```

2. **Review migration SQL**
   ```bash
   docker-compose exec backend python manage.py sqlmigrate user <migration_number>
   ```

3. **Check for data loss operations**
   - Look for `RemoveField`, `DeleteModel`, `AlterField` (esp. changing to non-null)
   - Consider data migrations if needed

4. **Test rollback**
   ```bash
   docker-compose exec backend python manage.py migrate user <previous_migration>
   docker-compose exec backend python manage.py migrate user <new_migration>
   ```

### During Django Upgrades

1. **Upgrade incrementally**: Don't skip major versions (e.g., 2.2 → 3.0 → 3.1 → 3.2)

2. **Test each step**: Run full test suite after each minor version upgrade

3. **Read release notes**: Django provides comprehensive upgrade guides

4. **Check third-party packages**: Ensure all dependencies support new Django version

5. **Update requirements.txt**: Pin exact versions that work together

---

## Automated Migration Testing

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml (example)
test-migrations:
  runs-on: ubuntu-latest
  steps:
    - name: Checkout code
      uses: actions/checkout@v2

    - name: Build containers
      run: docker-compose build

    - name: Start services
      run: docker-compose up -d

    - name: Wait for postgres
      run: docker-compose exec postgres pg_isready

    - name: Run migrations
      run: docker-compose exec backend python manage.py migrate

    - name: Check for unmade migrations
      run: docker-compose exec backend python manage.py makemigrations --check --dry-run

    - name: Run tests
      run: docker-compose exec backend python manage.py test

    - name: Shutdown
      run: docker-compose down -v
```

---

## Quick Reference

### Common Commands

```bash
# Check for unmade migrations
docker-compose exec backend python manage.py makemigrations --check --dry-run

# Show migration status
docker-compose exec backend python manage.py showmigrations

# Apply migrations
docker-compose exec backend python manage.py migrate

# Rollback migration
docker-compose exec backend python manage.py migrate <app> <migration_number>

# Fake migration (mark as applied without running)
docker-compose exec backend python manage.py migrate --fake

# Fake initial migrations (for existing databases)
docker-compose exec backend python manage.py migrate --fake-initial

# View SQL for migration
docker-compose exec backend python manage.py sqlmigrate <app> <migration_number>

# Run tests
docker-compose exec backend python manage.py test

# Run tests with deprecation warnings
docker-compose exec backend python -Wd manage.py test
```

---

## Related Documentation

- [Django Migration Documentation](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [Django Release Notes](https://docs.djangoproject.com/en/stable/releases/)
- [Phase 1.10 Milestone](milestones/2025-11-03-phase-1-10-model-migration-tests.md)
- User App Test Documentation (see `docs/milestones/2025-11-03-phase-1-10-model-migration-tests.md`)

---

**Last Updated**: 2025-11-03
**Django Version**: 2.2.28
**Python Version**: 3.12
**Total User Tests**: 236 (as of Phase 1.10)
