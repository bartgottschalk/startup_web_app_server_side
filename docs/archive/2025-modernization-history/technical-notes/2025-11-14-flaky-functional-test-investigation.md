# Flaky Functional Test Investigation and Fix

**Date**: November 14, 2025
**Status**: ✅ SUPERSEDED - See [2025-11-16-csrf-token-stale-variable-bug-fix.md](2025-11-16-csrf-token-stale-variable-bug-fix.md)
**Branch**: `bugfix/readme-linting-and-flaky-test` (initial investigation)
**Final Fix Branch**: `bugfix/csrf-token-stale-variable` (complete resolution)

> **Note**: This document describes the initial investigation that improved test pass rate from 50% to 80-90% through test-side workarounds. The root cause was fully resolved on November 16, 2025 by fixing the production JavaScript code, achieving 100% pass rate. See the linked document above for complete resolution details.

## Problem Statement

The functional test suite exhibited intermittent failures, passing approximately 50% of the time when run multiple times. This flakiness was originally attributed to the PythonABot chat dialogue test, but investigation revealed the actual culprit was the chat functionality test in `test_global_elements.py`.

## Root Cause Analysis

### Initial Investigation
- **Symptom**: Tests would pass 27/28 or 28/28 randomly
- **Original assumption**: `test_pythonabot_page_function_duplicate_error` was the flaky test
- **Actual culprit**: `test_chat` in `functional_tests/global/test_global_elements.py:120`

### Error Pattern
```
ERROR: test_chat (functional_tests.global.test_global_elements.AnonymousGlobalFunctionalTests.test_chat)
TimeoutError: The text value equality was not found before MAX_WAIT reached!
expected_value=Thank you. We got your message.
new_value=So sorry, but we're unavailable to chat at this time.
```

Accompanied by:
```
WARNING: Forbidden (CSRF token from the 'X-Csrftoken' HTTP header incorrect.): /user/put-chat-message
```

### Technical Root Cause

**Race Condition in CSRF Token Acquisition**:

1. **JavaScript Flow** (`js/index-0.0.2.js`):
   - Line 146: `$.get_token()` called asynchronously on page load
   - Line 51: Global `csrftoken` variable declared but not immediately set
   - Line 250: `csrftoken` used in AJAX request header

2. **The Problem**:
   - `$.get_token()` makes an AJAX call to `/user/token` endpoint
   - CSRF cookie is set by Django, then JavaScript reads it into `csrftoken` global
   - **If the test submits the form before this async operation completes, `csrftoken` is `undefined`**
   - Backend rejects request with CSRF error
   - Frontend shows fallback error message instead of success message

## Solution Implemented

### Fix 1: Wait for Page Element (Partial Fix)
**File**: `functional_tests/global/test_global_elements.py:124`
**Change**: Added explicit wait for chat icon to load before interacting
```python
functional_testing_utilities.wait_for_element_to_load_by_id(self, 'chat-icon-wrapper')
```
**Result**: Improved from ~50% to ~75% pass rate

### Fix 2: Wait for CSRF Token (Current Fix)
**File**: `functional_tests/global/test_global_elements.py:126-137`
**Change**: Added explicit wait for CSRF token to be fully initialized
```python
# wait for CSRF token to be fully ready (cookie + JS variable)
import time
start_time = time.time()
while True:
    # Check both cookie exists AND JavaScript variable is set
    csrf_cookie = self.browser.get_cookie('csrftoken')
    csrf_js_var = self.browser.execute_script("return typeof csrftoken !== 'undefined' && csrftoken !== null && csrftoken !== '';")
    if csrf_cookie is not None and csrf_js_var:
        break
    if time.time() - start_time > 10:
        raise TimeoutError('CSRF token was not fully initialized within 10 seconds')
    time.sleep(0.1)
```
**Result**: Improved to ~80-90% pass rate

## Test Results Summary

### Before Fix
- **Pass Rate**: ~50% (14/28 tests passing intermittently)
- **Pattern**: Completely random failures

### After Fix 1 (Element Wait)
- **Pass Rate**: ~75% (6/8 successful runs)
- **Improvement**: +25 percentage points

### After Fix 2 (CSRF Token Wait)
- **Pass Rate**: ~80-90% (7-9/10 successful runs, 16/20 in large sample)
- **Improvement**: +30-40 percentage points from baseline
- **Remaining Issue**: Still 10-20% failure rate

## Parallel Testing Discovery

During investigation, we discovered that `docker-compose run` enables parallel test execution:

**Command**:
```bash
seq 1 8 | xargs -P 4 -I {} bash -c 'docker-compose run --rm -e HEADLESS=TRUE backend bash -c "bash /app/setup_docker_test_hosts.sh > /dev/null 2>&1 && python manage.py test functional_tests --verbosity=1" 2>&1 | tail -3'
```

**Benefits**:
- Each `docker-compose run` creates isolated container with own Selenium instance
- 8 tests complete in ~2-3 minutes (vs 10+ minutes serially)
- Enables faster iteration during debugging

**Requirements**:
- Must run hosts setup script in each container
- Each container needs access to shared frontend via Docker network

## Remaining Work

### Current Status
- ✅ Identified root cause (CSRF token race condition)
- ✅ Implemented partial fix (80-90% success rate)
- ✅ All 693 unit tests still passing (zero regressions)
- ⏳ 10-20% failure rate remains

### Next Steps for Future Session
1. **Identify which test(s) still fail**: The chat test appears stable when run alone; failures may be in other tests
2. **Investigate test ordering effects**: Some tests may not properly clean up state
3. **Consider test isolation improvements**: Ensure each test starts with clean CSRF state
4. **Evaluate frontend code change**: Could make CSRF token acquisition synchronous or add ready callback

### Alternative Approaches Not Yet Tried
1. **Refactor frontend**: Make `$.get_token()` accept a callback and only enable forms after token ready
2. **Add test helper**: Create reusable wait function for CSRF token across all functional tests
3. **Increase wait time**: Current 0.1s sleep interval might be too aggressive
4. **Django test fixtures**: Ensure test database state is consistent between runs

## Files Modified

1. `startup_web_app_server_side/README.md:129`
   - Fixed linting command: `--max-line-length=100` → `--max-line-length=120`

2. `startup_web_app_server_side/StartupWebApp/functional_tests/global/test_global_elements.py:120-137`
   - Added CSRF token wait logic in `test_chat()` method

## Testing Verification

**Unit Tests**: ✅ All 693 passing
```bash
docker-compose exec backend python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests
```

**Functional Tests**: ⏳ 80-90% passing (target: 100%)
```bash
docker-compose exec -e HEADLESS=TRUE backend bash -c "bash /app/setup_docker_test_hosts.sh && python manage.py test functional_tests"
```

## Lessons Learned

1. **Test flakiness indicates real bugs**: The CSRF timing issue could affect real users on slow connections
2. **Async operations need explicit synchronization**: Frontend JavaScript race conditions are hard to debug
3. **Parallel testing accelerates debugging**: Being able to run 20 tests in 3 minutes vs 30 minutes is game-changing
4. **80-90% is not good enough**: Even 10% flakiness erodes trust in the entire test suite
5. **Root cause investigation is worth the time**: Understanding *why* tests fail is more valuable than quick fixes

## References

- SESSION_START_PROMPT.md: Lines 238, 316 (flaky test noted)
- PROJECT_HISTORY.md: Line 163 (27/28 functional tests passing)
- Django CSRF Documentation: https://docs.djangoproject.com/en/4.2/ref/csrf/
