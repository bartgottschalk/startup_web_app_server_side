# Phase 5.15: Full Production Deployment - ECS Service, ALB, Auto-Scaling

**Date**: November 26, 2025 (Planning) | November 27-28, 2025 (Implementation)
**Status**: 🚧 In Progress - Steps 1-5 Complete, Step 6 Next
**Branch**: `feature/phase-5-15-production-deployment`
**Version**: 1.2 (Implementation In Progress)
**Priority**: HIGH - Production deployment

## Executive Summary

Phase 5.15 deploys the full StartupWebApp application to production using AWS ECS Fargate with an Application Load Balancer (ALB), auto-scaling, and HTTPS. This phase builds on Phase 5.14's CI/CD infrastructure to deploy a long-running service (not just migration tasks).

### Key Decisions

- ✅ **ECS Service**: Long-running Fargate tasks (vs one-time migration tasks)
- ✅ **Application Load Balancer**: HTTPS termination, health checks, auto-scaling integration
- ✅ **Auto-Scaling**: Scale 1-4 tasks based on CPU/memory utilization
- ✅ **ACM Certificate**: Free SSL/TLS certificate from AWS (*.mosaicmeshai.com)
- ✅ **Full Stack Deployment**: Backend AND frontend included in Phase 5.15
- ✅ **Auto-Deploy on Master**: Continuous deployment enforces test quality
- ✅ **Blue-Green Deployment**: Zero-downtime deployments (deferred to Phase 5.16)

### What Gets Built

1. **ECS Service** - Long-running backend application (not one-time tasks)
2. **Application Load Balancer (ALB)** - HTTPS traffic distribution
3. **Target Group** - Health checks and traffic routing
4. **Auto-Scaling Policies** - Scale based on CPU/memory
5. **ACM Certificate** - Free SSL/TLS for *.mosaicmeshai.com (Namecheap DNS)
6. **S3 + CloudFront** - Frontend static hosting
7. **GitHub Actions Workflows** - Auto-deploy backend + frontend, migrations
8. **Security Groups** - ALB → ECS, allow HTTPS traffic

## ✅ Pre-Implementation Discussions Complete (November 27, 2025)

### Discussion 1: Cost Review and Optimization - DECIDED

**Decision**: Pragmatic approach - Keep current architecture, defer optimizations to Phase 5.16

**Cost Target**: $122-154/month (down from $129-161/month estimate)

**Decisions Made**:
1. ✅ **Bastion Host**: Stopped when not needed (saves $6/month) - Already done November 26, 2025
2. ✅ **NAT Gateway**: Keep current architecture ($32/month)
   - Rationale: Simpler than VPC Endpoints, already working, saves ~10 hours setup time
   - Future: Can optimize in Phase 5.16 if costs become a concern
3. ✅ **ECS Tasks**: Start with 2 tasks for high availability ($39/month base)
   - Rationale: Validates HA architecture, avoids downtime, proper production setup
4. ✅ **Pricing Model**: Stay on-demand (no reserved instances yet)
   - Rationale: Flexibility during development, don't know usage patterns yet
   - Future: After 6 months of production data, consider reserved instances/savings plans

**Deferred Optimizations** (Phase 5.16):
- NAT Gateway → VPC Endpoints (potential $22-25/month savings)
- RDS Reserved Instance (potential $8-10/month savings)
- ECS Compute Savings Plan (potential $8-12/month savings)

### Discussion 2: Automation Opportunities - DECIDED

**Decision**: Pragmatic automation - Automate where it matters, manual where appropriate

**Decisions Made**:
1. ✅ **Infrastructure Scripts**: Keep bash scripts (consistent with Phase 5.14)
   - Rationale: Simple, working well, fast to implement, consistent pattern
   - Future: Can migrate to Terraform in Phase 5.16 if complexity grows
2. ✅ **DNS Configuration**: Keep manual Namecheap DNS updates
   - Rationale: Infrequent changes (one-time per fork), reliable, takes 5-10 minutes
   - Future: If deploying many forks, consider Namecheap API automation
3. ✅ **ACM Certificate**: Keep manual validation (one-time CNAME in Namecheap)
   - Rationale: One-time setup per domain, takes 5 minutes, not worth automation effort
4. ✅ **Rollback Workflow**: Add manual-trigger GitHub Actions workflow
   - Benefit: Automated execution of rollback steps, reduces human error
5. ❌ **CloudFront Invalidation**: NOT needed (we use versioning strategy)
   - Rationale: Manual version increments (main-0.0.1.css → main-0.0.2.css) = new URLs = no cache issues
   - Versioned URLs are superior to cache invalidation (no race conditions, always works)
6. ❌ **Slack Notifications**: Not needed (email is sufficient)

