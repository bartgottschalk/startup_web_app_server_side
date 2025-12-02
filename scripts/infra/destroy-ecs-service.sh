#!/bin/bash

##############################################################################
# Destroy ECS Service for StartupWebApp
#
# This script destroys:
# - ECS Service (stops all running tasks)
# - Removes from load balancer target group
#
# WARNING:
# - This will stop all running application tasks
# - The application will be unavailable until service is recreated
# - Task definition is NOT deleted (allows quick recovery)
#
# Usage: ./scripts/infra/destroy-ecs-service.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
##############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Initialize environment file
source "${SCRIPT_DIR}/init-env.sh"
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"
PROJECT_NAME="startupwebapp"
SERVICE_NAME="${PROJECT_NAME}-service"

echo -e "${RED}========================================"
echo -e "Destroy ECS Service"
echo -e "========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if service exists in env
if [ -z "${ECS_SERVICE_NAME:-}" ] && [ -z "${ECS_SERVICE_ARN:-}" ]; then
    echo -e "${YELLOW}No ECS_SERVICE_NAME or ECS_SERVICE_ARN found in aws-resources.env${NC}"

    # Still check AWS in case it exists but wasn't tracked
    EXISTING_SERVICE=$(aws ecs describe-services \
        --cluster "${ECS_CLUSTER_NAME:-startupwebapp-cluster}" \
        --services "${SERVICE_NAME}" \
        --region "${AWS_REGION}" \
        --query 'services[?status!=`INACTIVE`].serviceArn' \
        --output text 2>/dev/null || echo "")

    if [ -z "$EXISTING_SERVICE" ]; then
        echo -e "${GREEN}✓ Service does not exist. Nothing to destroy.${NC}"
        exit 0
    fi

    echo -e "${YELLOW}Found untracked service: ${EXISTING_SERVICE}${NC}"
fi

# Check if service exists in AWS
EXISTING_SERVICE=$(aws ecs describe-services \
    --cluster "${ECS_CLUSTER_NAME}" \
    --services "${SERVICE_NAME}" \
    --region "${AWS_REGION}" \
    --query 'services[?status!=`INACTIVE`].{arn: serviceArn, status: status, running: runningCount, desired: desiredCount}' \
    --output json 2>/dev/null || echo "[]")

SERVICE_COUNT=$(echo "$EXISTING_SERVICE" | jq '. | length')

if [ "$SERVICE_COUNT" == "0" ]; then
    echo -e "${YELLOW}Service not found in AWS, clearing env file...${NC}"
    sed -i.bak \
        -e "s|^ECS_SERVICE_NAME=.*|ECS_SERVICE_NAME=\"\"|" \
        -e "s|^ECS_SERVICE_ARN=.*|ECS_SERVICE_ARN=\"\"|" \
        "$ENV_FILE" 2>/dev/null || true
    rm -f "${ENV_FILE}.bak"
    echo -e "${GREEN}✓ aws-resources.env cleared${NC}"
    exit 0
fi

# Show service status
SERVICE_STATUS=$(echo "$EXISTING_SERVICE" | jq -r '.[0].status')
RUNNING_COUNT=$(echo "$EXISTING_SERVICE" | jq -r '.[0].running')
DESIRED_COUNT=$(echo "$EXISTING_SERVICE" | jq -r '.[0].desired')

echo -e "${RED}WARNING: This will destroy the ECS Service!${NC}"
echo ""
echo -e "${YELLOW}Service to destroy:${NC}"
echo -e "  Name:            ${SERVICE_NAME}"
echo -e "  Cluster:         ${ECS_CLUSTER_NAME}"
echo -e "  Status:          ${SERVICE_STATUS}"
echo -e "  Running Tasks:   ${RUNNING_COUNT}"
echo -e "  Desired Tasks:   ${DESIRED_COUNT}"
echo ""
echo -e "${RED}Impact:${NC}"
echo -e "  - All ${RUNNING_COUNT} running tasks will be stopped"
echo -e "  - Application will be unavailable"
echo -e "  - Load balancer will have no healthy targets"
echo ""
echo -e "${YELLOW}To recover after destroy:${NC}"
echo -e "  Run: ./scripts/infra/create-ecs-service.sh"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

