# Stripe Promotion Codes Implementation Guide

**Created:** Session 81 (Jan 22, 2026)
**Status:** Ready to Implement (When Needed)
**Prerequisites:** Phase 1 Complete (Discount code functionality removed, `allow_promotion_codes: true` enabled)

---

## Executive Summary

This guide describes how to implement discount codes using Stripe's native promotion code functionality. This is **Phase 2** of the discount code migration, following the removal of custom Django discount logic in Phase 1.

**Key Benefits:**
- ✅ Zero backend code changes required
- ✅ Zero frontend code changes required
- ✅ Stripe handles all validation and calculations
- ✅ Built-in analytics in Stripe Dashboard
- ✅ Professional, tested UX

**Timeline:** ~1-1.5 hours to create and test codes

---

## How It Works

### User Experience Flow

1. **Customer browses and adds items to cart** on your site
2. **Customer clicks "Checkout"** → Backend creates Stripe Checkout Session with `allow_promotion_codes: true`
3. **Stripe Checkout page loads** with "Add promotion code" link
4. **Customer clicks link and enters code** (e.g., "SAVE20")
5. **Stripe validates and applies discount** in real-time
6. **Customer sees updated total** with discount applied
7. **Customer completes payment**
8. **Webhook receives discount data** in `checkout.session.completed` event

### Where Codes Are Entered

Customers enter codes on **Stripe's hosted checkout page**, not on your cart page. This is intentional:
- Stripe's checkout is PCI-compliant and optimized for conversions
- Stripe handles all edge cases (expired codes, minimum amounts, usage limits)
- No custom JavaScript or API endpoints needed on your site

---

## Implementation Steps

### Step 1: Create Stripe Coupons

Coupons define the discount amount and rules. Create them via Stripe Dashboard or API.

#### Option A: Stripe Dashboard (Easiest)

1. Log into Stripe Dashboard
2. Go to **Products** → **Coupons**
3. Click **Create coupon**
4. Configure:
   - **Name:** Internal name (e.g., "20% Off Spring Sale")
   - **Type:** Percentage or Amount off
   - **Discount:** Enter value (e.g., 20% or $10.00)
   - **Duration:** Once, Forever, or Repeating
5. Click **Create coupon**
6. Copy the **Coupon ID** (e.g., `promo_20_off`)

#### Option B: Stripe API

**Example: 20% off coupon**
```bash
curl https://api.stripe.com/v1/coupons \
  -u sk_test_YOUR_API_KEY: \
  -d percent_off=20 \
  -d duration=once \
  -d name="20% Off Spring Sale"
```

**Example: $10 off coupon**
```bash
curl https://api.stripe.com/v1/coupons \
  -u sk_test_YOUR_API_KEY: \
  -d amount_off=1000 \
  -d currency=usd \
  -d duration=once \
  -d name="$10 Off"
```

**Response:**
```json
{
  "id": "promo_20_off",
  "object": "coupon",
  "percent_off": 20,
  "duration": "once",
  "valid": true
}
```

### Step 2: Create Promotion Codes

Promotion codes are customer-facing codes linked to coupons. They support restrictions like minimum order amounts and expiration dates.

#### Option A: Stripe Dashboard (Easiest)

1. Go to **Products** → **Promotion codes**
2. Click **Create promotion code**
3. Configure:
   - **Code:** Customer-facing code (e.g., "SAVE20")
   - **Coupon:** Select coupon created in Step 1
   - **Restrictions:**
     - Minimum amount: $20.00 (optional)
     - First-time customers only: Toggle (optional)
     - Expiration date: Set date (optional)
     - Max redemptions: Set limit (optional)
4. Click **Create promotion code**

#### Option B: Stripe API

**Example: Create promotion code with $20 minimum**
```bash
curl https://api.stripe.com/v1/promotion_codes \
  -u sk_test_YOUR_API_KEY: \
  -d coupon=promo_20_off \
  -d code=SAVE20 \
  -d restrictions[minimum_amount]=2000 \
  -d restrictions[minimum_amount_currency]=usd
```

