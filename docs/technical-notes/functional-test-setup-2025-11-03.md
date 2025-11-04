# Functional Test Setup Investigation

**Date**: 2025-11-03
**Status**: Infrastructure Ready - Networking Challenges Remain
**Python Version**: 3.12.8
**Django Version**: 2.2.28
**Selenium Version**: 3.141.0

## Executive Summary

Successfully resolved infrastructure issues for functional tests (boto3, Firefox, geckodriver, urllib3). Tests can now initialize Selenium and Firefox in headless mode within Docker. However, full-stack functional tests require complex networking between Docker container, host machine, frontend server (port 8080), and backend API (port 60767).

## What Was Accomplished

### ✅ Fixed Infrastructure Issues

1. **boto3 Import Error** - Removed unused import from `functional_testing_utilities.py`
2. **Firefox & geckodriver** - Installed in Docker container (Firefox ESR + geckodriver 0.33.0)
3. **urllib3 Compatibility** - Pinned to <2.0.0 for Selenium 3.x compatibility
4. **Headless Mode** - Tests run successfully in headless mode with HEADLESS=TRUE

### ✅ Network Configuration Attempts

1. **Frontend Server** - Started Python HTTP server on port 8080 (avoiding port 80 conflict)
2. **Docker Networking** - Added `extra_hosts` to docker-compose.yml:
   ```yaml
   extra_hosts:
     - "localliveservertestcase.startupwebapp.com:host-gateway"
     - "localliveservertestcaseapi.startupwebapp.com:host-gateway"
   ```
3. **Port Exposure** - Exposed port 60767 for LiveServerTestCase API
4. **Base Test Update** - Modified `static_home_page_url` to use port 8080

## Architectural Challenge

The functional tests require coordination between multiple components:

```
┌─────────────────────────────────────────────────────────────┐
│ Docker Container (startupwebapp-backend-dev)                │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Selenium + Firefox (Headless)                       │   │
│  │  - Navigates to frontend URLs                       │   │
│  │  - Makes API calls to backend                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Django LiveServerTestCase (port 60767)              │   │
│  │  - Backend API for tests                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↕ (Network)
┌─────────────────────────────────────────────────────────────┐
│ Host Machine (Mac)                                           │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Python HTTP Server (port 8080)                      │   │
│  │  - Serves frontend static files                     │   │
│  │  - HTML, CSS, JavaScript                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Current Test Behavior

**Test Command**:
```bash
docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests.about.test_about --verbosity=2
```

**Observed Behavior**:
1. ✅ Test database creates successfully
2. ✅ Firefox initializes in headless mode
3. ✅ Test setup completes (28 model records created)
4. ⏸️ Test hangs when attempting to navigate to frontend URL

**Likely Issues**:
- Frontend JavaScript making API calls that time out
- CORS configuration preventing cross-origin requests
- Network routing between container and host
- Frontend expecting different API endpoint configuration

## Files Modified

### 1. StartupWebApp/functional_tests/base_functional_test.py
```python
# Line 26 changed from:
static_home_page_url = "http://localliveservertestcase.startupwebapp.com/"

# To:
static_home_page_url = "http://localliveservertestcase.startupwebapp.com:8080/"
```

### 2. docker-compose.yml
```yaml
# Added port exposure
ports:
  - "8000:8000"
  - "60767:60767"  # LiveServerTestCase API port

# Added host networking
extra_hosts:
  - "localliveservertestcase.startupwebapp.com:host-gateway"
  - "localliveservertestcaseapi.startupwebapp.com:host-gateway"
```

## Frontend Server Setup

**Started on host**:
```bash
cd ../startup_web_app_client_side
nohup python3 -m http.server 8080 > /tmp/frontend_8080.log 2>&1 &
```

**Accessible at**:
- http://localliveservertestcase.startupwebapp.com:8080/

## Next Steps for Full Resolution

### Option A: Simplified Approach (Recommended)
**Run tests outside Docker** where both frontend and backend are easily accessible:
1. Install Firefox and geckodriver on host machine
2. Run backend in Docker (port 60767 exposed)
3. Run frontend server on host (port 8080)
4. Run tests on host machine directly
5. Pros: Simpler networking, easier debugging
6. Cons: Requires host-level dependencies

### Option B: Docker Compose Approach
**Add frontend to docker-compose.yml**:
1. Create nginx service in docker-compose.yml
2. Mount frontend files as volume
3. Configure Docker network for inter-service communication
4. All components in Docker containers
5. Pros: Fully containerized, reproducible
6. Cons: More complex setup, larger docker-compose file

### Option C: Debug Current Setup
**Investigate current hanging issue**:
1. Check Firefox network logs inside container
2. Verify frontend JavaScript API calls
3. Review CORS configuration
4. Check if LiveServerTestCase is accessible from frontend
5. Pros: Minimal changes to current setup
6. Cons: Time-consuming debugging

## Test Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| boto3 Import | ✅ Fixed | Removed unused import |
| Firefox Installation | ✅ Working | Firefox ESR in Docker |
| geckodriver | ✅ Working | v0.33.0 installed |
| urllib3 Compatibility | ✅ Fixed | Pinned to 1.26.x |
| Headless Mode | ✅ Working | HEADLESS=TRUE functional |
| Frontend Server | ✅ Running | Port 8080 on host |
| Backend API | ✅ Running | Port 60767 in Docker |
| Docker Networking | ⚠️ Partial | host-gateway configured |
| Full Test Execution | ❌ Hanging | Network/timing issue |

## Recommendations

**Short Term**:
- Document current setup for future reference
- Consider Option A (run tests on host) for immediate functional test execution
- 626 unit tests provide excellent backend coverage

**Medium Term**:
- Implement Option B (Docker Compose) for CI/CD pipelines
- Create detailed functional test documentation
- Consider upgrading to Selenium 4.x (when upgrading Django)

**Long Term**:
- Evaluate moving to modern frontend framework (React/Vue)
- Consider Playwright or Cypress instead of Selenium
- Implement frontend unit tests independent of backend

## Related Documentation

- [Python Deprecation Audit](./python-deprecation-audit-2025-11-03.md)
- [Baseline Test Results](../milestones/2025-10-31-baseline-established.md)
- [Functional Test Utilities](../../StartupWebApp/functional_tests/functional_testing_utilities.py)

## Change Log

- **2025-11-03**: Fixed boto3, Firefox, geckodriver, urllib3 issues
- **2025-11-03**: Configured Docker networking with extra_hosts
- **2025-11-03**: Started frontend server on port 8080
- **2025-11-03**: Modified base test to use port 8080
- **2025-11-03**: Documented networking challenges and recommendations
