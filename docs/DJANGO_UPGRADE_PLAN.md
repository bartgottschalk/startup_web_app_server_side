# Django Upgrade Plan: 2.2 → 4.2 LTS

**Started**: 2025-11-06
**Current Django**: 2.2.28
**Target Django**: 4.2 LTS
**Python Version**: 3.12.12

## Executive Summary

This document tracks the incremental upgrade from Django 2.2.28 (EOL April 2022) to Django 4.2 LTS (supported until April 2026). We're taking an incremental approach, upgrading through each major version to minimize risk and make debugging easier.

## Pre-Upgrade State

### Test Coverage Baseline
- **Unit Tests**: 626/626 passing (100%)
- **Functional Tests**: 24/28 passing (86%)
- **Total**: 650/654 tests passing (99.4%)

### Current Dependencies
```
Django==2.2.28
django-cors-headers==3.7.0
django-import-export==2.6.1
stripe==5.5.0
selenium==3.141.0
urllib3<2.0.0
```

### Deprecation Warnings Baseline
Status: ✅ Documented

**Python-related warnings** (from Django 2.2 code):
1. `locale.getdefaultlocale` - Python 3.15 deprecation in `django/utils/encoding.py:262`
2. `cgi` module - Python 3.13 deprecation in `django/http/multipartparser.py:9`
3. `datetime.datetime.utcnow()` - Deprecated in `django/utils/timezone.py:230`

**Note**: These are Django 2.2 internals using deprecated Python features. Will be resolved by upgrading Django.

---

## Upgrade Path

We'll upgrade incrementally through these versions:

1. ⏳ Django 2.2.28 → **Django 3.0.14** (first stable 3.0.x)
2. ⏳ Django 3.0.14 → **Django 3.1.14** (last 3.1.x)
3. ⏳ Django 3.1.14 → **Django 3.2.25** (3.2 LTS - supported until April 2024)
4. ⏳ Django 3.2.25 → **Django 4.0.10** (last 4.0.x)
5. ⏳ Django 4.0.10 → **Django 4.1.13** (last 4.1.x)
6. ⏳ Django 4.1.13 → **Django 4.2.x** (4.2 LTS - target)

---

## Step 1: Django 2.2.28 → 3.0.14

**Status**: ✅ COMPLETED - 2025-11-06

### Pre-Upgrade Checklist
- [x] Run deprecation warnings: `python -Wd manage.py test`
- [x] Review Django 3.0 release notes
- [x] Identify breaking changes in codebase
- [x] Backup current test results

### Known Breaking Changes in Django 3.0
1. **`django.utils.encoding` changes**
   - `force_text()` → `force_str()`
   - `smart_text()` → `smart_str()`

2. **`django.utils.translation` changes**
   - `ugettext()` → `gettext()`
   - `ugettext_lazy()` → `gettext_lazy()`
   - `ugettext_noop()` → `gettext_noop()`
   - `ungettext()` → `ngettext()`
   - `ungettext_lazy()` → `ngettext_lazy()`

3. **URL routing changes**
   - `django.conf.urls.url()` → `django.urls.re_path()`
   - `django.urls.path()` is now preferred

4. **Models changes**
   - `Model.Meta.ordering` must be tuple/list (not string)

### Dependency Updates for Django 3.0
```
Django==3.0.14
django-cors-headers==3.11.0  # Compatible with Django 3.0
django-import-export==2.7.1  # Last version supporting Django 3.0-3.1 (2.8.0 requires Django 3.2+)
stripe==5.5.0  # No change needed
```

### Implementation Steps
- [x] Update requirements.txt
- [x] Rebuild Docker container
- [x] Check for new migrations: `python manage.py makemigrations --check`
- [x] Apply migrations: N/A (no new migrations needed)
- [x] Run unit tests: 626 tests
- [x] Run functional tests: 28 tests
- [x] Fix any failures: None to fix!
- [x] Document issues encountered
- [x] Commit when all tests pass

### Test Results
- **Unit Tests**: ✅ 626/626 passing (100%)
- **Functional Tests**: ✅ 24/28 passing (86% - same as baseline)
- **Issues Found**: None! Zero breaking changes detected.

### Code Changes Made
**None required!** Django 3.0 is fully backward compatible with our Django 2.2 codebase. All tests pass without any code modifications.

---

## Step 2: Django 3.0.14 → 3.1.14

**Status**: ✅ COMPLETED - 2025-11-06

### Known Breaking Changes in Django 3.1
1. **`JSONField` moved**
   - `django.contrib.postgres.fields.JSONField` → `django.db.models.JSONField`

