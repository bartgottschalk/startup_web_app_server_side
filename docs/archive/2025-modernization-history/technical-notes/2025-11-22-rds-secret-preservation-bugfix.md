# RDS Secret Preservation Bugfix - Phase 9 Completion

**Date:** November 22, 2025
**Author:** Bart Gottschalk with Claude Code
**Branch:** bugfix/fix-rds-secret-update
**PR:** #37
**Status:** Complete - Infrastructure recreated with fix

## Summary

Fixed critical bug in `create-rds.sh` that was overwriting the entire Secrets Manager secret when updating the RDS endpoint, causing loss of master_password and other critical fields. This broke the separate password architecture implemented for security (principle of least privilege).

## Problem

After deploying RDS with separate master and application passwords (PR #36), attempted to create databases but discovered the application password was missing from the secret:

```bash
# Expected secret structure (from create-secrets.sh)
{
  "master_username": "postgres",
  "master_password": "32-char-password-1",
  "username": "django_app",
  "password": "32-char-password-2",
  "django_secret_key": "50-char-key",
  "stripe_secret_key": "sk_live_...",
  "stripe_publishable_key": "pk_live_...",
  "email_host": "smtp.example.com",
  ...
}

# Actual secret structure (after create-rds.sh)
{
  "engine": "postgresql",
  "host": "startupwebapp-multi-tenant-prod...rds.amazonaws.com",
  "port": 5432,
  "username": "django_app",
  "password": "32-char-password-2",
  "dbClusterIdentifier": "startupwebapp-multi-tenant-prod"
}
```

**Lost fields:**
- `master_username` and `master_password` - Needed for RDS admin operations
- `django_secret_key` - Required for Django application
- `stripe_secret_key` and `stripe_publishable_key` - Payment processing
- `email_host`, `email_port`, `email_user`, `email_password` - Email notifications

## Root Cause

Lines 215-224 in `scripts/infra/create-rds.sh`:

```bash
# BEFORE (buggy code)
aws secretsmanager update-secret \
    --secret-id "$DB_SECRET_NAME" \
    --secret-string "{
        \"engine\": \"postgresql\",
        \"host\": \"${RDS_ENDPOINT}\",
        \"port\": 5432,
        \"username\": \"django_app\",
        \"password\": \"${DB_PASSWORD}\",
        \"dbClusterIdentifier\": \"${RDS_INSTANCE_ID}\"
    }" > /dev/null
```

**Why this happened:**
1. `create-secrets.sh` creates secret with full structure (12+ fields)
2. `create-rds.sh` retrieves only `master_password` via `jq -r '.master_password'`
3. `create-rds.sh` uses that password to create RDS instance
4. `create-rds.sh` then **overwrites** entire secret with hardcoded minimal structure
5. All other fields lost, including the `master_password` itself

**Impact:**
- Cannot connect to RDS as postgres (master) user - password missing
- Django SECRET_KEY lost - application would fail to start
- Stripe/Email credentials lost - would need manual re-entry
- Broke the separate password security architecture

## Solution

Updated `create-rds.sh` to preserve all fields by using `jq` to update only the `host` field:

```bash
# AFTER (fixed code)
# Get current secret and update only the host field
CURRENT_SECRET=$(aws secretsmanager get-secret-value \
    --secret-id "$DB_SECRET_NAME" \
    --query 'SecretString' \
    --output text)
UPDATED_SECRET=$(echo "$CURRENT_SECRET" | jq --arg host "$RDS_ENDPOINT" '.host = $host')
aws secretsmanager update-secret \
    --secret-id "$DB_SECRET_NAME" \
    --secret-string "$UPDATED_SECRET" > /dev/null
```

**How this works:**
1. Retrieve the current secret JSON
2. Use `jq` to update only the `host` field, preserving all others
3. Write back the complete secret with updated host

## Implementation

1. **Created bugfix branch:**
   ```bash
   git checkout -b bugfix/fix-rds-secret-update
   ```

2. **Updated create-rds.sh** (lines 213-224)

3. **Committed fix:**
   ```
   Fix: Preserve all secret fields when updating RDS endpoint
   ```

4. **Destroyed infrastructure:**
   ```bash
   ./scripts/infra/destroy-rds.sh
   ./scripts/infra/destroy-secrets.sh
   aws secretsmanager delete-secret --secret-id ... --force-delete-without-recovery
   ```

5. **Recreated with fixed script:**
   ```bash
   ./scripts/infra/create-secrets.sh  # Creates full secret structure
   ./scripts/infra/create-rds.sh      # Now preserves all fields when updating host
   ```

6. **Verified fix:**
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id rds/startupwebapp/multi-tenant/master \
     --query 'SecretString' \
     --output text | jq
   ```

   Result: All fields present including `master_password` ✅

7. **Created databases with separate passwords:**
   - Connected to bastion via SSM
   - Retrieved both `master_password` and `password` from secret
   - Connected to RDS as postgres user (master)
   - Created django_app user with application password
   - Created 3 databases owned by django_app
   - Verified both users can connect with their respective passwords

8. **Recreated monitoring:**
   ```bash
   ./scripts/infra/create-monitoring.sh bart@mosaicmeshai.com
   ```

9. **Created PR #37** and merged to master

## Testing

✅ **Verified secret has all fields after RDS creation**
```bash
# Expected 12+ fields all present
master_username, master_password, username, password,
django_secret_key, stripe_secret_key, stripe_publishable_key,
email_host, email_port, email_user, email_password,
host, port, engine, dbClusterIdentifier
```

✅ **Successfully created databases using separate passwords**
- postgres user: Uses `master_password` from secret
- django_app user: Uses `password` from secret
- Both passwords are different (32 chars each)

✅ **Verified connections work**
```bash
# Master connection
PGPASSWORD=$MASTER_PW psql -h $RDS_ENDPOINT -U postgres -d postgres

# Application connection
PGPASSWORD=$APP_PW psql -h $RDS_ENDPOINT -U django_app -d startupwebapp_prod
```

## Lessons Learned

1. **Always preserve existing data when updating**: Use selective updates (jq) rather than overwriting
2. **Test full workflows end-to-end**: The bug wasn't caught until trying to use the secret for database creation
3. **Infrastructure as Code needs tests**: Consider adding validation scripts that check secret structure
4. **Document expected data structures**: Clear expectations would have caught this sooner

## Prevention

Future improvements to prevent similar issues:

1. **Add validation to create-rds.sh:**
   ```bash
   # After updating secret, verify all required fields exist
   FIELD_COUNT=$(echo "$UPDATED_SECRET" | jq 'keys | length')
   if [ "$FIELD_COUNT" -lt 12 ]; then
     echo "ERROR: Secret missing fields after update"
     exit 1
   fi
   ```

2. **Add integration tests:**
   - Test that creates secret → creates RDS → verifies secret still has all fields
   - Automated test that catches regressions

3. **Document secret schema:**
   - Add JSON schema file defining required fields
   - Validate secrets against schema in scripts

## Related Work

- **PR #36**: Initial Phase 9 deployment (bastion host, separate passwords)
- **PR #37**: This bugfix (secret preservation)
- **Technical Notes**:
  - `2025-11-21-phase-9-deployment-guide.md` - Deployment instructions
  - `2025-11-22-phase-9-bastion-troubleshooting.md` - Bastion SSM connection fix
  - `2025-11-20-aws-rds-django-integration.md` - Phase 8 integration

## Outcome

✅ **Phase 9 Complete (100%, 7/7 steps)**
- Infrastructure deployed with proper secret preservation
- Separate master and application passwords working correctly
- 3 multi-tenant databases created on AWS RDS
- All security improvements intact
- Monthly cost: $36 ($30 with bastion stopped)

**Infrastructure Status:**
```
Step 1: VPC and Networking           ✅
Step 2: Security Groups               ✅
Step 3: Secrets Manager               ✅ (12+ fields preserved)
Step 4: RDS PostgreSQL                ✅ (using fixed script)
Step 5: Multi-Tenant Databases        ✅ (separate passwords)
Optional: Bastion Host                ✅
Step 6: CloudWatch Monitoring         ✅
Step 7: Verification                  ✅
```

## Next Steps

With Phase 9 complete, ready for Phase 10:
- Run Django migrations on AWS RDS
- Update production credentials (Stripe keys, Email SMTP)
- Test full Django application against AWS RDS
- Prepare containers for AWS deployment
