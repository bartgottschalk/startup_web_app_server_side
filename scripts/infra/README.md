# AWS Infrastructure Scripts

Infrastructure as Code (IaC) scripts for deploying StartupWebApp to AWS.

## ✅ Deployment Status

**Current Status: Phase 5.14 In Progress - Step 3 Complete & Tested**

- **Phase 5.13 Completed**: November 22, 2025 - RDS Infrastructure Deployed
- **Phase 5.14 In Progress**: November 24, 2025 - ECS/CI/CD Setup
- **Phase 5.14 Step 1**: ✅ Multi-Stage Dockerfile (Complete - November 23, 2025)
- **Phase 5.14 Step 2**: ✅ AWS ECR Repository (Complete - November 24, 2025)
- **Phase 5.14 Step 3**: ✅ ECS Infrastructure (Complete & Tested - November 24, 2025)
- **RDS Status**: Available
- **Monitoring**: Active (4 alarms, email confirmed)
- **Monthly Cost**: $36 (RDS: $26, Bastion: $7, Monitoring: $2, CloudWatch/ECR: $1)

**Deployed Resources:**
- VPC: vpc-0df90226462f00350 (startupwebapp-vpc, 10.0.0.0/16)
- RDS PostgreSQL 16.x: startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com:5432
- Security Groups: 3 (RDS, Bastion, Backend)
- Secrets Manager: rds/startupwebapp/multi-tenant/master
- CloudWatch Dashboard: StartupWebApp-RDS-MultiTenant
- SNS Topic: StartupWebApp-RDS-Alerts
- ECR Repository: startupwebapp-backend
- ECS Cluster: startupwebapp-cluster (Fargate)
- ECS IAM Roles: 2 (task execution + task role)

**Phase 5.14 Progress:**
1. ✅ Multi-Stage Dockerfile (development + production targets)
2. ✅ Create ECR repository (`create-ecr.sh`)
3. ✅ Create ECS infrastructure (cluster, IAM roles, security groups)
   - ✅ Tested: Full destroy → recreate lifecycle validated
4. 🚧 **Next: Create ECS task definition** (code-based)
5. Set up GitHub Actions CI/CD workflow
6. Configure GitHub secrets
7. Run automated migrations on all 3 RDS databases via pipeline
8. Verification and documentation

**After Phase 5.14:**
- Phase 5.15: Full production deployment (ECS service, ALB, auto-scaling)
- Phase 5.16: Production hardening (WAF, monitoring, load testing)

## CRITICAL WORKFLOW RULE

**⚠️ IMPORTANT**: All scripts in this directory must be executed manually in separate terminal windows. **DO NOT run these scripts within Claude Code chat sessions.**

Rationale:
- Infrastructure operations are sensitive and require manual oversight
- AWS resource creation incurs costs
- Better control and visibility over what's being created/destroyed
- Allows for review and confirmation before execution
- Easier debugging if issues occur

## Overview

This directory contains bash scripts to provision and manage AWS infrastructure for StartupWebApp's multi-tenant PostgreSQL database deployment.

**Architecture:**
- VPC with public/private subnets across 2 availability zones
- RDS PostgreSQL 16.x (db.t4g.small) for multi-tenant databases
- Security groups for RDS, bastion, and backend services
- AWS Secrets Manager for credential storage
- CloudWatch monitoring with alarms and dashboard
- NAT Gateway: **Optional** (default: not created, saves $32/month)

**Estimated Monthly Cost:**
- **Without NAT Gateway (default):** ~$29/month
  - RDS db.t4g.small: $26/month
  - Enhanced Monitoring: $2/month
  - CloudWatch/SNS: $1/month
- **With NAT Gateway (optional):** ~$61/month
  - NAT Gateway: $32/month (additional)
  - RDS db.t4g.small: $26/month
  - Enhanced Monitoring: $2/month
  - CloudWatch/SNS: $1/month

## Prerequisites

- AWS CLI installed and configured
- IAM user with appropriate permissions (RDS, EC2, Secrets Manager, CloudWatch)
- AWS region set to us-east-1 (or update scripts)
- Access to `aws-resources.env` file (auto-generated)

## File Structure

