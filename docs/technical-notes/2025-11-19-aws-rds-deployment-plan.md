# AWS RDS PostgreSQL Deployment Plan - Phase 7

**Date**: November 19, 2025
**Status**: 🔧 IN PROGRESS - Infrastructure as Code Development
**Branch**: `feature/aws-infrastructure-setup`
**Priority**: HIGH - Production database deployment
**Prerequisites**: Phases 1-6 complete (Local PostgreSQL working, all tests passing)

## Executive Summary

This document outlines Phase 7 of the PostgreSQL migration: deploying a production-ready PostgreSQL 16.x instance on AWS RDS with multi-tenant architecture. This will enable multiple forked applications to share a single RDS instance cost-effectively.

**Objective**: Deploy AWS RDS PostgreSQL 16.x with multi-tenant support
**Cost**: $26/month (db.t4g.small for 3-5 experimental forks)
**Timeline**: 4-6 hours (includes setup, testing, documentation)
**Risk**: Low (local PostgreSQL already validated, all 740 tests passing)

## Infrastructure as Code Approach

**IMPORTANT WORKFLOW RULE**: All AWS infrastructure scripts will be executed manually in separate terminal windows. Infrastructure setup scripts will NOT be run within Claude Code chat sessions.

**Rationale:**
- Infrastructure operations are sensitive and require manual oversight
- Costs can be incurred with AWS resource creation
- Better control and visibility over what's being created/destroyed
- Allows for review and confirmation before execution
- Easier debugging if issues occur

**Implementation:**
- All infrastructure scripts located in: `scripts/infra/`
- Scripts are idempotent (safe to run multiple times)
- Clear naming convention: `create-*.sh` for provisioning, `destroy-*.sh` for teardown
- Each script outputs created resource IDs for tracking
- Resource IDs stored in `scripts/infra/aws-resources.env` for reference

**Pre-Deployment Setup Completed (November 19, 2025):**
- ✅ AWS CLI installed (version 2.31.39)
- ✅ IAM user created: `startupwebapp-admin`
- ✅ AWS CLI configured (region: us-east-1, output: json)
- ✅ Credentials verified and working
- ✅ Feature branch created: `feature/aws-infrastructure-setup`
- ✅ Infrastructure scripts directory created: `scripts/infra/`

**Pre-Deployment Questions Answered:**
1. ✅ **AWS Account Access**: Yes, have Console access. Created IAM user `startupwebapp-admin`. AWS CLI configured.
2. ✅ **VPC Selection**: Create new VPC (`startupwebapp-vpc`) with proper subnet isolation
3. ⏳ **Bastion Host**: TBD - Do you have a bastion host for database access? Or should we use Cloud9/EC2?
4. ⏳ **Domain Names**: TBD - What domains will each fork use? (for ALLOWED_HOSTS)
5. ⏳ **Email Address**: TBD - What email should receive CloudWatch alerts?
6. ⏳ **Budget Approval**: TBD - Confirmed $26/month for db.t4g.small + ~$3-4 monitoring costs?
7. ⏳ **Timeline**: TBD - Ready to proceed with deployment now?

## Current State

### Completed (Phases 1-6)
- ✅ Phase 1: FloatField→DecimalField conversion (November 17, 2025)
- ✅ Phase 2: Docker PostgreSQL 16-alpine setup (November 18, 2025)
- ✅ Phase 3: Django environment-based configuration (November 18, 2025)
- ✅ Phase 4: Fresh PostgreSQL migrations - 57 tables (November 18, 2025)
- ✅ Phase 5: PostgreSQL test compatibility - 740 tests passing (November 18, 2025)
- ✅ Phase 6: Merged to master via PR #32 (November 19, 2025)

### Local Environment Status
- **Database**: PostgreSQL 16-alpine running in Docker
- **Databases**: startupwebapp_dev, healthtech_dev, fintech_dev
- **Test Suite**: 740/740 passing (712 unit + 28 functional)
- **Linting**: Zero errors (backend + frontend)
- **Configuration**: Environment-based database selection working

### What's Next
Phase 7 will replicate this working local setup to AWS RDS for production use.

## AWS RDS Configuration

### Instance Specifications

**Database Engine:**
- **Engine**: PostgreSQL 16.x (latest minor version)
- **Edition**: Amazon RDS for PostgreSQL (not Aurora)
- **License**: PostgreSQL License (open source)

**Instance Class:**
- **Type**: db.t4g.small
- **vCPU**: 2 vCPU (ARM-based Graviton2)
- **Memory**: 2 GB RAM
- **Network**: Up to 2085 Mbps
- **Cost**: ~$26/month (us-east-1)

