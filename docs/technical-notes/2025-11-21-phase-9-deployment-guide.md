# Phase 9: AWS RDS Database Creation & Django Deployment - Step-by-Step Guide

**Date**: November 21, 2025
**Status**: 🚧 In Progress
**Branch**: TBD (will create feature branch)

## Executive Summary

This document provides a step-by-step guide for completing Phase 9 of the AWS deployment, which includes updating production credentials in AWS Secrets Manager, creating multi-tenant databases on AWS RDS, and deploying Django to production.

## Prerequisites (Already Complete ✅)

- ✅ AWS RDS PostgreSQL 16 instance deployed and available
- ✅ AWS Secrets Manager secret created with placeholder values
- ✅ VPC, security groups, and networking configured
- ✅ CloudWatch monitoring and alarms active
- ✅ Django production settings module created (`settings_production.py`)
- ✅ All 740 tests passing locally with PostgreSQL

## Current RDS Infrastructure

**RDS Endpoint**: `startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com:5432`
**Instance Type**: db.t4g.small
**PostgreSQL Version**: 16.x
**Storage**: 20 GB gp3
**Monthly Cost**: $29

## Step 1: Retrieve Current AWS Secret Structure

First, let's see what's currently in AWS Secrets Manager:

```bash
aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --region us-east-1 \
  --query SecretString \
  --output text | python3 -m json.tool
```

**Expected Output Structure:**
```json
{
  "engine": "postgresql",
  "host": "startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com",
  "port": 5432,
  "username": "django_app",
  "password": "AUTO_GENERATED_32_CHARS",
  "dbClusterIdentifier": "startupwebapp-multi-tenant-prod",
  "django_secret_key": "AUTO_GENERATED_50_CHARS",
  "stripe_secret_key": "sk_live_PLACEHOLDER_UPDATE_WITH_REAL_KEY",
  "stripe_publishable_key": "pk_live_PLACEHOLDER_UPDATE_WITH_REAL_KEY",
  "email_host": "smtp.example.com",
  "email_port": 587,
  "email_user": "notifications@example.com",
  "email_password": "PLACEHOLDER_UPDATE_WITH_REAL_PASSWORD"
}
```

**Action**: Run the command above and save the output to a file for reference.

## Step 2: Gather Production Credentials

You need to gather the following production credentials:

### 2.1 Stripe API Credentials

**Phase 9 Status**: ⚠️ **No Stripe account yet - Using test keys for now**

Since we don't have a Stripe production account yet, we'll use test keys initially:
- `stripe_secret_key`: `sk_test_placeholder_no_stripe_account_yet`
- `stripe_publishable_key`: `pk_test_placeholder_no_stripe_account_yet`

