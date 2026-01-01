# Seed Data Migrations

**Date**: 2025-12-04
**Status**: Implemented
**Related PR**: #42

## Summary

Converted seed data from manual SQL/command execution to Django data migrations. This ensures all required reference data is automatically created when migrations run, preventing 500 errors in new deployments.

## Problem Statement

The production deployment was returning 500 errors on the `/user/logged-in` endpoint because the `clientevent_configuration` table was empty. The application code assumes this record exists:

```python
# user/views.py line 80
ClientEventConfiguration.objects.get(id=1).log_client_events
```

### Root Cause

Seed data was loaded via two mechanisms, both requiring manual execution:

1. **`db_inserts.sql`** - MySQL-formatted SQL file with INSERT statements
2. **`load_sample_data`** - Django management command

During the production deployment:
- CI/CD ran `python manage.py migrate` (schema only)
- Nobody ran `load_sample_data` or executed `db_inserts.sql`
- Result: Empty reference tables → 500 errors

### Why This Wasn't Caught Earlier

- Local development: Seed data was loaded once and persisted in Docker volumes
- Tests: `base_functional_test.py` creates its own seed data in `setUp()`
- The gap only appeared in fresh production deployments

## Solution

Created Django data migrations that run automatically with `migrate`:

### Migration Files Created

| File | App | Purpose |
|------|-----|---------|
| `0002_seed_configuration.py` | clientevent | ClientEvent Configuration (log_client_events) |
| `0002_seed_user_data.py` | user | Groups, Terms of Use, Email Types/Statuses, Ad Types/Statuses, Email Templates |
| `0004_seed_order_data.py` | order | Order Statuses, SKU Types, Order Config, Discount Types, Shipping Methods, Products |

Note: `order/0002_add_default_inventory_statuses.py` already existed and creates Skuinventory records.

### Design Decisions

1. **Use `get_or_create`** for idempotency - safe to run multiple times
2. **Skip during tests** - tests create their own isolated data
3. **Include sample products** - makes the demo site functional out of the box
4. **One example discount code** - demonstrates the discount system with valid dates

### Test Detection Pattern

Migrations detect test runs and skip data creation:

```python
db_name = schema_editor.connection.settings_dict.get('NAME', '')
if 'memory' in db_name.lower() or db_name.startswith('test_'):
    return  # Skip during tests
```

This works because:
- SQLite in-memory databases contain 'memory' in the name
- PostgreSQL test databases are prefixed with 'test_'

## Data Included

### Critical (Required for app to function)

| Table | Records | Why Required |
|-------|---------|--------------|
| `clientevent_configuration` | 1 | `logged_in` view queries this |
| `auth_group` | 1 (Members) | User registration assigns to group |
| `user_terms_of_use_version` | 1 | Account creation requires ToS |
| `user_email_type` | 2 | Email system lookup |
| `user_email_status` | 3 | Email system lookup |
| `order_status` | 4 | Order processing workflow |
| `order_sku_type` | 1 | Product catalog |
| `order_sku_inventory` | 3 | Product availability |
| `order_configuration` | 6 | Checkout settings |
| `order_shipping_method` | 5 | Checkout shipping options |

### Functional (Required for checkout to work)

| Table | Records | Why Required |
|-------|---------|--------------|
| `user_email` | 4 | Order confirmation email templates |
| `order_discount_type` | 4 | Discount system lookup |

### Demo Data (Makes example site functional)

| Table | Records | Purpose |
|-------|---------|---------|
| `user_ad_type` | 2 | Ad tracking examples |
| `user_ad_status` | 4 | Ad tracking examples |
| `order_discount_code` | 1 | WELCOME10 discount code |
| `order_product` | 3 | Paper Clips, Binder Clips, Rubber Bands |
| `order_sku` | 6 | Product variants |
| `order_sku_price` | 8 | Product pricing |
| `order_product_image` | 3 | Product images |
| `order_product_video` | 2 | Product videos |
| `order_sku_image` | 5 | SKU images |

## For Forks

Projects that fork StartupWebApp should customize these migrations:

### Must Change

- Email templates (`user_email`) - Update subject, body, from_address
- Terms of Use content
- Products and SKUs - Replace sample products with real ones

### Consider Changing

- Shipping methods and costs
- Discount codes
- Order configuration email codes (`em_cd` values)

### Keep As-Is

- Auth Group structure
- Email/Ad Type/Status lookup values
- Order Status workflow
- SKU Inventory statuses

## Verification

After deploying these migrations:

```bash
# Verify migrations ran
python manage.py showmigrations clientevent user order

# Verify data exists
python manage.py shell -c "
from clientevent.models import Configuration
from order.models import Product, Status
print('Config:', Configuration.objects.filter(id=1).exists())
print('Products:', Product.objects.count())
print('Statuses:', Status.objects.count())
"
```

Expected output:
```
Config: True
Products: 3
Statuses: 4
```

## Related Files

- `db_inserts.sql` - Legacy SQL file (MySQL format, kept for reference)
- `order/management/commands/load_sample_data.py` - Management command (kept for development convenience)
- `functional_tests/base_functional_test.py` - Test setup creates similar data

## Lessons Learned

1. **Seed data should be in migrations** - Manual steps get forgotten in CI/CD
2. **Test environments mask issues** - Tests create their own data, hiding missing production data
3. **Local volumes persist state** - Makes it easy to forget initialization steps
4. **`get_or_create` is essential** - Makes migrations idempotent and safe to re-run
