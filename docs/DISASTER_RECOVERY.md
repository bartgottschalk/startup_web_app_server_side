# Disaster Recovery Runbook

**Last Updated**: December 27, 2025
**Owner**: Bart Gottschalk
**RTO (Recovery Time Objective)**: 4 hours
**RPO (Recovery Point Objective)**: 24 hours (daily automated backups)

---

## Table of Contents

1. [Overview](#overview)
2. [Backup Strategy](#backup-strategy)
3. [Disaster Scenarios](#disaster-scenarios)
4. [Recovery Procedures](#recovery-procedures)
   - [Database Restore from RDS Snapshot](#scenario-1-database-corruption-or-data-loss)
   - [Application Rollback (Bad Deployment)](#scenario-2-bad-application-deployment)
   - [Complete Infrastructure Failure](#scenario-3-complete-aws-infrastructure-failure)
5. [Testing & Verification](#testing--verification)
6. [Contact Information](#contact-information)

---

## Overview

StartupWebApp runs on AWS with the following critical components:
- **Database**: RDS PostgreSQL (Multi-AZ, automated backups)
- **Backend**: ECS Fargate with auto-scaling
- **Frontend**: S3 + CloudFront CDN
- **Load Balancer**: Application Load Balancer (ALB)
- **Secrets**: AWS Secrets Manager

**Current Infrastructure**: All resources in `us-east-1` region

---

## Backup Strategy

### Automated Backups (In Place)

#### RDS Database Backups
- **Automated Daily Backups**: Enabled
- **Retention Period**: 7 days
- **Backup Window**: 3:00-4:00 AM EST (automatic)
- **Snapshot Location**: AWS RDS snapshots (same region)
- **Point-in-Time Recovery**: Available (up to 7 days back)
- **Multi-AZ**: Enabled (automatic failover to standby)

#### Application Code Backups
- **Source of Truth**: GitHub repository
  - Backend: `https://github.com/bartgottschalk/startup_web_app_server_side`
  - Frontend: `https://github.com/bartgottschalk/startup_web_app_client_side`
- **Branches**: `master` branch is production (auto-deploy enabled)
- **Container Images**: ECR retains images with tags

#### Infrastructure as Code
- **Location**: `scripts/infra/` directory in backend repository
- **Resource IDs**: `scripts/infra/aws-resources.env`
- **Backup**: Committed to Git, pushed to GitHub

---

## Disaster Scenarios

### Scenario 1: Database Corruption or Data Loss
**Likelihood**: Low
**Impact**: High
**RTO**: 2-4 hours
**RPO**: Up to 24 hours (last automated backup)

### Scenario 2: Bad Application Deployment
**Likelihood**: Medium
**Impact**: Medium-High
**RTO**: 15-30 minutes
**RPO**: 0 (no data loss, rollback to previous version)

### Scenario 3: Complete AWS Infrastructure Failure
**Likelihood**: Very Low
**Impact**: Critical
**RTO**: 6-8 hours
**RPO**: Up to 24 hours

### Scenario 4: Accidental Resource Deletion
**Likelihood**: Low
**Impact**: Medium-High
**RTO**: 1-4 hours (depends on resource)
**RPO**: Varies by resource

---

## Recovery Procedures

## Scenario 1: Database Corruption or Data Loss

### When to Use
- Accidental data deletion (DROP TABLE, DELETE without WHERE, etc.)
- Database corruption
- Need to recover data from a specific point in time
- Security incident requiring data restore

### Prerequisites
- AWS CLI configured with appropriate credentials
- Access to `scripts/infra/aws-resources.env`
- SSH access to bastion host (for verification)

---

### Step 1: Identify the Recovery Point

**List Available RDS Snapshots:**
```bash
aws rds describe-db-snapshots \
  --db-instance-identifier startupwebapp-multi-tenant-prod \
  --snapshot-type automated \
  --query 'DBSnapshots[*].[DBSnapshotIdentifier,SnapshotCreateTime,Status]' \
  --output table
```

**Example Output:**
```
-----------------------------------------------------------------------
|                      DescribeDBSnapshots                           |
+-------------------------------------------+------------------------+
|  rds:startupwebapp-multi-tenant-prod-... | 2025-12-27T08:00:00Z  |
|  rds:startupwebapp-multi-tenant-prod-... | 2025-12-26T08:00:00Z  |
|  rds:startupwebapp-multi-tenant-prod-... | 2025-12-25T08:00:00Z  |
+-------------------------------------------+------------------------+
```

**Note the snapshot identifier** for the restore point you want.

---

### Step 2: Restore RDS Snapshot to New Instance

**IMPORTANT**: Do NOT overwrite production database. Restore to a new instance first, verify data, then swap.

```bash
# Set variables
SNAPSHOT_ID="rds:startupwebapp-multi-tenant-prod-2025-12-27-08-00"  # Replace with actual snapshot ID
NEW_DB_INSTANCE_ID="startupwebapp-multi-tenant-restore-$(date +%Y%m%d)"
DB_SUBNET_GROUP="startupwebapp-db-subnet-group"
DB_SECURITY_GROUP="sg-046fd8c6f0c42a7a6"  # From aws-resources.env

# Restore snapshot to new RDS instance
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier "$NEW_DB_INSTANCE_ID" \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --db-instance-class db.t4g.micro \
  --db-subnet-group-name "$DB_SUBNET_GROUP" \
  --vpc-security-group-ids "$DB_SECURITY_GROUP" \
  --no-multi-az \
  --publicly-accessible false \
  --tags "Key=Name,Value=$NEW_DB_INSTANCE_ID" \
         "Key=Environment,Value=recovery" \
         "Key=Application,Value=StartupWebApp"
```

**Monitor restore progress:**
```bash
aws rds describe-db-instances \
  --db-instance-identifier "$NEW_DB_INSTANCE_ID" \
  --query 'DBInstances[0].[DBInstanceStatus,Endpoint.Address]' \
  --output table
```

**Wait for status**: `available` (typically 10-15 minutes)

---

### Step 3: Verify Restored Data

**Connect to bastion host:**
```bash
# Get bastion public IP
aws ec2 describe-instances \
  --instance-ids i-0d8d746dd8059de2c \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text

# SSH to bastion (replace IP)
ssh -i ~/.ssh/startupwebapp-bastion.pem ec2-user@<BASTION_IP>
```

**On bastion host, connect to restored database:**
```bash
# Get restored DB endpoint
RESTORED_DB_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier startupwebapp-multi-tenant-restore-YYYYMMDD \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

# Get database password from Secrets Manager
DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --query SecretString \
  --output text | jq -r .password)

# Connect to restored database
psql -h $RESTORED_DB_ENDPOINT -U postgres -d startupwebapp_prod
```

**Verify data integrity:**
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('startupwebapp_prod'));

-- Check table counts
SELECT
  schemaname,
  tablename,
  n_tup_ins - n_tup_del as row_count
FROM pg_stat_user_tables
ORDER BY tablename;

-- Check critical tables
SELECT COUNT(*) FROM order_order;
SELECT COUNT(*) FROM user_member;
SELECT COUNT(*) FROM order_product;

-- Check most recent orders (verify data freshness)
SELECT id, created_date_time, order_status_id
FROM order_order
ORDER BY created_date_time DESC
LIMIT 10;

-- Exit psql
\q
```

---

### Step 4: Swap Databases (Production Cutover)

**⚠️ WARNING: This will cause ~2-3 minutes of downtime**

#### Option A: Rename Databases (Recommended - Faster)

**On production database:**
```bash
# Connect to PRODUCTION database
PROD_DB_ENDPOINT="startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com"
psql -h $PROD_DB_ENDPOINT -U postgres -d postgres

# Terminate existing connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname IN ('startupwebapp_prod', 'healthtech_prod', 'fintech_prod');

# Rename current databases (backup)
ALTER DATABASE startupwebapp_prod RENAME TO startupwebapp_prod_old;
ALTER DATABASE healthtech_prod RENAME TO healthtech_prod_old;
ALTER DATABASE fintech_prod RENAME TO fintech_prod_old;

\q
```

**On restored database:**
```bash
# Connect to RESTORED database
psql -h $RESTORED_DB_ENDPOINT -U postgres -d postgres

# Rename restored databases to production names
ALTER DATABASE startupwebapp_prod RENAME TO startupwebapp_prod_new;
ALTER DATABASE healthtech_prod RENAME TO healthtech_prod_new;
ALTER DATABASE fintech_prod RENAME TO fintech_prod_new;

\q
```

**WAIT - Don't do this!** Better approach: Update application to point to restored database.

#### Option B: Update Application Connection (Recommended - Zero Data Loss)

**Update Secrets Manager with restored DB endpoint:**
```bash
# Get current secret value
CURRENT_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --query SecretString \
  --output text)

# Update host to restored DB endpoint (replace YYYYMMDD)
NEW_SECRET=$(echo $CURRENT_SECRET | jq \
  --arg host "startupwebapp-multi-tenant-restore-YYYYMMDD.cqbgoe8omhyh.us-east-1.rds.amazonaws.com" \
  '.host = $host')

# Update secret
aws secretsmanager update-secret \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --secret-string "$NEW_SECRET"
```

**Restart ECS tasks to pick up new secret:**
```bash
# Force new deployment (restarts tasks)
aws ecs update-service \
  --cluster startupwebapp-cluster \
  --service startupwebapp-service \
  --force-new-deployment

# Monitor deployment
aws ecs describe-services \
  --cluster startupwebapp-cluster \
  --services startupwebapp-service \
  --query 'services[0].[serviceName,runningCount,desiredCount,deployments[0].status]'
```

**Wait for deployment**: Tasks will restart with new DB connection (2-3 minutes)

---

### Step 5: Verify Application Recovery

**Health Check:**
```bash
curl -I https://startupwebapp-api.mosaicmeshai.com/order/products
# Should return: HTTP/2 200
```

**Test Critical Functionality:**
1. Visit: `https://startupwebapp.mosaicmeshai.com`
2. Browse products
3. Add to cart
4. View cart (confirms database read/write)
5. Check Django Admin: `https://startupwebapp-api.mosaicmeshai.com/admin/`

**Check CloudWatch Logs:**
```bash
aws logs tail /ecs/startupwebapp-service --follow
# Should see no database connection errors
```

---

### Step 6: Cleanup Old Database (After 24-48 Hours)

**⚠️ ONLY after confirming restored database is working correctly**

**Delete old production database:**
```bash
# Create final snapshot before deletion (safety)
aws rds create-db-snapshot \
  --db-instance-identifier startupwebapp-multi-tenant-prod \
  --db-snapshot-identifier startupwebapp-final-backup-$(date +%Y%m%d)

# Wait for snapshot to complete
aws rds describe-db-snapshots \
  --db-snapshot-identifier startupwebapp-final-backup-$(date +%Y%m%d) \
  --query 'DBSnapshots[0].Status'

# Delete old production database
aws rds delete-db-instance \
  --db-instance-identifier startupwebapp-multi-tenant-prod \
  --skip-final-snapshot \
  --delete-automated-backups
```

**Rename restored database to production ID:**
```bash
aws rds modify-db-instance \
  --db-instance-identifier startupwebapp-multi-tenant-restore-YYYYMMDD \
  --new-db-instance-identifier startupwebapp-multi-tenant-prod \
  --apply-immediately
```

**Update Secrets Manager back to production endpoint:**
```bash
# Update secret with production endpoint
NEW_SECRET=$(echo $CURRENT_SECRET | jq \
  --arg host "startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com" \
  '.host = $host')

aws secretsmanager update-secret \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --secret-string "$NEW_SECRET"

# Restart ECS tasks
aws ecs update-service \
  --cluster startupwebapp-cluster \
  --service startupwebapp-service \
  --force-new-deployment
```

**Update aws-resources.env:**
```bash
cd scripts/infra
# Edit aws-resources.env manually or regenerate:
./show-resources.sh > aws-resources.env
git add aws-resources.env
git commit -m "docs: Update RDS endpoint after database restore"
git push
```

---

## Scenario 2: Bad Application Deployment

### When to Use
- Application crashes after deployment
- Critical bug deployed to production
- Breaking changes in new code
- Failed database migration

### Rollback Options

#### Option A: Rollback via GitHub Actions (Recommended - Fastest)

**Use the manual rollback workflow:**

1. Go to GitHub Actions: `https://github.com/bartgottschalk/startup_web_app_server_side/actions`
2. Select **"Manual Rollback"** workflow (if exists)
3. Click **"Run workflow"**
4. Enter the ECR image tag to rollback to (e.g., `sha-abc1234`)
5. Click **"Run workflow"**

**If rollback workflow doesn't exist**, use Option B.

---

#### Option B: Manual Rollback via AWS CLI

**Step 1: Find the previous working image:**
```bash
# List recent ECR images
aws ecr describe-images \
  --repository-name startupwebapp-backend \
  --query 'sort_by(imageDetails,& imagePushedAt)[-10:].[imageTags[0],imagePushedAt]' \
  --output table

# Note the image tag BEFORE the bad deployment (e.g., sha-abc1234)
```

**Step 2: Get current task definition:**
```bash
aws ecs describe-task-definition \
  --task-definition startupwebapp-service-task \
  --query 'taskDefinition' \
  > task-definition.json
```

**Step 3: Update task definition with previous image:**
```bash
# Get previous working image
PREVIOUS_IMAGE="853463362083.dkr.ecr.us-east-1.amazonaws.com/startupwebapp-backend:sha-abc1234"

# Update task definition JSON (replace image)
jq --arg img "$PREVIOUS_IMAGE" \
  '.containerDefinitions[0].image = $img | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' \
  task-definition.json > task-definition-rollback.json

# Register new task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition-rollback.json
```

**Step 4: Update service with rolled-back task definition:**
```bash
# Update service
aws ecs update-service \
  --cluster startupwebapp-cluster \
  --service startupwebapp-service \
  --task-definition startupwebapp-service-task \
  --force-new-deployment

# Monitor deployment
watch -n 5 'aws ecs describe-services \
  --cluster startupwebapp-cluster \
  --services startupwebapp-service \
  --query "services[0].[deployments[0].status,runningCount,desiredCount]"'
```

**Step 5: Verify rollback:**
```bash
# Check health
curl -I https://startupwebapp-api.mosaicmeshai.com/order/products

# Check logs
aws logs tail /ecs/startupwebapp-service --follow
```

---

#### Option C: Rollback Database Migration (If Migration Failed)

**If bad deployment included database migration:**

```bash
# Connect to database via bastion
ssh -i ~/.ssh/startupwebapp-bastion.pem ec2-user@<BASTION_IP>

# Get DB password
DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --query SecretString \
  --output text | jq -r .password)

# Connect to database
psql -h startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com \
  -U postgres -d startupwebapp_prod
```

**Check applied migrations:**
```sql
SELECT id, app, name, applied
FROM django_migrations
ORDER BY applied DESC
LIMIT 10;
```

**Manually rollback migration** (if Django doesn't support automatic rollback):
```sql
-- Delete migration record
DELETE FROM django_migrations
WHERE app = 'order' AND name = '0006_problematic_migration';

-- Manually undo migration changes (depends on migration)
-- DROP TABLE if migration created table
-- ALTER TABLE if migration added column
-- etc.
```

**Better approach**: Restore database from snapshot before migration (see Scenario 1)

---

## Scenario 3: Complete AWS Infrastructure Failure

### When to Use
- AWS region outage
- Complete account compromise
- All resources accidentally deleted
- Need to rebuild from scratch

### Recovery Steps

**Prerequisites:**
- Access to GitHub repositories (source of truth)
- AWS CLI configured
- `scripts/infra/` directory from Git

**Estimated Time**: 6-8 hours

---

**Step 1: Recreate VPC and Network Infrastructure (1 hour)**
```bash
cd scripts/infra

# Create VPC
./create-vpc.sh

# Create security groups
./create-security-groups.sh

# Create NAT Gateway
./create-nat-gateway.sh
```

---

**Step 2: Restore Database from Latest Snapshot (2 hours)**
```bash
# Find latest snapshot (if snapshots survived)
aws rds describe-db-snapshots \
  --snapshot-type automated \
  --query 'sort_by(DBSnapshots,& SnapshotCreateTime)[-1].[DBSnapshotIdentifier,SnapshotCreateTime]'

# If snapshots exist, restore using Scenario 1 procedure
# If no snapshots, rebuild from data migrations (see below)
```

**If no snapshots available** (worst case):
```bash
# Create new RDS instance
./create-rds.sh

# Restore secrets
./create-secrets.sh

# Run migrations to recreate schema
# Deploy application (Step 3)
# Manually recreate critical reference data from Git (seed data migrations)
# ⚠️ User data and orders would be lost
```

---

**Step 3: Recreate ECS Infrastructure (2 hours)**
```bash
# Create ECR repository
./create-ecr.sh

# Build and push Docker image
cd ../..
docker build -t startupwebapp-backend --target production .
docker tag startupwebapp-backend:latest \
  853463362083.dkr.ecr.us-east-1.amazonaws.com/startupwebapp-backend:recovery
docker push 853463362083.dkr.ecr.us-east-1.amazonaws.com/startupwebapp-backend:recovery

# Create ECS cluster
cd scripts/infra
./create-ecs-cluster.sh

# Create task roles
./create-ecs-task-role.sh

# Create task definition
./create-ecs-service-task-definition.sh
```

---

**Step 4: Recreate Load Balancer and Service (1-2 hours)**
```bash
# Create ACM certificate (requires manual DNS validation)
./create-acm-certificate.sh

# Create ALB
./create-alb.sh

# Create HTTPS listener
./create-alb-https-listener.sh

# Create ECS service
./create-ecs-service.sh

# Create auto-scaling
./create-ecs-autoscaling.sh
```

---

**Step 5: Recreate Frontend Hosting (1 hour)**
```bash
# Create S3 bucket and CloudFront
./create-frontend-hosting.sh

# Deploy frontend files
cd ../../../startup_web_app_client_side
aws s3 sync . s3://startupwebapp-frontend-production/ \
  --exclude ".*" \
  --exclude "node_modules/*" \
  --exclude "playwright-tests/*"
```

---

**Step 6: Update DNS (Manual - 5-10 minutes)**
- Login to Namecheap
- Update CNAME records:
  - `startupwebapp-api.mosaicmeshai.com` → New ALB DNS name
  - `startupwebapp.mosaicmeshai.com` → New CloudFront distribution

---

**Step 7: Verify Recovery**
```bash
# Wait for DNS propagation (5-10 minutes)
dig startupwebapp-api.mosaicmeshai.com
dig startupwebapp.mosaicmeshai.com

# Test application
curl https://startupwebapp-api.mosaicmeshai.com/order/products
curl https://startupwebapp.mosaicmeshai.com

# Full browser test
open https://startupwebapp.mosaicmeshai.com
```

---

## Scenario 4: Accidental Resource Deletion

### When to Use
- Accidentally deleted ECS service
- Accidentally deleted S3 bucket
- Accidentally deleted security group
- Any resource accidentally deleted

### Recovery by Resource Type

#### ECS Service Deleted
```bash
cd scripts/infra
./create-ecs-service.sh
# Service will recreate with same configuration from script
```

#### ALB Deleted
```bash
./create-alb.sh
./create-alb-https-listener.sh
# Update DNS CNAMEs to new ALB DNS name
```

#### RDS Database Deleted
```bash
# If final snapshot was created:
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier startupwebapp-multi-tenant-prod \
  --db-snapshot-identifier <snapshot-id>

# If no snapshot: Follow Scenario 3 database recovery
```

#### S3 Bucket Deleted
```bash
./create-frontend-hosting.sh
# Re-deploy frontend files from Git
```

#### Security Group Deleted
```bash
./create-security-groups.sh
# May need to update references in other resources
```

---

## Testing & Verification

### Recommended Testing Schedule

**Quarterly (Every 3 Months):**
- ✅ List available RDS snapshots
- ✅ Verify automated backups are running
- ✅ Review and update this runbook

**Annual (Once Per Year):**
- ✅ Perform full database restore test (Scenario 1)
- ✅ Verify all infrastructure scripts still work
- ✅ Update contact information

---

### Test Procedure: Database Restore Verification

**Run this test once per year** (suggested: January)

1. Follow Scenario 1 steps 1-3 (restore to new instance)
2. Verify data integrity (Step 3)
3. **DO NOT proceed to Step 4** (production cutover)
4. Delete test restore instance:
   ```bash
   aws rds delete-db-instance \
     --db-instance-identifier startupwebapp-multi-tenant-restore-YYYYMMDD \
     --skip-final-snapshot
   ```
5. Document test results in runbook

**Last Test**: _Not yet performed_
**Next Test**: January 2026
**Test Results**: _TBD_

---

## Contact Information

**Primary Contact:**
- Name: Bart Gottschalk
- Email: bart@mosaicmeshai.com

**AWS Account:**
- Account ID: 853463362083
- Region: us-east-1

**Critical Services:**
- GitHub: https://github.com/bartgottschalk
- Email Alerts: CloudWatch → SNS → bart@mosaicmeshai.com

**Emergency Escalation:**
- AWS Support: https://console.aws.amazon.com/support/home
- Stripe Support: https://support.stripe.com

---

## Appendix: RTO/RPO Definitions

**RTO (Recovery Time Objective)**: Maximum acceptable time to restore service after disaster
- **Target**: 4 hours
- **Best Case**: 30 minutes (bad deployment rollback)
- **Worst Case**: 8 hours (complete infrastructure rebuild)

**RPO (Recovery Point Objective)**: Maximum acceptable data loss measured in time
- **Target**: 24 hours (daily RDS automated backups)
- **Best Case**: 0 hours (point-in-time recovery available up to 7 days)
- **Worst Case**: 24 hours (if restore from yesterday's backup)

---

**Document Version**: 1.0
**Created**: December 27, 2025
**Next Review**: January 2026