2. **`Signal` changes**
   - Signals must be connected with `weak=False` for class methods

3. **`SECURE_REFERRER_POLICY` default**
   - Now defaults to `'same-origin'`

### Dependency Updates for Django 3.1
```
Django==3.1.14
django-cors-headers==3.11.0
django-import-export==2.7.1  # Same as 3.0 (2.8.0 requires Django 3.2+)
```

### Implementation Steps
- [x] Update requirements.txt
- [x] Rebuild Docker container
- [x] Check/apply migrations: No new migrations needed
- [x] Run all tests
- [x] Fix failures: None!
- [x] Commit

### Test Results
- **Unit Tests**: ✅ 626/626 passing (100%)
- **Functional Tests**: ✅ 24/28 passing (86% - same as baseline)
- **Issues Found**: None! Zero breaking changes detected.

### Code Changes Made
**None required!** Django 3.1 is fully backward compatible with our Django 3.0 codebase.

---

## Step 3: Django 3.1.14 → 3.2.25 (LTS)

**Status**: ✅ COMPLETED - 2025-11-06

### Known Breaking Changes in Django 3.2
1. **`DEFAULT_AUTO_FIELD` setting**
   - New default: `BigAutoField` (64-bit primary keys)
   - Need to explicitly set: `DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'`
   - Or migrate to BigAutoField (requires migration)

2. **`USE_L10N` deprecation**
   - Will be removed in Django 5.0
   - Localization now always enabled

3. **Admin `ModelAdmin.lookup_allowed()` changes**
   - Signature changed

### Dependency Updates for Django 3.2
```
Django==3.2.25
django-cors-headers==3.13.0
django-import-export==2.8.0
```

### Implementation Steps
- [x] Update requirements.txt
- [x] Add `DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'` to settings.py
- [x] Rebuild Docker container
- [x] Check/apply migrations: No new migrations needed
- [x] Run all tests
- [x] Fix failures: None!
- [x] Commit

### Test Results
- **Unit Tests**: ✅ 626/626 passing (100%)
- **Functional Tests**: ✅ 24/28 passing (86% - same as baseline)
- **Issues Found**: None!

### Code Changes Made
- **settings.py**: Added `DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'` to maintain backward compatibility with existing database schema
- This prevents Django from generating migrations to convert all primary keys to BigAutoField

---

## Step 4: Django 3.2.25 → 4.0.10

**Status**: ✅ COMPLETED - 2025-11-06

### Known Breaking Changes in Django 4.0
1. **`django.utils.timezone` changes**
   - `django.utils.timezone.utc` replaces `pytz.UTC`

2. **`CSRF_COOKIE_SAMESITE` default**
   - Now defaults to `'Lax'` (was `None`)

3. **`CSRF_TRUSTED_ORIGINS` format** ⚠️ **REQUIRED CODE CHANGE**
   - Must include scheme: `['https://example.com']` not `['example.com']`
   - Old format was a string, new format must be a list with schemes

4. **`get_response_async()` required**
   - For async middleware

### Dependency Updates for Django 4.0
```
Django==4.0.10
django-cors-headers==3.13.0
django-import-export==3.2.0
```

### Implementation Steps
- [x] Update requirements.txt
- [x] Check CSRF_TRUSTED_ORIGINS format
- [x] Add CSRF_TRUSTED_ORIGINS compatibility layer to settings.py
- [x] Rebuild Docker container
- [x] Check/apply migrations: No new migrations needed
- [x] Run all tests
- [x] Fix failures: None!
- [x] Manual browser testing
- [x] Commit

### Test Results
- **Unit Tests**: ✅ 626/626 passing (100%)
- **Functional Tests**: ✅ 24/28 passing (86% - same as baseline)
- **Issues Found**: None! CSRF_TRUSTED_ORIGINS fixed, zero regressions.

### Code Changes Made
**settings.py**: Added Django 4.0+ compatibility layer for CSRF_TRUSTED_ORIGINS (lines 34-54)
- Automatically converts old string format to new list format
- Uses http:// for localhost in development
- Uses https:// with wildcard subdomains in production
- Maintains backward compatibility with existing settings_secret.py

---

## Step 5: Django 4.0.10 → 4.1.13

**Status**: ⏳ Not Started

### Known Breaking Changes in Django 4.1
1. **`QuerySet.values_list()` changes**
   - `flat=True` with multiple fields now raises error

2. **`Subquery` changes**
   - Must provide `queryset` or `sql` parameter

3. **`csrf_token` tag changes**
   - More strict validation

