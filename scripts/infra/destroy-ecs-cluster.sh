#!/bin/bash

##############################################################################
# Destroy AWS ECS Cluster
#
# This script destroys:
# - ECS cluster
# - CloudWatch log group
#
# Usage: ./scripts/infra/destroy-ecs-cluster.sh
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
CLUSTER_NAME="${PROJECT_NAME}-cluster"
LOG_GROUP_NAME="/ecs/${PROJECT_NAME}-migrations"

echo -e "${RED}========================================${NC}"
echo -e "${RED}DESTROY AWS ECS Cluster${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if cluster exists
if [ -z "${ECS_CLUSTER_NAME:-}" ]; then
    echo -e "${YELLOW}No ECS cluster found in aws-resources.env${NC}"
    exit 0
fi

echo -e "${YELLOW}WARNING: This will delete the ECS cluster and all associated logs!${NC}"
echo -e "${YELLOW}Cluster: ${CLUSTER_NAME}${NC}"
echo ""
read -p "Are you sure you want to delete the ECS cluster? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Check for running tasks
echo -e "${YELLOW}Checking for running tasks...${NC}"
RUNNING_TASKS=$(aws ecs list-tasks \
    --cluster "${CLUSTER_NAME}" \
    --region "${AWS_REGION}" \
    --query 'taskArns[]' \
    --output text 2>/dev/null || echo "")

if [ -n "$RUNNING_TASKS" ]; then
    echo -e "${YELLOW}Found running tasks. Stopping them...${NC}"
    for TASK_ARN in $RUNNING_TASKS; do
        aws ecs stop-task \
            --cluster "${CLUSTER_NAME}" \
            --task "$TASK_ARN" \
            --region "${AWS_REGION}" > /dev/null 2>&1 || true
        echo -e "${GREEN}✓ Stopped task: ${TASK_ARN}${NC}"
    done
    echo -e "${YELLOW}Waiting 10 seconds for tasks to stop...${NC}"
    sleep 10
else
    echo -e "${GREEN}✓ No running tasks${NC}"
fi

# Delete ECS cluster
echo -e "${YELLOW}Deleting ECS cluster...${NC}"
aws ecs delete-cluster \
    --cluster "${CLUSTER_NAME}" \
    --region "${AWS_REGION}" > /dev/null 2>&1 || true

echo -e "${GREEN}✓ ECS cluster deleted${NC}"

# Delete CloudWatch log group
echo -e "${YELLOW}Deleting CloudWatch log group...${NC}"
aws logs delete-log-group \
    --log-group-name "${LOG_GROUP_NAME}" \
    --region "${AWS_REGION}" > /dev/null 2>&1 || true

echo -e "${GREEN}✓ CloudWatch log group deleted${NC}"

# Update environment file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^ECS_CLUSTER_NAME=.*|ECS_CLUSTER_NAME=\"\"|" \
    -e "s|^ECS_CLUSTER_ARN=.*|ECS_CLUSTER_ARN=\"\"|" \
    -e "s|^ECS_LOG_GROUP_NAME=.*|ECS_LOG_GROUP_NAME=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ECS Cluster Destroyed${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Cluster '${CLUSTER_NAME}' has been deleted."
echo ""
