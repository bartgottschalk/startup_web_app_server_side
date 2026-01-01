# Session 9: Stripe Webhook Production Configuration

**Date**: December 19, 2025
**Branch**: `feature/stripe-webhook-production`
**Status**: Complete
**Session Duration**: ~3 hours (including troubleshooting)

## Executive Summary

Successfully configured and deployed Stripe webhook infrastructure in production. The webhook endpoint now receives checkout completion events from Stripe, providing backup order creation for reliability.

**Impact:**
- ✅ Stripe webhook configured in TEST mode dashboard
- ✅ Webhook signing secret added to AWS Secrets Manager
- ✅ Production Docker image fixed (added curl for health checks)
- ✅ Webhook delivery tested and verified working in production
- ✅ Order creation idempotency confirmed (webhook + success handler)
- ✅ **Bonus**: Fixed checkout login race condition (Frontend PR #16)
- ✅ **Bonus**: Removed deprecated "save payment info" checkbox (Frontend PR #16)

## What Was Completed

### 1. Stripe Webhook Configuration

**Stripe Dashboard (TEST mode):**
- **URL**: `https://startupwebapp-api.mosaicmeshai.com/order/stripe-webhook`
- **Destination ID**: `we_1Sg7IY1L9oz9ETFuPSIFcsem`
- **Events**:
  - `checkout.session.completed`
  - `checkout.session.expired`
- **API Version**: 2025-11-17.clover
- **Payload Style**: Snapshot

**Why TEST mode?**
StartUpWebApp is a demo/template project that ALWAYS uses Stripe TEST mode keys, even in production. Real Stripe transactions will only occur in forks of this project.

### 2. AWS Secrets Manager Configuration

**Secret**: `rds/startupwebapp/multi-tenant/master`

**Added Key**:
```json
{
  "stripe_webhook_secret": "whsec_..."
}
```

**Code Integration**:
- `settings_production.py:166`: Reads `stripe_webhook_secret` from secrets
- `order/views.py:1378`: Uses secret for webhook signature verification
- Webhook handler validates all requests using `stripe.Webhook.construct_event()`

### 3. Docker Health Check Fix (Critical Bug)

**Problem Discovered:**
- ECS task definition health check: `curl -f http://localhost:8000/order/products`
- Production Docker image: **curl not installed**
- Result: Tasks failed health checks repeatedly, deployment stuck for 20+ minutes

**Root Cause:**
- Dockerfile had Python-based HEALTHCHECK (line 89)
- ECS task definition had curl-based health check (from Phase 5.15)
- Mismatch caused continuous deployment failures

**Solution (Dockerfile:75-78):**
```dockerfile
# Install curl for ECS health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

**Files Modified:**
- `Dockerfile` - Added curl to production stage (5 lines)

## Deployment Timeline

### Initial Deployment Attempt (Failed)

**11:20 AM CST**: ECS service force restart (to load webhook secret)
- New deployment started: `ecs-svc/4607990484302914693`
- Task definition: `startupwebapp-service-task:22`

**11:26-11:35 AM**: Tasks failing health checks
- Tasks started, then stopped after ~13 minutes
- Error: "Task failed container health checks"
- Application working (logs show 200 OK responses)
- Health check failing (curl not found in container)

**CloudWatch Logs Analysis:**
- ✅ Application healthy: `/order/products` returning 200
- ✅ User requests working: `/user/logged-in` successful
- ❌ Health check command failing (curl missing)

### Fix and Redeploy

**11:40 AM**: Identified curl missing in production image
**11:45 AM**: Fixed Dockerfile, committed, pushed to PR #55
**12:00 PM**: PR #55 validation passed (724 tests)
**12:05 PM**: Merged to master, auto-deploy triggered
**12:15 PM**: Deployment completed successfully

## Testing and Verification

### Production Test Checkout

**12:11 PM CST**: Completed test checkout
- **URL**: `https://startupwebapp.mosaicmeshai.com`
- **User**: bart+tester4@mosaicmeshai.com (logged in)
- **Card**: 4242 4242 4242 4242 (Stripe test card)
- **Order ID**: `qWUrhAgvtU`

### Webhook Delivery Confirmed

**CloudWatch Logs (12:11:53 PM):**
```
Order created successfully via webhook: qWUrhAgvtU
10.0.2.185 - - [19/Dec/2025:12:11:53 -0600] "POST /order/stripe-webhook HTTP/1.1" 200 52 "-" "Stripe/1.0 (+https://stripe.com/docs/webhooks)"
```

**Stripe Dashboard:**
- **Event**: `checkout.session.completed`
- **Event ID**: `evt_1Sg89c1L9oz9ETFunheMNiun`
- **Status**: Delivered (200 OK)
- **Response**: `{"received": true, "order_identifier": "qWUrhAgvtU"}`
- **Origin**: Dec 19, 2025, 12:11:53 PM CST
- **Signature**: Verified successfully

**Webhook Payload Highlights:**
```json
{
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_test_b1Wj8X7NXy10z4JwjhRys6n0R8iPFCb1OP3ceflTliskHslSJuTARs3BQS",
      "status": "complete",
      "payment_status": "paid",
      "payment_intent": "pi_3Sg89Y1L9oz9ETFu0c9gdwqR",
      "customer_email": "bart+tester4@mosaicmeshai.com",
      "metadata": {
        "cart_id": "5"
      },
      "collected_information": {
        "shipping_details": {
          "address": {
            "line1": "5605 Humboldt Avenue South",
            "city": "Minneapolis",
            "state": "MN",
            "postal_code": "55419",
            "country": "US"
          },
          "name": "Bart Tester4"
        }
      }
    }
  }
}
```

### Idempotency Verification

**Two paths to order creation:**
1. **Success handler** (`/order/checkout-session-success`): User redirected after payment
2. **Webhook handler** (`/order/stripe-webhook`): Stripe sends event

**Idempotency mechanism:**
- Both handlers check for existing order by `stripe_payment_intent_id`
- Database unique constraint on `Orderpayment.stripe_payment_intent_id`
- Only one order created, regardless of which handler runs first

**Test result:**
- ✅ Order `qWUrhAgvtU` created successfully
- ✅ No duplicate orders
- ✅ Webhook and success handler both handled same session

## Technical Implementation

### Webhook Handler Flow (order/views.py:1367-1408)

1. **Receive POST** from Stripe
2. **Verify signature** using `stripe_webhook_secret`
3. **Parse event type**
4. **Handle checkout.session.completed**:
   - Retrieve full session from Stripe API
   - Extract cart_id from metadata
   - Check for existing order (idempotency)
   - Create order with all details
   - Send confirmation email
   - Return 200 OK
5. **Handle checkout.session.expired**:
   - Log expiration
   - Return 200 OK

### Security

**Signature Verification:**
```python
webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
event = stripe.Webhook.construct_event(
    payload, sig_header, webhook_secret
)
```

**Why this is secure:**
- `@csrf_exempt` required for webhooks (Stripe can't send CSRF tokens)
- Signature verification more secure than CSRF tokens
- Only Stripe can generate valid signatures
- Webhook secret stored in AWS Secrets Manager
- Secret rotatable without code changes

### Reliability Benefits

**Before Webhooks:**
- User must complete redirect to success page
- If user closes browser → order lost
- If redirect fails → order lost

**After Webhooks:**
- Stripe sends webhook regardless of user action
- Order created even if browser closed
- Backup mechanism for reliability
- Production-grade payment processing

## Challenges and Resolutions

### Challenge 1: Deployment Stuck for 20+ Minutes

**Symptom:**
- ECS deployment "IN_PROGRESS" for 20+ minutes
- Tasks continuously starting, failing health checks, stopping
- `runningCount: 2`, `failedTasks: 2`, `desiredCount: 1`

**Root Cause:**
- ECS task definition health check uses curl
- Production Docker image doesn't have curl
- Health check command fails → task marked unhealthy → stopped

**Investigation:**
```bash
# Checked service events
aws ecs describe-services --query 'services[0].events[:10]'
# Result: "Task failed container health checks"

# Checked CloudWatch logs
aws logs tail /ecs/startupwebapp-service --since 20m
# Result: Application working, health checks timing out
```

**Resolution:**
- Added curl to production Dockerfile (5 lines)
- Redeployed via PR #55
- Deployment completed successfully in ~10 minutes

### Challenge 2: Frontend Login Detection (Minor)

**Symptom:**
- User logged in on backend (verified with API call)
- Frontend checkout page showing login/anonymous buttons
- "Place Order" button grayed out

**Cause:**
- CloudFront cache invalidation not yet complete
- Old frontend JavaScript served to browser

**Resolution:**
- Waited for CloudFront cache to refresh (~5 minutes)
- Frontend updated automatically
- Issue resolved without code changes

**Note:** Not related to Session 9 changes, just coincidental timing with deployment.

### Challenge 3: Checkout Login Race Condition (Critical - Frontend PR #16)

**Symptom:**
- Logged-in users saw Login/Create Account/Checkout Anonymous buttons on checkout page
- Place Order button was grayed out (disabled)
- Required clicking "Login" again even though already authenticated
- Intermittent - sometimes worked, sometimes didn't

**Root Cause:**
- Session 8 removed `/order/confirm-payment-data` endpoint (provided synchronous login status)
- Hotfix (commit 54787f7) assumed `index.js` would set `$.user_logged_in` before checkout JavaScript ran
- **Race condition**: Checkout's `load_confirm_totals` checked `$.user_logged_in` before `/user/logged-in` API call completed
- Fast network: index.js usually won (bug hidden in development)
- Slow network: checkout won (bug appeared in production)

**Discovery Process:**
1. Noticed issue in production during webhook testing
2. Initially thought it was CloudFront cache (was partially correct earlier)
3. Issue persisted after cache cleared - identified as actual bug
4. Reviewed Session 8 hotfix commit - found race condition assumption

**Investigation:**
```javascript
// index.js - Sets $.user_logged_in asynchronously
$.ajax('/user/logged-in', success: set_logged_in)  // ~200-500ms

// checkout/confirm.js - Checks immediately
load_confirm_totals = function(data) {
    if ($.user_logged_in) {  // ← RACE: Might still be false!
        // Show Place Order button
    }
}
```

**Solution (Promise Pattern):**
1. **index.js**: Expose `$.loginStatusReady` promise (AJAX return value)
2. **checkout/confirm.js**: Wait for promise with `.then()` before checking login status

```javascript
// index.js
$.loginStatusReady = $.ajax('/user/logged-in', success: set_logged_in)

// checkout/confirm.js
$.loginStatusReady.then(function() {
    if ($.user_logged_in) {
        // NOW it's safe to check - promise resolved
    }
});
```

**Additional Cleanup:**
- Removed deprecated "Save shipping and payment information" checkbox (3 lines HTML)
- Checkbox was misleading - Stripe Checkout Sessions don't save payment info
- Aligns with Session 7 decision (removed payment info from account page)

**Testing:**
- Added 3-second sleep to backend `/user/logged-in` endpoint for testing
- Verified promise flow with debug console logging
- Tested anonymous user: Shows login/anonymous buttons after 3-second delay
- Tested logged-in user: Shows Place Order button after 3-second delay
- Removed sleep and debug logging before production deployment

**Files Modified (Frontend PR #16):**
- `js/index-0.0.2.js` - Expose `$.loginStatusReady` promise (3 lines changed)
- `js/checkout/confirm-0.0.1.js` - Wait for promise before showing UI (18 lines changed)
- `checkout/confirm` - Remove deprecated checkbox HTML (3 lines removed)

**Production Verification:**
- ✅ Logged-in users see Place Order button immediately (~100ms flash of buttons)
- ✅ Anonymous users see login/anonymous buttons
- ✅ No deprecated "save payment info" checkbox visible
- ✅ All 88 frontend tests passing
- ✅ ESLint: 0 errors, 3 warnings (unchanged)

**Impact:**
- Fixes critical UX bug preventing logged-in checkout
- Clean architecture: Single source of truth for login status
- Pattern reusable for future pages that need login status
- No impact on other pages (cart, products, orders all work unchanged)

## Production Architecture

### Webhook Flow

```
Stripe → ALB → ECS Task → Django → Database
         ↓
    Signature Verification (AWS Secrets Manager)
         ↓
    Order Creation (if not exists)
         ↓
    Email Notification
         ↓
    HTTP 200 Response
```

### Success Handler Flow

```
User → Stripe Checkout → Success Redirect → Frontend
                                              ↓
                                         Backend API
                                              ↓
                                    Order Creation (if not exists)
                                              ↓
                                        Email Notification
```

### Idempotency Design

Both flows check:
1. Does order with this `stripe_payment_intent_id` exist?
2. If yes → return existing order
3. If no → create order, send email
4. Database constraint prevents race conditions

## Files Modified

**Backend:**
- `Dockerfile` - Added curl to production stage (lines 75-78)

**Configuration (Manual):**
- Stripe Dashboard: Created webhook destination
- AWS Secrets Manager: Added `stripe_webhook_secret` key

**No Code Changes Required:**
- Webhook handler implemented in Session 5 (PR #52)
- Settings already configured to read secret
- Only configuration needed for Session 9

## Test Results

**Production Test:**
- ✅ Webhook endpoint receives events from Stripe
- ✅ Signature verification working (secret from Secrets Manager)
- ✅ Order created via webhook: `qWUrhAgvtU`
- ✅ Confirmation email sent successfully
- ✅ Idempotency working (no duplicate orders)
- ✅ Stripe Dashboard shows 200 OK responses
- ✅ CloudWatch logs show successful webhook processing

**All 724 Tests Passing:**
- 692 unit tests (includes 6 webhook tests from Session 5)
- 32 functional tests
- Zero linting errors

## Monitoring

### CloudWatch Logs

**Successful webhook:**
```
Order created successfully via webhook: qWUrhAgvtU
POST /order/stripe-webhook HTTP/1.1" 200 52 "Stripe/1.0"
```

**Failed signature verification (if secret wrong):**
```
ERROR Invalid webhook signature: ...
POST /order/stripe-webhook HTTP/1.1" 400 "invalid-signature"
```

**Missing secret (if not configured):**
```
ERROR STRIPE_WEBHOOK_SECRET not configured
POST /order/stripe-webhook HTTP/1.1" 500 "webhook-not-configured"
```

### Stripe Dashboard

**View webhook events:**
1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click: "StartUpWebApp Production Checkout Webhooks"
3. See: Recent events with delivery status

**Test webhook manually:**
1. Click "Send test events" button
2. Select event type: `checkout.session.completed`
3. Verify: Backend receives and processes correctly

## Next Steps

### Session 10: Email Updates (Future)

**Goal:** Update email addresses throughout the application

**Tasks:**
- Update: `contact@startupwebapp.com` → `bart+startupwebapp@mosaicmeshai.com`
- Remove: BCC from all emails
- Update: Phone numbers and signatures
- Test: All 9 email types in production (including order emails!)

**Why after Session 9:**
- Stripe must be working to test order confirmation emails
- This was the original blocker that started the Stripe upgrade
- Can now test complete email flow end-to-end

### Session 11: Final Documentation (Future)

**Goal:** Comprehensive documentation for entire Stripe upgrade

**Tasks:**
- Create master technical note for Sessions 1-10
- Update README with new Stripe setup instructions
- Archive upgrade planning document
- Close Session 1 branch
- Mark Phase 5.16 complete

## References

- **Session 5 Technical Notes**: Webhook handler implementation
- **Stripe Upgrade Plan**: `docs/technical-notes/2025-12-11-stripe-upgrade-plan.md`
- **Stripe Webhooks Docs**: https://stripe.com/docs/webhooks
- **AWS Secrets Manager**: Console → `rds/startupwebapp/multi-tenant/master`
- **Stripe Dashboard**: https://dashboard.stripe.com/test/webhooks

## Key Learnings

1. **Health Check Consistency**: Ensure Docker HEALTHCHECK matches ECS task definition health check
2. **Curl in Production**: Production images need curl if ECS health checks use it
3. **Webhook Testing**: Always test in production to verify signature verification works
4. **CloudFront Caching**: Account for cache invalidation time when testing frontend changes
5. **Idempotency**: Critical for payment systems - both webhook and success handler must handle duplicates

---

**Session completed**: December 19, 2025
**PR**: #55 (merged)
**Status**: Stripe webhooks fully operational in production
