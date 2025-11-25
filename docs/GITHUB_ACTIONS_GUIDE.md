# GitHub Actions Guide for StartupWebApp

**Date**: November 25, 2025
**Purpose**: Step-by-step guide for using GitHub Actions workflows

## Table of Contents

1. [What is GitHub Actions?](#what-is-github-actions)
2. [Our Workflow Explained](#our-workflow-explained)
3. [Setting Up GitHub Secrets](#setting-up-github-secrets)
4. [How to Run Migrations](#how-to-run-migrations)
5. [Reading Workflow Results](#reading-workflow-results)
6. [Troubleshooting](#troubleshooting)

---

## What is GitHub Actions?

GitHub Actions is an automation platform built into GitHub. Think of it as a robot that:
- Lives in GitHub's cloud
- Watches your repository for events (pushes, pull requests, manual triggers)
- Runs commands automatically when triggered
- Reports back with success or failure

**Key Benefits:**
- **Consistency**: Same steps run every time (no human error)
- **Speed**: Tests run in parallel, faster than local
- **Visibility**: Everyone on the team sees results
- **Free**: GitHub provides 2,000 free minutes/month for private repos

---

## Our Workflow Explained

### File Location
`.github/workflows/run-migrations.yml`

### What It Does

```
┌─────────────────────────────────────────────────┐
│  You click "Run workflow" in GitHub UI          │
│  and select a database                          │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  JOB 1: Test Suite                              │
│  ✓ Spin up PostgreSQL container                │
│  ✓ Install Python 3.12 and dependencies        │
│  ✓ Run flake8 linting (code quality)           │
│  ✓ Run 712 unit tests (parallel)               │
│  ✓ Run 28 functional tests (Selenium)          │
│  Duration: ~5-7 minutes                         │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  JOB 2: Build & Push Docker Image               │
│  ✓ Build production Docker image                │
│  ✓ Tag with git commit SHA                      │
│  ✓ Push to AWS ECR                              │
│  Duration: ~3-5 minutes                         │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  JOB 3: Run Migrations                          │
│  ✓ Create new ECS task definition               │
│  ✓ Set DATABASE_NAME environment variable       │
│  ✓ Launch ECS Fargate task                     │
│  ✓ Wait for task completion                    │
│  ✓ Fetch CloudWatch logs                       │
│  ✓ Check exit code (0 = success)               │
│  Duration: ~2-5 minutes                         │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  JOB 4: Summary                                 │
│  ✓ Display results of all jobs                 │
│  ✓ Show success/failure message                │
└─────────────────────────────────────────────────┘
```

**Total Duration**: ~10-17 minutes

---

## Setting Up GitHub Secrets

Before you can run the workflow, you need to add AWS credentials to GitHub.

### Step 1: Create IAM User (If Not Done Already)

1. Go to AWS Console → IAM → Users
2. Click "Create user"
3. Username: `github-actions-startupwebapp`
4. Select "Attach policies directly"
5. Add these policies:
   - `AmazonEC2ContainerRegistryPowerUser` (for ECR push/pull)
   - `AmazonECS_FullAccess` (for running ECS tasks)
   - `CloudWatchLogsReadOnlyAccess` (for reading logs)
6. Click "Create user"
7. Go to user → Security credentials → Create access key
8. Select "Third-party service"
9. **Save the access key ID and secret access key** (you'll only see them once!)

### Step 2: Add Secrets to GitHub Repository

1. Go to your GitHub repository: `https://github.com/bartgottschalk/startup_web_app_server_side`
2. Click **Settings** (top navigation)
3. In left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add three secrets:

**Secret 1:**
- Name: `AWS_ACCESS_KEY_ID`
- Secret: (paste the access key ID from Step 1)
- Click "Add secret"

**Secret 2:**
- Name: `AWS_SECRET_ACCESS_KEY`
- Secret: (paste the secret access key from Step 1)
- Click "Add secret"

**Secret 3:**
- Name: `AWS_REGION`
- Secret: `us-east-1`
- Click "Add secret"

### Step 3: Verify Secrets

You should now see three secrets listed:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

**Security Note**: Once saved, you can't view these secrets again in GitHub. They're encrypted and only available to workflows.

---

## How to Run Migrations

### Prerequisites
- ✅ GitHub secrets configured (see above)
- ✅ Code pushed to GitHub
- ✅ You have new migrations to apply

### Step-by-Step Instructions

1. **Go to GitHub Actions Tab**
   - Navigate to: `https://github.com/bartgottschalk/startup_web_app_server_side/actions`

2. **Select the Workflow**
   - In the left sidebar, click **"Run Database Migrations"**

3. **Click "Run workflow" Button**
   - You'll see a blue button on the right: **"Run workflow"**
   - Click it

4. **Fill in the Form**
   - A dropdown appears with options:
     - **Branch**: Select your branch (usually `feature/phase-5-14-ecs-cicd-migrations`)
     - **Target Database**: Choose from:
       - `startupwebapp_prod` (main application)
       - `healthtech_experiment` (HealthTech fork)
       - `fintech_experiment` (FinTech fork)
     - **Skip tests**: Leave unchecked (only check for emergency hotfixes)

5. **Click "Run workflow"**
   - Workflow starts immediately
   - You'll see it appear in the workflow runs list

6. **Monitor Progress**
   - Click on the workflow run (it will have a yellow dot = running)
   - You'll see 4 jobs:
     - **Run Test Suite** (5-7 min)
     - **Build and Push Docker Image** (3-5 min)
     - **Run Migrations on [database]** (2-5 min)
     - **Workflow Summary** (10 sec)

7. **Watch Real-Time Logs**
   - Click on any job name to see detailed logs
   - Each step shows output as it runs
   - Green checkmark ✅ = success
   - Red X ❌ = failure

8. **Completion**
   - All jobs complete: Green checkmark = success!
   - Any job fails: Red X = check logs for error details

---

## Reading Workflow Results

### Understanding the UI

**Workflow Run Page:**
```
┌──────────────────────────────────────────────────────────────┐
│  Run Database Migrations #42                                 │
│  ● In Progress | 🟢 Success | 🔴 Failed                      │
│                                                              │
│  Branch: feature/phase-5-14-ecs-cicd-migrations             │
│  Database: startupwebapp_prod                               │
│  Triggered by: bartgottschalk                               │
│  Duration: 12m 34s                                          │
│                                                              │
│  Jobs:                                                       │
│  ✅ Run Test Suite          (7m 12s)                        │
│  ✅ Build and Push Image    (4m 8s)                         │
│  ✅ Run Migrations          (3m 45s)                        │
│  ✅ Workflow Summary        (8s)                            │
└──────────────────────────────────────────────────────────────┘
```

### Key Information to Check

**1. Test Results** (Job 1):
- Look for: `712 tests passed` (unit tests)
- Look for: `28 tests passed` (functional tests)
- If any fail, workflow stops here

**2. Docker Build** (Job 2):
- Look for: `Image built and pushed successfully`
- Note the image tag (git commit SHA)

**3. Migration Output** (Job 3):
- Look for migration log output:
  ```
  Running migrations:
    Applying user.0001_initial... OK
    Applying order.0001_initial... OK
    No migrations to apply.
  ```
- Look for: `✅ Migration completed successfully!`

**4. CloudWatch Logs**:
- Full Django migration output appears in the logs
- Shows exactly which migrations were applied
- Shows any errors or warnings

---

## Troubleshooting

### Issue: "Invalid AWS credentials"

**Error Message:**
```
Error: The security token included in the request is invalid
```

**Cause**: GitHub secrets not set correctly or IAM user lacks permissions

**Solution**:
1. Verify secrets in GitHub: Settings → Secrets → Actions
2. Check IAM user has correct policies attached
3. Try regenerating AWS access keys

---

### Issue: "Tests failed"

**Error Message:**
```
FAILED order/tests/test_checkout.py::TestCheckout::test_stripe_payment
```

**Cause**: Code has a bug or test is flaky

**Solution**:
1. Click on the "Run Test Suite" job to see which test failed
2. Look at the error details
3. Fix the bug locally and push again
4. Re-run the workflow

**Emergency Option**: If you need to deploy urgently (production is down), you can check "Skip tests" when running workflow. **Use this sparingly!**

---

### Issue: "Cannot find task definition"

**Error Message:**
```
An error occurred (ClientException) when calling the DescribeTaskDefinition operation
```

**Cause**: ECS task definition doesn't exist or wrong name

**Solution**:
1. Verify task definition exists:
   ```bash
   aws ecs describe-task-definition --task-definition startupwebapp-migration-task
   ```
2. Check `ECS_TASK_DEFINITION` variable in workflow file matches actual name

---

### Issue: "Task failed with exit code 1"

**Error Message:**
```
❌ Migration failed with exit code 1
```

**Cause**: Django migration encountered an error (database issue, syntax error, etc.)

**Solution**:
1. Look at CloudWatch logs in the workflow output
2. Common issues:
   - **Conflicting migrations**: Run `python manage.py makemigrations --merge` locally
   - **Database locked**: Another process is using the database
   - **Missing dependency**: Migration depends on another app's migration
3. Fix the issue and run workflow again

---

### Issue: "Workflow gets stuck on 'Wait for task to complete'"

**Error Message:**
```
Waiting for migration task to complete...
(hangs for 10 minutes)
```

**Cause**: ECS task can't reach RDS or is stuck

**Solution**:
1. Check AWS Console → ECS → Clusters → startupwebapp-cluster
2. Look at task status (is it running, stopped, pending?)
3. Check security groups allow ECS → RDS communication
4. Check CloudWatch logs for task error messages

---

### Issue: "No logs available yet"

**Error Message:**
```
Fetching CloudWatch logs...
No logs available yet
```

**Cause**: Task failed to start or CloudWatch logging not configured

**Solution**:
1. Check ECS task status in AWS Console
2. Verify log group exists: `/ecs/startupwebapp-migrations`
3. Wait 1-2 minutes and check CloudWatch Logs directly in AWS Console

---

## Advanced: Workflow Customization

### Running Without Tests (Emergency Only)

When manually triggering the workflow, check the "Skip tests" option. This is useful for:
- Emergency hotfixes when production is down
- Re-running migrations after a transient failure
- Testing the deployment pipeline itself

**Warning**: Never skip tests for normal deployments! Tests prevent broken code from reaching production.

### Monitoring Multiple Databases

To run migrations on all three databases sequentially:
1. Run workflow for `startupwebapp_prod`
2. Wait for completion
3. Run workflow for `healthtech_experiment`
4. Wait for completion
5. Run workflow for `fintech_experiment`

**Note**: You can't run migrations on multiple databases simultaneously (same ECS cluster).

### Checking Migration Status

To see which migrations have been applied to a database:

```bash
# Set environment variables
export DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production
export DATABASE_NAME=startupwebapp_prod
export DB_SECRET_NAME=rds/startupwebapp/multi-tenant/master
export AWS_REGION=us-east-1

# Run showmigrations
cd StartupWebApp
python manage.py showmigrations
```

Output shows:
```
user
 [X] 0001_initial
 [X] 0002_add_email_verification
 [ ] 0003_add_profile_fields  <- Not applied yet
```

---

## Cost of Running Workflows

### GitHub Actions Minutes
- **Free tier**: 2,000 minutes/month (private repos)
- **Our workflow**: ~15 minutes per run
- **Usage**: 133 runs/month within free tier

### AWS Costs
- **ECS Task**: $0.0137/hour = ~$0.001 per 5-minute migration
- **ECR Storage**: Covered by existing ~$0.10-$0.20/month
- **CloudWatch Logs**: Covered by existing monitoring costs

**Total additional cost**: Negligible (~$0.10/month for ~100 migration runs)

---

## Next Steps

1. **Push this branch to GitHub**:
   ```bash
   git add .github/workflows/run-migrations.yml
   git commit -m "Add GitHub Actions CI/CD workflow for migrations"
   git push origin feature/phase-5-14-ecs-cicd-migrations
   ```

2. **Set up GitHub Secrets** (see above)

3. **Test the workflow**:
   - Run it on `startupwebapp_prod` database
   - Verify all jobs succeed
   - Check CloudWatch logs show migrations

4. **Document success in PROJECT_HISTORY.md**

---

## Resources

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **AWS ECS Documentation**: https://docs.aws.amazon.com/ecs/
- **Django Migrations**: https://docs.djangoproject.com/en/4.2/topics/migrations/
- **Workflow File**: `.github/workflows/run-migrations.yml`
- **Phase 5.14 Plan**: `docs/technical-notes/2025-11-23-phase-5-14-ecs-cicd-migrations.md`

---

**Questions?** Review the workflow file - it has extensive inline comments explaining each step!