### Dependency Updates for Django 4.1
```
Django==4.1.13
django-cors-headers==4.0.0
django-import-export==3.3.0
```

### Implementation Steps
- [ ] Update requirements.txt
- [ ] Rebuild Docker container
- [ ] Check/apply migrations
- [ ] Run all tests
- [ ] Fix failures
- [ ] Commit

### Test Results
⏳ Pending

---

## Step 6: Django 4.1.13 → 4.2.x (LTS - Final Target)

**Status**: ⏳ Not Started

### Known Breaking Changes in Django 4.2
1. **`index_together` deprecation**
   - `Meta.index_together` → `Meta.indexes`

2. **`unique_together` deprecation**
   - `Meta.unique_together` → `Meta.constraints`

3. **`Keyset pagination`**
   - New pagination method available

4. **`psycopg` version 3 support**
   - Now supports PostgreSQL psycopg v3

### Dependency Updates for Django 4.2
```
Django==4.2.16  # Latest 4.2.x as of 2025-11
django-cors-headers==4.4.0
django-import-export==4.0.0
stripe==11.1.0  # Consider upgrading
selenium==4.25.0  # Consider after Django stable
```

### Implementation Steps
- [ ] Update requirements.txt
- [ ] Check for `index_together` usage
- [ ] Check for `unique_together` usage
- [ ] Rebuild Docker container
- [ ] Check/apply migrations
- [ ] Run all tests
- [ ] Fix failures
- [ ] Final validation
- [ ] Update all documentation
- [ ] Commit

### Test Results
⏳ Pending

---

## Post-Upgrade Tasks

After reaching Django 4.2 LTS:

### Validation
- [ ] Run full test suite 3 times (ensure consistency)
- [ ] Manual browser testing of critical user journeys
- [ ] Check for deprecation warnings with `-Wd`
- [ ] Performance testing (compare with baseline)

### Documentation
- [ ] Update README.md with new Django version
- [ ] Update requirements.txt comments
- [ ] Update KNOWN_ISSUES.md if needed
- [ ] Create milestone document in docs/milestones/

### Optional Improvements
- [ ] Consider upgrading Selenium 3.x → 4.x
- [ ] Consider upgrading Stripe 5.x → 11.x
- [ ] Address any remaining deprecation warnings
- [ ] Fix remaining 4 functional test failures

---

## Rollback Plan

If critical issues are encountered at any step:

1. **Immediate rollback**:
   ```bash
   git checkout master
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Partial rollback** (to previous working version):
   ```bash
   git revert HEAD  # Revert last commit
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Document the issue** in this file for future reference

---

## Issues Encountered

### Issue Log
Track any problems encountered during upgrade:

| Step | Issue | Solution | Commit |
|------|-------|----------|--------|
| - | - | - | - |

---

## Success Metrics

### Before Merge to Master
- [ ] All 626 unit tests passing
- [ ] At least 24/28 functional tests passing (no regressions)
- [ ] Zero deprecation warnings
- [ ] Manual testing completed
- [ ] Documentation updated
- [ ] PR reviewed and approved

---

## Timeline

- **Started**: 2025-11-06
- **Django 3.0**: ✅ Completed 2025-11-06 (1 hour)
- **Django 3.1**: ✅ Completed 2025-11-06 (15 minutes)
- **Django 3.2**: ✅ Completed 2025-11-06 (20 minutes)
- **Django 4.0**: ✅ Completed 2025-11-06 (45 minutes)
- **Django 4.1**: ⏳ Not started
- **Django 4.2**: ⏳ Not started
- **Completed**: ⏳ In progress (67% complete - 4 of 6 steps done)

**Estimated total time**: 18-30 hours across multiple sessions
**Actual time so far**: 2.6 hours

---

## References

- [Django 3.0 Release Notes](https://docs.djangoproject.com/en/3.0/releases/3.0/)
- [Django 3.1 Release Notes](https://docs.djangoproject.com/en/3.1/releases/3.1/)
- [Django 3.2 Release Notes](https://docs.djangoproject.com/en/3.2/releases/3.2/)
- [Django 4.0 Release Notes](https://docs.djangoproject.com/en/4.0/releases/4.0/)
- [Django 4.1 Release Notes](https://docs.djangoproject.com/en/4.1/releases/4.1/)
- [Django 4.2 Release Notes](https://docs.djangoproject.com/en/4.2/releases/4.2/)
- [Django Deprecation Timeline](https://docs.djangoproject.com/en/4.2/internals/deprecation/)

---

**Last Updated**: 2025-11-06
**Current Django Version**: 4.0.10
**Next Step**: Django 4.0 → 4.1 upgrade