**Example: Create code that expires on a specific date**
```bash
curl https://api.stripe.com/v1/promotion_codes \
  -u sk_test_YOUR_API_KEY: \
  -d coupon=promo_20_off \
  -d code=SAVE20 \
  -d expires_at=1735689600
```

**Response:**
```json
{
  "id": "promo_1234567890",
  "object": "promotion_code",
  "code": "SAVE20",
  "coupon": {
    "id": "promo_20_off",
    "percent_off": 20
  },
  "restrictions": {
    "minimum_amount": 2000,
    "minimum_amount_currency": "usd"
  },
  "active": true
}
```

### Step 3: Verify Backend Configuration

**Already done in Phase 1!** Your Stripe Checkout Session creation includes:

```python
# order/views.py::create_checkout_session()
session = stripe.checkout.Session.create(
    line_items=[...],
    mode='payment',
    allow_promotion_codes=True,  # ← This enables promotion codes
    success_url='...',
    cancel_url='...',
)
```

No changes needed!

### Step 4: Testing in Test Mode

1. **Create test coupon and promotion code** in Stripe test mode (see Steps 1-2)

2. **Test checkout flow:**
   - Add items to cart on your site
   - Click "Checkout"
   - On Stripe checkout page, click "Add promotion code"
   - Enter test code (e.g., "SAVE20")
   - Verify discount applies correctly

3. **Test validation rules:**
   - Try code with order below minimum amount (should fail)
   - Try expired code (should fail)
   - Try invalid code (should fail)
   - Try valid code (should succeed)

4. **Complete test purchase:**
   - Use test card: `4242 4242 4242 4242`
   - Any future expiry date
   - Any CVC

5. **Verify webhook data:**
   - Check server logs for `checkout.session.completed` webhook
   - Verify discount data is present in session object:

```python
{
  "id": "cs_test_...",
  "discount": {
    "coupon": {
      "id": "promo_20_off",
      "percent_off": 20
    },
    "promotion_code": "promo_1234567890"
  },
  "total_details": {
    "amount_discount": 1000,  # $10.00 in cents
    "amount_subtotal": 5000,  # $50.00 in cents
    "amount_total": 4000      # $40.00 in cents
  }
}
```

### Step 5: Create Production Codes

Once testing is complete, create production coupons and promotion codes:

1. Switch to **Live mode** in Stripe Dashboard
2. Repeat Steps 1-2 to create production coupons and codes
3. Announce codes to customers (email, social media, etc.)

**Important:** Production codes use your live Stripe API keys. Test mode codes won't work in production.

---

## Common Use Cases

### Use Case 1: Percentage Off All Orders

**Goal:** 20% off any order

```bash
# Create coupon
curl https://api.stripe.com/v1/coupons \
  -u sk_live_YOUR_API_KEY: \
  -d percent_off=20 \
  -d duration=once \
  -d name="20% Off"

# Create promotion code
curl https://api.stripe.com/v1/promotion_codes \
  -u sk_live_YOUR_API_KEY: \
  -d coupon=COUPON_ID \
  -d code=SAVE20
```

### Use Case 2: Dollar Amount Off Orders Over $X

**Goal:** $10 off orders $50+

```bash
# Create coupon
curl https://api.stripe.com/v1/coupons \
  -u sk_live_YOUR_API_KEY: \
  -d amount_off=1000 \
  -d currency=usd \
  -d duration=once \
  -d name="$10 Off Orders $50+"

# Create promotion code with minimum
curl https://api.stripe.com/v1/promotion_codes \
  -u sk_live_YOUR_API_KEY: \
  -d coupon=COUPON_ID \
  -d code=SAVE10 \
  -d restrictions[minimum_amount]=5000 \
  -d restrictions[minimum_amount_currency]=usd
```

### Use Case 3: Limited-Time Offer

**Goal:** 15% off, expires in 30 days, max 100 uses

```bash
# Create coupon
curl https://api.stripe.com/v1/coupons \
  -u sk_live_YOUR_API_KEY: \
  -d percent_off=15 \
  -d duration=once \
  -d name="15% Off Limited Time"

# Create promotion code with expiration and limit
curl https://api.stripe.com/v1/promotion_codes \
  -u sk_live_YOUR_API_KEY: \
  -d coupon=COUPON_ID \
  -d code=LIMITED15 \
  -d max_redemptions=100 \
  -d expires_at=$(date -v+30d +%s)  # Unix timestamp 30 days from now
```

