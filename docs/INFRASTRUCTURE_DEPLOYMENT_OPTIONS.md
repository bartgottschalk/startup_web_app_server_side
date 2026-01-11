# Infrastructure Deployment Options

StartupWebApp is designed to be flexible and can be deployed in multiple ways depending on your needs and budget.

---

## Table of Contents

1. [Deployment Models](#deployment-models)
2. [Option 1: Standalone Deployment](#option-1-standalone-deployment-simplest)
3. [Option 2: Shared Infrastructure](#option-2-shared-infrastructure-cost-savings)
4. [Option 3: Other Platforms](#option-3-other-platforms)
5. [Shared Infrastructure Best Practices](#shared-infrastructure-best-practices)
6. [Resource Tagging Strategy](#resource-tagging-strategy)
7. [IAM Policy Examples](#iam-policy-examples)

---

## Deployment Models

### Quick Comparison

| Model | AWS Cost/Month | Complexity | Best For |
|-------|----------------|------------|----------|
| **Standalone** | ~$100 | Low | Single app, learning, prototyping |
| **Shared Infrastructure** | ~$15-20/app | Medium | Multiple apps, cost optimization |
| **Other Platforms** | Varies | Varies | Platform-specific needs |

---

## Option 1: Standalone Deployment (Simplest)

### Overview

Deploy StartupWebApp with **dedicated AWS resources**. This is the simplest approach and provides complete isolation.

### Architecture

```
Your AWS Account
└── StartupWebApp (standalone)
    ├── Dedicated VPC
    ├── Dedicated ECS Cluster
    ├── Dedicated RDS Instance
    ├── Dedicated Application Load Balancer
    └── Dedicated NAT Gateway
```

### Cost Estimate

| Resource | Monthly Cost |
|----------|--------------|
| ECS Fargate (2 tasks) | $15 |
| RDS db.t4g.micro | $12 |
| RDS storage (20 GB) | $2.30 |
| Application Load Balancer | $16 |
| NAT Gateway | $32 |
| S3, CloudFront, ECR | $2 |
| **Total** | **~$100/month** |

### When to Use

- ✅ Learning AWS/Docker/Django
- ✅ Prototyping or MVP
- ✅ Single application deployment
- ✅ Want complete control and simplicity
- ✅ Cost is not a primary concern

### Deployment

Follow the standard AWS deployment scripts in `scripts/infra/`:
- All resources are dedicated to StartupWebApp
- No coordination with other applications needed
- Simple to set up and tear down

---

## Option 2: Shared Infrastructure (Cost Savings)

### Overview

Deploy **multiple applications** sharing the same AWS infrastructure. Each application has its own ECS service, database, and storage, but shares the VPC, ECS cluster, RDS instance, and load balancer.

### Architecture

```
Your AWS Account
├── Shared Infrastructure
│   ├── VPC & Subnets
│   ├── ECS Cluster (multi-tenant)
│   ├── RDS Instance (multiple databases)
│   ├── Application Load Balancer (host-based routing)
│   └── NAT Gateway
│
├── StartupWebApp
│   ├── ECS Service: startupwebapp-service
│   ├── Database: startupwebapp_prod (in shared RDS)
│   ├── S3 Buckets (dedicated)
│   └── ALB Listener Rule (host: startupwebapp.*)
│
└── Other Application(s)
    ├── ECS Service: app2-service
    ├── Database: app2_prod (in shared RDS)
    ├── S3 Buckets (dedicated)
    └── ALB Listener Rule (host: app2.*)
```

### Cost Estimate (2 Applications)

| Resource | Cost/Month | Notes |
|----------|------------|-------|
| **Shared** |
| VPC, Subnets, NAT | $32 | Split across apps |
| Application Load Balancer | $16 | Split across apps |
| RDS Instance | $12 | Split across apps |
| RDS Storage | $2.30 | Split across apps |
| **Per Application** |
| ECS Fargate (2 tasks) | $15 | Per app |
| S3, CloudFront, ECR | $2 | Per app |
| **Total per App** | **~$15-20/month** | **80%+ savings** |
| **Total for 2 Apps** | **~$95/month** | vs $200 standalone |

### When to Use

- ✅ Running multiple applications in same AWS account
- ✅ Cost optimization is important
- ✅ Applications have similar traffic patterns
- ✅ Comfortable managing shared resources
- ✅ Need production-grade infrastructure on a budget

### Requirements

1. **Resource naming convention** - Use unique prefixes/suffixes per app
2. **Resource tagging** - Tag all resources with project names
3. **Host-based routing** - Different domains per application
4. **Separate databases** - Each app gets its own database in shared RDS
5. **Coordination** - Be careful when modifying shared resources

---

## Option 3: Other Platforms

StartupWebApp is containerized (Docker) and can run on various platforms:

### Heroku

**Pros**: Simplest deployment, managed database, automatic SSL
**Cons**: More expensive (~$25-50/month), less control
**Deployment**: Use Heroku container registry

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
heroku container:push web
heroku container:release web
```

### DigitalOcean App Platform

**Pros**: Affordable ($12-25/month), managed, good DX
**Cons**: Less features than AWS
**Deployment**: Connect GitHub repo, configure build settings

### Google Cloud Run / Azure Container Instances

**Pros**: Pay-per-request pricing, auto-scaling
**Cons**: Platform-specific configuration
**Deployment**: Similar to AWS ECS, use respective CLIs

### Docker Compose on VPS

**Pros**: Cheapest option (~$5-10/month), full control
**Cons**: Manual management, no auto-scaling, you handle backups
**Deployment**:
```bash
# On your VPS
git clone <your-repo>
docker-compose up -d
```

---

## Shared Infrastructure Best Practices

### 1. Resource Naming Convention

Use consistent naming to identify which resources belong to which application:

**Example Convention:**
```
Application 1: startupwebapp-service, startupwebapp-tg, startupwebapp-*
Application 2: app2-service, app2-tg, app2-*
Shared: multi-app-alb, multi-tenant-rds, shared-cluster
```

**Why it matters:**
- Easy to identify resources in AWS Console
- Prevents accidental deletion
- Makes cost tracking easier

### 2. Resource Tagging Strategy

Tag **every resource** with appropriate tags:

**Shared Infrastructure Tags:**
```
SharedInfrastructure: true
Critical: true
ManagedBy: multi-app-infrastructure
```

**Application-Specific Tags:**
```
Project: StartupWebApp
ManagedBy: startupwebapp-infra-scripts
Environment: production
```

**Benefits:**
- Visual indication in AWS Console
- Filter resources by tag
- Create cost reports per application
- IAM policies can enforce tag-based permissions
- CloudWatch alarms can target specific tags

### 3. Safety Checklist for Shared Resources

Before modifying resources tagged `SharedInfrastructure: true`:

**Check for Other Applications:**
```bash
# List all ECS services in cluster
aws ecs list-services --cluster <cluster-name> --output table

# List all databases in RDS instance
psql -h <rds-endpoint> -U postgres -c "\l"

# List all ALB listener rules
aws elbv2 describe-rules --listener-arn <listener-arn> --query 'Rules[*].[Priority,Conditions[0].Values[0]]' --output table

# List all target groups
aws elbv2 describe-target-groups --query 'TargetGroups[*].[TargetGroupName,TargetType]' --output table
```

**Questions to Ask:**
- ✅ Will this change affect other applications?
- ✅ Do I need to coordinate with other app maintainers?
- ✅ Is there a maintenance window needed?
- ✅ Can this change be rolled back easily?
- ✅ Have I tested this in a non-production environment?

### 4. What's Safe to Modify vs What's Shared

**Safe to Modify (Per-Application Resources):**
- ✅ Your ECS service (e.g., `startupwebapp-service`)
- ✅ Your ECS task definition (e.g., `startupwebapp-service-task`)
- ✅ Your target group (e.g., `startupwebapp-tg`)
- ✅ Your ALB listener rules (e.g., `Host=startupwebapp.*`)
- ✅ Your database schema (in your own database)
- ✅ Your S3 buckets (dedicated to your app)
- ✅ Your CloudFront distributions
- ✅ Your ECR repository

**Requires Coordination (Shared Resources):**
- ⚠️ VPC, subnets, routing tables
- ⚠️ ECS cluster (settings, capacity providers)
- ⚠️ RDS instance (version upgrades, instance size, maintenance windows)
- ⚠️ Application Load Balancer (deletion, security groups)
- ⚠️ NAT Gateway
- ⚠️ Internet Gateway
- ⚠️ Security group rules that multiple apps depend on

### 5. Deployment Isolation

Even with shared infrastructure, deployments should be independent:

**How to Achieve:**
- ✅ Separate Git repositories per application
- ✅ Separate GitHub Actions workflows
- ✅ Separate Docker images (different ECR repos)
- ✅ Separate ECS services (can update independently)
- ✅ Separate databases (schema changes don't affect others)

**You should be able to:**
- Deploy App A without affecting App B
- Roll back App A without affecting App B
- Scale App A without affecting App B
- Debug App A without accessing App B's data

---

## Resource Tagging Strategy

### Recommended Tags

Apply these tags to **all AWS resources**:

**Required Tags:**
```
Project: <ApplicationName>           # e.g., "StartupWebApp"
Environment: <environment>            # e.g., "production", "staging"
ManagedBy: <tool-or-script>          # e.g., "terraform", "infra-scripts"
```

**Optional Tags:**
```
CostCenter: <team-or-department>     # For cost allocation
Owner: <email-or-team>                # Who to contact
SharedInfrastructure: <true|false>   # Indicates shared resources
Critical: <true|false>                # Indicates business-critical resources
```

### Tagging Examples

**Standalone Deployment:**
```bash
# Tag all resources with:
Project: StartupWebApp
Environment: production
ManagedBy: swa-infra-scripts
```

**Shared Infrastructure Deployment:**

*Shared Resources:*
```bash
Project: SharedInfrastructure
Environment: production
ManagedBy: multi-app-scripts
SharedInfrastructure: true
Critical: true
```

*App-Specific Resources:*
```bash
Project: StartupWebApp
Environment: production
ManagedBy: swa-infra-scripts
SharedInfrastructure: false
```

### Viewing Resources by Tag

**AWS Console:**
- Tag Editor: Search and filter resources by tag
- Resource Groups: Create groups based on tags
- Cost Explorer: View costs by tag

**AWS CLI:**
```bash
# Find all resources for a project
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=StartupWebApp

# Find all shared infrastructure
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=SharedInfrastructure,Values=true
```

---

## IAM Policy Examples

### Standalone Deployment - Full Permissions

For standalone deployments, use an IAM user with broad permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:*",
        "ecr:*",
        "rds:*",
        "s3:*",
        "cloudfront:*",
        "elasticloadbalancing:*",
        "ec2:*",
        "secretsmanager:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### Shared Infrastructure - Restricted Permissions

For shared infrastructure, create separate IAM users per application:

**IAM User: `startupwebapp-deploy`**

This user can only modify StartupWebApp resources, not other applications or shared infrastructure:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadSharedResources",
      "Effect": "Allow",
      "Action": [
        "ecs:Describe*",
        "ecs:List*",
        "rds:Describe*",
        "elasticloadbalancing:Describe*",
        "ec2:Describe*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowModifyOwnECSService",
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:RegisterTaskDefinition",
        "ecs:DeregisterTaskDefinition",
        "ecs:RunTask",
        "ecs:StopTask"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Project": "StartupWebApp"
        }
      }
    },
    {
      "Sid": "AllowModifyOwnECRRepository",
      "Effect": "Allow",
      "Action": [
        "ecr:*"
      ],
      "Resource": "arn:aws:ecr:*:*:repository/startupwebapp-*"
    },
    {
      "Sid": "AllowModifyOwnS3Buckets",
      "Effect": "Allow",
      "Action": [
        "s3:*"
      ],
      "Resource": [
        "arn:aws:s3:::startupwebapp-*",
        "arn:aws:s3:::startupwebapp-*/*"
      ]
    },
    {
      "Sid": "AllowAccessOwnSecrets",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:startupwebapp/*"
    },
    {
      "Sid": "AllowLogsForOwnService",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/ecs/startupwebapp-*"
    },
    {
      "Sid": "DenyDeleteSharedResources",
      "Effect": "Deny",
      "Action": [
        "ecs:DeleteCluster",
        "rds:DeleteDBInstance",
        "elasticloadbalancing:DeleteLoadBalancer",
        "ec2:DeleteVpc",
        "ec2:DeleteSubnet",
        "ec2:DeleteNatGateway"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/SharedInfrastructure": "true"
        }
      }
    }
  ]
}
```

**Key Features:**
- ✅ Can deploy/update StartupWebApp service
- ✅ Can push Docker images to StartupWebApp ECR
- ✅ Can modify StartupWebApp S3 buckets
- ✅ Can access StartupWebApp secrets
- ✅ Can read (but not modify) shared resources
- ❌ Cannot delete shared infrastructure
- ❌ Cannot modify other applications' resources

### Using IAM Policies

**1. Create IAM User:**
```bash
aws iam create-user --user-name startupwebapp-deploy
```

**2. Attach Policy:**
```bash
# Save policy JSON to file: startupwebapp-deploy-policy.json
aws iam put-user-policy \
  --user-name startupwebapp-deploy \
  --policy-name StartupWebAppDeployPolicy \
  --policy-document file://startupwebapp-deploy-policy.json
```

**3. Create Access Keys:**
```bash
aws iam create-access-key --user-name startupwebapp-deploy
```

**4. Configure GitHub Secrets:**
- Add `AWS_ACCESS_KEY_ID` to repository secrets
- Add `AWS_SECRET_ACCESS_KEY` to repository secrets
- GitHub Actions will use these restricted credentials

**5. Use Locally:**
```bash
# Add to ~/.aws/credentials
[startupwebapp]
aws_access_key_id = AKIA...
aws_secret_access_key = ...

# Use profile
aws --profile startupwebapp ecs describe-services ...
```

---

## Monitoring Multiple Applications

### CloudWatch Dashboards

Create separate dashboards per application:

**Dashboard: StartupWebApp**
- ECS Service: `startupwebapp-service` (CPU, Memory, Task Count)
- ALB Target Group: `startupwebapp-tg` (Healthy/Unhealthy targets, Request count)
- Database: Filter by `startupwebapp_prod` connection count
- Logs: `/ecs/startupwebapp-service`

**Dashboard: Shared Infrastructure**
- RDS Instance: Overall CPU, Memory, Connections
- ALB: Overall request count, 2xx/4xx/5xx responses
- ECS Cluster: Total CPU, Memory reservation

### Cost Tracking

Use AWS Cost Explorer with tag-based filtering:

```
Filter: Project = StartupWebApp       → StartupWebApp costs (~$15-20/month)
Filter: Project = OtherApp            → Other app costs (~$15-20/month)
Filter: SharedInfrastructure = true   → Shared costs (~$60/month, split between apps)
```

---

## Additional Resources

### AWS Documentation
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [RDS Multi-Tenant Patterns](https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/multi-tenant-data-partitioning.html)
- [ALB Host-Based Routing](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-update-rules.html)

### StartupWebApp Infrastructure Scripts
- See `scripts/infra/` directory for AWS deployment scripts
- Scripts support both standalone and shared infrastructure models
- Follow script comments for customization

---

## Summary

**Choose Your Deployment Model:**

1. **Standalone** - Simplest, ~$100/month, complete isolation
2. **Shared Infrastructure** - Most cost-effective, ~$15-20/month per app, requires coordination
3. **Other Platforms** - Varies by platform, may be simpler or cheaper depending on needs

**If Using Shared Infrastructure:**
- ✅ Use consistent resource naming conventions
- ✅ Tag all resources appropriately
- ✅ Check for other applications before modifying shared resources
- ✅ Use separate IAM users per application (optional but recommended)
- ✅ Maintain deployment independence (separate repos, workflows, images)

**Key Principle:**
> Applications should be **logically isolated** (separate services, databases, buckets) even when **physically sharing** infrastructure (VPC, cluster, RDS instance).

---

**Last Updated:** January 2026
**Applies To:** StartupWebApp v2.0+ (Django 5.2, Docker-based deployment)
