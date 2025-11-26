# Phase 5.15: Full Production Deployment - ECS Service, ALB, Auto-Scaling

**Date**: November 26, 2025
**Status**: 📋 Planned - Ready to Begin
**Branch**: TBD (`feature/phase-5-15-production-deployment`)
**Version**: 1.0 (Planning Phase)
**Priority**: HIGH - Production deployment

## Executive Summary

Phase 5.15 deploys the full StartupWebApp application to production using AWS ECS Fargate with an Application Load Balancer (ALB), auto-scaling, and HTTPS. This phase builds on Phase 5.14's CI/CD infrastructure to deploy a long-running service (not just migration tasks).

### Key Decisions

- ✅ **ECS Service**: Long-running Fargate tasks (vs one-time migration tasks)
- ✅ **Application Load Balancer**: HTTPS termination, health checks, auto-scaling integration
- ✅ **Auto-Scaling**: Scale 1-4 tasks based on CPU/memory utilization
- ✅ **ACM Certificate**: Free SSL/TLS certificate from AWS
- ✅ **Phased Deployment**: Backend first, frontend later (de-risk)
- ✅ **Blue-Green Deployment**: Zero-downtime deployments (deferred to Phase 5.16)

### What Gets Built

1. **ECS Service** - Long-running backend application (not one-time tasks)
2. **Application Load Balancer (ALB)** - HTTPS traffic distribution
3. **Target Group** - Health checks and traffic routing
4. **Auto-Scaling Policies** - Scale based on CPU/memory
5. **ACM Certificate** - Free SSL/TLS for custom domain
6. **Route 53 DNS** - Point domain to ALB
7. **Updated GitHub Actions** - Deploy service (not just migrations)
8. **Security Groups** - ALB → ECS, allow HTTPS traffic

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
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS (443)
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   Route 53 (DNS)                                 │
│           api.startupwebapp.com → ALB                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              Application Load Balancer (ALB)                     │
│                  (Public Subnets × 2 AZs)                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Listener: HTTPS:443 → Target Group                      │   │
│  │  SSL Certificate: ACM (*.startupwebapp.com)              │   │
│  │  Health Check: /health → 200 OK every 30s                │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP (8000)
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      Target Group                                │
│            Registered Targets: ECS Tasks (1-4)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    ECS Service (Fargate)                         │
│                  (Private Subnets × 2 AZs)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Desired Count: 2 tasks (1 per AZ for HA)                │  │
│  │  Min: 1, Max: 4 (auto-scaling)                           │  │
│  │  CPU: 0.5 vCPU, Memory: 1 GB                             │  │
│  │  Port: 8000 (gunicorn)                                   │  │
│  │  Command: gunicorn StartupWebApp.wsgi:application        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
    ┌───────────────┐         ┌──────────────────┐
    │  Secrets Mgr  │         │  RDS PostgreSQL  │
    │  (credentials)│         │  (multi-tenant)  │
    └───────────────┘         └──────────────────┘
```

## Implementation Steps

### Estimated Timeline: 8-10 hours

### Step 1: Create Application Load Balancer (ALB) ⏱️ 60 minutes

**Goal**: Create ALB in public subnets to handle HTTPS traffic

**Tasks**:
1. Create infrastructure script: `scripts/infra/create-alb.sh`
2. Create ALB in public subnets (both AZs for high availability)
3. Create HTTPS listener (port 443)
4. Create HTTP listener (port 80) → redirect to HTTPS
5. Create target group for ECS service
6. Configure health check: `/health` endpoint
7. Update security groups:
   - ALB SG: Allow HTTPS (443) from internet (0.0.0.0/0)
   - ALB SG: Allow HTTP (80) from internet (redirect to HTTPS)
   - Backend SG: Allow port 8000 from ALB SG only
8. Create destroy script: `scripts/infra/destroy-alb.sh`
9. Test: Create → verify → destroy → recreate

**Resources Created**:
- ALB: `startupwebapp-alb`
- Target Group: `startupwebapp-tg`
- ALB Security Group: `startupwebapp-alb-sg`
- Listeners: HTTPS (443), HTTP (80)

**Cost**: ~$16/month (ALB) + ~$0.008/LCU-hour

---

### Step 2: Request ACM Certificate ⏱️ 30 minutes

**Goal**: Get free SSL/TLS certificate for custom domain

**Tasks**:
1. Create infrastructure script: `scripts/infra/create-acm-certificate.sh`
2. Request certificate for: `*.startupwebapp.com` (wildcard)
3. Choose DNS validation (automated with Route 53)
4. Wait for validation (5-30 minutes, automated)
5. Document certificate ARN in aws-resources.env
6. Associate certificate with ALB HTTPS listener

**Resources Created**:
- ACM Certificate: `*.startupwebapp.com`

**Cost**: $0 (ACM certificates are free)

---

### Step 3: Configure Route 53 DNS ⏱️ 30 minutes

**Goal**: Point custom domain to ALB

**Tasks**:
1. Create infrastructure script: `scripts/infra/create-route53-records.sh`
2. Create hosted zone (if not exists): `startupwebapp.com`
3. Create A record: `api.startupwebapp.com` → ALB (alias)
4. Create CNAME for ACM validation (automated by script)
5. Test DNS propagation: `dig api.startupwebapp.com`
6. Verify HTTPS: `curl https://api.startupwebapp.com/health`

