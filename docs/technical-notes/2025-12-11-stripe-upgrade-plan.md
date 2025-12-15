# Stripe Integration Upgrade Plan

**Date**: December 11, 2025
**Status**: Planning Phase
**Priority**: HIGH - Current integration is deprecated and broken

## Executive Summary

The current Stripe Checkout v2 integration is deprecated and non-functional. Stripe is phasing out the old APIs, causing "integration surface is unsupported for publishable key tokenization" errors. This document outlines a multi-phase upgrade plan to migrate to modern Stripe Checkout Sessions.

---

## Current State (Broken)

### Integration Details

**Stripe Library Version:**
- Current: `stripe==5.5.0` (released ~2020)
- Latest: `stripe==10.x+` (2024+)
- Status: **SEVERELY OUTDATED**

**Frontend Integration:**
- **Method**: Stripe Checkout v2 (deprecated, being shut down)
- **Script**: `https://checkout.stripe.com/checkout.js`
- **API**: `StripeCheckout.configure()`
- **Status**: **DEPRECATED - NO LONGER SUPPORTED**

**Backend Integration:**
- **Method**: Token-based flow with Sources API
- **Pattern**: `stripe.Customer.create(source=stripe_token)`
- **API**: Sources API (deprecated)
- **Status**: **DEPRECATED**

### Error Encountered

**Error Message:**
```
This integration surface is unsupported for publishable key tokenization.
To enable this surface, please go to your dashboard
(https://dashboard.stripe.com/settings/integration).
```

**Root Cause:**
Stripe is actively deprecating and shutting down Checkout v2 and the Sources API. New Stripe accounts and many existing accounts can no longer use these deprecated APIs.

### Files Using Deprecated Stripe APIs

**Frontend (4 files):**
1. `js/checkout/confirm-0.0.1.js:367-379` - StripeCheckout.configure()
2. `js/account-0.0.1.js:171-185` - StripeCheckout.configure()
3. `checkout/confirm:129` - Script include
4. `account/index.html:37` - Script include

**Backend (3 files):**
1. `order/views.py` - Token processing, charge creation
   - `process_stripe_payment_token()` (1317-1445)
   - `confirm_place_order()` (908-1314)
   - `confirm_payment_data()` (431-498)
2. `user/views.py` - Account payment processing
   - `process_stripe_payment_token()` (1445-1542)
3. `order/utilities/order_utils.py` - Customer/card management
   - `create_stripe_customer()` (613-626)
   - `retrieve_stripe_customer()` (600-610)
   - `stripe_customer_add_card()` (646-658)
   - `stripe_customer_change_default_payemnt()` (661-675)

---

## Modern Stripe Integration Options

### Option A: Checkout Sessions (Recommended)

**Description:**
Stripe-hosted checkout page with redirect flow. Stripe handles the entire payment UI.

**Pros:**
- Fastest to implement (3 days)
- Stripe handles PCI compliance
- Automatic SCA/3D Secure
- Built-in mobile optimization
- Less code to maintain
- Stripe handles UI updates

**Cons:**
- Less UI customization
- User redirected to Stripe
- Less control over flow

**Best For:**
- Getting off deprecated APIs quickly
- Standard checkout flows
- Teams with limited frontend resources

### Option B: Payment Intents + Elements

**Description:**
Custom payment form embedded in your site using Stripe Elements with Payment Intents API.

**Pros:**
- Full UI control
- Seamless user experience
- Custom error handling
- Better branding

**Cons:**
- More complex (6-9 days)
- More code to maintain
- More testing required
- Higher development cost

**Best For:**
- Custom checkout experiences
- When UI control is critical
- After getting basic payments working

---

## Recommended Upgrade Strategy

### Phase 1: Migrate to Checkout Sessions (This Project)

**Goal:** Get off deprecated APIs, restore payment functionality

**Approach:**
1. Start with Checkout Sessions (faster, lower risk)
2. Get payments working in 3 days
3. Maintain all existing functionality
4. Can migrate to Elements later if needed

### Phase 2: Optional - Migrate to Elements (Future)

**Goal:** More UI control and better UX

**Timing:** After Phase 1 is stable and tested

---

## Implementation Plan - Broken into Session-Sized Chunks

### Session 1: Research & Planning (1-2 hours)
**Branch:** `feature/stripe-upgrade-planning`

**Tasks:**
- ✅ Document current state (this document)
- ✅ Assess upgrade options
- ✅ Choose approach (Checkout Sessions)
- Read Stripe Checkout Sessions documentation
- Identify all affected endpoints
- Create detailed task breakdown
- Update PROJECT_HISTORY.md