```
scripts/infra/
├── README.md                        # This file
├── init-env.sh                      # Common initialization (sourced by all scripts)
├── aws-resources.env.template       # Template for resource IDs (committed to git)
├── aws-resources.env                # Resource IDs (gitignored, auto-created from template)
├── status.sh                        # Deployment progress and next steps
├── show-resources.sh                # Display all resources
│
├── create-vpc.sh                    # Create VPC and networking
├── destroy-vpc.sh                   # Delete VPC and networking
│
├── create-security-groups.sh        # Create security groups
├── destroy-security-groups.sh       # Delete security groups
│
├── create-secrets.sh                # Create Secrets Manager secret
├── destroy-secrets.sh               # Delete secret (30-day recovery)
│
├── create-rds.sh                    # Create RDS PostgreSQL instance
├── destroy-rds.sh                   # Delete RDS instance
│
├── create-bastion.sh                # Create bastion host (optional, for database access)
├── destroy-bastion.sh               # Delete bastion host
│
├── create-databases.sh              # Create multi-tenant databases
│
├── create-monitoring.sh             # Create CloudWatch monitoring
├── destroy-monitoring.sh            # Delete monitoring
│
├── create-ecr.sh                    # Create ECR repository (Phase 5.14)
├── destroy-ecr.sh                   # Delete ECR repository
│
├── create-ecs-cluster.sh            # Create ECS cluster (Phase 5.14)
├── destroy-ecs-cluster.sh           # Delete ECS cluster
│
├── create-ecs-task-role.sh          # Create IAM roles for ECS (Phase 5.14)
├── destroy-ecs-task-role.sh         # Delete ECS IAM roles
│
└── update-security-groups-ecs.sh    # Update security groups for ECS
```

**Security Pattern:**
- `aws-resources.env.template` - Empty template committed to git (like `settings_secret.py.template`)
- `aws-resources.env` - Populated during deployment, gitignored (like `settings_secret.py`)
- `init-env.sh` - Creates `aws-resources.env` from template on first run

## Deployment Order

### Check Deployment Status

At any time, check your deployment progress and see what's next:

```bash
./scripts/infra/status.sh
```

This script shows:
- What infrastructure has been created (✓)
- What's blocked or not started (✗)
- Exact command to run next
- Current progress (X/7 steps complete)
- Estimated monthly cost for created resources
- Live RDS status (if applicable)

**Tip:** Run `status.sh` after each script to see your progress and get the next command.

### Full Infrastructure Deployment

Execute scripts in this order:

**Phase 5.13: RDS Infrastructure (Steps 1-7)**

```bash
# 1. Create VPC and networking (10-15 minutes)
./scripts/infra/create-vpc.sh

# 2. Create security groups (1 minute)
./scripts/infra/create-security-groups.sh

# 3. Create Secrets Manager secret (1 minute)
./scripts/infra/create-secrets.sh

# 4. Create RDS PostgreSQL instance (10-15 minutes)
./scripts/infra/create-rds.sh

# 5. (Optional) Create bastion host for database access (5 minutes)
./scripts/infra/create-bastion.sh

# 6. Create multi-tenant databases (manual - requires bastion or SSM)
./scripts/infra/create-databases.sh

# 7. Create CloudWatch monitoring (2 minutes)
./scripts/infra/create-monitoring.sh your-email@domain.com

# 8. Show all resources
./scripts/infra/show-resources.sh
```

**Phase 5.13 Total Time:** ~30-40 minutes (mostly AWS provisioning time)

**Phase 5.14: ECS/CI/CD Infrastructure**

```bash
# 1. Multi-stage Dockerfile (already complete - see Dockerfile)

# 2. Create ECR repository for Docker images (2 minutes)
./scripts/infra/create-ecr.sh

# 3. Create ECS Fargate cluster (2 minutes)
./scripts/infra/create-ecs-cluster.sh

# 4. Create IAM roles for ECS tasks (2 minutes)
./scripts/infra/create-ecs-task-role.sh

# 5. Update security groups for ECS (1 minute)
./scripts/infra/update-security-groups-ecs.sh

# 6. (Future) Create ECS task definition for migrations (code-based)
# 7. (Future) Create GitHub Actions workflow
# 8. (Future) Run migrations via CI/CD pipeline

# Check status
./scripts/infra/status.sh
```

### Teardown Order

Execute scripts in reverse order:

**Phase 5.14: ECS/CI/CD Infrastructure**