**Rationale for db.t4g.small:**
- Supports 100 simultaneous connections (sufficient for 3-5 low-traffic apps)
- Cost-effective for multi-tenant experimentation phase
- Easy to scale up to db.t4g.medium (4 GB RAM, $52/month) when needed
- ARM-based (Graviton2) provides better price/performance than x86

**Storage Configuration:**
- **Type**: General Purpose SSD (gp3)
- **Size**: 20 GB (starting size)
- **IOPS**: 3000 baseline (included with gp3)
- **Throughput**: 125 MB/s (included with gp3)
- **Auto-scaling**: Enabled (up to 100 GB)
- **Auto-scaling threshold**: 90% capacity

**Backup Configuration:**
- **Automated backups**: Enabled
- **Retention period**: 7 days
- **Backup window**: 03:00-04:00 AM UTC (low traffic period)
- **Copy tags to snapshots**: Enabled
- **Backup storage**: Included in pricing up to database size

**Maintenance Configuration:**
- **Auto minor version upgrade**: Enabled (security patches)
- **Maintenance window**: Sunday 04:00-05:00 AM UTC
- **Notification**: SNS topic for maintenance events

**High Availability:**
- **Multi-AZ**: Disabled initially (can enable later)
- **Rationale**: Cost savings for experimental phase
- **Upgrade path**: Enable Multi-AZ when any fork reaches production traffic

**Monitoring & Logs:**
- **Enhanced monitoring**: Enabled (60-second granularity)
- **Performance Insights**: Enabled (7-day retention free tier)
- **Log exports**: postgresql (query logs), error logs
- **CloudWatch Logs**: Enabled

### Multi-Tenant Database Setup

**Database Architecture:**
```
AWS RDS Instance: startupwebapp-multi-tenant-prod
├── postgres (default system database)
├── startupwebapp_prod (main application - production)
├── healthtech_experiment (fork #1 - experimental)
├── fintech_experiment (fork #2 - experimental)
├── edtech_experiment (fork #3 - future)
└── saas_experiment (fork #4 - future)
```

**Database Naming Convention:**
- Production apps: `{appname}_prod` (e.g., `startupwebapp_prod`)
- Experimental forks: `{vertical}_experiment` (e.g., `healthtech_experiment`)
- Testing databases: `{appname}_staging` (if needed)
- Archived databases: Keep backups in S3, not in RDS

**Initial Databases to Create:**
1. `startupwebapp_prod` - Main production application
2. `healthtech_experiment` - HealthTech fork (placeholder, ready for deployment)
3. `fintech_experiment` - FinTech fork (placeholder, ready for deployment)

**Database Creation Script:**
```sql
-- Connect to default postgres database
psql -h your-rds-endpoint.us-east-1.rds.amazonaws.com -U postgres -d postgres

-- Create databases
CREATE DATABASE startupwebapp_prod WITH ENCODING='UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';
CREATE DATABASE healthtech_experiment WITH ENCODING='UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';
CREATE DATABASE fintech_experiment WITH ENCODING='UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';

-- Create application user (if not using master user)
CREATE USER django_app WITH PASSWORD 'STRONG_PASSWORD_FROM_SECRETS_MANAGER';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE startupwebapp_prod TO django_app;
GRANT ALL PRIVILEGES ON DATABASE healthtech_experiment TO django_app;
GRANT ALL PRIVILEGES ON DATABASE fintech_experiment TO django_app;

-- Verify databases created
\l

-- Verify user permissions
\du
```

### Security Configuration

**Network Security:**
- **VPC**: Use existing VPC or create new dedicated VPC
- **Subnet Group**: Private subnets only (no public access)
- **Public accessibility**: No
- **VPC Security Group**: Create `rds-startupwebapp-sg`
  - Inbound rule: PostgreSQL (5432) from backend security group only
  - No outbound rules needed
  - Description: "PostgreSQL access for StartupWebApp multi-tenant backends"

**Security Group Configuration:**
```
Name: rds-startupwebapp-multi-tenant-sg
Description: PostgreSQL access for StartupWebApp and forks

Inbound Rules:
- Type: PostgreSQL (5432)
- Source: sg-xxxxx (backend-services security group)
- Description: Allow PostgreSQL from backend services

- Type: PostgreSQL (5432)
- Source: sg-yyyyy (bastion host security group)
- Description: Allow PostgreSQL from bastion for admin access

Outbound Rules:
- (Default: All traffic allowed)
```

