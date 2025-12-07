# Production Frontend Issues - Investigation Needed

**Date**: December 7, 2025
**Status**: 🔍 Discovered - Investigation Pending
**Priority**: High (user-facing pages not working)

## Overview

During verification of Phase 5.16 completion (Production Superuser & Django Admin), discovered that two user-facing pages in production are returning errors.

## Issues Discovered

### Issue 1: `/account` - 403 AccessDenied (S3/CloudFront)

**URL**: https://startupwebapp.mosaicmeshai.com/account

**Error**:
```xml
<Error>
  <Code>AccessDenied</Code>
  <Message>Access Denied</Message>
</Error>
```

**HTTP Status**: 403 Forbidden

**Browser Console Error**:
```
GET https://startupwebapp.mosaicmeshai.com/account [HTTP/2 403]
```

**Additional Error** (browser extension unrelated):
```
TypeError: right-hand side of 'in' should be an object, got undefined
web-client-content-script.js:2:996709
```
*(This appears to be a Firefox extension error, not related to our application)*

**Analysis**:
- This is an S3/CloudFront issue
- S3 is returning AccessDenied XML response
- Likely causes:
  - File doesn't exist in S3 bucket (`account` or `account.html`)
  - S3 bucket policy doesn't allow access
  - CloudFront OAI/OAC configuration issue
  - File permissions in S3

**Not Related To**:
- Phase 5.16 changes (superuser, Django Admin, WhiteNoise)
- Backend API code changes
- Recent deployments (likely pre-existing)

---

### Issue 2: `/create-account` - 500 Internal Server Error (Backend API)

**URL**: https://startupwebapp.mosaicmeshai.com/create-account (frontend page)
**API Endpoint**: https://startupwebapp-api.mosaicmeshai.com/user/create-account

**HTTP Status**: 500 Internal Server Error

**Headers**:
```
scheme: https
host: startupwebapp-api.mosaicmeshai.com
filename: /user/create-account
Address: 52.44.129.87:443
Status: 500
Version: HTTP/2
Transferred: 796 B (145 B size)
```

**Analysis**:
- Backend API is returning 500 error
- This is a code/database issue on the backend
- Likely causes:
  - Missing database record (configuration, reference data)
  - Code exception (unhandled error in view)
  - Database query failure
  - Missing environment variable or secret

**Not Related To**:
- Phase 5.16 changes (superuser, Django Admin, WhiteNoise)
- Frontend code (the error is from the backend API)
- S3/CloudFront configuration

---

## Investigation Plan

### For Issue 1: `/account` - 403 AccessDenied

**Step 1: Verify S3 bucket contents**
```bash
# List files in S3 bucket
aws s3 ls s3://startupwebapp-frontend-production/ --recursive | grep account

# Check if account.html exists
aws s3 ls s3://startupwebapp-frontend-production/account
aws s3 ls s3://startupwebapp-frontend-production/account.html
```

**Step 2: Check S3 bucket policy**
```bash
# Get bucket policy
aws s3api get-bucket-policy --bucket startupwebapp-frontend-production

# Check if CloudFront OAC has access
aws cloudfront get-distribution-config --id E1HZ3V09L2NDK1
```

**Step 3: Check CloudFront cache**
- CloudFront might be caching the error
- Consider invalidating cache for `/account` path

**Step 4: Check frontend source code**
```bash
# In client-side repo, verify account page exists
ls -la ~/Projects/WebApps/StartUpWebApp/startup_web_app_client_side/account*

# Check if it was deployed to S3
```

**Likely Fix**:
- Add missing `account.html` file to S3
- Or fix S3 bucket policy to allow access
- Or add CloudFront cache invalidation

---

### For Issue 2: `/create-account` - 500 Internal Server Error

**Step 1: Check backend logs**
```bash
# Get recent ECS task
aws ecs list-tasks --cluster startupwebapp-cluster --service-name startupwebapp-service

# Get logs from running task
aws logs tail /ecs/startupwebapp-service --follow
```