```bash
# 1. (Future) Destroy ECS task definition

# 2. Destroy ECS IAM roles
./scripts/infra/destroy-ecs-task-role.sh

# 3. Destroy ECS cluster
./scripts/infra/destroy-ecs-cluster.sh

# 4. Destroy ECR repository (deletes all images)
./scripts/infra/destroy-ecr.sh

# Note: Security group rules are left intact (no dedicated destroy script)
```

**Phase 5.13: RDS Infrastructure**

```bash
# 1. Destroy monitoring
./scripts/infra/destroy-monitoring.sh

# 2. (Optional) Destroy bastion host
./scripts/infra/destroy-bastion.sh

# 3. Destroy RDS instance (5-10 minutes)
./scripts/infra/destroy-rds.sh

# 4. Destroy secret (30-day recovery window)
./scripts/infra/destroy-secrets.sh

# 5. Destroy security groups
./scripts/infra/destroy-security-groups.sh

# 6. Destroy VPC (5-10 minutes)
./scripts/infra/destroy-vpc.sh
```

**Total Time:** ~15-25 minutes

## Script Details

### create-vpc.sh

Creates complete VPC infrastructure:
- VPC (10.0.0.0/16)
- 2 public subnets (10.0.1.0/24, 10.0.2.0/24) in us-east-1a, us-east-1b
- 2 private subnets (10.0.10.0/24, 10.0.11.0/24) in us-east-1a, us-east-1b
- Internet Gateway
- NAT Gateway (with Elastic IP) - **OPTIONAL** (default: no)
- Route tables (public and private)
- DB Subnet Group (for RDS)

**NAT Gateway Decision:**
The script will prompt: "Create NAT Gateway? (yes/no) [default: no]"

- **Choose NO (default, recommended for cost savings):**
  - Saves $32/month (~52% cost reduction)
  - Private subnets (RDS) have no internet access (fine for databases)
  - Deploy backend services to **public subnets** for internet access (Stripe API, email, etc.)
  - Total monthly cost: ~$29

- **Choose YES (for private subnet backend):**
  - Adds $32/month
  - Private subnets can access internet via NAT Gateway
  - Deploy backend services to **private subnets** (more secure, enterprise pattern)
  - Total monthly cost: ~$61

**Time:**
- Without NAT Gateway: ~5-7 minutes
- With NAT Gateway: ~10-15 minutes (NAT Gateway provisioning)

### create-security-groups.sh

Creates three security groups:
- **RDS SG**: PostgreSQL (5432) from Backend SG and Bastion SG
- **Bastion SG**: SSH (22) from your current IP
- **Backend SG**: Ready for backend services

**Time:** 1 minute

### create-secrets.sh

Creates AWS Secrets Manager secret with:
- Auto-generated secure password (32 characters)
- Placeholder for RDS endpoint (updated by create-rds.sh)
- Username: django_app
- Port: 5432

**Time:** 1 minute

### create-rds.sh

Creates RDS PostgreSQL instance:
- Engine: PostgreSQL 16.x (latest minor version)
- Instance: db.t4g.small (2 vCPU, 2 GB RAM)
- Storage: 20 GB gp3 (auto-scaling to 100 GB)
- Backups: 7-day retention, daily at 03:00-04:00 UTC
- Monitoring: Enhanced (60-second intervals), Performance Insights (7 days)
- Security: Private subnets only, SSL required, deletion protection enabled

**Time:** 10-15 minutes

**Post-creation:**
- Updates Secrets Manager with actual RDS endpoint
- Outputs connection information

### create-bastion.sh

Creates a bastion host (EC2 instance) for secure database access:
- Instance: t3.micro (1 vCPU, 1 GB RAM)
- Location: Public subnet with public IP address
- OS: Amazon Linux 2023 with PostgreSQL client pre-installed
- Access: AWS Systems Manager Session Manager (no SSH keys required)
- Security: IAM instance profile with SSM permissions
- Tools: psql, jq, aws-cli pre-configured

**Time:** ~5 minutes

**Optional:** Only needed if you want a dedicated bastion host for database operations. Alternative approaches:
- Launch temporary EC2 instance as needed
- Use AWS CloudShell with port forwarding
- Connect from your backend application

**Cost:**
- Running: ~$7/month (t3.micro 24/7)
- Stopped: ~$1/month (EBS storage only)
- **Tip:** Stop when not in use to save ~$6/month