**Deliverable:** Complete upgrade plan with task breakdown

---

### Session 2: Stripe Library Upgrade (2-3 hours) ✅ COMPLETE
**Branch:** `feature/stripe-upgrade-library` (merged to master via PR #49)
**Date:** December 11, 2025
**Duration:** ~2 hours

**Tasks:**
- ✅ Upgrade `requirements.txt`: `stripe==5.5.0` → `stripe==14.0.1` (latest stable)
- ✅ Update Docker image with new library
- ✅ Review breaking changes in stripe library (v6-v14)
- ✅ Update any deprecated API calls in existing code (none found!)
- ✅ Run all 715 unit tests (ensure mocks still work)
- ✅ Fix any test failures (none!)
- ✅ Fix docker-compose.yml configuration (added `target: development`)
- ✅ Commit and merge

**Deliverable:** ✅ Updated stripe library with passing tests, deployed to production

**Actual Results:**
- **Library Version:** Upgraded to 14.0.1 (November 2025 release)
- **Breaking Changes:** None affecting our code (already using keyword arguments)
- **Code Changes:** Zero - existing code is fully compatible
- **Tests:** 715/715 unit tests passed, 30/31 functional tests passed (1 unrelated failure)
- **Bonus Fix:** Discovered and fixed docker-compose.yml missing `target: development` from Phase 5.14

**Key Findings:**
- Our Stripe usage is simple and stable (Customer.create/retrieve/modify)
- All Stripe calls are mocked in tests (27 mock statements across 5 files)
- Real API validation will happen in Sessions 3-6 when implementing Checkout Sessions
- Docker multi-stage build configuration was incomplete (now fixed)

**Risk Assessment:** ✅ Low risk - Upgrade went smoothly, no compatibility issues

---

### Session 3: Backend - Create Checkout Session Endpoint (2-3 hours) ✅ COMPLETE
**Branch:** `feature/stripe-checkout-session-endpoint` (merged to master via PR #50)
**Date:** December 12, 2025

**Tasks Completed:**
- ✅ Create new endpoint: `/order/create-checkout-session`
- ✅ Implement `stripe.checkout.Session.create()`
- ✅ Calculate order total and line items
- ✅ Handle member vs prospect flows
- ✅ Add proper error handling
- ✅ Write unit tests for new endpoint (7 tests)
- ✅ Run all tests (722 unit tests passing)
- ✅ Commit and merge

**Deliverable:** ✅ Working checkout session creation endpoint

**Files Modified:**
- `order/views.py` (new `create_checkout_session()` function)
- `order/urls.py` (added route)
- `order/tests/test_stripe_checkout_session.py` (new test file, 7 tests)

---

### Session 4: Backend - Checkout Session Success Handler (2-3 hours) ✅ COMPLETE
**Branch:** `feature/stripe-checkout-success-handler` (PR #51, pending review)
**Date:** December 12, 2025

**Tasks Completed:**
- ✅ Create success endpoint: `/order/checkout-session-success`
- ✅ Retrieve session data from Stripe with `stripe.checkout.Session.retrieve()`
- ✅ Create order in database with all related objects
- ✅ Send order confirmation email (member and prospect flows)
- ✅ Add database migration for `stripe_payment_intent_id` field (prevents duplicates)
- ✅ Update checkout session creation to collect addresses
- ✅ Write unit tests (7 comprehensive tests, TDD approach)
- ✅ Run all tests (729 unit tests passing)
- ✅ Commit and push

**Deliverable:** ✅ Order creation after successful payment

**Files Modified:**
- `order/models.py` (added `stripe_payment_intent_id` to Orderpayment)
- `order/views.py` (new `checkout_session_success()` function - 344 lines)
- `order/views.py` (updated `create_checkout_session()` to collect addresses)
- `order/urls.py` (added route)
- `order/migrations/0005_orderpayment_stripe_payment_intent_id.py` (new migration)
- `order/tests/test_checkout_session_success.py` (new test file, 7 tests)

**Key Features:**
- Idempotent order creation (prevents duplicates via unique constraint)
- Extracts shipping and billing addresses from Stripe session
- Handles both authenticated members and anonymous prospects
- Creates Prospect records automatically for guest checkouts
- Sends order confirmation emails with full order details
- Deletes cart after successful order creation

---

### Session 5: Backend - Stripe Webhook Handler (2-4 hours) ✅ COMPLETE
**Branch:** `feature/stripe-webhooks` (merged to master via PR #52)
**Date:** December 13, 2025

**Tasks Completed:**
- ✅ Create webhook endpoint: `/order/stripe-webhook` with `@csrf_exempt`
- ✅ Implement webhook signature verification using `stripe.Webhook.construct_event()`
- ✅ Handle `checkout.session.completed` event (creates orders if webhook arrives first)
- ✅ Handle `checkout.session.expired` event (logging only)
- ✅ Add proper logging for all webhook events
- ✅ Write comprehensive tests (6 tests, TDD approach, mocking webhook events)
- ✅ Add `STRIPE_WEBHOOK_SECRET` setting
- ✅ Add `cart_id` to checkout session metadata for webhook access
- ✅ Extract email helper function for code reuse
- ✅ Run all 735 unit tests (729 → 735, +6 new tests)
- ✅ Zero linting errors

**Deliverable:** ✅ Webhook handler providing production reliability

**Files Modified:**
- `StartupWebApp/order/views.py` - New `stripe_webhook()`, `handle_checkout_session_completed()`, `handle_checkout_session_expired()`, `send_order_confirmation_email()` functions (~350 lines)
- `StartupWebApp/order/views.py` - Updated `create_checkout_session()` to include `cart_id` in metadata
- `StartupWebApp/order/urls.py` - Added route for webhook endpoint
- `StartupWebApp/StartupWebApp/settings_secret.py` - Added `STRIPE_WEBHOOK_SECRET` setting
- `StartupWebApp/order/tests/test_stripe_webhook.py` - New test file (6 tests, 425 lines)

**Implementation Highlights:**
- **Security:** `@csrf_exempt` + signature verification (more secure than CSRF tokens)
- **Reliability:** Webhooks ensure orders created even if user closes browser
- **Idempotency:** Both success handler AND webhook check for existing orders
- **Code Reuse:** Extracted email helper function used by both handlers

**Note:** AWS infrastructure update (allow Stripe webhook IPs) deferred to Session 9 production deployment

---

### Session 6: Frontend - Update Checkout Flow (3-4 hours)
**Branch:** `feature/stripe-frontend-checkout`

**Tasks:**
- Remove old `checkout.js` script includes
- Add new Stripe.js v3 script
- Replace `StripeCheckout.configure()` with checkout session redirect
- Update "Place Order" button to create session and redirect
- Update success/cancel return URLs
- Test complete flow locally
- Run functional tests
- Commit and merge

**Deliverable:** Working frontend checkout with Stripe

**Files Modified:**
- `js/checkout/confirm-0.0.1.js`
- `checkout/confirm` (HTML)

---

### Session 6.5: Frontend CI/CD - Add PR Validation Workflow (1-2 hours)
**Branch:** `feature/frontend-pr-validation`

**Context:**
Frontend repository lacks PR validation workflow. Backend has comprehensive PR checks
(ESLint, tests, etc.) but frontend PRs merge without automated validation. This was
discovered during Session 6 review.

**Tasks:**
- Create `.github/workflows/pr-validation.yml` for frontend repository
- Run ESLint on all JavaScript files (should pass - 0 errors currently)
- Run QUnit tests in headless browser (Puppeteer or Playwright)
  - Test file: `unittests/checkout_confirm_tests.html` (13 tests)
  - Test file: `unittests/index_tests.html` (existing tests)
- Fail PR if linting errors or test failures
- Add workflow badge to README.md
- Test workflow with dummy PR
- Commit and merge

**Deliverable:** Automated PR validation for frontend repository

**Why This Matters:**
- Ensures code quality before merge
- Catches regressions automatically
- Matches backend workflow consistency
- Prevents broken code from reaching master

**Reference:** Backend PR validation: `.github/workflows/pr-validation.yml` (server repo)

---

### Session 7: Frontend - Update Account Payment Management (2-3 hours)
**Branch:** `feature/stripe-frontend-account`

**Tasks:**
- Update account page Stripe integration
- Replace old checkout handler
- Update saved payment method management
- Test account payment flows
- Run functional tests
- Commit and merge

**Deliverable:** Updated account payment management

**Files Modified:**
- `js/account-0.0.1.js`
- `account/index.html`

---

### Session 8: Testing & Bug Fixes (3-4 hours)
**Branch:** `feature/stripe-testing`

**Tasks:**
- ~~**Fix known backend bug**: Image URLs (FIXED IN SESSION 6)~~
- **Add functional tests for 3 critical flows tested manually in Session 6**:
  - **Test 1**: Logged-in member checkout flow (Selenium)
    - Login, add to cart, checkout, complete Stripe payment, verify order created
  - **Test 2**: Anonymous user checkout flow (Selenium)
    - Add to cart, anonymous checkout with email, Stripe payment, verify order
  - **Test 3**: Declined card error handling (Selenium)
    - Attempt checkout with test declined card `4000 0000 0000 0002`
    - Verify error shown, no order created, user can retry
- Add missing unit tests for Session 6 bugfixes:
  - Backend: Shipping line item in checkout session
  - Backend: Prospect creation includes `created_date_time`
  - Backend: `collected_information.shipping_details` handling
  - Frontend: Decimal parsing helper or tests
- Test saved payment methods (if applicable)
- Test order confirmation emails in all scenarios
- Test other error scenarios (network errors, timeouts, etc.)
- **Remove dead code from frontend** (Session 6 marked as unused):
  - `display_payment_data()` - ~45 lines
  - `process_stripe_payment_token()` - ~45 lines
  - `process_stripe_payment_token_callback()` - ~25 lines
  - `confirm_place_order()` - ~120 lines
  - `confirm_place_order_callback()` - ~50 lines
  - Total: ~285 lines to remove from js/checkout/confirm-0.0.1.js
- Fix any other bugs discovered
- Run all 737+ backend tests
- Run all 13+ frontend QUnit tests
- Commit and merge

**Deliverable:** Fully tested Stripe integration with comprehensive test coverage

**Critical**: Session 6 manual testing revealed 9 bugs that were fixed. Session 8
must add automated tests to prevent regressions.

---

### Session 9: Production Deployment (2-3 hours)
**Branch:** `feature/stripe-production-config`

**Tasks:**
- Configure production Stripe keys in AWS Secrets Manager
- Set up Stripe webhook endpoint in production
- Configure webhook secret in Secrets Manager
- Test in production environment
- Monitor CloudWatch logs
- Test all email types in production (including order emails)
- Document production configuration

**Webhook Configuration Steps:**

1. **Add webhook secret to AWS Secrets Manager**:
   - Secret name: `rds/startupwebapp/multi-tenant/master`
   - Add new key: `stripe_webhook_secret`
   - Get value from Stripe Dashboard after step 2

2. **Configure webhook in Stripe Dashboard**:
   - Go to: https://dashboard.stripe.com/webhooks
   - Click "Add endpoint"
   - URL: `https://startupwebapp-api.mosaicmeshai.com/order/stripe-webhook`
   - Events to send: `checkout.session.completed`, `checkout.session.expired`
   - Copy the webhook signing secret (starts with `whsec_`)

3. **Update AWS Secrets Manager**:
   - Add the webhook signing secret as `stripe_webhook_secret` key
   - Production code reads from: `settings_production.py:165`

4. **Verify webhook**:
   - Stripe Dashboard shows webhook as "Enabled"
   - Test by triggering a checkout session
   - Check CloudWatch logs for webhook events
   - Verify idempotency (webhook + success handler both create same order)

**Security Notes:**
- Webhook endpoint uses `@csrf_exempt` (required for webhooks)
- Security provided by signature verification (more secure than CSRF)
- Webhook secret must match between Stripe and AWS Secrets Manager
- Production code automatically retrieves secret from Secrets Manager

**Deliverable:** Stripe working in production with webhook backup for order creation

---

### Session 10: Email Updates from Session 1 (2-3 hours)
**Branch:** `feature/email-address-updates`

**Context:**
Session 1 included email address updates that were never merged. After Stripe is fully working in production (Session 9), we can finally test ALL 9 email types including order confirmation emails.

**Tasks:**
- Apply email address changes from Session 1:
  - Update: `contact@startupwebapp.com` → `bart+startupwebapp@mosaicmeshai.com`
  - Remove: BCC from all emails
  - Update: Phone to 1-800-123-4567
  - Update: Signatures to "StartUpWebApp"
  - Files: 7 user emails + 2 order emails + 1 chat email
- Create database migration to update email templates
- Test ALL 9 email types in local environment
- Test ALL 9 email types in production
- Run all backend tests (should be 735+ passing)
- Update documentation
- Commit and merge

**Why After Session 9:**
- Stripe must be working to test order confirmation emails
- This was the original blocker that started the Stripe upgrade
- Production testing ensures emails work end-to-end

**Deliverable:** All email addresses updated and fully tested

**Reference:** Session 1 branch `feature/email-updates-and-stripe-planning` (will be closed)

---

### Session 11: Final Documentation & Cleanup (1-2 hours)
**Branch:** `feature/stripe-final-docs`

**Tasks:**
- Create comprehensive technical note for entire Stripe upgrade
- Update README.md with new Stripe setup
- Update SESSION_START_PROMPT.md
- Update PROJECT_HISTORY.md
- Clean up old Stripe code (if any remains)
- Archive this planning document
- Close Session 1 branch
- Commit and merge

**Deliverable:** Complete documentation

---

## Effort Estimate

**Total Sessions:** 12 sessions (includes Session 6.5 for frontend PR validation)
**Total Time:** 23-35 hours
**Timeline:** 2-3 weeks (at ~2 sessions per day)

**Per Session:**
- Average: 2-3 hours
- Max: 4 hours
- Includes: coding, testing, documentation, commits

---

## Risk Assessment

**High Risk Areas:**
1. **Payment Processing Logic** - Critical business function
2. **Order Creation** - Must not create duplicate orders
3. **Email Notifications** - Must send order confirmations
4. **Webhook Security** - Must verify signatures
5. **Production Deployment** - Must not break existing orders

**Mitigation Strategies:**
1. **TDD Approach** - Write tests first for all changes
2. **Small Commits** - One session = one PR
3. **Thorough Testing** - Test each session's changes independently
4. **Rollback Plan** - Each PR is independently revertible
5. **Monitoring** - CloudWatch logging for production

---

## Prerequisites

**Before Starting Session 2:**
- [ ] Stripe account confirmed active
- [ ] Test mode keys verified working in Stripe dashboard
- [ ] Production keys available (for later sessions)
- [ ] Review Stripe Checkout Sessions documentation
- [ ] Review Stripe Webhooks documentation

---

## Success Criteria

**Checkout Sessions Implementation:**
- [ ] Stripe library upgraded to 10.x+
- [ ] Checkout session creation working
- [ ] Payment processing functional
- [ ] Order confirmation emails sending
- [ ] Webhooks configured and tested
- [ ] All 746 tests passing
- [ ] Zero linting errors
- [ ] Production deployment successful
- [ ] All 9 email types tested in production

---

## Current Session Status

**Session:** Session 6 In Progress - Frontend Checkout Flow
**Date:** December 14, 2025

**Session 1 (Complete - SUPERSEDED, NOT TO BE MERGED):**
- ✅ Email address changes in code (7 email types updated)
- ✅ BCC removed from all emails
- ✅ Phone number updated to 1-800-123-4567
- ✅ Email signatures updated to "StartUpWebApp"
- ✅ Frontend checkout decimal bugs fixed
- ✅ Migration created to update database email templates
- ✅ 7/9 email types tested locally (order emails blocked by Stripe)
- ✅ Stripe upgrade assessment and planning complete
- ✅ Branch: `feature/email-updates-and-stripe-planning` (backend + frontend, NOT merged)
- ⚠️ **IMPORTANT**: Decimal parsing fixes from this branch were re-applied in Session 6
- ⚠️ **ACTION**: Close this branch - email updates can be done in separate PR later

**Session 2 (Complete - Merged to Master):**
- ✅ Stripe library upgraded: `5.5.0` → `14.0.1` (PR #49)
- ✅ Docker configuration fixed: Added `target: development` to docker-compose.yml
- ✅ All 715 unit tests passing
- ✅ All 30 functional tests passing (1 unrelated failure from Session 1 changes)
- ✅ Zero code changes needed (fully compatible)
- ✅ Deployed to production successfully
- ✅ PROJECT_HISTORY.md updated

**Session 3 (Complete - Merged to Master):**
- ✅ New endpoint: `/order/create-checkout-session` (PR #50)
- ✅ Implemented `stripe.checkout.Session.create()`
- ✅ 7 new unit tests, all 722 tests passing
- ✅ Merged to master and deployed

**Session 4 (Complete - Merged to Master):**
- ✅ New endpoint: `/order/checkout-session-success` (PR #51)
- ✅ Database migration: Added `stripe_payment_intent_id` field
- ✅ Updated checkout session creation to collect addresses
- ✅ Implemented complete order creation flow
- ✅ 7 new unit tests (TDD approach), all 729 tests passing
- ✅ Idempotent design prevents duplicate orders
- ✅ Merged to master and deployed

**Session 5 (Complete - Merged to Master):**
- ✅ New endpoint: `/order/stripe-webhook` with signature verification (PR #52)
- ✅ Handles `checkout.session.completed` event (creates orders via webhook)
- ✅ Handles `checkout.session.expired` event (logging only)
- ✅ Added `cart_id` to checkout session metadata
- ✅ Extracted `send_order_confirmation_email()` helper function
- ✅ 6 new unit tests (TDD approach), all 735 tests passing
- ✅ Zero linting errors
- ✅ Idempotent with success handler (prevents duplicate orders)
- ✅ Merged to master and deployed to production

**Session 6 (In Progress - Frontend Checkout):**
- ✅ Branch: `feature/stripe-frontend-checkout` (Client PR #12)
- ✅ Replaced `checkout.stripe.com/checkout.js` with `js.stripe.com/v3/`
- ✅ Added `create_stripe_checkout_session()` function
- ✅ Added `handle_checkout_session_success()` function
- ✅ Updated checkout flow to redirect to Stripe
- ✅ 10 new QUnit unit tests (TDD approach), all passing
- ✅ ESLint: 0 errors, 2 warnings
- ✅ **Decimal parsing bugfixes included** (parseFloat on price/shipping fields)
- ⚠️ **NOTE**: These decimal fixes duplicate Session 1 work (Session 1 branch will NOT be merged)
- ⚠️ **KNOWN ISSUE**: Backend sends relative image URLs to Stripe (e.g., `/img/product/...`)
  - Stripe requires absolute URLs (e.g., `https://domain.com/img/...`)
  - Error: "url_invalid" on `line_items[0][price_data][product_data][images][0]`
  - **Fix in Session 8**: Add domain prefix to image URLs in backend
  - **Impact**: Checkout works but no product images shown on Stripe checkout page
  - **Workaround**: None needed - no real users yet
- 🔄 Currently: Manual testing in progress

---

## Notes

**Why This Matters:**
- Stripe Checkout v2 is being shut down
- Without this upgrade, payment processing will stop working
- Order confirmation emails depend on functional checkout
- This blocks completion of email testing

**Session 1 Branch Superseded (December 14, 2025):**
- **Issue**: Session 1 branch `feature/email-updates-and-stripe-planning` included decimal parsing bugfixes
- **Problem**: Session 6 needed same fixes to test checkout flow
- **Decision**: Re-applied decimal fixes in Session 6 to avoid blocking testing
- **Impact**: Session 1 branch should NOT be merged (would create conflicts/duplicates)
- **Action Required**:
  - Close Session 1 branch after Session 6 merges
  - Email updates from Session 1 can be redone in new PR later if needed
- **Affected Files** (frontend): `js/checkout/confirm-0.0.1.js` (7 parseFloat fixes)
- **Lesson**: Merge bugfixes quickly to avoid duplication across branches

**Integration with Other Work:**
- Email address changes from Session 1 can be done in separate PR later
- Stripe upgrade is separate concern from email updates
- After Stripe works, complete email testing

---

## Session 3 Starting Prompt

**Use this prompt to start Session 3 in a new Claude Code session:**

```
Read docs/SESSION_START_PROMPT.md for project context.

Session Goal: Phase 5.16 Stripe Upgrade - Session 3: Create Checkout Session Endpoint

Context:
- Session 1 (December 11, 2025): Planning complete, email updates in feature branch
- Session 2 (December 11, 2025): Library upgraded to 14.0.1, merged to master, deployed to production

Current Task: Start Stripe upgrade Session 3

Session 3 Goal: Create backend endpoint to generate Stripe Checkout Sessions

Tasks for this session:
1. Review docs/technical-notes/2025-12-11-stripe-upgrade-plan.md (Session 3 section)
2. Create new branch: feature/stripe-checkout-session-endpoint (from master)
3. Read Stripe Checkout Sessions documentation
4. Create new endpoint: /order/create-checkout-session
5. Implement stripe.checkout.Session.create() with:
   - Line items from cart
   - Success/cancel URLs
   - Customer email
   - Member vs prospect handling
6. Write unit tests (TDD approach)
7. Run all 715 unit tests and fix any failures
8. Commit and push changes
9. Create PR for review

Important: Follow TDD methodology - write tests first!
```

---

## References

- Stripe Checkout Sessions: https://stripe.com/docs/payments/checkout
- Stripe Webhooks: https://stripe.com/docs/webhooks
- Migration Guide: https://stripe.com/docs/payments/checkout/migration
- Python Library: https://stripe.com/docs/api/python
