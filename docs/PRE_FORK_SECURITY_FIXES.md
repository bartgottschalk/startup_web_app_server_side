# Pre-Fork Security Fixes - Multi-Session Plan

**Created:** December 29, 2025
**Status:** 🔴 IN PROGRESS
**Target Completion:** January 15, 2026
**Goal:** Fix all critical and high-priority security issues before forking SWA for first business experiment

---

## 📊 PROGRESS TRACKER

### Critical Issues (MUST FIX - 5/5 remaining)
- [ ] **CRITICAL-001:** Email credentials in git history
- [ ] **CRITICAL-002:** XSS vulnerabilities (unescaped user input)
- [ ] **CRITICAL-003:** Active console.log statements
- [ ] **CRITICAL-004:** Hardcoded production API URLs
- [ ] **CRITICAL-005:** CSRF token retry logic race condition

### High Priority Issues (SHOULD FIX - 9/9 remaining)
- [ ] **HIGH-001:** Stripe test keys in code
- [ ] **HIGH-002:** Database password fallback
- [ ] **HIGH-003:** Missing @login_required decorators
- [ ] **HIGH-004:** No transaction protection on order creation
- [ ] **HIGH-005:** No rate limiting
- [ ] **HIGH-006:** No server-side price validation confirmation
- [ ] **HIGH-007:** Weak password validation
- [ ] **HIGH-008:** Login status race condition
- [ ] **HIGH-009:** Insufficient error handling

### Sessions Completed: 0
### Estimated Sessions Remaining: 5-7

---

## 🎯 SESSION PLAN

### SESSION 1: Credential Rotation & Secret Management (IMMEDIATE)
**Estimated Time:** 2-3 hours
**Branch:** `feature/pre-fork-security-hardening`
**PRs:** Server #59, Client #18

**Tasks:**
1. [ ] **BEFORE CODING:** Human rotates Gmail App Password
2. [ ] Review current `settings_secret.py` structure
3. [ ] Create environment variable migration plan
4. [ ] Update `settings.py` to require env vars (no fallbacks)
5. [ ] Update `settings_production.py` validation
6. [ ] Move Stripe keys to env vars
7. [ ] Remove database password fallback
8. [ ] Update `.env.example` with all required variables
9. [ ] Update deployment documentation
10. [ ] Verify `settings_secret.py` still in `.gitignore`
11. [ ] Test local development with env vars
12. [ ] Run all 730 tests
13. [ ] Update `docs/technical-notes/` with changes

**Fixes:**
- ✅ CRITICAL-001 (Email credentials)
- ✅ HIGH-001 (Stripe test keys)
- ✅ HIGH-002 (Database password fallback)

**Deliverables:**
- Server PR #59: Secret management migration
- Documentation: Environment variable setup guide
- Technical note: 2026-01-XX-secret-management-migration.md

---

### SESSION 2: XSS Vulnerability Remediation (Client-Side)
**Estimated Time:** 3-4 hours
**Branch:** `feature/xss-vulnerability-fixes`
**PR:** Client #19

**Tasks:**
1. [ ] Create HTML escaping utility function in `form-utilities-0.0.1.js`
2. [ ] Fix `/js/index-0.0.2.js` (lines 288-290, 412)
3. [ ] Fix `/js/checkout/confirm-0.0.1.js` (lines 338-344, 349-355, 360, 372, 487)
4. [ ] Fix `/js/account-0.0.1.js` (lines 87-97, 104-110)
5. [ ] Fix `/js/account/order-0.0.1.js` (lines 41, 64, 97, 165-168, 175-178, 187, 192, 200)
6. [ ] Fix `/js/product-0.0.1.js` (lines 68, 138, 212, 219, 226)
7. [ ] Fix `/js/checkout/success-0.0.1.js` (line 76)
8. [ ] Add Content-Security-Policy header in Django settings
9. [ ] Create XSS regression tests
10. [ ] Test all user flows with XSS payloads
11. [ ] Run ESLint
12. [ ] Update technical documentation

**Testing Payloads:**
```javascript
// Test these inputs in all fixed fields
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
<svg onload=alert('XSS')>
```

**Fixes:**
- ✅ CRITICAL-002 (XSS vulnerabilities)