**Post-creation:**
- Connect via: `aws ssm start-session --target <instance-id>`
- Already configured with RDS endpoint and credentials access
- Ready for database operations immediately

### create-databases.sh

Generates SQL script to create:
- User: django_app
- Database: startupwebapp_prod
- Database: healthtech_experiment
- Database: fintech_experiment

**Important:** This script cannot automatically execute SQL. You must:
1. Connect via **AWS Systems Manager Session Manager** (recommended, free, no bastion needed)
2. Execute the generated SQL script manually
3. Verify databases created

**Connection method:** AWS Systems Manager Session Manager
- No bastion host required
- No SSH keys needed
- Free service
- IAM-based access control

### create-monitoring.sh

Creates CloudWatch monitoring:
- SNS topic for alerts
- Email subscription: `bart@mosaicmeshai.com` (requires confirmation)
- 4 CloudWatch alarms:
  - CPU > 70% for 10 minutes
  - Connections > 80 for 10 minutes
  - Free storage < 2 GB
  - Free memory < 500 MB for 10 minutes
- CloudWatch dashboard with 6 metric widgets

**Usage:**
```bash
./scripts/infra/create-monitoring.sh your-email@domain.com
```

**Time:** 2 minutes

**Important:** Check your email and confirm the SNS subscription!

### create-ecr.sh (Phase 5.14)

Creates AWS ECR (Elastic Container Registry) repository:
- Repository: `startupwebapp-backend`
- Image scanning: Enabled (scan on push)
- Encryption: AES256 at rest
- Lifecycle policy: Keep last 10 images
- Tags for organization and cost tracking

**Usage:**
```bash
./scripts/infra/create-ecr.sh
```

**Time:** ~2 minutes

**After Creation:**

```bash
# Build production image
docker build --target production -t startupwebapp-backend:latest .

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <REPOSITORY_URI>

# Tag image
docker tag startupwebapp-backend:latest <REPOSITORY_URI>:latest

# Push image
docker push <REPOSITORY_URI>:latest
```

**Cost:** ~$0.10/GB/month storage (~$0.10-$0.20/month for 1-2 images)

### create-ecs-cluster.sh (Phase 5.14)

Creates AWS ECS Fargate cluster for running containerized tasks:
- Cluster: `startupwebapp-cluster`
- Launch type: Fargate (serverless, no EC2 management)
- Capacity providers: FARGATE and FARGATE_SPOT
- CloudWatch log group: `/ecs/startupwebapp-migrations` (7-day retention)
- Tags for organization and cost tracking

**Prerequisites:**
- VPC must exist

**Usage:**
```bash
./scripts/infra/create-ecs-cluster.sh
```

**Time:** ~2 minutes

**What Gets Created:**
- ECS Fargate cluster (serverless container orchestration)
- CloudWatch log group for task logs

**Cost:**
- ECS cluster: $0 (no cost for cluster itself)
- Fargate tasks: Pay-per-use (~$0.0137/hour per 0.25 vCPU + 0.5 GB task)
- CloudWatch logs: ~$0.50/GB ingested

### create-ecs-task-role.sh (Phase 5.14)

Creates IAM roles for ECS tasks:
- **Task Execution Role** (`ecsTaskExecutionRole-startupwebapp`):
  - Pulls Docker images from ECR
  - Writes logs to CloudWatch
  - Reads secrets from Secrets Manager
- **Task Role** (`ecsTaskRole-startupwebapp`):
  - Application runtime permissions
  - Read secrets during task execution

**Prerequisites:**
- Secrets Manager secret must exist

**Usage:**
```bash
./scripts/infra/create-ecs-task-role.sh
```

**Time:** ~2 minutes (includes 10-second IAM propagation wait)

**What Gets Created:**
- 2 IAM roles with appropriate policies
- Inline policies for Secrets Manager access

**Cost:** $0 (IAM roles are free)

### update-security-groups-ecs.sh (Phase 5.14)

Updates existing security groups to allow ECS tasks to communicate with RDS:
- Verifies Backend SG → RDS SG rule exists (port 5432)
- Adds outbound rules to Backend SG for RDS and ECR
- ECS tasks will use the Backend security group

**Prerequisites:**
- Security groups must exist

**Usage:**
```bash
./scripts/infra/update-security-groups-ecs.sh
```

**Time:** ~1 minute