**When you create a Stripe account (before accepting real payments):**
1. Sign up at [Stripe Dashboard](https://dashboard.stripe.com/)
2. Complete account verification
3. Navigate to: Developers → API keys
4. Copy **Production** keys (start with `sk_live_...` and `pk_live_...`)
5. Update AWS Secrets Manager with real keys
6. **Important**: Switch from test to live mode in Stripe dashboard

**Current local test values** (for reference only):
- Test secret key: `sk_test_secret_key`
- Test publishable key: `pk_test_secret_key`

### 2.2 Email SMTP Credentials

**Current local development setup:**
- Host: `localhost` (mailhog/test server)
- Port: `1025`
- No authentication

**Phase 9 Approach**: ✅ **Gmail SMTP (Initial Production Setup)**

We're using Gmail for Phase 9 because:
- ✅ Already have Google Workspace for MosaicMeshAI.com
- ✅ Quick 5-minute setup (no waiting for approvals)
- ✅ Reliable for MVP/early testing (up to 500 emails/day with Google Workspace)
- ✅ Easy to set up and test immediately
- ✅ Perfect for initial deployment without real users yet

**Migration Plan**: 🔄 **Switch to AWS SES before real user launch**

We'll migrate to AWS SES 1-2 weeks before launching to real users:
- **Why**: Better for production scale, detailed metrics, $0.10 per 1,000 emails
- **When**: Before real user launch (currently ~few weeks away)
- **Effort**: 1-2 days (domain verification + production access request)
- **Migration**: Simple - update 4 values in AWS Secrets Manager, no code changes

---

**Gmail Configuration for Phase 9:**

**Settings needed:**
- Host: `smtp.gmail.com`
- Port: `587`
- User: Your MosaicMeshAI.com email address
- Password: App-specific password (NOT your regular Gmail password)
- TLS: Yes (Django automatically uses `EMAIL_USE_TLS = True`)

**How to create Gmail App-Specific Password:**

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to: **Security** → **2-Step Verification** (must be enabled first)
3. Scroll to bottom: **App passwords**
4. Click "App passwords"
5. Select app: **"Mail"**
6. Select device: **"Other (Custom name)"** → Enter: `StartupWebApp Production`
7. Click **"Generate"**
8. Copy the 16-character password (format: `xxxx-xxxx-xxxx-xxxx`)
9. **Important**: Remove the spaces when entering into AWS Secrets Manager
10. **Save it**: You won't be able to see this password again!

**Example:**
- Generated: `abcd-efgh-ijkl-mnop`
- Use in secret: `abcdefghijklmnop` (no spaces)

---

**Future: AWS SES Migration (Planned for Pre-Launch)**

When we migrate to AWS SES before real user launch, the configuration will be:
- Host: `email-smtp.us-east-1.amazonaws.com`
- Port: `587`
- User: AWS SES SMTP username (from IAM)
- Password: AWS SES SMTP password (from IAM)
- Benefits: 50,000 emails/day, detailed metrics, better deliverability, $0.10 per 1,000 emails

**Migration process documented in planned work items below.**

### 2.3 Verify Database Credentials

The database password and Django SECRET_KEY are **auto-generated** by the infrastructure scripts and should already be in AWS Secrets Manager. You do **not** need to change these unless you want to rotate them.

**To verify they exist:**
```bash
aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --region us-east-1 \
  --query SecretString \
  --output text | jq -r '.password, .django_secret_key'
```

## Step 3: Create Updated Secret JSON

Once you have created your Gmail App-Specific Password (from Step 2.2), create a file with the complete updated secret structure.

**Create a file**: `~/updated-secret.json`

**Template for Phase 9** (replace placeholders with your actual values):
```json
{
  "engine": "postgresql",
  "host": "startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com",
  "port": 5432,
  "username": "django_app",
  "password": "PASTE_EXISTING_PASSWORD_FROM_STEP_1",
  "dbClusterIdentifier": "startupwebapp-multi-tenant-prod",
  "django_secret_key": "PASTE_EXISTING_SECRET_KEY_FROM_STEP_1",
  "stripe_secret_key": "sk_test_placeholder_no_stripe_account_yet",
  "stripe_publishable_key": "pk_test_placeholder_no_stripe_account_yet",
  "email_host": "smtp.gmail.com",
  "email_port": 587,
  "email_user": "your-email@mosaicmeshai.com",
  "email_password": "REPLACE_WITH_GMAIL_APP_PASSWORD"
}
```

**Important**:
- Keep the existing `password` and `django_secret_key` values from Step 1 (don't change these!)
- **Stripe keys**: Use placeholder test keys for now (we don't have a Stripe account yet)
- **Email host**: `smtp.gmail.com` for Gmail
- **Email port**: `587` for TLS
- **Email user**: Your full MosaicMeshAI.com email address
- **Email password**: Your Gmail app-specific password (16 chars, no spaces)
- Make sure the JSON is valid (use `python3 -m json.tool` to validate if needed)

**Validation command** (before uploading):
```bash
cat ~/updated-secret.json | python3 -m json.tool
```
If this returns formatted JSON, your file is valid. If it shows an error, fix the JSON syntax.

## Step 4: Update AWS Secrets Manager

Once you've created the `updated-secret.json` file with real credentials:

```bash
aws secretsmanager update-secret \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --region us-east-1 \
  --secret-string file://~/updated-secret.json
```

**Verify the update:**
```bash
aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --region us-east-1 \
  --query SecretString \
  --output text | python3 -m json.tool
```

**Security Note**: After updating, delete the local file with credentials:
```bash
rm ~/updated-secret.json
```

## Step 5: Create Multi-Tenant Databases on AWS RDS

Now we need to create the three databases on the RDS instance.

### 5.1 Generate SQL Script

Run the infrastructure script to generate the SQL:

```bash
cd ~/Projects/WebApps/StartUpWebApp/startup_web_app_server_side
./scripts/infra/create-databases.sh
```

This will create a SQL script at: `/tmp/create-databases-startupwebapp-multi-tenant-prod.sql`

### 5.2 Access RDS Instance

**Option A: Use AWS RDS Query Editor** (easiest if available)
- Go to AWS Console → RDS → Query Editor
- Select your database instance
- Use master username: `postgres`
- Get password from Secrets Manager (see below)

**Option B: Create SSH Tunnel via Bastion Host**
```bash
# Create an EC2 bastion host in the public subnet (if you don't have one)
# Then create SSH tunnel:
ssh -i your-key.pem -L 5432:startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com:5432 ec2-user@bastion-host-ip
```

**Option C: Temporarily Modify Security Group** (not recommended, but works for testing)
- Add your IP address to the RDS security group to allow port 5432
- **Remember to remove it after database creation!**

### 5.3 Get Postgres Master Password

The master password should be in your AWS Secrets Manager secret:

```bash
aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --region us-east-1 \
  --query SecretString \
  --output text | jq -r '.password'
```

**Note**: This is the `django_app` user password. The `postgres` master user password was set when you created the RDS instance. If you don't have it, you may need to reset it via AWS Console.

### 5.4 Execute SQL

Connect to the database and run the SQL script:

```bash
psql -h startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d postgres \
     -f /tmp/create-databases-startupwebapp-multi-tenant-prod.sql
```

Or copy/paste the SQL commands from the generated file.

### 5.5 Verify Database Creation

```bash
psql -h startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com \
     -U django_app \
     -d startupwebapp_prod \
     -c '\dt'
```

**Expected**: Empty database (no tables yet - we'll create them with migrations)

## Step 6: Test RDS Connectivity from Local Machine

Now let's verify we can connect from your local machine using the production settings:

```bash
cd ~/Projects/WebApps/StartUpWebApp/startup_web_app_server_side/StartupWebApp

# Set environment variables
export DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production
export DATABASE_NAME=startupwebapp_prod
export DB_SECRET_NAME=rds/startupwebapp/multi-tenant/master
export AWS_REGION=us-east-1
export ALLOWED_HOSTS=www.mosaicmeshai.com,localhost

# Run connection test
python ../scripts/infra/test-rds-connection.py
```

**Expected Output:**
```
✓ Successfully retrieved secrets from AWS Secrets Manager
✓ Database configuration validated
✓ Successfully connected to AWS RDS PostgreSQL
✓ Successfully executed test query
✓ Django apps configuration loaded successfully
```

## Step 7: Run Django Migrations on AWS RDS

If the connection test passes, run the migrations:

```bash
# Still in StartupWebApp directory with environment variables set
python manage.py migrate
```

**Expected Output**: All 57 tables should be created successfully.

**Verify tables were created:**
```bash
python manage.py dbshell
# In psql:
\dt
# Should see all Django tables: user_member, order_order, etc.
\q
```

## Step 8: Create Superuser on Production Database

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

## Step 9: Load Sample Data (Optional)

If you have a fixture or sample data script:

```bash
python manage.py load_sample_data  # If this command exists
# Or load specific fixtures:
python manage.py loaddata your_fixture.json
```

## Step 10: Run Unit Tests Against AWS RDS (Local Validation)

Let's verify the tests still pass using the production database configuration:

```bash
# Still with production environment variables set
python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests --parallel=4
```

**Expected**: All 712 tests should pass.

**Note**: Tests will use the test database (`test_startupwebapp_prod`) which Django creates automatically.

## Step 11: Verify Complete Setup

Run a comprehensive verification:

```bash
# Check migrations are up to date
python manage.py showmigrations

# Check database structure
python manage.py sqlmigrate user 0001 | head -20  # Show first migration SQL

# Test database query
python manage.py shell
>>> from user.models import Member
>>> Member.objects.count()
0
>>> exit()
```

## Step 12: Document What We've Accomplished

Once everything is working, we'll:
1. Create a feature branch
2. Update documentation
3. Create technical note for Phase 9
4. Update PROJECT_HISTORY.md
5. Update SESSION_START_PROMPT.md
6. Commit and create PR

## Security Checklist

Before proceeding to production deployment:

- [ ] All production secrets stored in AWS Secrets Manager (not in code)
- [ ] Stripe production keys configured (not test keys)
- [ ] Email SMTP credentials configured and tested
- [ ] Database passwords are strong (32+ characters, auto-generated)
- [ ] Django SECRET_KEY is unique for production (50+ characters)
- [ ] RDS security group only allows access from backend application
- [ ] No temporary security group rules left open
- [ ] Bastion host secured (if created)
- [ ] AWS IAM permissions follow least privilege principle
- [ ] CloudWatch alarms configured and email verified
- [ ] RDS automated backups enabled
- [ ] RDS deletion protection enabled

## Troubleshooting

### Issue: Cannot connect to RDS from local machine

**Cause**: RDS is in private subnet and security group blocks external access.

**Solution**:
1. Create SSH tunnel via bastion host (recommended)
2. Temporarily modify security group to allow your IP (not for production!)
3. Use AWS Cloud9 or AWS Systems Manager Session Manager

### Issue: "password authentication failed for user django_app"

**Cause**: Password mismatch between Secrets Manager and what was used to create RDS.

**Solution**: Verify password with:
```bash
aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --query SecretString --output text | jq -r '.password'
```

### Issue: "permission denied to create database"

**Cause**: Using `django_app` user which doesn't have CREATEDB privilege.

**Solution**: Use `postgres` master user to create databases, then switch to `django_app` for migrations.

### Issue: boto3.exceptions.NoCredentialsError

**Cause**: AWS credentials not configured on local machine.

**Solution**:
```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

## Next Steps After Phase 9

Once Phase 9 is complete, the next phases will be:

### Immediate Pre-Launch Tasks (Before Real Users)

1. **Migrate to AWS SES** (1-2 weeks before user launch)
   - **Timeline**: Start 1-2 weeks before real user launch
   - **Why**: Professional email infrastructure for production scale
   - **Steps**:
     - Set up AWS SES in us-east-1 region
     - Verify MosaicMeshAI.com domain ownership
     - Configure DNS records (SPF, DKIM, DMARC)
     - Request production access (1-2 day automated approval)
     - Create SMTP credentials
     - Update AWS Secrets Manager (4 values):
       - `email_host`: `smtp.gmail.com` → `email-smtp.us-east-1.amazonaws.com`
       - `email_port`: `587` (stays same)
       - `email_user`: Gmail address → AWS SES SMTP username
       - `email_password`: Gmail app password → AWS SES SMTP password
     - Test email delivery
     - Monitor bounce/complaint rates
   - **Benefits**: 50,000 emails/day, detailed metrics, $0.10 per 1,000 emails
   - **Cost**: Free tier: 62,000 emails/month for first 12 months

2. **Create Stripe Account and Configure Production Keys**
   - **Timeline**: Before accepting real payments
   - **Steps**:
     - Sign up at https://dashboard.stripe.com/
     - Complete business verification
     - Configure payment methods and settings
     - Get production API keys (sk_live_* and pk_live_*)
     - Update AWS Secrets Manager with real Stripe keys
     - Test payment flow with Stripe test mode first
     - Switch to live mode for production
   - **Important**: Keep test keys in local dev, use live keys only in production

### Future Production Deployment Phases

3. **Phase 10: Container Deployment to AWS**
   - Build production Docker images
   - Set up ECS or EC2 deployment
   - Configure Application Load Balancer
   - Set up S3 for static files and media uploads
   - Configure CloudFront CDN
   - SSL/TLS certificates via AWS Certificate Manager

4. **Phase 11: CI/CD Pipeline**
   - GitHub Actions or AWS CodePipeline
   - Automated testing on push (740 tests)
   - Automated deployment to staging/production
   - Blue-green deployment strategy
   - Automated rollback on failure

5. **Phase 12: Production Hardening & Monitoring**
   - AWS WAF (Web Application Firewall)
   - Enhanced CloudWatch dashboards
   - Django logs integration with CloudWatch Logs
   - Performance optimization (caching, query optimization)
   - Automated RDS snapshots and backup testing
   - Security audit and penetration testing
   - Load testing and capacity planning

## References

- Phase 8 Documentation: `docs/technical-notes/2025-11-20-aws-rds-django-integration.md`
- AWS RDS Deployment Plan: `docs/technical-notes/2025-11-19-aws-rds-deployment-plan.md`
- PostgreSQL Migration: `docs/technical-notes/2025-11-18-postgresql-migration-phases-2-5-complete.md`
- Django Production Settings: `StartupWebApp/StartupWebApp/settings_production.py`
- Infrastructure Scripts: `scripts/infra/`
