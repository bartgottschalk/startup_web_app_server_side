# Known Issues

This document tracks known issues and incomplete features discovered during development and testing.

## Recent Testing Session (November 4, 2024)

### jQuery 3.7.1 Upgrade Status
✅ **COMPLETED** - Frontend jQuery successfully upgraded from 3.2.1 to 3.7.1
- All functional tests passing (24/28 baseline maintained)
- QUnit tests passing (58/60 assertions)
- Zero regressions introduced
- Documentation updated

### Pre-Existing Application Issues Discovered

#### 1. Product Detail API Endpoint Missing/Incomplete
**Location**: `/order/product/{identifier}`
**Impact**: HIGH
**Description**:
- Frontend calls `GET /order/product/{identifier}` in `js/product-0.0.1.js:21`
- Backend endpoint doesn't exist or returns incomplete data
- Causes JavaScript error: `TypeError: undefined is not an object (evaluating 'data['product_data']['title']')` at line 76
- Database has minimal sample data (only 1 product record)

**Steps to Reproduce**:
1. Navigate to http://localhost:8080/product?id=bSusp6dBHm
2. Check browser console
3. See error about undefined `product_data`

**Next Steps**:
- Verify if `/order/product/{identifier}` endpoint exists in Django URLs
- Check if Product API view is properly configured
- Load full sample data from `db_inserts.sql` into database
- Test product detail page functionality

#### 2. Account Page Authentication Redirect Loses Port
**Location**: `/account/*` pages
**Impact**: MEDIUM
**Description**:
- When accessing account pages without authentication, redirect strips port number
- URL changes from `http://localhost:8080/account/` to `http://localhost/account/`
- Results in connection failure (port 80 instead of 8080)

**Steps to Reproduce**:
1. Navigate to http://localhost:8080/account/
2. Observe URL changes to http://localhost/account/ (missing :8080)
3. Page fails to load

**Next Steps**:
- Review authentication redirect code in Django views
- Check if redirect URLs are properly constructed with port preservation
- May be related to `ALLOWED_HOSTS` or domain configuration

### Functional Test Failures (Pre-Existing)

These 4 tests were failing before jQuery upgrade and remain unchanged:

1. **test_chat** - `ElementNotInteractableException: Element could not be scrolled into view`
2. **test_review_and_accept_terms_of_service** - `ElementNotInteractableException: Element could not be scrolled into view`
3. **test_footer** - `ElementNotInteractableException: Element could not be scrolled into view`
4. **test_header** - `NoSuchElementException: Unable to locate element: [id="cart-item-count-wrapper"]`

**Impact**: LOW (Test infrastructure issues, not application bugs)
**Next Steps**: Fix Selenium test timing/scrolling issues

## Working Features Verified

The following pages/features were tested and work correctly:

- ✅ Home page (http://localhost:8080/)
- ✅ About page (http://localhost:8080/about)
- ✅ Contact page (http://localhost:8080/contact)
- ✅ Products list (http://localhost:8080/products)
- ✅ Login page (http://localhost:8080/login)
- ✅ Create account page (http://localhost:8080/create-account)
- ✅ jQuery 3.7.1 AJAX functionality
- ✅ Environment detection (localhost routing)
- ✅ User API endpoint (`/user/logged-in`)

## Development Environment

**Stack**:
- Frontend: nginx:alpine (Docker)
- Backend: Django 2.2.28, Python 3.12.12 (Docker)
- Database: SQLite
- jQuery: 3.7.1

**URLs**:
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000

**Running Services**:
```bash
cd /Users/bartgottschalk/Projects/startup_web_app_server_side
docker-compose up -d
docker-compose exec -d backend python manage.py runserver 0.0.0.0:8000
```

## Next Session Priorities

1. **Fix Product Detail API** (HIGH)
   - Implement or repair `/order/product/{identifier}` endpoint
   - Load complete sample data into database
   - Test product detail page end-to-end

2. **Fix Account Redirect Issue** (MEDIUM)
   - Debug authentication redirect code
   - Ensure port preservation in redirects
   - Test all account pages

3. **Address Functional Test Failures** (LOW)
   - Fix Selenium scrolling issues
   - Add proper waits for dynamic content
   - Ensure cart counter renders before testing

4. **Consider Django Upgrade** (FUTURE)
   - Current: Django 2.2.28 (EOL April 2022)
   - Target: Django 4.2 LTS or Django 5.0+
   - Requires compatibility testing