**What Gets Updated:**
- Backend SG: Outbound to RDS (port 5432)
- Backend SG: Outbound to internet (port 443 for ECR)

**Cost:** $0 (security group rules are free)

### show-resources.sh

Displays all created resources:
- Configuration (region, account, project)
- VPC resources (VPC, subnets, gateways)
- Security groups
- Secrets Manager
- RDS instance (with live status)
- Bastion host (if created)
- CloudWatch monitoring
- ECR repository (Phase 5.14)
- ECS cluster (Phase 5.14)
- ECS IAM roles (Phase 5.14)
- Cost estimate
- Quick links to AWS Console

**Usage:**
```bash
./scripts/infra/show-resources.sh
```

## Resource Tracking

All created resource IDs are stored in `aws-resources.env`. This file follows the same pattern as `settings_secret.py`:

- **`aws-resources.env.template`** - Empty template committed to git
- **`aws-resources.env`** - Populated during deployment, gitignored
- Created automatically from template on first script execution
- Updated by creation scripts as resources are provisioned
- Read by destruction scripts to know what to delete

**Do not edit `aws-resources.env` manually.** It's auto-managed by the scripts.

## Idempotency

All creation scripts are idempotent:
- Running a script multiple times is safe
- If resources already exist, scripts will skip creation
- To recreate, run the corresponding destroy script first

## Cost Management

**Daily Cost Breakdown (without NAT Gateway - default):**
- RDS db.t4g.small: ~$0.87/day ($26/month)
- Enhanced Monitoring: ~$0.07/day ($2/month)
- CloudWatch/SNS: ~$0.03/day ($1/month)
- ECR Storage (Phase 5.14): ~$0.01/day ($0.10-$0.20/month for 1-2 images)

**Total (default):** ~$0.98/day or ~$29-30/month

**With optional NAT Gateway:**
- Add NAT Gateway: ~$1.07/day ($32/month)
- **Total with NAT:** ~$2.05/day or ~$61-62/month

**With optional Bastion Host:**
- Bastion running: ~$0.23/day ($7/month)
- Bastion stopped: ~$0.03/day ($1/month, EBS storage only)

**Cost Optimization:**
1. **Skip NAT Gateway (default):** Save $32/month (52% savings) - deploy backend to public subnets
2. **Stop bastion when not in use:** Save $6/month ($7 running → $1 stopped)
3. **Stop RDS during inactivity:** Save $26/month when not in use
4. **Use Reserved Instances:** Save 30-60% on RDS with 1-3 year commitment
5. **Scale down:** Use db.t4g.micro ($13/month) for very low traffic
6. **ECR lifecycle policy:** Automatically keeps only last 10 images (already configured)

## Multi-Tenant Architecture

The RDS instance supports multiple databases:
- `startupwebapp_prod` - Main application
- `healthtech_experiment` - Fork #1
- `fintech_experiment` - Fork #2

**Benefits:**
- 75-80% cost savings vs separate RDS instances
- Shared resources (CPU, memory, connections)
- Easy to add/remove experimental databases
- Isolated data per application

**Connection:**
Each application sets `DATABASE_NAME` environment variable:
```bash
export DATABASE_NAME=startupwebapp_prod
export DATABASE_NAME=healthtech_experiment
export DATABASE_NAME=fintech_experiment
```

## Backend Deployment Architecture

This infrastructure supports two common AWS deployment patterns for your Django backend:

### Option A: Backend in Public Subnets (Recommended - Default)

**When NAT Gateway is NOT created (default):**

```
Internet → ALB (public subnet) → Backend (public subnet) → RDS (private subnet)
                                          ↓
                                    Internet (Stripe API, email, etc.)
```

**Characteristics:**
- Backend EC2/ECS instances in **public subnets** with public IPs
- Backend can directly access internet for outbound calls (Stripe API, SMTP, package updates)
- RDS remains in private subnets (not directly accessible from internet)
- Security groups restrict backend access (only ALB can reach backend)
- **Cost:** ~$29/month (no NAT Gateway)
- **Use case:** Most common for small-to-medium deployments

**Configuration:**
- Deploy backend to: Public Subnet 1 (10.0.1.0/24) or Public Subnet 2 (10.0.2.0/24)
- Backend security group: Allow inbound from ALB security group only
- RDS security group: Allow inbound from backend security group (port 5432)