**Access Control:**
- **Master username**: `postgres` (default, avoid using for application)
- **Application username**: `django_app` (created separately)
- **Password management**: AWS Secrets Manager
- **SSL/TLS**: Required (enforce SSL connections)
- **IAM authentication**: Disabled initially (can enable later)

**SSL Configuration:**
```python
# Django settings for SSL connection
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'sslmode': 'require',  # Require SSL connection
            'sslrootcert': '/path/to/rds-ca-2019-root.pem',  # AWS RDS CA certificate
        },
        # ... other settings
    }
}
```

**Parameter Group:**
- **Family**: postgres16
- **Name**: startupwebapp-postgres16-params
- **Parameters to customize**:
  - `shared_preload_libraries`: (default, can add extensions later)
  - `log_statement`: 'none' (production) or 'all' (debugging)
  - `log_min_duration_statement`: 1000 (log queries >1 second)
  - `max_connections`: 100 (default for db.t4g.small)

**Option Group:**
- **Engine**: postgres
- **Major version**: 16
- **Name**: default:postgres-16 (use default)

### AWS Secrets Manager Configuration

**Secret Structure:**
```json
{
  "name": "rds/startupwebapp/multi-tenant/master",
  "description": "PostgreSQL credentials for multi-tenant RDS instance",
  "secretString": {
    "engine": "postgresql",
    "host": "startupwebapp-multi-tenant-prod.xxxxxx.us-east-1.rds.amazonaws.com",
    "port": 5432,
    "username": "django_app",
    "password": "GENERATED_STRONG_PASSWORD_32_CHARS",
    "dbClusterIdentifier": "startupwebapp-multi-tenant-prod"
  },
  "tags": [
    {"Key": "Environment", "Value": "Production"},
    {"Key": "Application", "Value": "StartupWebApp"},
    {"Key": "Purpose", "Value": "MultiTenantDatabase"}
  ]
}
```

**Secret Rotation:**
- **Enable automatic rotation**: No initially
- **Rotation Lambda**: Create later if needed
- **Rationale**: Manual rotation acceptable during experimentation phase
- **Upgrade**: Enable rotation when forks reach production scale

**Access Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:role/backend-ecs-task-role"
      },
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:rds/startupwebapp/multi-tenant/master"
    }
  ]
}
```

## Implementation Steps

### Step 1: Pre-Deployment Checklist

**Verify Local Environment:**
- [ ] All 740 tests passing locally with PostgreSQL
- [ ] Zero linting errors (flake8 + ESLint)
- [ ] Docker PostgreSQL running successfully
- [ ] Multi-database configuration working locally
- [ ] Environment variables documented

**AWS Account Preparation:**
- [ ] AWS account access confirmed
- [ ] AWS CLI configured (`aws configure`)
- [ ] Appropriate IAM permissions for RDS creation
- [ ] VPC and subnets identified or created
- [ ] Security groups planned

**Cost Confirmation:**
- [ ] Budget approved: $26/month for db.t4g.small
- [ ] CloudWatch monitoring costs understood (~$3-5/month)
- [ ] Backup storage costs understood (included up to DB size)

### Step 2: Create RDS Instance

**Via AWS Console:**

1. Navigate to RDS → Databases → Create database
2. **Choose database creation method**: Standard create
3. **Engine options**:
   - Engine type: PostgreSQL
   - Version: PostgreSQL 16.x (latest minor version)
4. **Templates**: Free tier (if eligible) OR Production
5. **Settings**:
   - DB instance identifier: `startupwebapp-multi-tenant-prod`
   - Master username: `postgres`
   - Master password: Auto-generate (store in Secrets Manager)
6. **Instance configuration**:
   - DB instance class: Burstable classes → db.t4g.small
7. **Storage**:
   - Storage type: gp3
   - Allocated storage: 20 GB
   - Storage autoscaling: Enable (max 100 GB)
8. **Connectivity**:
   - VPC: Select your VPC
   - Subnet group: Create new or select existing
   - Public access: No
   - VPC security group: Create new `rds-startupwebapp-sg`
9. **Database authentication**: Password authentication
10. **Monitoring**:
    - Enable Enhanced monitoring: Yes (60 seconds)
    - Enable Performance Insights: Yes (7 days)
11. **Additional configuration**:
    - Initial database name: `postgres` (default)
    - Backup retention: 7 days
    - Backup window: 03:00-04:00 UTC
    - Maintenance window: Sun 04:00-05:00 UTC
    - Enable auto minor version upgrade: Yes
    - Enable deletion protection: Yes

12. **Create database** (takes 5-15 minutes)

**Via AWS CLI:**
```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier startupwebapp-multi-tenant-prod \
  --db-instance-class db.t4g.small \
  --engine postgres \
  --engine-version 16.x \
  --master-username postgres \
  --master-user-password "$(openssl rand -base64 32)" \
  --allocated-storage 20 \
  --storage-type gp3 \
  --max-allocated-storage 100 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name default \
  --backup-retention-period 7 \
  --preferred-backup-window 03:00-04:00 \
  --preferred-maintenance-window sun:04:00-sun:05:00 \
  --enable-cloudwatch-logs-exports postgresql \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::ACCOUNT_ID:role/rds-monitoring-role \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --no-publicly-accessible \
  --deletion-protection \
  --tags Key=Environment,Value=Production Key=Application,Value=StartupWebApp