**Resources Created**:
- Route 53 Hosted Zone: `startupwebapp.com`
- A Record: `api.startupwebapp.com` → ALB

**Cost**: ~$0.50/month (hosted zone)

---

### Step 4: Create ECS Service Task Definition ⏱️ 45 minutes

**Goal**: Define long-running service task (not migration task)

**Tasks**:
1. Create infrastructure script: `scripts/infra/create-ecs-service-task-definition.sh`
2. Base on existing migration task definition
3. Update command: `gunicorn StartupWebApp.wsgi:application --bind 0.0.0.0:8000 --workers 3`
4. Update resources: 0.5 vCPU, 1 GB memory (more than migration task)
5. Update port mappings: containerPort 8000
6. Keep Secrets Manager integration
7. Add environment variables: DJANGO_SETTINGS_MODULE, DATABASE_NAME
8. Register task definition family: `startupwebapp-service-task`
9. Create destroy script: `scripts/infra/destroy-ecs-service-task-definition.sh`

**Resources Created**:
- Task Definition: `startupwebapp-service-task:1`

**Cost**: $0 (task definition free; tasks cost ~$0.027/hour)

---

### Step 5: Create ECS Service ⏱️ 60 minutes

**Goal**: Deploy long-running service with 2 tasks across 2 AZs

**Tasks**:
1. Create infrastructure script: `scripts/infra/create-ecs-service.sh`
2. Create ECS service in existing cluster
3. Configure:
   - Desired count: 2 (one per AZ for HA)
   - Launch type: Fargate
   - Network: Private subnets, backend security group
   - Load balancer: Connect to target group
   - Health check grace period: 120 seconds
4. Configure deployment:
   - Rolling update: 100% minimum, 200% maximum
   - Circuit breaker: Enable (auto rollback on failure)
5. Create destroy script: `scripts/infra/destroy-ecs-service.sh`
6. Test: Deploy → verify tasks running → health check passing

**Resources Created**:
- ECS Service: `startupwebapp-service`
- Running Tasks: 2 (one per AZ)

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

### Step 7: Add Health Check Endpoint ⏱️ 30 minutes

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

### Step 8: Update GitHub Actions for Service Deployment ⏱️ 90 minutes

**Goal**: Deploy service updates via CI/CD (not just migrations)

**Tasks**:
1. Create new workflow: `.github/workflows/deploy-service.yml`
2. Trigger: Manual dispatch OR merge to main (discuss with user)
3. Jobs:
   - Test: Run all 740 tests
   - Build: Build production image, push to ECR
   - Deploy: Update ECS service with new task definition
   - Verify: Wait for deployment, check health endpoint
4. Deployment strategy:
   - Update task definition with new image
   - Update ECS service (rolling deployment)
   - Wait for tasks to become healthy
   - Monitor CloudWatch logs
5. Add rollback capability (manual trigger)
6. Test: Trigger workflow → verify deployment → verify rollback

**Files Created**:
- `.github/workflows/deploy-service.yml`

**Cost**: $0 (GitHub Actions free for public repos)

---