### Option B: Backend in Private Subnets (Enterprise Pattern)

**When NAT Gateway IS created (optional):**

```
Internet → ALB (public subnet) → Backend (private subnet) → RDS (private subnet)
                                          ↓
                                    NAT Gateway → Internet (Stripe API, etc.)
```

**Characteristics:**
- Backend EC2/ECS instances in **private subnets** with no public IPs
- Backend accesses internet via NAT Gateway for outbound calls
- Backend not directly accessible from internet (more secure)
- **Cost:** ~$61/month (includes NAT Gateway $32/month)
- **Use case:** Enterprise deployments, compliance requirements (PCI DSS, HIPAA)

**Configuration:**
- Deploy backend to: Private Subnet 1 (10.0.10.0/24) or Private Subnet 2 (10.0.11.0/24)
- NAT Gateway provides outbound internet access
- RDS security group: Allow inbound from backend security group (port 5432)

### Adding NAT Gateway Later

If you initially chose Option A (no NAT Gateway) and later need Option B:

**Option 1: Recreate VPC (clean approach)**
```bash
./scripts/infra/destroy-vpc.sh
./scripts/infra/create-vpc.sh  # Choose "yes" for NAT Gateway this time
```

**Option 2: Manually add via AWS Console**
1. Create Elastic IP
2. Create NAT Gateway in Public Subnet 1
3. Add route in Private Route Table: 0.0.0.0/0 → NAT Gateway
4. Update `scripts/infra/aws-resources.env` with NAT_GATEWAY_ID and ELASTIC_IP_ID

**Note:** Option 1 requires RDS recreation (downtime). Option 2 has no downtime.

### Future: Application Load Balancer (ALB)

Both patterns work with ALB (not included in these scripts):
- ALB always in **public subnets** (receives internet traffic)
- ALB forwards to backend (public or private subnets based on your choice)
- ALB handles SSL/TLS termination
- ALB performs health checks on backend instances

## Security Best Practices

1. **Private RDS:** No public accessibility, private subnets only
2. **SSL/TLS:** Required for all connections
3. **Secrets Manager:** Credentials stored securely, not in code
4. **Security Groups:** Least privilege access (RDS from backend/bastion only)
5. **Deletion Protection:** Enabled on RDS (must disable before deletion)
6. **Backups:** 7-day automated backups, manual snapshots before major changes
7. **Monitoring:** CloudWatch alarms notify of unusual activity

## Troubleshooting

### VPC Creation Fails

**Issue:** NAT Gateway creation timeout
**Solution:** Check AWS service health, retry after 5 minutes

### RDS Creation Fails

**Issue:** "DBSubnetGroupDoesNotCoverEnoughAZs"
**Solution:** Verify VPC created with 2 subnets in different AZs

### Cannot Connect to RDS

**Issue:** Connection timeout
**Solutions:**
1. Verify security group rules allow access from your IP/bastion
2. Check RDS is in "available" state: `show-resources.sh`
3. Verify you're connecting via bastion in same VPC
4. Check RDS endpoint is correct (from Secrets Manager)

### Script Permission Denied

**Issue:** `permission denied: ./create-vpc.sh`
**Solution:** Make script executable: `chmod +x scripts/infra/*.sh`

### AWS CLI Not Found

**Issue:** `command not found: aws`
**Solution:** Install AWS CLI: https://aws.amazon.com/cli/

### Insufficient IAM Permissions

**Issue:** "User is not authorized to perform..."
**Solution:** Add required IAM policies:
- AmazonRDSFullAccess
- AmazonEC2FullAccess
- SecretsManagerReadWrite
- CloudWatchFullAccess

## Monitoring

### CloudWatch Dashboard

View real-time metrics:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=StartupWebApp-RDS-MultiTenant
```

**Metrics:**
- CPU utilization
- Database connections
- Freeable memory
- Free storage space
- Read/write latency
- Read/write throughput

### CloudWatch Alarms

Receive email alerts for:
- High CPU (>70% for 10 min)
- High connections (>80 for 10 min)
- Low storage (<2 GB)
- Low memory (<500 MB for 10 min)

### Logs

PostgreSQL logs exported to CloudWatch Logs:
```
/aws/rds/instance/startupwebapp-multi-tenant-prod/postgresql
```

## Database Connection

### Option 1: Via Bastion Host (Recommended - Using create-bastion.sh)

**Use this approach if you've created a bastion host using `create-bastion.sh`:**

```bash
# Connect to bastion via AWS Systems Manager Session Manager (no SSH keys needed)
aws ssm start-session --target <BASTION_INSTANCE_ID>