### Use Case 4: First-Time Customer Discount

**Goal:** 25% off first purchase only

```bash
# Create coupon
curl https://api.stripe.com/v1/coupons \
  -u sk_live_YOUR_API_KEY: \
  -d percent_off=25 \
  -d duration=once \
  -d name="25% Off First Purchase"

# Create promotion code for first-time customers
curl https://api.stripe.com/v1/promotion_codes \
  -u sk_live_YOUR_API_KEY: \
  -d coupon=COUPON_ID \
  -d code=WELCOME25 \
  -d restrictions[first_time_transaction]=true
```

---

## Analytics & Monitoring

### Stripe Dashboard Analytics

Stripe provides built-in analytics for promotion codes:

1. Go to **Products** → **Promotion codes**
2. Click on a promotion code
3. View metrics:
   - **Times redeemed:** Total usage count
   - **Revenue impact:** Total discount amount given
   - **Redemption list:** Individual orders with discount applied
   - **Timeline:** Redemptions over time

### Optional: Store in Django

If you need custom reporting beyond Stripe's analytics, you can optionally store discount data in your Order model.

**Step 1: Add fields to Order model (optional)**

```python
# order/models.py
class Order(models.Model):
    # ... existing fields ...
    discount_code_used = models.CharField(max_length=100, null=True, blank=True)
    discount_amount_cents = models.IntegerField(null=True, blank=True)
```

**Step 2: Create and run migration**

```bash
python manage.py makemigrations
python manage.py migrate
```

**Step 3: Update webhook handler**

```python
# order/views.py::checkout_session_success()
def checkout_session_success(request):
    # ... existing code ...

    # Expand session to get discount data
    session = stripe.checkout.Session.retrieve(
        session_id,
        expand=['total_details.breakdown']
    )

    # Store discount info if present (optional)
    if session.get('discount'):
        order.discount_code_used = session['discount']['promotion_code']
        order.discount_amount_cents = session['total_details']['amount_discount']
        order.save()

    # ... rest of code ...
```

**Note:** This is purely optional. Stripe Dashboard provides comprehensive analytics, so you may not need this.

---

## Best Practices

### Code Naming

✅ **Good codes:**
- `SAVE20` (clear benefit)
- `WELCOME10` (indicates first-time offer)
- `SPRING25` (seasonal, limited time)
- `FREESHIP` (clear benefit, even if technically percentage off)

❌ **Bad codes:**
- `PROMO123` (no context)
- `XYZ` (cryptic)
- `AAAA` (looks like placeholder)

### Restrictions

**Always consider:**
- **Minimum amount:** Prevents abuse on tiny orders
- **Expiration date:** Creates urgency
- **Max redemptions:** Limits budget impact
- **First-time transaction:** Rewards new customers

**Example configuration:**
```
Code: SAVE20
Discount: 20% off
Minimum: $25.00
Expires: End of month
Max uses: 500
```

### Communication

When sharing codes with customers:

✅ **Clear instructions:**
> "Use code SAVE20 at checkout for 20% off orders $25+"

✅ **Set expectations:**
> "Enter code on the payment page (after clicking Checkout)"

❌ **Avoid confusion:**
> "Use discount code" (where? when? how much?)

### Testing

**Before launching any code:**
1. Test in Stripe test mode first
2. Verify all restrictions work (minimum amount, expiration, etc.)
3. Test invalid code scenarios
4. Complete full checkout flow
5. Verify webhook receives discount data
6. Check order confirmation email

---

## Troubleshooting

### Issue: "Promotion code not found"

**Cause:** Code doesn't exist or is in wrong mode (test vs live)

**Solution:**
- Verify code exists in Stripe Dashboard
- Ensure using correct mode (test codes only work in test mode)
- Check for typos in code

### Issue: "Promotion code is not currently active"

**Cause:** Code has been deactivated or hasn't been activated yet

