# Baseline Test Results - Backend Unit Tests

**Date**: 2025-10-31
**Goal**: Establish "known working" state before upgrades

---

## Environment

- **Python Version**: 3.12.8
- **Django Version**: 2.2.28
- **Test Type**: Backend unit tests only (user, order, clientevent apps)
- **Database**: SQLite (in-memory for tests)

---

## Test Execution Command

```bash
source venv/bin/activate
cd StartupWebApp
python manage.py test user order clientevent
```

---

## Results

✅ **ALL TESTS PASSED**

```
Creating test database for alias 'default'...
..........
----------------------------------------------------------------------
Ran 10 tests in 0.947s

OK
Destroying test database for alias 'default'...
System check identified no issues (0 silenced).
```

**Test Count**: 10 tests
**Duration**: 0.947 seconds
**Failures**: 0
**Errors**: 0

---

## Issues Encountered & Resolved

### 1. Python 3.12 Compatibility - distutils
**Issue**: Django 2.2 requires `distutils` which was removed in Python 3.12
```
ModuleNotFoundError: No module named 'distutils'
```

**Solution**: Installed `setuptools` which provides distutils compatibility
```bash
pip install setuptools
```

### 2. Python 3.12 Compatibility - Stripe Library
**Issue**: Stripe 2.63.0 uses deprecated `six.moves` module
```
ModuleNotFoundError: No module named 'stripe.six.moves'
```

**Solution**: Upgraded Stripe to version 5.5.0
```bash
pip install --upgrade "stripe>=5.0,<6.0"
```

### 3. CORS Configuration
**Issue**: django-cors-headers 3.7.0 requires full URLs with scheme
```
ERRORS:
?: (corsheaders.E013) Origin 'localhost.startupwebapp.com' in CORS_ORIGIN_WHITELIST is missing scheme or netloc
```

**Solution**: Updated `settings_secret.py` to include http:// scheme:
```python
# OLD
CORS_ORIGIN_WHITELIST = (
    'localhost.startupwebapp.com',
)

# NEW
CORS_ORIGIN_WHITELIST = (
    'http://localhost.startupwebapp.com',
)
```

---

## Dependencies Installed

Created `requirements.txt` with these versions:

```
Django==2.2.28
django-cors-headers==3.7.0
django-import-export==2.6.1
configparser==5.2.0
titlecase==2.3.0
stripe==5.5.0  # Upgraded from 2.63.0
coverage==6.2
selenium==3.141.0
setuptools  # Added for Python 3.12 compatibility
```

---

## Warnings Observed (Non-blocking)

The following warnings were observed but did not prevent tests from passing:

1. **Regex escape sequences** in `validator.py`:
   ```
   SyntaxWarning: invalid escape sequence '\@'
   SyntaxWarning: invalid escape sequence '\['
   ```
   *Should be fixed by using raw strings: `r"..."`*

2. **Regex escape sequence** in `order/urls.py`:
   ```
   SyntaxWarning: invalid escape sequence '\d'
   ```
   *Should be fixed by using raw strings: `r"..."`*

---

## Test Coverage

The 10 tests cover:
- **user app**: User authentication, account creation, API endpoints
- **order app**: Cart operations, SKU management, order processing APIs
- **clientevent app**: Client event logging APIs

---

## Files Created/Modified

### Created:
1. `/requirements.txt` - Python dependencies
2. `/StartupWebApp/StartupWebApp/settings_secret.py` - Local test configuration
3. `/venv/` - Virtual environment (not committed)
4. `/BASELINE_TEST_RESULTS.md` - This document

### Modified:
- None (settings_secret.py was created, not modified)

---

## Next Steps

Now that we have a verified "known working" baseline, we can proceed with upgrades incrementally:

1. ✅ **COMPLETED**: Backend unit tests pass
2. **TODO**: Run frontend QUnit tests (requires PhantomJS setup)
3. **TODO**: Run Selenium functional tests (requires both backend + frontend)
4. **TODO**: Document all three test suites as complete baseline
5. **TODO**: Begin incremental upgrades (Python, Django, jQuery, etc.)

---

## Notes

- Tests run successfully on macOS with Python 3.12.8
- Required minor adjustments (setuptools, stripe upgrade, CORS config)
- All adjustments were backwards-compatible
- No code changes were needed in the application itself
- Ready to proceed with upgrade plan

---

## Verification Command

To verify this baseline state in the future:

```bash
cd /Users/bartgottschalk/Projects/WebApps/StartUpWebApp/startup_web_app_server_side
source venv/bin/activate
cd StartupWebApp
python manage.py test user order clientevent
```

Expected output: `Ran 10 tests in ~1s - OK`