# Wait for instance to be available
aws rds wait db-instance-available --db-instance-identifier startupwebapp-multi-tenant-prod

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier startupwebapp-multi-tenant-prod \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

### Step 3: Configure Security Groups

**Create Security Group:**
```bash
# Create security group
aws ec2 create-security-group \
  --group-name rds-startupwebapp-multi-tenant-sg \
  --description "PostgreSQL access for StartupWebApp backends" \
  --vpc-id vpc-xxxxx

# Add inbound rule for backend services
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 5432 \
  --source-group sg-yyyyy \
  --group-owner ACCOUNT_ID

# Add inbound rule for bastion host (optional, for admin access)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 5432 \
  --source-group sg-zzzzz \
  --group-owner ACCOUNT_ID
```

### Step 4: Store Credentials in Secrets Manager

**Create Secret:**
```bash
# Store RDS credentials in Secrets Manager
aws secretsmanager create-secret \
  --name rds/startupwebapp/multi-tenant/master \
  --description "PostgreSQL credentials for multi-tenant RDS" \
  --secret-string '{
    "engine": "postgresql",
    "host": "startupwebapp-multi-tenant-prod.xxxxxx.us-east-1.rds.amazonaws.com",
    "port": 5432,
    "username": "django_app",
    "password": "GENERATED_STRONG_PASSWORD"
  }' \
  --tags Key=Environment,Value=Production Key=Application,Value=StartupWebApp

# Retrieve secret (verify)
aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --query SecretString \
  --output text | jq .
```

### Step 5: Create Multi-Tenant Databases

**Connect to RDS:**
```bash
# Option 1: From bastion host
ssh -i key.pem ec2-user@bastion-host
psql -h startupwebapp-multi-tenant-prod.xxxxxx.us-east-1.rds.amazonaws.com -U postgres -d postgres

# Option 2: Via SSH tunnel from local machine
ssh -i key.pem -L 5432:startupwebapp-multi-tenant-prod.xxxxxx.us-east-1.rds.amazonaws.com:5432 ec2-user@bastion-host
psql -h localhost -U postgres -d postgres

# Option 3: From AWS Cloud9 or EC2 instance in same VPC
psql -h startupwebapp-multi-tenant-prod.xxxxxx.us-east-1.rds.amazonaws.com -U postgres -d postgres
```

**Create Databases and Users:**
```sql
-- Create application user
CREATE USER django_app WITH PASSWORD 'STRONG_PASSWORD_FROM_SECRETS_MANAGER';

-- Create databases with proper encoding
CREATE DATABASE startupwebapp_prod
  WITH ENCODING='UTF8'
  LC_COLLATE='en_US.UTF-8'
  LC_CTYPE='en_US.UTF-8'
  OWNER=django_app;

CREATE DATABASE healthtech_experiment
  WITH ENCODING='UTF8'
  LC_COLLATE='en_US.UTF-8'
  LC_CTYPE='en_US.UTF-8'
  OWNER=django_app;

CREATE DATABASE fintech_experiment
  WITH ENCODING='UTF8'
  LC_COLLATE='en_US.UTF-8'
  LC_CTYPE='en_US.UTF-8'
  OWNER=django_app;

-- Grant all privileges (django_app already owns databases)
GRANT ALL PRIVILEGES ON DATABASE startupwebapp_prod TO django_app;
GRANT ALL PRIVILEGES ON DATABASE healthtech_experiment TO django_app;
GRANT ALL PRIVILEGES ON DATABASE fintech_experiment TO django_app;

-- Verify databases created
\l

-- Verify user exists
\du

-- Test connection as django_app user
\c startupwebapp_prod django_app
\dt

-- Exit
\q
```

### Step 6: Update Django Configuration for AWS RDS