**Solution:**
- Go to Stripe Dashboard → Promotion codes
- Click on the code
- Toggle "Active" to ON

### Issue: "Promotion code cannot be applied to this order"

**Causes:**
- Order total below minimum amount
- Code expired
- Max redemptions reached
- First-time restriction not met

**Solution:**
- Check code restrictions in Stripe Dashboard
- Verify order meets all requirements
- Check expiration date and redemption count

### Issue: Discount not appearing in webhook

**Cause:** Session not expanded to include discount data

**Solution:**
Expand session when retrieving:
```python
session = stripe.checkout.Session.retrieve(
    session_id,
    expand=['total_details.breakdown']
)
```

---

## API Reference

### Stripe Coupon Object

```python
{
  "id": "coupon_id",
  "object": "coupon",
  "amount_off": 1000,           # Dollar discount in cents (optional)
  "percent_off": 20,            # Percentage discount (optional)
  "currency": "usd",            # Required if amount_off
  "duration": "once",           # once, forever, repeating
  "duration_in_months": 3,      # Required if duration=repeating
  "name": "20% Off",
  "valid": true,
  "created": 1625097600
}
```

### Stripe Promotion Code Object

```python
{
  "id": "promo_id",
  "object": "promotion_code",
  "code": "SAVE20",
  "coupon": {
    "id": "coupon_id",
    "percent_off": 20
  },
  "restrictions": {
    "minimum_amount": 2000,
    "minimum_amount_currency": "usd",
    "first_time_transaction": false
  },
  "active": true,
  "expires_at": 1735689600,     # Unix timestamp (optional)
  "max_redemptions": 100,       # Total usage limit (optional)
  "times_redeemed": 42,
  "created": 1625097600
}
```

### Checkout Session with Discount

```python
{
  "id": "cs_test_...",
  "object": "checkout.session",
  "amount_total": 4000,         # $40.00 after discount
  "discount": {
    "coupon": {
      "id": "promo_20_off",
      "percent_off": 20
    },
    "promotion_code": "promo_1234567890"
  },
  "total_details": {
    "amount_discount": 1000,    # $10.00 discount
    "amount_shipping": 0,
    "amount_subtotal": 5000,    # $50.00 before discount
    "amount_tax": 0,
    "amount_total": 4000        # $40.00 final total
  }
}
```

---

## Security Considerations

### Code Sharing

**Risk:** Public codes can be shared widely (Reddit, coupon sites)

**Mitigation:**
- Set `max_redemptions` to limit budget impact
- Use expiration dates to time-bound exposure
- Monitor redemption rates in Stripe Dashboard
- Deactivate codes if abuse detected

### First-Time Customer Codes

**Risk:** Customers could create multiple accounts to reuse code

**Mitigation:**
- Use `restrictions.first_time_transaction=true` (Stripe checks by email)
- Monitor for duplicate email patterns
- Limit discount amount on first-time codes

### Minimum Amount Requirements

**Risk:** Customers add cheap items to meet minimum

**Mitigation:**
- Set reasonable minimums based on typical order values
- Monitor order patterns after code launches
- Adjust minimums if needed

---

## Related Documentation

- **Phase 1 Plan:** `Discount_Code_Removal_Plan.md` (removed custom discount logic)
- **Stripe Discount Docs:** https://docs.stripe.com/payments/checkout/discounts
- **Stripe Coupons API:** https://docs.stripe.com/api/coupons
- **Stripe Promotion Codes API:** https://docs.stripe.com/api/promotion_codes

---

## When to Implement

**Implement Phase 2 when:**
- ✅ You want to offer discount codes to customers
- ✅ You have a marketing campaign that needs codes
- ✅ You want to test conversion rates with discounts
- ✅ You need to reward loyal customers

**Wait on Phase 2 if:**
- ⏸️ No immediate need for discount codes
- ⏸️ Want to validate product-market fit first
- ⏸️ Prefer to keep things simple initially

There's no rush! The infrastructure is ready whenever you need it.

---

**Last Updated:** Session 81 (Jan 22, 2026)
**Status:** Ready to implement when needed