**Deliverables:**
- Client PR #19: XSS vulnerability fixes
- Unit tests for HTML escaping
- Security test documentation

---

### SESSION 3: Frontend Security Hardening
**Estimated Time:** 2-3 hours
**Branch:** `feature/frontend-security-cleanup`
**PR:** Client #20

**Tasks:**
1. [ ] Remove all active console.log statements
   - `/js/login-0.0.1.js` (line 32)
   - `/js/create-account-0.0.1.js` (lines 73, 132, 203, 206, 210)
   - `/js/index-0.0.2.js` (line 291)
   - `/js/product-0.0.1.js` (line 336)
2. [ ] Move API URLs to configuration
   - Create `config.js` or use environment-based build
   - Update all files using hardcoded URLs
3. [ ] Fix CSRF token retry logic race condition
   - Replace global `token_retried` with request-specific tracking
   - Test concurrent AJAX requests
4. [ ] Fix login status race condition
   - Audit all uses of `$.user_logged_in`
   - Ensure all use `$.loginStatusReady.then()`
5. [ ] Run ESLint
6. [ ] Test all authentication flows
7. [ ] Run frontend unit tests

**Fixes:**
- ✅ CRITICAL-003 (console.log statements)
- ✅ CRITICAL-004 (Hardcoded API URLs)
- ✅ CRITICAL-005 (CSRF retry logic)
- ✅ HIGH-008 (Login status race condition)

**Deliverables:**
- Client PR #20: Frontend security cleanup
- Configuration documentation
- Updated frontend deployment guide

---

### SESSION 4: Backend Security Hardening
**Estimated Time:** 3-4 hours
**Branch:** `feature/backend-security-hardening`
**PR:** Server #60

**Tasks:**
1. [ ] Add `@transaction.atomic` to order creation
   - `order/views.py` - `handle_checkout_session_completed`
   - `order/views.py` - Cart-to-order conversion
   - Test rollback on errors
2. [ ] Add `@login_required` decorators to protected views
   - Audit all view functions in `user/views.py`
   - Audit all view functions in `order/views.py`
   - Test authentication enforcement
3. [ ] Add server-side price validation
   - Verify checkout totals match server calculations
   - Reject tampered amounts
4. [ ] Strengthen password validation
   - Increase min length to 12 characters
   - Expand special character set
   - Update client-side validation to match
5. [ ] Run all 730 tests
6. [ ] Run flake8

**Fixes:**
- ✅ HIGH-003 (@login_required decorators)
- ✅ HIGH-004 (Transaction protection)
- ✅ HIGH-006 (Server-side price validation)
- ✅ HIGH-007 (Password validation)

**Deliverables:**
- Server PR #60: Backend security hardening
- Updated password policy documentation
- Transaction test coverage

---

### SESSION 5: Rate Limiting & Error Handling
**Estimated Time:** 3-4 hours
**Branch:** `feature/rate-limiting-and-errors`
**PRs:** Server #61, Client #21

**Tasks:**

**Server-Side:**
1. [ ] Install django-ratelimit: `pip install django-ratelimit`
2. [ ] Add rate limiting to public endpoints
   - Client events: 1000/hour per IP
   - Password reset: 5/hour per email
   - Contact form: 10/hour per IP
   - Checkout: 20/hour per session
3. [ ] Test rate limiting enforcement
4. [ ] Add CloudWatch alarms for rate limit violations
5. [ ] Update requirements.txt

**Client-Side:**
1. [ ] Improve AJAX error handling
   - Distinguish network vs server vs validation errors
   - Add actionable error messages
   - Implement retry logic for transient failures
2. [ ] Add client-side error logging
   - Log to backend endpoint for monitoring
   - Include user agent, URL, error details
3. [ ] Test error scenarios
4. [ ] Run ESLint

**Fixes:**
- ✅ HIGH-005 (Rate limiting)
- ✅ HIGH-009 (Error handling)

**Deliverables:**
- Server PR #61: Rate limiting implementation
- Client PR #21: Improved error handling
- Monitoring/alerting documentation

---

### SESSION 6: Testing & Validation
**Estimated Time:** 2-3 hours
**Branch:** `feature/security-testing`
**PR:** Server #62