**Create Production Settings Module:**

Create `StartupWebApp/StartupWebApp/settings_production.py`:

```python
"""
Production settings for AWS deployment with RDS PostgreSQL
Uses AWS Secrets Manager for credential management
"""
import os
import json
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

# Import base settings
from .settings import *

# Override DEBUG for production
DEBUG = False

# Allowed hosts from environment
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# AWS Region
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

def get_secret(secret_name):
    """
    Retrieve secret from AWS Secrets Manager
    """
    client = boto3.client('secretsmanager', region_name=AWS_REGION)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise

# Retrieve database credentials from Secrets Manager
secret_name = os.environ.get('DB_SECRET_NAME', 'rds/startupwebapp/multi-tenant/master')
db_credentials = get_secret(secret_name)

# Database configuration for AWS RDS PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'startupwebapp_prod'),  # Fork-specific
        'USER': db_credentials['username'],
        'PASSWORD': db_credentials['password'],
        'HOST': db_credentials['host'],
        'PORT': db_credentials.get('port', 5432),
        'CONN_MAX_AGE': 600,  # Connection pooling (10 minutes)
        'OPTIONS': {
            'sslmode': 'require',  # Require SSL for security
            'connect_timeout': 10,  # Connection timeout
        },
    }
}

# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging configuration (CloudWatch)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Only log slow queries and errors
            'propagate': False,
        },
    },
}

# Static and Media files (S3)
# TODO: Configure S3 bucket for static/media files
# STATIC_URL = f'https://{S3_BUCKET}.s3.amazonaws.com/static/'
# MEDIA_URL = f'https://{S3_BUCKET}.s3.amazonaws.com/media/'
```

**Update requirements.txt for AWS:**
```
boto3==1.34.162  # AWS SDK for Python
```

**Docker Environment Variables for Production:**
```bash
# .env.production or docker-compose.production.yml
DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production
DATABASE_NAME=startupwebapp_prod  # Fork-specific
DB_SECRET_NAME=rds/startupwebapp/multi-tenant/master
AWS_REGION=us-east-1
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
LOG_LEVEL=INFO
```

### Step 7: Run Migrations on AWS RDS

**Test Connection First:**
```bash
# Set environment variables
export DATABASE_NAME=startupwebapp_prod
export DB_SECRET_NAME=rds/startupwebapp/multi-tenant/master
export AWS_REGION=us-east-1
export DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production

# Test database connection
python -c "
from django.db import connection
connection.ensure_connection()
print(f'Connected to: {connection.settings_dict[\"NAME\"]}')
print(f'Host: {connection.settings_dict[\"HOST\"]}')
"
```

**Run Migrations:**
```bash
# Run migrations for startupwebapp_prod
python manage.py migrate

# Verify tables created
python manage.py dbshell
\dt
\q

# Create superuser
python manage.py createsuperuser --username admin --email admin@yourdomain.com

# Verify admin user created
python manage.py shell
from django.contrib.auth.models import User
print(User.objects.count())
exit()
```

**Repeat for Each Fork Database:**
```bash
# HealthTech fork
export DATABASE_NAME=healthtech_experiment
python manage.py migrate
python manage.py createsuperuser --username admin_healthtech --email admin@healthtech.com

# FinTech fork
export DATABASE_NAME=fintech_experiment
python manage.py migrate
python manage.py createsuperuser --username admin_fintech --email admin@fintech.com
```

### Step 8: Monitoring and Alerts Setup

**CloudWatch Alarms:**
```bash
# CPU Utilization Alert (>70% for 5 minutes)
aws cloudwatch put-metric-alarm \
  --alarm-name rds-cpu-high-startupwebapp \
  --alarm-description "Alert when RDS CPU exceeds 70%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 70 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=DBInstanceIdentifier,Value=startupwebapp-multi-tenant-prod \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:rds-alerts

# Database Connections Alert (>80 connections)
aws cloudwatch put-metric-alarm \
  --alarm-name rds-connections-high-startupwebapp \
  --alarm-description "Alert when RDS connections exceed 80" \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=DBInstanceIdentifier,Value=startupwebapp-multi-tenant-prod \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:rds-alerts

# Free Storage Space Alert (<2 GB)
aws cloudwatch put-metric-alarm \
  --alarm-name rds-storage-low-startupwebapp \
  --alarm-description "Alert when RDS free storage below 2GB" \
  --metric-name FreeStorageSpace \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 2147483648 \
  --comparison-operator LessThanThreshold \
  --dimensions Name=DBInstanceIdentifier,Value=startupwebapp-multi-tenant-prod \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:rds-alerts

# Free Memory Alert (<500 MB)
aws cloudwatch put-metric-alarm \
  --alarm-name rds-memory-low-startupwebapp \
  --alarm-description "Alert when RDS free memory below 500MB" \
  --metric-name FreeableMemory \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 524288000 \
  --comparison-operator LessThanThreshold \
  --dimensions Name=DBInstanceIdentifier,Value=startupwebapp-multi-tenant-prod \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:rds-alerts
```

