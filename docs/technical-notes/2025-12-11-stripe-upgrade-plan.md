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

### Session 2: Stripe Library Upgrade (2-3 hours)
**Branch:** `feature/stripe-upgrade-library`

**Tasks:**
- Upgrade `requirements.txt`: `stripe==5.5.0` → `stripe==10.x`
- Update Docker image with new library
- Review breaking changes in stripe library
- Update any deprecated API calls in existing code
- Run all 715 unit tests (ensure mocks still work)
- Fix any test failures
- Commit and merge

**Deliverable:** Updated stripe library with passing tests

**Risk:** Medium - API changes may break existing code

---

### Session 3: Backend - Create Checkout Session Endpoint (2-3 hours)
**Branch:** `feature/stripe-checkout-session-endpoint`

**Tasks:**
- Create new endpoint: `/order/create-checkout-session`
- Implement `stripe.checkout.Session.create()`
- Calculate order total and line items
- Handle member vs prospect flows
- Add proper error handling
- Write unit tests for new endpoint
- Run all tests (715 + new tests)
- Commit and merge

**Deliverable:** Working checkout session creation endpoint

**Files Modified:**
- `order/views.py` (new function)
- `order/tests/` (new test file)

---

### Session 4: Backend - Checkout Session Success Handler (2-3 hours)
**Branch:** `feature/stripe-checkout-success`

**Tasks:**
- Create success endpoint: `/order/checkout-session-success`
- Retrieve session data from Stripe
- Create order in database
- Send order confirmation email
- Write unit tests
- Run all tests
- Commit and merge

**Deliverable:** Order creation after successful payment

**Files Modified:**
- `order/views.py` (new function)
- `order/tests/` (new tests)

---

### Session 5: Backend - Stripe Webhook Handler (2-4 hours)
**Branch:** `feature/stripe-webhooks`

**Tasks:**
- Create webhook endpoint: `/order/stripe-webhook`
- Implement webhook signature verification
- Handle `checkout.session.completed` event
- Handle `checkout.session.expired` event
- Add proper logging
- Write tests (mocking webhook events)
- Update AWS infrastructure (allow Stripe webhook IPs)
- Commit and merge

**Deliverable:** Webhook handler for payment confirmations

**Files Modified:**
- `order/views.py` (new webhook endpoint)
- `order/tests/` (webhook tests)

**Critical:** Required for production reliability

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
- Test complete checkout flow (member)
- Test complete checkout flow (prospect/guest)
- Test saved payment methods
- Test order confirmation emails (finally!)
- Test error scenarios
- Fix any bugs discovered
- Update functional tests if needed
- Run all 746 tests
- Commit and merge

**Deliverable:** Fully tested Stripe integration

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

**Deliverable:** Stripe working in production

---

### Session 10: Documentation & Cleanup (1-2 hours)
**Branch:** `feature/stripe-docs`

**Tasks:**
- Create comprehensive technical note
- Update README.md with new Stripe setup
- Update SESSION_START_PROMPT.md
- Update PROJECT_HISTORY.md
- Clean up old Stripe code (if any remains)
- Archive this planning document
- Commit and merge

**Deliverable:** Complete documentation

---

## Effort Estimate

**Total Sessions:** 10 sessions
**Total Time:** 20-30 hours
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

**Session:** Planning & Email Address Changes (Session 0)
**Date:** December 11, 2025

**Completed:**
- ✅ Email address changes in code (7 email types updated)
- ✅ BCC removed from all emails
- ✅ Phone number updated to 1-800-123-4567
- ✅ Email signatures updated to "StartUpWebApp"
- ✅ Frontend checkout decimal bugs fixed
- ✅ Migration created to update database email templates
- ✅ 7/9 email types tested locally (order emails blocked by Stripe)
- ✅ Stripe upgrade assessment complete

**In Progress:**
- Creating comprehensive Stripe upgrade documentation

**Next Steps:**
1. Commit email address changes (WIP state)
2. Update SESSION_START_PROMPT.md with Stripe upgrade priority
3. Update PROJECT_HISTORY.md
4. Start Session 1 (Stripe planning) in next Claude Code session

---

## Notes

**Why This Matters:**
- Stripe Checkout v2 is being shut down
- Without this upgrade, payment processing will stop working
- Order confirmation emails depend on functional checkout
- This blocks completion of email testing

**Integration with Other Work:**
- Email address changes are ready (just need order email testing)
- Can deploy email changes independently
- Stripe upgrade is separate concern
- After Stripe works, complete email testing

---

## References

- Stripe Checkout Sessions: https://stripe.com/docs/payments/checkout
- Stripe Webhooks: https://stripe.com/docs/webhooks
- Migration Guide: https://stripe.com/docs/payments/checkout/migration
- Python Library: https://stripe.com/docs/api/python