**Result**: Maximum automation where it matters (deployments via GitHub Actions), manual where appropriate (one-time DNS/certificate setup)

---

## Prerequisites (Already Complete ✅)

- ✅ Phase 5.14 complete (ECS cluster, ECR, GitHub Actions, NAT Gateway)
- ✅ RDS PostgreSQL with 3 databases and 57 tables each
- ✅ All 740 tests passing in CI/CD
- ✅ Production Docker image in ECR (692 MB, optimized)
- ✅ Secrets Manager with all credentials
- ✅ VPC with public/private subnets
- ✅ CloudWatch logging configured

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Internet                                │
└────────────┬───────────────────────────────────┬────────────────┘
             │                                   │
             │ HTTPS (443)                       │ HTTPS (443)
             │                                   │
┌────────────▼─────────────────┐   ┌────────────▼────────────────┐
│  Namecheap DNS (CNAME)       │   │  CloudFront CDN             │
│  startupwebapp-api           │   │  startupwebapp              │
│  .mosaicmeshai.com → ALB     │   │  .mosaicmeshai.com          │
└────────────┬─────────────────┘   └────────────┬────────────────┘
             │                                   │
┌────────────▼─────────────────────────────────┐│
│       Application Load Balancer (ALB)        ││
│          (Public Subnets × 2 AZs)            ││
│  ┌──────────────────────────────────────┐   ││
│  │  Listener: HTTPS:443 → Target Group  │   ││
│  │  SSL: ACM (*.mosaicmeshai.com)       │   ││
│  │  Health: /health → 200 OK (30s)      │   ││
│  └──────────────────────────────────────┘   ││
└────────────┬─────────────────────────────────┘│
             │ HTTP (8000)                       │
┌────────────▼─────────────────────────────────┐│
│          Target Group (ECS Tasks)            ││
└────────────┬─────────────────────────────────┘│
             │                                   │
┌────────────▼─────────────────────────────────┐│
│       ECS Service (Fargate)                  ││
│       (Private Subnets × 2 AZs)              ││
│  ┌──────────────────────────────────────┐   ││
│  │  Count: 2 tasks (1 per AZ)           │   ││
│  │  Min: 1, Max: 4 (auto-scaling)       │   ││
│  │  CPU: 0.5 vCPU, Memory: 1 GB         │   ││
│  │  Port: 8000 (gunicorn)               │   ││
│  └──────────────────────────────────────┘   ││
└───────┬──────────────────┬───────────────────┘│
        │                  │                     │
        ▼                  ▼                     ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Secrets Mgr  │  │ RDS Postgres │  │  S3 Bucket       │