# Step 1: Scale down to 0 tasks (graceful shutdown)
echo ""
echo -e "${YELLOW}Step 1: Scaling service down to 0 tasks...${NC}"

aws ecs update-service \
    --cluster "${ECS_CLUSTER_NAME}" \
    --service "${SERVICE_NAME}" \
    --desired-count 0 \
    --region "${AWS_REGION}" > /dev/null 2>&1

echo -e "${GREEN}✓ Service scaled to 0 desired tasks${NC}"

# Step 2: Wait for tasks to stop
echo ""
echo -e "${YELLOW}Step 2: Waiting for tasks to stop...${NC}"

MAX_WAIT=120  # 2 minutes
WAIT_INTERVAL=10
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    RUNNING_COUNT=$(aws ecs describe-services \
        --cluster "${ECS_CLUSTER_NAME}" \
        --services "${SERVICE_NAME}" \
        --region "${AWS_REGION}" \
        --query 'services[0].runningCount' \
        --output text 2>/dev/null || echo "0")

    echo -e "  Running tasks: ${RUNNING_COUNT}"

    if [ "$RUNNING_COUNT" == "0" ]; then
        echo -e "${GREEN}✓ All tasks stopped${NC}"
        break
    fi

    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${YELLOW}⚠ Tasks did not stop within ${MAX_WAIT} seconds, continuing with delete...${NC}"
fi

# Step 3: Delete the service
echo ""
echo -e "${YELLOW}Step 3: Deleting ECS Service...${NC}"

aws ecs delete-service \
    --cluster "${ECS_CLUSTER_NAME}" \
    --service "${SERVICE_NAME}" \
    --force \
    --region "${AWS_REGION}" > /dev/null 2>&1

echo -e "${GREEN}✓ ECS Service deleted${NC}"

# Step 4: Wait for service to be fully removed
echo ""
echo -e "${YELLOW}Step 4: Waiting for service to be fully removed...${NC}"

ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    SERVICE_STATUS=$(aws ecs describe-services \
        --cluster "${ECS_CLUSTER_NAME}" \
        --services "${SERVICE_NAME}" \
        --region "${AWS_REGION}" \
        --query 'services[0].status' \
        --output text 2>/dev/null || echo "INACTIVE")

    echo -e "  Service status: ${SERVICE_STATUS}"

    if [ "$SERVICE_STATUS" == "INACTIVE" ]; then
        echo -e "${GREEN}✓ Service is now INACTIVE${NC}"
        break
    fi

    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

# Step 5: Clear environment file
echo ""
echo -e "${YELLOW}Step 5: Clearing aws-resources.env...${NC}"

sed -i.bak \
    -e "s|^ECS_SERVICE_NAME=.*|ECS_SERVICE_NAME=\"\"|" \
    -e "s|^ECS_SERVICE_ARN=.*|ECS_SERVICE_ARN=\"\"|" \
    "$ENV_FILE" 2>/dev/null || true
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================"
echo -e "ECS Service Destroyed Successfully"
echo -e "========================================${NC}"
echo ""
echo -e "${GREEN}What was destroyed:${NC}"
echo -e "  - ECS Service: ${SERVICE_NAME}"
echo -e "  - Running tasks: All stopped"
echo -e "  - Load balancer targets: Deregistered"
echo ""
echo -e "${GREEN}What was preserved:${NC}"
echo -e "  - Task definition: ${ECS_SERVICE_TASK_DEFINITION_ARN:-startupwebapp-service-task}"
echo -e "  - CloudWatch log group: /ecs/${PROJECT_NAME}-service"
echo -e "  - ALB and target group: Intact"
echo -e "  - ECR images: Intact"
echo ""
echo -e "${GREEN}To recreate the service:${NC}"
echo -e "  ./scripts/infra/create-ecs-service.sh"
echo ""
echo -e "${YELLOW}Note: The application is now unavailable.${NC}"
echo -e "${YELLOW}Recreate the service to restore availability.${NC}"
echo ""
