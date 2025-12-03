#!/bin/bash

##############################################################################
# Create ECS Service for StartupWebApp
#
# This script creates:
# - ECS Service running 2 Fargate tasks across 2 AZs
# - Load balancer integration with existing ALB target group
# - Rolling deployment configuration (zero-downtime updates)
# - Circuit breaker for automatic rollback on failed deployments
#
# The ECS Service maintains a desired count of tasks running continuously,
# unlike one-time migration tasks. Tasks are registered with the ALB
# target group to receive HTTP traffic.
#
# Prerequisites:
# - ECS cluster must exist (run create-ecs-cluster.sh)
# - Service task definition must exist (run create-ecs-service-task-definition.sh)
# - ALB and target group must exist (run create-alb.sh)
# - HTTPS listener must exist (run create-alb-https-listener.sh)
#
# Usage: ./scripts/infra/create-ecs-service.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
##############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Initialize environment file
source "${SCRIPT_DIR}/init-env.sh"
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"
PROJECT_NAME="startupwebapp"
ENVIRONMENT="production"
SERVICE_NAME="${PROJECT_NAME}-service"
DESIRED_COUNT="2"  # 2 tasks for high availability (1 per AZ)
CONTAINER_NAME="web"
CONTAINER_PORT="8000"
HEALTH_CHECK_GRACE_PERIOD="120"  # Seconds to wait before checking health

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create ECS Service${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify prerequisites
echo -e "${YELLOW}Verifying prerequisites...${NC}"

if [ -z "${ECS_CLUSTER_NAME:-}" ]; then
    echo -e "${RED}Error: ECS_CLUSTER_NAME not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-ecs-cluster.sh first${NC}"
    exit 1
fi

if [ -z "${ECS_SERVICE_TASK_DEFINITION_ARN:-}" ]; then
    echo -e "${RED}Error: ECS_SERVICE_TASK_DEFINITION_ARN not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-ecs-service-task-definition.sh first${NC}"
    exit 1
fi

if [ -z "${TARGET_GROUP_ARN:-}" ]; then
    echo -e "${RED}Error: TARGET_GROUP_ARN not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-alb.sh first${NC}"
    exit 1
fi

if [ -z "${PRIVATE_SUBNET_1_ID:-}" ] || [ -z "${PRIVATE_SUBNET_2_ID:-}" ]; then
    echo -e "${RED}Error: Private subnet IDs not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-vpc.sh first${NC}"
    exit 1
fi

if [ -z "${BACKEND_SECURITY_GROUP_ID:-}" ]; then
    echo -e "${RED}Error: BACKEND_SECURITY_GROUP_ID not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please verify security groups are configured${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites verified${NC}"
echo ""

# Check if service already exists
echo -e "${YELLOW}Checking for existing service...${NC}"
EXISTING_SERVICE=$(aws ecs describe-services \
    --cluster "${ECS_CLUSTER_NAME}" \
    --services "${SERVICE_NAME}" \
    --region "${AWS_REGION}" \
    --query 'services[?status!=`INACTIVE`].serviceArn' \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_SERVICE" ]; then
    echo -e "${GREEN}✓ ECS Service already exists: ${SERVICE_NAME}${NC}"

    # Get current running count
    RUNNING_COUNT=$(aws ecs describe-services \
        --cluster "${ECS_CLUSTER_NAME}" \
        --services "${SERVICE_NAME}" \
        --region "${AWS_REGION}" \
        --query 'services[0].runningCount' \
        --output text)

    echo -e "  Running tasks: ${RUNNING_COUNT}"
    echo ""
    echo -e "${YELLOW}To update the service, use: aws ecs update-service${NC}"
    echo -e "${YELLOW}To destroy and recreate, use: ./scripts/infra/destroy-ecs-service.sh${NC}"
    exit 0
fi

echo -e "${YELLOW}No existing service found. Creating new service...${NC}"
echo ""

# Display configuration
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Service Name:           ${SERVICE_NAME}"
echo -e "  Cluster:                ${ECS_CLUSTER_NAME}"
echo -e "  Task Definition:        ${ECS_SERVICE_TASK_DEFINITION_ARN}"
echo -e "  Desired Count:          ${DESIRED_COUNT} tasks"
echo -e "  Container Name:         ${CONTAINER_NAME}"
echo -e "  Container Port:         ${CONTAINER_PORT}"
echo -e "  Launch Type:            Fargate"
echo -e "  Network Mode:           awsvpc"
echo ""
echo -e "${YELLOW}Networking:${NC}"
echo -e "  Subnets:                ${PRIVATE_SUBNET_1_ID}, ${PRIVATE_SUBNET_2_ID}"
echo -e "  Security Group:         ${BACKEND_SECURITY_GROUP_ID}"
echo -e "  Public IP:              DISABLED (private subnets)"
echo ""
echo -e "${YELLOW}Load Balancer:${NC}"
echo -e "  Target Group:           ${TARGET_GROUP_ARN}"
echo -e "  Health Check Grace:     ${HEALTH_CHECK_GRACE_PERIOD} seconds"
echo ""
echo -e "${YELLOW}Deployment Configuration:${NC}"
echo -e "  Strategy:               Rolling update"
echo -e "  Min Healthy:            100% (keep all tasks running during deploy)"
echo -e "  Max Percent:            200% (can double tasks during deploy)"
echo -e "  Circuit Breaker:        Enabled (auto rollback on failure)"
echo ""
echo -e "${YELLOW}Cost Estimate:${NC}"
echo -e "  Per task:               ~\$0.027/hour"
echo -e "  2 tasks (base):         ~\$39/month"
echo ""

read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Create ECS Service
echo ""
echo -e "${YELLOW}Step 1: Creating ECS Service...${NC}"

SERVICE_ARN=$(aws ecs create-service \
    --cluster "${ECS_CLUSTER_NAME}" \
    --service-name "${SERVICE_NAME}" \
    --task-definition "${ECS_SERVICE_TASK_DEFINITION_ARN}" \
    --desired-count "${DESIRED_COUNT}" \
    --launch-type "FARGATE" \
    --platform-version "LATEST" \
    --network-configuration "awsvpcConfiguration={subnets=[${PRIVATE_SUBNET_1_ID},${PRIVATE_SUBNET_2_ID}],securityGroups=[${BACKEND_SECURITY_GROUP_ID}],assignPublicIp=DISABLED}" \
    --load-balancers "targetGroupArn=${TARGET_GROUP_ARN},containerName=${CONTAINER_NAME},containerPort=${CONTAINER_PORT}" \
    --health-check-grace-period-seconds "${HEALTH_CHECK_GRACE_PERIOD}" \
    --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},minimumHealthyPercent=100,maximumPercent=200" \
    --scheduling-strategy "REPLICA" \
    --deployment-controller "type=ECS" \
    --enable-execute-command \
    --tags "key=Name,value=${SERVICE_NAME}" "key=Environment,value=${ENVIRONMENT}" "key=Project,value=${PROJECT_NAME}" \
    --region "${AWS_REGION}" \
    --query 'service.serviceArn' \
    --output text)

echo -e "${GREEN}✓ ECS Service created: ${SERVICE_NAME}${NC}"
echo -e "  ARN: ${SERVICE_ARN}"

# Wait for service to stabilize (tasks to start)
echo ""
echo -e "${YELLOW}Step 2: Waiting for service to stabilize...${NC}"
echo -e "  This may take 2-5 minutes as tasks start and pass health checks."
echo ""

# Monitor task startup
MAX_WAIT=300  # 5 minutes
WAIT_INTERVAL=15
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Get service status
    SERVICE_STATUS=$(aws ecs describe-services \
        --cluster "${ECS_CLUSTER_NAME}" \
        --services "${SERVICE_NAME}" \
        --region "${AWS_REGION}" \
        --query 'services[0].{running: runningCount, desired: desiredCount, pending: pendingCount, status: status}' \
        --output json)

    RUNNING=$(echo "$SERVICE_STATUS" | jq -r '.running')
    DESIRED=$(echo "$SERVICE_STATUS" | jq -r '.desired')
    PENDING=$(echo "$SERVICE_STATUS" | jq -r '.pending')
    STATUS=$(echo "$SERVICE_STATUS" | jq -r '.status')

    echo -e "  Status: ${STATUS} | Running: ${RUNNING}/${DESIRED} | Pending: ${PENDING}"

    if [ "$RUNNING" == "$DESIRED" ] && [ "$RUNNING" != "0" ]; then
        echo ""
        echo -e "${GREEN}✓ Service stabilized! All ${RUNNING} tasks running.${NC}"
        break
    fi

    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo ""
    echo -e "${YELLOW}⚠ Service did not stabilize within ${MAX_WAIT} seconds.${NC}"
    echo -e "${YELLOW}  Tasks may still be starting. Check CloudWatch logs for errors.${NC}"
    echo -e "${YELLOW}  Monitor with: aws ecs describe-services --cluster ${ECS_CLUSTER_NAME} --services ${SERVICE_NAME}${NC}"
fi

# Check target group health
echo ""
echo -e "${YELLOW}Step 3: Checking target group health...${NC}"

# Give targets time to register
sleep 10

TARGET_HEALTH=$(aws elbv2 describe-target-health \
    --target-group-arn "${TARGET_GROUP_ARN}" \
    --region "${AWS_REGION}" \
    --query 'TargetHealthDescriptions[*].{Target: Target.Id, Port: Target.Port, Health: TargetHealth.State, Reason: TargetHealth.Reason}' \
    --output json)

HEALTHY_COUNT=$(echo "$TARGET_HEALTH" | jq '[.[] | select(.Health == "healthy")] | length')
TOTAL_COUNT=$(echo "$TARGET_HEALTH" | jq '. | length')

echo -e "  Targets registered: ${TOTAL_COUNT}"
echo -e "  Healthy targets: ${HEALTHY_COUNT}"

if [ "$HEALTHY_COUNT" == "0" ]; then
    echo ""
    echo -e "${YELLOW}⚠ No healthy targets yet. This is normal during initial startup.${NC}"
    echo -e "${YELLOW}  Health checks take ${HEALTH_CHECK_GRACE_PERIOD} seconds grace period + 30s check interval.${NC}"
    echo -e "${YELLOW}  Check target health with:${NC}"
    echo -e "${YELLOW}    aws elbv2 describe-target-health --target-group-arn ${TARGET_GROUP_ARN}${NC}"
else
    echo -e "${GREEN}✓ ${HEALTHY_COUNT} healthy targets registered with ALB${NC}"
fi

# Update aws-resources.env
echo ""
echo -e "${YELLOW}Step 4: Updating aws-resources.env...${NC}"

# Check if variables exist, add or update
if grep -q "^ECS_SERVICE_NAME=" "$ENV_FILE"; then
    sed -i.bak \
        -e "s|^ECS_SERVICE_NAME=.*|ECS_SERVICE_NAME=\"${SERVICE_NAME}\"|" \
        -e "s|^ECS_SERVICE_ARN=.*|ECS_SERVICE_ARN=\"${SERVICE_ARN}\"|" \
        "$ENV_FILE"
else
    # Add new variables
    echo "" >> "$ENV_FILE"
    echo "# ECS Service (Phase 5.15)" >> "$ENV_FILE"
    echo "ECS_SERVICE_NAME=\"${SERVICE_NAME}\"" >> "$ENV_FILE"
    echo "ECS_SERVICE_ARN=\"${SERVICE_ARN}\"" >> "$ENV_FILE"
fi
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env updated${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ECS Service Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Service Details:${NC}"
echo -e "  Name:                   ${SERVICE_NAME}"
echo -e "  ARN:                    ${SERVICE_ARN}"
echo -e "  Cluster:                ${ECS_CLUSTER_NAME}"
echo -e "  Desired Count:          ${DESIRED_COUNT}"
echo -e "  Launch Type:            Fargate"
echo ""
echo -e "${GREEN}Network Configuration:${NC}"
echo -e "  Subnets:                ${PRIVATE_SUBNET_1_ID}"
echo -e "                          ${PRIVATE_SUBNET_2_ID}"
echo -e "  Security Group:         ${BACKEND_SECURITY_GROUP_ID}"
echo -e "  Public IP:              DISABLED"
echo ""
echo -e "${GREEN}Load Balancer Integration:${NC}"
echo -e "  Target Group:           startupwebapp-tg"
echo -e "  Container:              ${CONTAINER_NAME}:${CONTAINER_PORT}"
echo -e "  Health Check Grace:     ${HEALTH_CHECK_GRACE_PERIOD} seconds"
echo ""
echo -e "${GREEN}Deployment Configuration:${NC}"
echo -e "  Circuit Breaker:        Enabled (auto rollback)"
echo -e "  Min Healthy Percent:    100%"
echo -e "  Max Percent:            200%"
echo -e "  ECS Exec:               Enabled (for debugging)"
echo ""
echo -e "${GREEN}Access URLs:${NC}"
echo -e "  HTTPS:                  https://startupwebapp-api.mosaicmeshai.com"
echo -e "  Health Check:           https://startupwebapp-api.mosaicmeshai.com/order/products/"
echo ""
echo -e "${GREEN}Cost Estimate:${NC}"
echo -e "  Per task (running):     ~\$0.027/hour"
echo -e "  2 tasks monthly:        ~\$39/month"
echo ""
echo -e "${GREEN}Useful Commands:${NC}"
echo -e "  View service:           aws ecs describe-services --cluster ${ECS_CLUSTER_NAME} --services ${SERVICE_NAME}"
echo -e "  View tasks:             aws ecs list-tasks --cluster ${ECS_CLUSTER_NAME} --service-name ${SERVICE_NAME}"
echo -e "  View logs:              aws logs tail /ecs/${PROJECT_NAME}-service --follow"
echo -e "  Target health:          aws elbv2 describe-target-health --target-group-arn ${TARGET_GROUP_ARN}"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Wait for health checks to pass (~2-3 minutes)"
echo -e "  2. Test endpoint: curl -v https://startupwebapp-api.mosaicmeshai.com/order/products/"
echo -e "  3. Configure auto-scaling: ./scripts/infra/create-ecs-autoscaling.sh"
echo ""
echo -e "${YELLOW}Note: If health checks fail, check CloudWatch logs:${NC}"
echo -e "  aws logs tail /ecs/${PROJECT_NAME}-service --since 10m"
echo ""
echo -e "${YELLOW}Phase 5.15 Progress:${NC}"
echo -e "  ✓ Step 1: Create Application Load Balancer (ALB)"
echo -e "  ✓ Step 2: Create ACM Certificate"
echo -e "  ✓ Step 3: Create HTTPS Listener"
echo -e "  ✓ Step 4: Configure Namecheap DNS"
echo -e "  ✓ Step 5: Create ECS Service Task Definition"
echo -e "  ✓ Step 6: Create ECS Service"
echo -e "  → Step 7: Configure Auto-Scaling"
echo ""