# Once connected, retrieve RDS password
aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --query 'SecretString' \
  --output text | jq -r '.password'

# Connect to RDS
psql -h <RDS_ENDPOINT> -U postgres -d postgres
```

**Benefits:**
- Persistent bastion host available whenever needed
- Pre-configured with all necessary tools (psql, jq, aws-cli)
- No SSH key management (uses AWS Systems Manager)
- IAM-based access control
- Can be stopped when not in use (~$1/month vs ~$7/month running)

### Option 2: Via Temporary EC2 Instance

**Use this approach if you don't want a persistent bastion host:**

1. Launch a temporary EC2 instance in a public subnet with Systems Manager enabled
2. Use Session Manager to connect (browser-based or AWS CLI)
3. Install PostgreSQL client on the EC2 instance
4. Connect to RDS from the EC2 instance
5. Execute SQL scripts
6. Terminate EC2 instance when done

**Benefits:**
- No persistent infrastructure to maintain
- Only pay for temporary EC2 time (pennies per hour)
- Same security benefits as bastion (no SSH keys, IAM-based)

### Option 3: Via SSH Tunnel from Local Machine

**Only available if you have SSH access configured to bastion:**

```bash
# Create SSH tunnel through bastion
ssh -i key.pem -L 5432:<RDS_ENDPOINT>:5432 ec2-user@bastion-host

# Connect via localhost (in another terminal)
psql -h localhost -U django_app -d startupwebapp_prod
```

**Note:** The bastion created by `create-bastion.sh` does NOT use SSH keys - it uses AWS Systems Manager Session Manager instead.

### Get Credentials

```bash
# Get password from Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id rds/startupwebapp/multi-tenant/master \
  --query 'SecretString' \
  --output text | jq -r '.password'
```

## Backup Management

### Current Backup Strategy

**Automated Backups (Configured by create-rds.sh):**
- **Retention:** 7 days
- **Schedule:** Daily at 03:00-04:00 UTC
- **Type:** Instance-level snapshots (all databases)
- **Point-in-time recovery:** Within 7-day window
- **Storage:** AWS S3 (managed)
- **Cost:** Included up to RDS storage size

**Manual Snapshots:**
- Created via `destroy-rds.sh` before deletion (optional)
- Kept indefinitely until manually deleted
- Instance-level only (all databases)
- Cost: $0.095/GB-month

### What's NOT Included

The current setup does NOT include:
- ❌ Per-database logical backups (pg_dump)
- ❌ Long-term retention beyond 7 days
- ❌ Cross-region backup copies
- ❌ Export to custom S3 bucket
- ❌ Automated backup rotation scripts

### When to Add Custom Backup Scripts

**Skip custom backup scripts if:**
- ✅ In development/experimentation phase (current state)
- ✅ 7-day retention is sufficient
- ✅ Okay with instance-level snapshots
- ✅ No production data yet

**Add custom backup scripts when:**
- ⚠️ Moving to production with real user data
- ⚠️ Need compliance (SOC2, HIPAA) requiring longer retention
- ⚠️ Want per-database backups (not entire instance)
- ⚠️ Need monthly/yearly archives
- ⚠️ Require disaster recovery with cross-region copies

### Future Backup Scripts (When Needed)

If custom backup management becomes necessary, create:

```bash
scripts/infra/backup-database.sh <database_name>        # pg_dump to S3
scripts/infra/backup-all-databases.sh                   # Backup all DBs
scripts/infra/rotate-backups.sh                         # Delete old backups
scripts/infra/restore-database.sh <backup_file> <db>    # Restore from S3
```

### Manual Database Backup (Current Approach)

For per-database backups when needed:

```bash
# Backup single database to local file
pg_dump -h <RDS_ENDPOINT> -U django_app -d startupwebapp_prod \
  | gzip > startupwebapp_prod_$(date +%Y%m%d).sql.gz

# Upload to S3 (if desired)
aws s3 cp startupwebapp_prod_20251119.sql.gz \
  s3://your-backup-bucket/database-backups/

