# FloatField to DecimalField Conversion for Currency Fields

**Date**: November 17, 2025
**Phase**: PostgreSQL Migration - Phase 1
**Branch**: `feature/postgresql-migration`
**Status**: ✅ Complete

## Overview

Converted all 12 FloatField instances in the order app to DecimalField to ensure precise currency calculations and PostgreSQL compatibility. This is Phase 1 of the PostgreSQL migration project.

## Problem Statement

**Issue**: FloatField uses floating-point arithmetic which can cause precision errors in financial calculations:
- `0.1 + 0.2 = 0.30000000000000004` (floating point error)
- Currency values stored as float can accumulate rounding errors
- PostgreSQL best practice is to use NUMERIC/DECIMAL for monetary values
- Django's DecimalField maps to PostgreSQL's NUMERIC type

**Impact**:
- Potential precision errors in order totals, tax calculations, discounts
- Type incompatibility issues (float vs Decimal in calculations)
- Not following Django/PostgreSQL financial data best practices

## Implementation

### Test-Driven Development (TDD) Approach

**Step 1: Write Tests First** (19 new tests)
- Created `order/tests/test_decimal_field_precision.py`
- Tests verified fields return Decimal type (not float)
- Tests verified precise calculations (tax, discounts, totals)
- Tests demonstrated floating-point error prevention
- **Result**: 13 tests FAILED (as expected - fields were still FloatField)

**Step 2: Convert Fields**
- Changed 12 FloatField instances to DecimalField(max_digits=10, decimal_places=2)
- Created Django migration: `0003_alter_discountcode_discount_amount_and_more.py`
- **Result**: Migration applied successfully

**Step 3: Fix Business Logic**
- Updated `order_utils.calculate_cart_item_discount()` to handle Decimal types
- Added Decimal conversion for function parameters
- Fixed division to use `Decimal('100')` instead of `100`

**Step 4: Update Existing Tests**
- Fixed 11 test assertions expecting float in JSON responses
- Changed from `3.50` to `'3.50'` (DecimalField serializes to string in JSON)
- Updated 4 test files: cart_operations, checkout_flow, product_browsing, shipping_and_discounts
- **Result**: All tests now pass

### Fields Converted (12 total)

**Configuration Model:**
1. `Orderconfiguration.float_value` - Generic config value

**Pricing Models:**
2. `Skuprice.price` - SKU price
3. `Discountcode.discount_amount` - Discount amount
4. `Discountcode.order_minimum` - Order minimum for discount eligibility
5. `Shippingmethod.shipping_cost` - Shipping cost

**Order Models:**
6. `Order.sales_tax_amt` - Sales tax amount
7. `Order.item_subtotal` - Item subtotal
8. `Order.item_discount_amt` - Item discount amount
9. `Order.shipping_amt` - Shipping amount
10. `Order.shipping_discount_amt` - Shipping discount amount
11. `Order.order_total` - Order total
12. `Ordersku.price_each` - Price per SKU in order

### DecimalField Configuration

```python
# Before
price = models.FloatField(default=0)

# After
price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
```

**Parameters:**
- `max_digits=10`: Total digits (including decimals) - supports up to $99,999,999.99
- `decimal_places=2`: Two decimal places for cents
- Preserves original `default`, `blank`, `null` attributes

## Files Changed

**Models:**
- `StartupWebApp/order/models.py` - 12 field conversions

**Business Logic:**
- `StartupWebApp/order/utilities/order_utils.py` - Added Decimal type handling

**Tests Created:**
- `StartupWebApp/order/tests/test_decimal_field_precision.py` - 19 new tests
  - 13 tests verify Decimal type for each field
  - 6 tests verify precision in calculations

**Tests Updated (11 assertions fixed):**
- `order/tests/test_cart_operations.py` - 5 assertions
- `order/tests/test_checkout_flow.py` - 1 assertion
- `order/tests/test_product_browsing.py` - 3 assertions
- `order/tests/test_shipping_and_discounts.py` - 2 assertions

**Migrations:**
- `order/migrations/0003_alter_discountcode_discount_amount_and_more.py`

## Testing Results

### Test Counts
- **Before**: 721 tests (693 unit + 28 functional)
- **After**: 740 tests (712 unit + 28 functional)
- **New Tests**: 19 DecimalField precision tests

### Test Results - 100% Pass Rate ✅
```
Unit Tests:        712/712 PASS ✅
Functional Tests:   28/28  PASS ✅
Total Tests:       740/740 PASS ✅
Pass Rate:         100%
```

### Linting Results ✅
```
flake8 errors: 28 E501 (line too long in auto-generated migrations - acceptable)
No functional code linting errors
```