**Step 2: Check CloudWatch logs for the specific error**
- Look for exception traceback
- Check timestamp around when you accessed the page

**Step 3: Test endpoint directly**
```bash
# Test API endpoint (might need authentication)
curl -X POST https://startupwebapp-api.mosaicmeshai.com/user/create-account \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}'
```

**Step 4: Check for missing configuration**
- Is `ClientEventConfiguration` record present? (We added seed data migration)
- Are all required reference data tables populated?
- Check for any new database constraints or requirements

**Step 5: Review recent code changes**
- Check if `/user/create-account` endpoint was modified
- Review any validation logic changes
- Check for new required fields

**Likely Causes**:
1. Missing database configuration record
2. Stripe API key issue (if account creation involves payment setup)
3. Email service configuration missing
4. Validation error not being caught properly

---

## Testing Strategy

### Verify Issue Scope

**Check if other pages work**:
- `/` (homepage) - Does it load?
- `/products` - Does it load?
- `/about` - Does it load?
- `/login` - Does it load?

**Check if issue is environment-specific**:
- Does `/account` work locally? (`http://localhost.startupwebapp.com:8080/account`)
- Does `/create-account` work locally?

### Systematic Debugging

1. **Start with backend logs** (CloudWatch) - Most likely to show root cause
2. **Check S3 bucket contents** - Quick verification
3. **Test API endpoints directly** - Isolate backend vs frontend
4. **Check database state** - Verify seed data is present

---

## Questions to Answer

1. **When did these issues start?**
   - Were these pages working before Phase 5.16?
   - Were they working before Phase 5.15?
   - Have they ever worked in production?

2. **What changed recently?**
   - Phase 5.16: Superuser, WhiteNoise, static files (unlikely to affect these pages)
   - Phase 5.15: Full deployment, seed data migrations
   - Could seed data migrations be missing something?

3. **Do these pages work locally?**
   - Test in local Docker environment
   - Compare behavior local vs production

---

## Risk Assessment

**Impact**:
- **High** - User-facing pages not working
- `/create-account` blocks new user registration
- `/account` blocks existing users from managing their accounts

**Urgency**:
- **Medium-High** - Production issue but application is still in development/testing phase
- Not revenue-impacting yet (no active users)
- Should be fixed before public launch

**Complexity**:
- **Unknown** - Need to investigate logs and reproduce locally
- Could be simple (missing file) or complex (backend logic issue)

---

## Next Session Action Items

1. **Investigate backend `/create-account` 500 error**
   - Check CloudWatch logs for exception traceback
   - Reproduce locally in Docker
   - Test API endpoint directly
   - Fix root cause and add regression test

2. **Investigate frontend `/account` 403 error**
   - Check S3 bucket for missing files
   - Verify S3 bucket policy and CloudFront OAC
   - Check frontend deployment process
   - Fix missing files or permissions

3. **Verify fix in production**
   - Test both pages after fix
   - Add functional tests to prevent regression
   - Document resolution in technical notes

4. **Check for other broken pages**
   - Systematically test all frontend pages
   - Test all backend API endpoints
   - Create comprehensive smoke test checklist

---

## Temporary Workarounds

**None recommended** - These are core user functionality pages. Should be fixed properly rather than worked around.

---

## Related Documentation

- Frontend deployment: `docs/technical-notes/2025-11-26-phase-5-15-production-deployment.md`
- Seed data migrations: `docs/technical-notes/2025-12-04-seed-data-migrations.md`
- CloudFront setup: `scripts/infra/create-frontend-hosting.sh`

---

## Status

- [ ] Backend logs reviewed
- [ ] Root cause identified for `/create-account` 500 error
- [ ] Root cause identified for `/account` 403 error
- [ ] Issues reproduced locally
- [ ] Fixes implemented
- [ ] Tests added to prevent regression
- [ ] Verified in production
- [ ] Documentation updated