# Restore from backup
gunzip < startupwebapp_prod_20251119.sql.gz | \
  psql -h <RDS_ENDPOINT> -U django_app -d startupwebapp_prod
```

### AWS RDS Snapshot Management

```bash
# List automated backups
aws rds describe-db-snapshots \
  --db-instance-identifier startupwebapp-multi-tenant-prod \
  --snapshot-type automated

# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier startupwebapp-multi-tenant-prod \
  --db-snapshot-identifier manual-snapshot-$(date +%Y%m%d)

# Delete old manual snapshot
aws rds delete-db-snapshot \
  --db-snapshot-identifier manual-snapshot-20251101

# Restore from snapshot (creates new RDS instance)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier startupwebapp-restored \
  --db-snapshot-identifier manual-snapshot-20251119
```

### Recommendation

**Current Phase (Development/Experimentation):**
- Use AWS automated backups (7-day retention)
- Create manual snapshots before major changes
- No custom backup scripts needed yet

**Future Phase (Production):**
- Implement automated per-database backups to S3
- Set up S3 lifecycle policies for long-term archival
- Configure cross-region replication for disaster recovery
- Monitor backup success with CloudWatch alarms

## Next Steps After Infrastructure Deployment

**Status**: Phase 5.13 complete (RDS infrastructure). Phase 5.14 in progress (ECS/CI/CD).

### Phase 5.13 Complete - RDS Infrastructure (7/7 steps)

All infrastructure destroy/create cycles have been validated:
- ✅ VPC: create → destroy → create (tested)
- ✅ Security Groups: create → destroy → create (tested)
- ✅ Secrets Manager: create → destroy → create (tested)
- ✅ RDS: create → destroy → create (tested)
- ✅ Bastion: create → destroy → create (tested)
- ✅ Databases: 3 multi-tenant databases created
- ✅ Monitoring: create → destroy → create (tested)

**Time Investment**: ~7 hours total for Phase 5.13 infrastructure deployment

### Phase 5.14 In Progress - ECS/CI/CD Infrastructure

**Completed:**
1. ✅ **Step 1: Multi-Stage Dockerfile** (November 23, 2025)
   - Development image: 1.69 GB with test dependencies
   - Production image: 692 MB (59% smaller)
   - See `Dockerfile` in repository root

2. 🚧 **Step 2: AWS ECR Repository** (Scripts ready - November 24, 2025)
   - Run: `./scripts/infra/create-ecr.sh`
   - Creates Docker image registry in AWS
   - ~2 minutes, ~$0.10-$0.20/month

**Remaining Steps:**
3. Create ECS Fargate cluster
4. Create IAM roles for ECS tasks
5. Create ECS task definition for migrations
6. Set up GitHub Actions CI/CD workflow
7. Configure GitHub secrets (AWS credentials)
8. Run migrations via pipeline on all 3 databases
9. Verification and documentation

**Estimated Time Remaining**: ~5-6 hours

### Manual Steps After Phase 5.14

Once Phase 5.14 is complete, you can:

1. **Test migrations locally against RDS:**
   ```bash
   export DATABASE_NAME=startupwebapp_prod
   python manage.py migrate
   ```

2. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

3. **Build and push Docker images:**
   ```bash
   docker build --target production -t startupwebapp-backend:latest .
   docker push <ECR_REPOSITORY_URI>:latest
   ```

4. **Trigger GitHub Actions workflow** to run migrations via ECS

### After Phase 5.14

**Phase 5.15: Full Production Deployment**
- Long-running ECS service (not just migration tasks)
- Application Load Balancer with HTTPS
- Auto-scaling policies (2-10 tasks)
- Frontend deployment (S3 + CloudFront)
- Blue-green deployments

**Phase 5.16: Production Hardening**
- AWS WAF for security
- Load testing and performance optimization
- Automated disaster recovery testing

## References

- [AWS RDS PostgreSQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/)
- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/)
- [CloudWatch Alarms Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- [Project Documentation](../../docs/technical-notes/2025-11-19-aws-rds-deployment-plan.md)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review AWS Console for error messages
3. Check CloudWatch Logs for detailed errors
4. Consult project documentation in `docs/technical-notes/`

---

**Last Updated:** November 19, 2025
**Version:** 2.0 - Infrastructure Deployed
**Author:** Infrastructure as Code Scripts
**Status:** Phase 7 Complete - 5/7 Steps Deployed