### Step 9: Update Django Settings for Production ⏱️ 30 minutes

**Goal**: Ensure Django is production-ready with correct settings

**Tasks**:
1. Review `settings_production.py`:
   - ALLOWED_HOSTS: Add ALB DNS and custom domain
   - CORS_ORIGIN_WHITELIST: Add frontend domain
   - SESSION_COOKIE_DOMAIN: Set to `.startupwebapp.com`
   - CSRF_TRUSTED_ORIGINS: Add `https://api.startupwebapp.com`
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

### Step 10: Verification & Documentation ⏱️ 60 minutes

**Goal**: Verify production deployment and document

**Tasks**:
1. Smoke tests:
   - `curl https://api.startupwebapp.com/health` → 200 OK
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
| Route 53 Hosted Zone | ~$0.50/month | One-time setup |
| ACM Certificate | $0 | Free |
| **Total New Costs** | **~$60-80/month** | Depends on traffic and scaling |

### Total Infrastructure Cost

| Component | Monthly Cost |
|-----------|--------------|
| **Phase 5.13-5.14** | $68/month |
| VPC, NAT Gateway, RDS, ECS Cluster | (baseline) |
| **Phase 5.15 (New)** | $60-80/month |
| ALB, ECS Service, Auto-scaling | (new) |
| **Total** | **$128-148/month** |

### Cost Optimization Opportunities

1. **NAT Gateway** ($32/month):
   - Could use VPC Endpoints for ECR/S3 ($7-10/month)
   - Savings: ~$22-25/month
   - Trade-off: More complex setup

2. **RDS Instance** ($26/month):
   - Currently db.t4g.small
   - Could use Reserved Instance (1-year): Save 30-40%
   - Savings: ~$8-10/month

3. **ALB vs ALB + CloudFront**:
   - CloudFront adds $1-5/month but reduces ALB traffic costs
   - Better for static assets (future optimization)

### Estimated Timeline

- **Planning**: 1 hour (this document)
- **Implementation**: 8-10 hours (Steps 1-10)
- **Testing**: 2-3 hours (verification, smoke tests)
- **Documentation**: 1-2 hours
- **Total**: **12-16 hours**

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
   - `curl https://api.startupwebapp.com/health`
   - Check critical endpoints work

### Complete Rollback (30 minutes)

If entire Phase 5.15 needs to be torn down:

1. **Delete ECS Service**: `./scripts/infra/destroy-ecs-service.sh`
2. **Delete ALB**: `./scripts/infra/destroy-alb.sh`
3. **Remove DNS Records**: `./scripts/infra/destroy-route53-records.sh`
4. **Delete ACM Certificate**: `./scripts/infra/destroy-acm-certificate.sh`
5. **Assess damage**: Phase 5.14 infrastructure remains intact

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

- [ ] CloudFront CDN for static assets (Phase 5.16)
- [ ] WAF rules configured (Phase 5.16)
- [ ] Blue-green deployment strategy (Phase 5.16)
- [ ] Load testing with realistic traffic patterns (Phase 5.16)
- [ ] Automated rollback on deployment failure (Phase 5.16)

## Open Questions / Decisions Needed

1. **Domain Name**: Do you own `startupwebapp.com`?
   - If yes: Use it
   - If no: Use ALB DNS for now, add custom domain later

2. **Deployment Trigger**: Auto-deploy on merge to main, or manual only?
   - Recommendation: Manual for now (safety), auto-deploy in Phase 5.16

3. **Frontend Deployment**: Deploy with Phase 5.15 or defer?
   - Recommendation: Defer to separate phase (de-risk)
   - Frontend options: S3+CloudFront, or nginx in ECS

4. **Database Selection**: Which database for production traffic?
   - Use `startupwebapp_prod` by default
   - Allow selection via environment variable

5. **Monitoring**: Basic CloudWatch or add third-party (Datadog, New Relic)?
   - Recommendation: CloudWatch for Phase 5.15, evaluate third-party later

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

**Document Status**: 📋 Planning Complete - Ready for Implementation
**Author**: Claude Code (AI Assistant) & Bart Gottschalk
**Last Updated**: November 26, 2025
**Version**: 1.0 (Planning Phase)
**Next Step**: Review with user, begin Step 1 when ready