│ (credentials)│  │ (multi-tenant│  │  (frontend files)│
└──────────────┘  └──────────────┘  └──────────────────┘
```

## Implementation Steps

### Estimated Timeline: 9-10 hours (implementation only, see full timeline at end)

---

### Step 1: Create Application Load Balancer (ALB) ✅ COMPLETE (November 27, 2025)

**Goal**: Create ALB in public subnets to handle HTTPS traffic

**Completed**:
- ✅ Created `scripts/infra/create-alb.sh` and `destroy-alb.sh`
- ✅ ALB created in public subnets (both AZs)
- ✅ HTTP listener (port 80) → redirect to HTTPS
- ✅ Target group created for ECS service (port 8000, health check `/health`)
- ✅ Security groups configured (ALB SG, Backend SG updated)
- ✅ Full create → destroy → recreate cycle tested

**Resources Created**:
- ALB: `startupwebapp-alb` (DNS: startupwebapp-alb-978036304.us-east-1.elb.amazonaws.com)
- Target Group: `startupwebapp-tg`
- ALB Security Group: `sg-07bb8f82ec378f6d4`
- HTTP Listener: Port 80 → redirect to HTTPS

**Cost**: ~$16/month (ALB) + ~$0.008/LCU-hour

---

### Step 2: Request ACM Certificate ✅ COMPLETE (November 27, 2025)

**Goal**: Get free SSL/TLS certificate for custom domain

**Completed**:
- ✅ Created `scripts/infra/create-acm-certificate.sh` and `destroy-acm-certificate.sh`
- ✅ Requested wildcard certificate: `*.mosaicmeshai.com`
- ✅ DNS validation CNAME added to Namecheap
- ✅ Certificate status: ISSUED

**Resources Created**:
- ACM Certificate: `*.mosaicmeshai.com` (ARN: arn:aws:acm:us-east-1:853463362083:certificate/51913dd1-b907-49cd-bd0e-4b04218c4d30)

**Cost**: $0 (ACM certificates are free)

---

### Step 3: Create HTTPS Listener ✅ COMPLETE (November 28, 2025)

**Goal**: Add HTTPS listener to ALB with TLS termination

**Completed**:
- ✅ Created `scripts/infra/create-alb-https-listener.sh` and `destroy-alb-https-listener.sh`
- ✅ HTTPS listener on port 443 with ACM certificate
- ✅ SSL Policy: ELBSecurityPolicy-TLS13-1-2-2021-06 (TLS 1.2/1.3)
- ✅ Routes to target group on port 8000
- ✅ Full destroy → recreate cycle tested

**Resources Created**:
- HTTPS Listener: Port 443 with TLS termination

**Cost**: Included in ALB cost

---

### Step 4: Configure Namecheap DNS ✅ COMPLETE (November 28, 2025)

**Goal**: Point custom subdomains to AWS resources

**Completed**:
- ✅ Added CNAME: `startupwebapp-api` → `startupwebapp-alb-978036304.us-east-1.elb.amazonaws.com`
- ✅ TTL: Automatic
- ✅ Verified via nslookup: `startupwebapp-api.mosaicmeshai.com` resolves to ALB

**Resources Created**:
- CNAME record in Namecheap (no AWS resources)

**Cost**: $0 (no AWS charges for DNS queries to Namecheap)

**Note**: CloudFront CNAME (`startupwebapp` → CloudFront) will be added in Step 7.

---

### Step 5: Create ECS Service Task Definition ✅ COMPLETE (November 28, 2025)

**Goal**: Define long-running service task (not migration task)

**Completed**:
- ✅ Created `scripts/infra/create-ecs-service-task-definition.sh` and `destroy-ecs-service-task-definition.sh`
- ✅ Task family: `startupwebapp-service-task`
- ✅ Command: `gunicorn StartupWebApp.wsgi:application --workers 3 --timeout 30 --bind 0.0.0.0:8000`
- ✅ Resources: 0.5 vCPU, 1 GB memory
- ✅ Port mappings: containerPort 8000
- ✅ Secrets Manager integration (DATABASE_PASSWORD, DATABASE_USER, DATABASE_HOST, DATABASE_PORT)
- ✅ Health check: `curl -f http://localhost:8000/health`
- ✅ CloudWatch log group: `/ecs/startupwebapp-service`
- ✅ Full destroy → recreate cycle tested

**Resources Created**:
- Task Definition: `startupwebapp-service-task:2`
- CloudWatch Log Group: `/ecs/startupwebapp-service`

**Cost**: $0 (task definition free; tasks cost ~$0.027/hour)

---

### Step 6: Create ECS Service 🚧 SCRIPTS READY - DEPLOY NEXT

**Goal**: Deploy long-running service with 2 tasks across 2 AZs

**Scripts Created** (November 28, 2025):
- ✅ `scripts/infra/create-ecs-service.sh` - Creates ECS service with full configuration
- ✅ `scripts/infra/destroy-ecs-service.sh` - Graceful teardown of service

**Configuration**:
- Service Name: `startupwebapp-service`
- Desired count: 2 (one per AZ for HA)
- Launch type: Fargate
- Network: Private subnets, backend security group
- Load balancer: Connected to target group
- Health check grace period: 120 seconds

**Deployment Configuration**:
- Rolling update: 100% minimum healthy, 200% maximum
- Circuit breaker: Enabled with automatic rollback
- ECS Exec: Enabled (for debugging)

**To Deploy**:
```bash
./scripts/infra/create-ecs-service.sh
```

**Resources Created**:
- ECS Service: `startupwebapp-service`
- Running Tasks: 2 (one per AZ)
- Target group registration for ALB health checks

**Access URLs** (after deployment):
- HTTPS: `https://startupwebapp-api.mosaicmeshai.com`
- Health Check: `https://startupwebapp-api.mosaicmeshai.com/health`

**Cost**: ~$39/month (2 tasks × 0.5 vCPU × 1GB × $0.027/hour × 730 hours)

---

### Step 6: Configure Auto-Scaling ⏱️ 45 minutes

**Goal**: Scale ECS tasks based on CPU/memory utilization

**Tasks**:
1. Create infrastructure script: `scripts/infra/create-ecs-autoscaling.sh`
2. Create Application Auto Scaling target:
   - Service: `startupwebapp-service`
   - Min capacity: 1 task
   - Max capacity: 4 tasks
3. Create CPU-based scaling policy:
   - Target: 70% CPU utilization
   - Scale out: +1 task when above target for 3 minutes
   - Scale in: -1 task when below target for 5 minutes
4. Create memory-based scaling policy:
   - Target: 80% memory utilization
   - Same scale out/in rules
5. Test: Generate load → verify scaling → verify scale-down
6. Create destroy script: `scripts/infra/destroy-ecs-autoscaling.sh`

**Resources Created**:
- Auto Scaling Target
- CPU Scaling Policy
- Memory Scaling Policy

**Cost**: $0 (auto-scaling free; pay for additional tasks when scaled)

---

### Step 7: Setup S3 + CloudFront for Frontend ⏱️ 60 minutes

**Goal**: Create static hosting infrastructure for frontend

**Tasks**:
1. Create infrastructure script: `scripts/infra/create-frontend-hosting.sh`
2. Create S3 bucket for frontend files
3. Configure S3 bucket:
   - Enable static website hosting
   - Set bucket policy for CloudFront access
   - Configure CORS for API access
4. Create CloudFront distribution:
   - Origin: S3 bucket
   - SSL Certificate: Use same ACM cert (*.mosaicmeshai.com)
   - Cache behaviors: HTML (no-cache), JS/CSS (1 year)
   - Custom domain: startupwebapp.mosaicmeshai.com
5. Configure cache-control headers:
   - HTML: `Cache-Control: no-cache, must-revalidate`
   - JS/CSS: `Cache-Control: public, max-age=31536000`
6. Create destroy script: `scripts/infra/destroy-frontend-hosting.sh`
7. Test: Upload test file → verify CloudFront serves it

**Resources Created**:
- S3 Bucket: `startupwebapp-frontend-prod`
- CloudFront Distribution: `startupwebapp.mosaicmeshai.com`

**Cost**: ~$1-5/month (S3 storage + CloudFront requests)

---

### Step 8: Add Health Check Endpoint ⏱️ 30 minutes

**Goal**: Add `/health` endpoint for ALB health checks

**Tasks**:
1. Create Django view: `StartupWebApp/views/health.py`
2. Add URL route: `/health` → `health_check`
3. Check database connectivity
4. Check Secrets Manager connectivity (optional)
5. Return 200 OK with JSON: `{"status": "healthy", "database": "ok"}`
6. Write tests: Unit test + functional test
7. Deploy to ECS via GitHub Actions

**Files Created**:
- `StartupWebApp/views/health.py`
- `StartupWebApp/tests/test_health.py`

**Cost**: $0 (no additional infrastructure)

---

### Step 9: Create Production Deployment Workflow ⏱️ 120 minutes

**Goal**: Auto-deploy backend + frontend on merge to master with migrations

**Tasks**:
1. Create new workflow: `.github/workflows/deploy-production.yml`
2. **Trigger**: Automatic on merge to `master` branch (enforces test quality)
3. Jobs (sequential):
   - **Job 1 - Test**:
     - Clone frontend repo for functional tests
     - Run Flake8 linting
     - Run 712 unit tests (PostgreSQL)
     - Run 28 functional tests (validates backend + frontend)
   - **Job 2 - Migrate**:
     - Run Django migrations on RDS (startupwebapp_prod)
     - Monitor CloudWatch logs
     - If migration fails → STOP deployment
   - **Job 3 - Deploy Backend**:
     - Build production Docker image
     - Tag with git commit SHA
     - Push to ECR
     - Update ECS service with new task definition
     - Wait for tasks to become healthy
   - **Job 4 - Deploy Frontend**:
     - Trigger frontend workflow via repository_dispatch
     - Frontend workflow: ESLint → QUnit → S3 upload
     - Wait for frontend deployment complete
   - **Job 5 - Verify**:
     - Check health endpoint
     - Basic smoke tests
4. Add manual rollback workflow (separate file)
5. Set 20-minute timeout for entire workflow

**Files Created**:
- `.github/workflows/deploy-production.yml` (auto-deploy on master merge)
- `.github/workflows/rollback-production.yml` (manual trigger)

**Cost**: $0 (GitHub Actions free for public repos)

---

### Step 10: Update Django Settings for Production ⏱️ 30 minutes

**Goal**: Ensure Django is production-ready with correct settings

**Tasks**:
1. Review `settings_production.py`:
   - ALLOWED_HOSTS: Add ALB DNS and custom domain `startupwebapp-api.mosaicmeshai.com`
   - CORS_ORIGIN_WHITELIST: Add frontend domain `https://startupwebapp.mosaicmeshai.com`
   - SESSION_COOKIE_DOMAIN: Set to `.mosaicmeshai.com`
   - CSRF_TRUSTED_ORIGINS: Add `https://startupwebapp-api.mosaicmeshai.com`
2. Add gunicorn configuration:
   - Workers: 3 (2 × CPU cores + 1)
   - Worker class: sync
   - Timeout: 30 seconds
   - Access log: CloudWatch
3. Test locally with production settings
4. Commit and deploy

**Files Modified**:
- `StartupWebApp/settings_production.py`

**Cost**: $0

---

### Step 11: Verification & Documentation ⏱️ 60 minutes

**Goal**: Verify production deployment and document

**Tasks**:
1. Smoke tests:
   - `curl https://startupwebapp-api.mosaicmeshai.com/health` → 200 OK
   - Test frontend loads: `https://startupwebapp.mosaicmeshai.com`
   - Test login endpoint
   - Test order creation
   - Test Stripe integration
   - Test database connectivity (all 3 databases)
2. Load testing (optional, basic):
   - Use `ab` or `wrk` to generate load
   - Verify auto-scaling triggers
   - Verify tasks scale back down
3. Monitor CloudWatch:
   - Verify logs flowing
   - Check for errors
   - Verify metrics (CPU, memory, request count)
4. Update documentation:
   - SESSION_START_PROMPT.md
   - PROJECT_HISTORY.md
   - Infrastructure README
5. Create Phase 5.15 summary

---

## Cost Estimation

### New Monthly Costs (Phase 5.15)

| Resource | Cost | Notes |
|----------|------|-------|
| Application Load Balancer | ~$16/month | Fixed cost |
| ALB LCU (Load Balancer Units) | ~$5-10/month | Based on traffic |
| ECS Service (2 tasks) | ~$39/month | 2 × 0.5 vCPU × 1GB × 730 hours |
| Auto-scaling (peak: 4 tasks) | ~$39/month | Only when scaled, assume 50% time |
| S3 + CloudFront (frontend) | ~$1-5/month | Static hosting |
| ACM Certificate | $0 | Free |
| DNS (Namecheap) | $0 | Using existing domain |
| **Total New Costs** | **~$61-93/month** | Depends on traffic and scaling |

### Total Infrastructure Cost

| Component | Monthly Cost |
|-----------|--------------|
| **Phase 5.13-5.14** | $68/month |
| VPC, NAT Gateway, RDS, ECS Cluster | (baseline) |
| **Phase 5.15 (New)** | $61-93/month |
| ALB, ECS Service, S3, CloudFront | (new) |
| **Total** | **$129-161/month** |

### Cost Optimization Opportunities

1. **NAT Gateway** ($32/month):
   - Could use VPC Endpoints for ECR/S3 ($7-10/month)
   - Savings: ~$22-25/month
   - Trade-off: More complex setup

2. **RDS Instance** ($26/month):
   - Currently db.t4g.small
   - Could use Reserved Instance (1-year): Save 30-40%
   - Savings: ~$8-10/month

3. **ECS Reserved Capacity**:
   - Currently using on-demand Fargate pricing
   - Could use Compute Savings Plans (1-year): Save 20-30%
   - Savings: ~$8-12/month on ECS tasks

### Estimated Timeline

- **Planning**: 1 hour (this document)
- **Implementation**: 9-10 hours (Steps 1-11)
- **Testing**: 2-3 hours (verification, smoke tests)
- **Documentation**: 1-2 hours
- **Total**: **13-16 hours**

## Security Considerations

### Implemented in Phase 5.15 ✅

- ✅ **HTTPS Only**: All traffic encrypted with TLS 1.2+ (ACM certificate)
- ✅ **Private Subnets**: ECS tasks have no public IPs, only accessible via ALB
- ✅ **Security Groups**: Least privilege (ALB → ECS, ECS → RDS)
- ✅ **Secrets Manager**: All credentials from Secrets Manager (not environment variables)
- ✅ **IAM Roles**: ECS tasks use roles (no hardcoded AWS credentials)
- ✅ **Health Checks**: ALB monitors task health, replaces unhealthy tasks
- ✅ **CloudWatch Logs**: All application logs centralized
- ✅ **Auto-scaling**: Handles traffic spikes without manual intervention

### To Implement in Phase 5.16 ⏭️

- ⏭️ **WAF (Web Application Firewall)**: Block common attacks (SQL injection, XSS)
- ⏭️ **Rate Limiting**: Prevent DDoS and abuse
- ⏭️ **AWS Shield**: DDoS protection (Standard is free, Advanced is $3,000/month)
- ⏭️ **GuardDuty**: Threat detection for suspicious activity
- ⏭️ **CloudTrail**: Audit all API calls
- ⏭️ **Secrets Rotation**: Automatic password rotation

## Rollback Procedure

### Quick Rollback (5 minutes)

If deployment fails or production issues occur:

1. **Rollback ECS Service**:
   ```bash
   # Get previous task definition revision
   PREVIOUS_REVISION=$(aws ecs describe-services \
     --cluster startupwebapp-cluster \
     --services startupwebapp-service \
     --query 'services[0].deployments[1].taskDefinition' \
     --output text)

   # Update service to previous revision
   aws ecs update-service \
     --cluster startupwebapp-cluster \
     --service startupwebapp-service \
     --task-definition $PREVIOUS_REVISION \
     --force-new-deployment
   ```

2. **Monitor rollback**:
   - Watch CloudWatch logs for errors
   - Check ALB health checks pass
   - Verify tasks reach "RUNNING" state

3. **Verify**:
   - `curl https://startupwebapp-api.mosaicmeshai.com/health`
   - Check critical endpoints work

### Complete Rollback (30 minutes)

If entire Phase 5.15 needs to be torn down:

1. **Delete ECS Service**: `./scripts/infra/destroy-ecs-service.sh`
2. **Delete ALB**: `./scripts/infra/destroy-alb.sh`
3. **Delete S3 + CloudFront**: `./scripts/infra/destroy-frontend-hosting.sh`
4. **Remove DNS Records**: Manually remove CNAME records in Namecheap
5. **Delete ACM Certificate**: `./scripts/infra/destroy-acm-certificate.sh`
6. **Assess damage**: Phase 5.14 infrastructure remains intact

**Risk**: Low - No database changes, all data safe

## Success Criteria

### Must Have (Blocking) ✅

- [ ] Application Load Balancer created and accessible
- [ ] HTTPS working with valid ACM certificate
- [ ] ECS service running with 2 tasks (one per AZ)
- [ ] Health check passing: `/health` endpoint returns 200 OK
- [ ] Auto-scaling configured and tested (scale out and scale in)
- [ ] GitHub Actions workflow deploys service successfully
- [ ] All 740 tests pass before deployment
- [ ] Production domain resolves and serves traffic
- [ ] Database connectivity verified (all 3 databases)
- [ ] CloudWatch logs flowing from ECS tasks
- [ ] Zero downtime during rolling deployments

### Should Have (Important) ⚙️

- [ ] Auto-scaling tested under load
- [ ] Rollback procedure tested and documented
- [ ] Smoke tests pass (login, orders, Stripe)
- [ ] CloudWatch alarms configured for service health
- [ ] Infrastructure scripts tested (create → destroy → recreate)
- [ ] Documentation complete (SESSION_START_PROMPT, PROJECT_HISTORY, README)

### Nice to Have (Future) 💡

- [ ] WAF rules configured (Phase 5.16)
- [ ] Blue-green deployment strategy (Phase 5.16)
- [ ] Load testing with realistic traffic patterns (Phase 5.16)
- [ ] Automated rollback on deployment failure (Phase 5.16)
- [ ] Frontend optimization (image compression, CDN caching policies)

## Deployment Coordination Strategy ✅ DECIDED

### Architecture Decisions (November 26, 2025)

**Domain Configuration**:
- Backend: `startupwebapp-api.mosaicmeshai.com` (subdomain pattern for scalability)
- Frontend: `startupwebapp.mosaicmeshai.com` (S3 + CloudFront)
- Pattern for forks: `{fork}-api.mosaicmeshai.com` and `{fork}.mosaicmeshai.com`
- DNS: Managed via Namecheap, ACM certificate for `*.mosaicmeshai.com`

**Deployment Trigger**:
- Backend: **Auto-deploy on merge to master** (enforces test quality)
- Frontend: **Backend-triggered or manual only** (no auto-deploy on frontend merge)
- Database: Use `startupwebapp_prod` as default

**Frontend Included in Phase 5.15**: Yes (S3 + CloudFront)

---

### Coordinated Deployment Workflow

**Problem**: Backend API changes and frontend JS/CSS must deploy atomically to avoid breaking production

**Solution**: Frontend merges first (no deploy), backend tests validate compatibility, backend merge deploys both

#### For Coordinated Changes (Backend + Frontend)

```
Step 1: Develop both PRs
- Backend PR: feature/new-api (includes NEW functional test)
- Frontend PR: feature/new-api (includes new JS calling new API)

Step 2: Merge frontend FIRST
- Frontend PR reviewed → merge to frontend master
- Frontend does NOT auto-deploy (manual/backend-triggered only)
- Frontend changes sit in master but not in production yet ✅

Step 3: Backend PR validation
- Backend CI clones frontend master branch
- Runs 712 unit tests
- Runs 28 functional tests (validates NEW backend + NEW frontend)
- Tests PASS ✅ (proves compatibility)

Step 4: Backend merge triggers deployment
- Backend merges to master → auto-deploy workflow starts
- Tests run AGAIN (safety check - catches last-minute frontend changes)
- Deploy backend to ECS → wait for healthy
- Trigger frontend deployment → deploys frontend master
- Both deploy in correct order (backend first, then frontend) ✅
```

#### For Backend-Only Changes

```
- Backend PR merged → auto-deploy
- Backend deploys → triggers frontend deploy (even if unchanged)
- Simple, no coordination needed
```

#### For Frontend-Only Changes

```
- Frontend PR merged to master (no auto-deploy)
- Manual trigger of frontend workflow
- Frontend deploys (no backend changes)
```

---

### Edge Cases & Risk Mitigation

**Edge Case 1: Frontend master changes between backend test and deploy**
- **Scenario**: Frontend changes after backend tests pass but before deploy
- **Window**: Very short (2-5 minutes)
- **Mitigation**: Tests run AGAIN in deploy workflow (catches breaking changes)
- **Acceptance**: Acknowledged risk, acceptable for rare edge case

**Edge Case 2: Frontend deployment fails**
- **Scenario**: Backend deploys ✅, frontend deploy fails ❌
- **Mitigation**: Auto-retry frontend deploy (3 attempts)
- **Fallback**: Alert + manual intervention if all retries fail
- **Impact**: Brief inconsistency (monitored)

**Edge Case 3: Backend-only changes trigger frontend deploy**
- **Scenario**: Backend change doesn't need frontend update
- **Behavior**: Frontend deploys anyway (no changes)
- **Cost**: 2-3 minutes deployment time (acceptable)
- **Future**: Could optimize to skip if frontend SHA unchanged

**Edge Case 4: Frontend-only changes**
- **Scenario**: CSS/HTML changes, no backend needed
- **Behavior**: Manual trigger of frontend workflow
- **Safety**: ESLint + QUnit tests validate before deploy

---

### Cache Busting Strategy

**Manual Version Incrementing** (existing pattern):
- CSS: `main-0.0.1.css` → `main-0.0.2.css` → `main-0.0.3.css`
- JS: `index-0.0.2.js` → `index-0.0.3.js` → `index-0.0.4.js`
- HTML files reference versioned assets: `<script src="/js/index-0.0.3.js">`

**No CloudFront Invalidation Needed**:
- Versioned files = different URLs = always fetched fresh
- HTML served with `Cache-Control: no-cache, must-revalidate`
- JS/CSS served with `Cache-Control: public, max-age=31536000` (1 year cache, safe because versioned)

---

### Testing Requirements

**Backend Workflow**:
1. ✅ Flake8 linting (backend code quality)
2. ✅ 712 unit tests (PostgreSQL)
3. ✅ 28 functional tests (validates backend + frontend together)
4. ✅ Tests run in PR AND in deploy workflow (double safety)

**Frontend Workflow**:
1. ✅ ESLint linting (frontend code quality)
2. ✅ QUnit tests (frontend unit tests)
3. ✅ Deployment to S3 + CloudFront

---

## Open Questions / Decisions Needed

~~All questions resolved as of November 26, 2025~~

**Monitoring**: CloudWatch for Phase 5.15 (can add Datadog/New Relic in Phase 5.16)

---

### Database Migration Strategy ✅ DECIDED

**Approach**: Auto-migrations in deploy workflow (lean into automation)

**Deployment Workflow Order**:
```
1. Run all tests (validates migration + code together)
2. Run migrations on RDS (for selected database)
3. Deploy backend to ECS (new code expects migrated schema)
4. Deploy frontend to S3/CloudFront
```

**Safety Rules for Phase 5.15**:
- ✅ **Backward compatible migrations only**:
  - ✅ ADD COLUMN (old code ignores new column)
  - ✅ CREATE TABLE (old code doesn't use it)
  - ✅ ADD INDEX with CONCURRENTLY (doesn't lock table)
  - ❌ DROP COLUMN (breaks old code during rollback)
  - ❌ RENAME COLUMN (breaks old code during rollback)
  - ❌ ALTER COLUMN TYPE (can break old code)
- ✅ **Use `CREATE INDEX CONCURRENTLY`** (avoids table locks)
- ✅ **Test migrations on production snapshot** before merging PR
- ✅ **Keep migrations fast** (<30 seconds ideally, <5 minutes max)
- ✅ **Set 20-minute timeout** for deploy workflow (handles long migrations)
- ✅ **Monitor CloudWatch logs** during migration execution

**Safety Nets**:
- If migration fails → Django rolls back transaction → Deploy stops ✅
- Functional tests validate schema compatibility before deploy ✅
- Manual rollback procedure available if needed (Phase 5.15)
- CloudWatch alarms for migration duration

**Phase 5.16 Enhancements**:
- Blue-green deployment (migrations compatible with both versions)
- Automatic rollback if post-deploy health check fails
- Migration testing on RDS read replica before production
- Multi-step migrations for destructive changes

**Rollback Considerations**:
- Backend code can be rolled back quickly (previous ECS task definition)
- Migrations may need manual reversal if destructive
- Backward compatible migrations minimize rollback complexity

---

### Rollback Strategy ✅ DECIDED

**Rollback Scenario A: Backend Deploy Fails**
- **Trigger**: ECS service update fails, tasks won't start
- **Procedure**:
  - Automatic via ECS circuit breaker (configured in service)
  - Manual fallback:
    ```bash
    aws ecs update-service \
      --cluster startupwebapp-cluster \
      --service startupwebapp-service \
      --task-definition startupwebapp-service-task:PREVIOUS_REVISION \
      --force-new-deployment
    ```

**Rollback Scenario B: Frontend Deploy Fails**
- **Trigger**: S3 upload fails, CloudFront distribution broken
- **Procedure**:
  - Auto-retry frontend deploy (3 attempts in workflow)
  - Manual: Re-run frontend workflow with previous commit SHA

**Rollback Scenario C: Post-Deploy Smoke Test Fails**
- **Trigger**: Health checks pass but application broken
- **Procedure**:
  1. Rollback backend (revert ECS task definition)
  2. Rollback frontend (redeploy previous version)
  3. Investigate logs, fix issue, redeploy

**Rollback Scenario D: Migration Succeeded But Need to Rollback Code**
- **Trigger**: Deploy succeeded but bug discovered later
- **Procedure**:
  - If migration was backward compatible → rollback code only (safe) ✅
  - If migration was destructive → manual migration reversal required ⚠️
  - Backward compatibility rule minimizes this scenario

**Implementation**:
- Manual rollback workflows for Phase 5.15 (GitHub Actions manual trigger)
- Phase 5.16: Automated rollback based on CloudWatch metrics
- CloudWatch alarms notify on deployment failures

---

### Frontend API URL Configuration ✅ DECIDED

**Current Implementation**: Frontend uses hostname-based API URL detection (`js/index-0.0.2.js`)

**Required Change for Production**:
```javascript
case 'startupwebapp.mosaicmeshai.com':
    api_url = 'https://startupwebapp-api.mosaicmeshai.com';
    break;
```

**Pattern for Forks**:
- `healthtech.mosaicmeshai.com` → `https://healthtech-api.mosaicmeshai.com`
- `fintech.mosaicmeshai.com` → `https://fintech-api.mosaicmeshai.com`

---

### GitHub Repository Access ✅ DECIDED

**Backend Workflow Triggers Frontend Deployment**:
- Backend uses GitHub Personal Access Token (PAT) to trigger frontend workflow
- Uses `repository_dispatch` event

**Setup Steps**:
1. Create GitHub PAT (classic) with `repo` scope
2. Add as secret in backend repo: `FRONTEND_REPO_TOKEN`
3. Backend workflow uses token to trigger frontend deployment

**Implementation**:
```yaml
- name: Trigger frontend deployment
  uses: peter-evans/repository-dispatch@v2
  with:
    token: ${{ secrets.FRONTEND_REPO_TOKEN }}
    repository: bartgottschalk/startup_web_app_client_side
    event-type: deploy-production
```

---

**Monitoring**: CloudWatch for Phase 5.15 (can add Datadog/New Relic in Phase 5.16)

## Phase 5.16 Preview - Production Hardening

After Phase 5.15, the next phase will focus on:

1. **WAF (Web Application Firewall)**: Protect against common attacks
2. **Enhanced Monitoring**: Datadog/New Relic integration (optional)
3. **Load Testing**: Realistic traffic patterns, identify bottlenecks
4. **Blue-Green Deployment**: Zero-downtime deployments with instant rollback
5. **Disaster Recovery**: Backup/restore procedures, RTO/RPO targets
6. **Performance Optimization**: Caching, CDN, database indexing
7. **Cost Optimization**: Reserved instances, Savings Plans

## References

- **AWS ECS Service**: https://docs.aws.amazon.com/ecs/latest/developerguide/service_definition_parameters.html
- **Application Load Balancer**: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/
- **ACM Certificates**: https://docs.aws.amazon.com/acm/latest/userguide/
- **Route 53**: https://docs.aws.amazon.com/route53/
- **Auto Scaling**: https://docs.aws.amazon.com/autoscaling/application/userguide/
- **Gunicorn Production**: https://docs.gunicorn.org/en/stable/deploy.html
- **Django Deployment Checklist**: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

---

**Document Status**: 🚧 Implementation In Progress - Steps 1-5 Complete
**Author**: Claude Code (AI Assistant) & Bart Gottschalk
**Last Updated**: November 28, 2025
**Version**: 1.2 (Implementation In Progress)
**Next Step**: Step 6 - Create ECS Service