**SNS Topic for Alerts:**
```bash
# Create SNS topic
aws sns create-topic --name rds-alerts

# Subscribe email to topic
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:rds-alerts \
  --protocol email \
  --notification-endpoint your-email@domain.com

# Confirm subscription (check email and click confirm)
```

**CloudWatch Dashboard:**
```bash
# Create dashboard for RDS monitoring
aws cloudwatch put-dashboard \
  --dashboard-name StartupWebApp-RDS-MultiTenant \
  --dashboard-body file://rds-dashboard.json
```

Create `rds-dashboard.json`:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/RDS", "CPUUtilization", {"stat": "Average"}],
          [".", "DatabaseConnections", {"stat": "Average"}],
          [".", "FreeableMemory", {"stat": "Average"}],
          [".", "FreeStorageSpace", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "RDS Multi-Tenant Metrics",
        "yAxis": {"left": {"min": 0}}
      }
    }
  ]
}
```

### Step 9: Testing and Validation

**Database Connectivity Test:**
```python
# test_rds_connection.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'StartupWebApp.settings_production')
django.setup()

from django.db import connection

def test_connection():
    """Test RDS connection"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Connected to PostgreSQL: {version[0]}")

            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            print(f"✅ Current database: {db_name[0]}")

            cursor.execute("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';")
            table_count = cursor.fetchone()
            print(f"✅ Tables in public schema: {table_count[0]}")

            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == '__main__':
    test_connection()
```

**Run Test Suite Against RDS:**
```bash
# Set production environment
export DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production
export DATABASE_NAME=startupwebapp_prod
export DB_SECRET_NAME=rds/startupwebapp/multi-tenant/master

# Run unit tests
python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests --parallel=4

# Expected: 712 tests passing

# Run functional tests
bash /app/setup_docker_test_hosts.sh
HEADLESS=TRUE python manage.py test functional_tests

# Expected: 28 tests passing

# Total: 740/740 tests passing
```

**Manual Testing Checklist:**
- [ ] Admin panel accessible
- [ ] User registration works
- [ ] Login/logout works
- [ ] Shopping cart operations work
- [ ] Stripe payment test succeeds
- [ ] Email sending works
- [ ] Session persistence verified
- [ ] CSRF token validation works

### Step 10: Documentation

**Create Database Registry:**

Create `docs/DATABASE_REGISTRY.md`:
```markdown
# Multi-Tenant Database Registry

**RDS Instance**: startupwebapp-multi-tenant-prod.xxxxxx.us-east-1.rds.amazonaws.com
**Instance Class**: db.t4g.small (2 vCPU, 2 GB RAM)
**PostgreSQL Version**: 16.x
**Region**: us-east-1
**Cost**: $26/month (shared across all databases)

## Active Databases

| Database Name           | Application    | Status       | Owner | Deployed   | Notes |
|------------------------|----------------|--------------|-------|------------|-------|
| startupwebapp_prod     | StartupWebApp  | Production   | Bart  | 2025-11-19 | Main app |
| healthtech_experiment  | HealthTech     | Experimental | Bart  | TBD        | Placeholder |
| fintech_experiment     | FinTech        | Experimental | Bart  | TBD        | Placeholder |

## Connection Information

**Endpoint**: startupwebapp-multi-tenant-prod.xxxxxx.us-east-1.rds.amazonaws.com
**Port**: 5432
**SSL**: Required
**Credentials**: Stored in AWS Secrets Manager (`rds/startupwebapp/multi-tenant/master`)

## Resource Limits

- **Max Connections**: 100
- **Current Usage**: ~10-20 connections (1 app active)
- **Capacity**: 3-5 low-traffic apps comfortably
- **Scale Trigger**: >70 sustained connections → upgrade to db.t4g.medium

## Monitoring

- **CloudWatch Dashboard**: [StartupWebApp-RDS-MultiTenant](https://console.aws.amazon.com/cloudwatch/...)
- **Performance Insights**: Enabled (7-day retention)
- **Alerts**: SNS topic `rds-alerts` → your-email@domain.com

## Backup Policy

- **Automated Backups**: Daily at 03:00-04:00 UTC
- **Retention**: 7 days
- **Manual Snapshots**: Before major migrations/changes
- **Archive**: S3 bucket for long-term storage

## Management Commands

```bash
# List all databases
psql -h ENDPOINT -U django_app -d postgres -c "\l"

# Check connections per database
psql -h ENDPOINT -U django_app -d postgres -c "
  SELECT datname, count(*)
  FROM pg_stat_activity
  WHERE datname IS NOT NULL
  GROUP BY datname;
"

# Database sizes
psql -h ENDPOINT -U django_app -d postgres -c "
  SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
  FROM pg_database
  WHERE datname NOT IN ('postgres', 'template0', 'template1')
  ORDER BY pg_database_size(datname) DESC;
"

# Create new database for new fork
psql -h ENDPOINT -U django_app -d postgres -c "
  CREATE DATABASE newfork_experiment
  WITH ENCODING='UTF8'
  LC_COLLATE='en_US.UTF-8'
  LC_CTYPE='en_US.UTF-8'
  OWNER=django_app;
"

# Backup specific database
pg_dump -h ENDPOINT -U django_app -d healthtech_experiment | gzip > healthtech_backup_$(date +%Y%m%d).sql.gz

# Archive to S3
aws s3 cp healthtech_backup_20251119.sql.gz s3://your-bucket/database-backups/

# Drop database (CAREFUL!)
psql -h ENDPOINT -U django_app -d postgres -c "DROP DATABASE failed_experiment;"
```

## Contacts

- **DBA**: Bart Gottschalk (bart@yourdomain.com)
- **AWS Admin**: Bart Gottschalk
- **On-Call**: Bart Gottschalk

## Change Log

| Date       | Change | By | Notes |
|------------|--------|-----|-------|
| 2025-11-19 | Initial RDS deployment | Bart | Phase 7 complete |
```

**Update PROJECT_HISTORY.md:**
```markdown
## November 19, 2025 - AWS RDS PostgreSQL Deployment (Phase 7)

**Branch**: master (direct production deployment)
**Status**: ✅ Complete
**Phase**: PostgreSQL Migration - Production Deployment

Successfully deployed AWS RDS PostgreSQL 16.x with multi-tenant architecture. All databases created, migrations run successfully, full test suite passing against production database.

**Achievements:**
- ✅ Created db.t4g.small RDS instance ($26/month)
- ✅ Configured security groups and network access
- ✅ Stored credentials in AWS Secrets Manager
- ✅ Created 3 databases (startupwebapp_prod, healthtech_experiment, fintech_experiment)
- ✅ Ran migrations successfully (57 tables created per database)
- ✅ Created superuser accounts for each database
- ✅ Configured CloudWatch monitoring and alerts
- ✅ All 740 tests passing against AWS RDS
- ✅ Documentation complete (DATABASE_REGISTRY.md)

**Cost Efficiency:**
- Multi-tenant setup: $26/month for 3-5 apps
- Single app equivalent: $26/month per app
- **Savings: 67-80% during experimentation phase**

**Next Steps:**
- Deploy backend application to AWS (ECS/EC2)
- Configure environment variables for production
- Set up CI/CD pipeline for automated deployments
- Monitor performance and scale as needed
```

## Success Criteria

### Must Have (Blocking) ✅

- [ ] RDS instance created successfully (db.t4g.small, PostgreSQL 16.x)
- [ ] Security groups configured (private access only)
- [ ] Credentials stored in AWS Secrets Manager
- [ ] Three databases created (startupwebapp_prod, healthtech_experiment, fintech_experiment)
- [ ] Django can connect to RDS from local machine (via bastion/tunnel)
- [ ] Migrations run successfully on all databases
- [ ] Superuser created for each database
- [ ] CloudWatch monitoring enabled
- [ ] Database connectivity test passes
- [ ] DATABASE_REGISTRY.md created and up to date

### Should Have (Important) ⚙️

- [ ] All 740 tests passing against AWS RDS
- [ ] CloudWatch alarms configured (CPU, connections, storage, memory)
- [ ] SNS alerts configured for database issues
- [ ] Manual testing completed (login, cart, checkout, admin)
- [ ] Performance baseline established
- [ ] Backup verified (automated daily backups)
- [ ] PROJECT_HISTORY.md updated

### Nice to Have (Future) 💡

- [ ] Read replica for reporting (when traffic scales)
- [ ] Enhanced monitoring dashboard customized
- [ ] Automated backup testing
- [ ] Secret rotation enabled
- [ ] Multi-AZ enabled (when production-critical)

## Rollback Procedure

If critical issues are discovered after AWS RDS deployment:

1. **Identify Issue**: Document what's not working
2. **Revert Django Configuration**: Switch back to local PostgreSQL
   ```bash
   export DJANGO_SETTINGS_MODULE=StartupWebApp.settings
   # Use settings_secret.py with local PostgreSQL config
   ```
3. **Update Environment Variables**: Point to local Docker PostgreSQL
4. **Restart Services**: docker-compose restart backend
5. **Verify Tests**: Run full test suite locally (should pass)
6. **Investigate RDS Issue**: Debug without production pressure
7. **Fix and Redeploy**: Once issue resolved, redeploy to RDS

**Note**: This rollback only affects configuration. RDS instance and data remain intact for debugging.

## Cost Breakdown

### Monthly Costs
- **RDS db.t4g.small**: $26.00
- **Storage (20 GB)**: Included
- **Backup storage (≤20 GB)**: Included
- **Enhanced Monitoring**: $1.50 (60-second intervals)
- **Performance Insights (7 days)**: Free tier
- **CloudWatch Logs**: ~$1.00
- **Secrets Manager**: $0.40/secret
- **Data transfer out**: Minimal (<$1)

**Total Estimated Monthly Cost**: ~$29-30/month

### Annual Savings Opportunities
- **Reserved Instance (1 year)**: Save $8/month ($96/year)
- **Reserved Instance (3 year)**: Save $14/month ($168/year)

### Multi-Tenant Savings
- **Without Multi-Tenant**: 3 apps × $26 = $78/month
- **With Multi-Tenant**: 1 instance = $29/month
- **Savings**: $49/month ($588/year) for 3 apps

## Timeline

**Estimated Total Time**: 4-6 hours

| Task | Time | Notes |
|------|------|-------|
| Pre-deployment checklist | 30 min | Verify local setup |
| Create RDS instance | 30 min | Mostly AWS provisioning time |
| Configure security groups | 15 min | Network access setup |
| Store credentials | 15 min | Secrets Manager |
| Create databases | 30 min | 3 databases + users |
| Update Django config | 45 min | Production settings module |
| Run migrations | 30 min | All 3 databases |
| Testing | 60 min | Full test suite + manual |
| Monitoring setup | 45 min | CloudWatch alarms |
| Documentation | 45 min | DATABASE_REGISTRY.md |

**Total**: ~5 hours 20 minutes

## Risk Assessment

### Low Risk ✅
- **Schema compatibility**: Already validated locally
- **Django ORM**: Working perfectly with PostgreSQL locally
- **Test coverage**: 740 tests all passing locally
- **Network security**: Private subnet, security groups

### Medium Risk ⚠️
- **Connection pooling**: Monitor connection count (100 max)
- **Performance**: May differ from local (likely better)
- **Cost overruns**: Monitor usage, stay within budget
- **SSL configuration**: Ensure proper certificate setup

### Mitigation Strategies
1. **Test locally first**: Already done (Phases 1-6 complete)
2. **Staged rollout**: Test with non-production database first
3. **Monitoring**: CloudWatch alarms catch issues early
4. **Rollback plan**: Can revert to local PostgreSQL instantly
5. **Documentation**: Comprehensive DATABASE_REGISTRY.md

## Questions to Resolve

Before beginning deployment:

1. **AWS Account Access**: Do you have AWS Console access? AWS CLI configured?
2. **VPC Selection**: Which VPC should we use? Existing or create new?
3. **Bastion Host**: Do you have a bastion host for database access? Or should we use Cloud9/EC2?
4. **Domain Names**: What domains will each fork use? (for ALLOWED_HOSTS)
5. **Email Address**: What email should receive CloudWatch alerts?
6. **Budget Approval**: Confirmed $26/month for db.t4g.small?
7. **Timeline**: Ready to proceed now or schedule for later?

## Next Steps

After this document review:

1. **Answer questions above** (blockers for deployment)
2. **Approve deployment plan** (confirm approach is correct)
3. **Begin Step 1**: Pre-deployment checklist
4. **Execute Steps 2-10**: Systematic deployment following this plan
5. **Validate success**: All success criteria met
6. **Update documentation**: PROJECT_HISTORY.md, SESSION_START_PROMPT.md

---

**Document Status**: 📋 Draft - Awaiting Review
**Author**: Claude Code (AI Assistant)
**Last Updated**: November 19, 2025
**Version**: 1.0