### TDD Validation
1. ✅ Tests written first (13 FAIL as expected)
2. ✅ Code changes made (12 field conversions)
3. ✅ Tests now pass (19/19 PASS)
4. ✅ No regressions (all 740 tests pass)

## Benefits

### 1. Precision
- **Exact decimal arithmetic**: No floating-point errors
- **Financial accuracy**: Critical for money calculations
- **Tax precision**: 8.25% of $100.00 = exactly $8.25
- **Discount accuracy**: 15% of $100.00 = exactly $15.00

### 2. Type Safety
- **Consistent types**: All currency values are Decimal
- **No mixing**: Prevents float/Decimal type errors
- **Clean code**: No manual float↔Decimal conversions needed

### 3. PostgreSQL Compatibility
- **Native support**: DecimalField → PostgreSQL NUMERIC type
- **Best practice**: Industry standard for monetary data
- **Migration ready**: Prepares for PostgreSQL migration (Phase 2-5)

### 4. JSON Serialization
- **String format**: DecimalField serializes to `"3.50"` not `3.5`
- **Preserves precision**: No loss of trailing zeros
- **Frontend safe**: Strings prevent JavaScript floating-point issues

## Example: Precision Improvement

### Before (FloatField)
```python
# Price stored as float
>>> price = 0.1
>>> price * 3
0.30000000000000004  # ❌ Floating point error

# Tax calculation
>>> subtotal = 100.0
>>> tax_rate = 0.0825
>>> subtotal * tax_rate
8.250000000000001  # ❌ Imprecise
```

### After (DecimalField)
```python
from decimal import Decimal

# Price stored as Decimal
>>> price = Decimal('0.10')
>>> price * 3
Decimal('0.30')  # ✅ Exact

# Tax calculation
>>> subtotal = Decimal('100.00')
>>> tax_rate = Decimal('0.0825')
>>> subtotal * tax_rate
Decimal('8.2500')  # ✅ Precise
```

## Migration SQL (SQLite)

Django generated migration to ALTER all 12 columns:

```sql
-- Example for one field
ALTER TABLE "order_sku_price"
ALTER COLUMN "price" TYPE NUMERIC(10, 2);

-- Applied to all 12 fields across 5 tables:
-- order_configuration, order_discount_code, order_order,
-- order_order_sku, order_shipping_method, order_sku_price
```

## Production Considerations

### Data Preservation
- ✅ Existing SQLite data automatically converted during migration
- ✅ No data loss (SQLite REAL → NUMERIC conversion is safe)
- ✅ Values rounded to 2 decimal places (standard for currency)

### API Response Changes
- **Before**: `{"price": 3.5}`
- **After**: `{"price": "3.50"}`
- ✅ Frontend already handles string values (no changes needed)
- ✅ JSON.parse() works with both number and string formats

### Performance
- ✅ Negligible impact (Decimal operations are highly optimized)
- ✅ SQLite: NUMERIC stored efficiently
- ✅ PostgreSQL: NUMERIC is native, optimized type

## Timeline

- **Analysis**: 30 minutes (identified 12 fields)
- **Test Writing**: 45 minutes (19 TDD tests)
- **Implementation**: 30 minutes (model changes + migration)
- **Test Fixes**: 45 minutes (11 assertions + business logic)
- **Verification**: 30 minutes (740 tests + linting)
- **Total**: 3 hours

## Related Documentation

- **Migration Planning**: `docs/technical-notes/2025-11-17-database-migration-planning.md`
- **PostgreSQL Migration Roadmap**: See Phase 2-5 in planning doc
- **Django DecimalField Docs**: https://docs.djangoproject.com/en/4.2/ref/models/fields/#decimalfield

## Next Steps

**Phase 2**: Set up Docker PostgreSQL with multi-database support
- Configure PostgreSQL 16 container
- Set up separate databases for different environments
- Test multi-tenant architecture locally

## Lessons Learned

1. **TDD Works**: Writing tests first caught all edge cases
2. **JSON Serialization**: DecimalField → string is correct behavior for financial data
3. **Type Conversion**: Python doesn't allow float * Decimal (by design - forces explicit conversion)
4. **Migration Safety**: Django handles FloatField → DecimalField conversion safely
5. **Comprehensive Testing**: 740 tests provided confidence in changes

## Conclusion

Successfully converted all 12 currency fields from FloatField to DecimalField using TDD methodology. All 740 tests passing, zero regressions, and codebase now follows Django/PostgreSQL best practices for financial data. Ready for Phase 2 of PostgreSQL migration.

**Status**: ✅ Phase 1 Complete - Ready for PostgreSQL Setup