**Tasks:**
1. [ ] Run full security audit
   - Test XSS payloads in all forms
   - Test CSRF protection
   - Test rate limiting
   - Test authentication enforcement
2. [ ] Run all 730 backend tests
3. [ ] Run all frontend unit tests
4. [ ] Run flake8 + ESLint (zero errors)
5. [ ] Test deployment to staging
6. [ ] Load test critical flows
7. [ ] Document remaining known issues
8. [ ] Update PROJECT_HISTORY.md
9. [ ] Create technical note summary

**Deliverables:**
- Security test suite
- Technical note: 2026-01-XX-pre-fork-security-fixes-complete.md
- Updated PROJECT_HISTORY.md

---

### SESSION 7: Production Deployment & Monitoring (Optional)
**Estimated Time:** 2-3 hours
**Tasks:**

1. [ ] Configure client-side error tracking (Sentry or similar)
2. [ ] Set up CloudWatch dashboards
3. [ ] Configure alarms for:
   - 5xx errors
   - Rate limit violations
   - Failed authentication attempts
   - Stripe webhook failures
4. [ ] Document incident response procedures
5. [ ] Create rollback runbook
6. [ ] Test monitoring/alerting

**Deliverables:**
- Monitoring dashboard
- Incident response documentation
- Rollback procedure

---

## 📋 PRE-SESSION CHECKLIST

Before starting each session:
1. [ ] Review previous session's merged PRs
2. [ ] Check production health (no issues from recent changes)
3. [ ] Create feature branch from latest master
4. [ ] Review session tasks and acceptance criteria
5. [ ] Ensure Docker Desktop is running

---

## 🧪 TESTING REQUIREMENTS

Every PR must include:
- [ ] All 730 backend tests passing
- [ ] Frontend unit tests passing (if client-side changes)
- [ ] Zero linting errors (flake8 + ESLint)
- [ ] Manual testing of affected flows
- [ ] Documentation updates

---

## 📝 DOCUMENTATION UPDATES

Each session should update:
1. `docs/PROJECT_HISTORY.md` - Add milestone entry
2. `docs/technical-notes/YYYY-MM-DD-description.md` - Detailed technical note
3. `README.md` - If user-facing changes
4. This file (`PRE_FORK_SECURITY_FIXES.md`) - Check off completed tasks

---

## 🎯 SUCCESS CRITERIA

All fixes complete when:
- [x] All 5 CRITICAL issues resolved
- [x] All 9 HIGH priority issues resolved
- [x] All 730 tests passing
- [x] Zero linting errors
- [x] Security audit passed
- [x] Production deployment successful
- [x] Monitoring/alerting configured
- [x] Documentation complete

**THEN:** ✅ **SAFE TO FORK FOR BUSINESS EXPERIMENT**

---

## 🚨 ROLLBACK PLAN

If any session causes production issues:
1. Use GitHub Actions rollback workflow
2. Revert merged PR
3. Document issue in technical notes
4. Fix in new PR before continuing

---

## 📚 REFERENCE DOCUMENTATION

**Audit Reports:**
- Full server-side audit: (see exploration agent output from Session 15)
- Full client-side audit: (see exploration agent output from Session 15)

**Related Documentation:**
- `docs/PROJECT_HISTORY.md` - Project timeline
- `docs/DISASTER_RECOVERY.md` - Rollback procedures
- `docs/PROJECT_ROADMAP_2026.md` - Long-term planning

**Security Resources:**
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Django Security: https://docs.djangoproject.com/en/5.2/topics/security/
- CSP Guide: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP

---

## 💡 NOTES & LESSONS LEARNED

### Session 15 (December 29, 2025) - Pre-Fork Audit
**Findings:**
- Email credentials were in git history (early commits)
- `settings_secret.py` is NOW properly gitignored (only `.template` tracked)
- XSS vulnerabilities extensive across client-side
- Production is healthy and operational
- 730 tests all passing - excellent coverage
- Multi-tenant database design is ideal for forks

**Key Insight:** Infrastructure and architecture are solid. Issues are fixable code-level problems, not architectural flaws.

### Session X - Add notes as we complete sessions

---

**Last Updated:** December 29, 2025
**Next Session:** #1 - Credential Rotation & Secret Management
