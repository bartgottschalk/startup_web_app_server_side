#!/bin/bash

##############################################################################
# Destroy ECS Service Task Definition for StartupWebApp
#
# This script deregisters:
# - ECS service task definition (all revisions)
# - CloudWatch log group for service logs
#
# WARNING:
# - Cannot destroy if ECS service is still using this task definition
# - Destroy ECS service first: ./scripts/infra/destroy-ecs-service.sh
#
# Usage: ./scripts/infra/destroy-ecs-service-task-definition.sh
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
TASK_FAMILY="${PROJECT_NAME}-service-task"

echo -e "${RED}========================================"
echo -e "Destroy ECS Service Task Definition"
echo -e "========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if task definition exists in env
if [ -z "${ECS_SERVICE_TASK_DEFINITION_ARN:-}" ]; then
    echo -e "${YELLOW}No ECS_SERVICE_TASK_DEFINITION_ARN found in aws-resources.env${NC}"
    echo -e "${GREEN}Nothing to destroy.${NC}"
    exit 0
fi

# Check if task definition exists in AWS
EXISTING_TASK_DEF=$(aws ecs describe-task-definition \
    --task-definition "${TASK_FAMILY}" \
    --region "${AWS_REGION}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$EXISTING_TASK_DEF" ] || [ "$EXISTING_TASK_DEF" == "None" ]; then
    echo -e "${YELLOW}Task definition not found in AWS, clearing env file...${NC}"
    sed -i.bak \
        -e "s|^ECS_SERVICE_TASK_DEFINITION_FAMILY=.*|ECS_SERVICE_TASK_DEFINITION_FAMILY=\"\"|" \
        -e "s|^ECS_SERVICE_TASK_DEFINITION_ARN=.*|ECS_SERVICE_TASK_DEFINITION_ARN=\"\"|" \
        -e "s|^ECS_SERVICE_TASK_DEFINITION_REVISION=.*|ECS_SERVICE_TASK_DEFINITION_REVISION=\"\"|" \
        "$ENV_FILE" 2>/dev/null || true
    rm -f "${ENV_FILE}.bak"
    echo -e "${GREEN}✓ aws-resources.env cleared${NC}"
    exit 0
fi

# Confirm destruction
echo -e "${RED}WARNING: This will deregister all revisions of the service task definition!${NC}"
echo ""
echo -e "${YELLOW}Task Definition to destroy:${NC}"
echo -e "  Family: ${TASK_FAMILY}"
echo -e "  Current ARN: ${ECS_SERVICE_TASK_DEFINITION_ARN:-N/A}"
echo ""
echo -e "${YELLOW}Note: Task definitions cannot be deleted, only deregistered.${NC}"
echo -e "${YELLOW}Deregistered task definitions remain in INACTIVE state.${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

# Step 1: Deregister all task definition revisions
echo ""
echo -e "${YELLOW}Step 1: Deregistering all task definition revisions...${NC}"

# Get all revisions
REVISIONS=$(aws ecs list-task-definitions \
    --family-prefix "${TASK_FAMILY}" \
    --region "${AWS_REGION}" \
    --query 'taskDefinitionArns[]' \
    --output text 2>/dev/null || echo "")

if [ -n "$REVISIONS" ]; then
    for revision in $REVISIONS; do
        echo -e "  Deregistering: ${revision}"
        aws ecs deregister-task-definition \
            --task-definition "${revision}" \
            --region "${AWS_REGION}" > /dev/null 2>&1 || true
    done
    echo -e "${GREEN}✓ All revisions deregistered${NC}"
else
    echo -e "${YELLOW}  No revisions found${NC}"
fi

# Step 2: Delete CloudWatch log group (optional)
echo ""
echo -e "${YELLOW}Step 2: Deleting CloudWatch log group (optional)...${NC}"

SERVICE_LOG_GROUP="${ECS_SERVICE_LOG_GROUP:-/ecs/${PROJECT_NAME}-service}"
if aws logs describe-log-groups --log-group-name-prefix "${SERVICE_LOG_GROUP}" --region "${AWS_REGION}" --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "${SERVICE_LOG_GROUP}"; then
    read -p "Delete log group ${SERVICE_LOG_GROUP}? (yes/no): " delete_logs
    if [ "$delete_logs" == "yes" ]; then
        aws logs delete-log-group \
            --log-group-name "${SERVICE_LOG_GROUP}" \
            --region "${AWS_REGION}" 2>/dev/null || true
        echo -e "${GREEN}✓ Log group deleted${NC}"
    else
        echo -e "${YELLOW}  Log group preserved${NC}"
    fi
else
    echo -e "${YELLOW}  Log group not found, skipping${NC}"
fi

# Step 3: Clear environment file
echo ""
echo -e "${YELLOW}Step 3: Clearing aws-resources.env...${NC}"

sed -i.bak \
    -e "s|^ECS_SERVICE_TASK_DEFINITION_FAMILY=.*|ECS_SERVICE_TASK_DEFINITION_FAMILY=\"\"|" \
    -e "s|^ECS_SERVICE_TASK_DEFINITION_ARN=.*|ECS_SERVICE_TASK_DEFINITION_ARN=\"\"|" \
    -e "s|^ECS_SERVICE_TASK_DEFINITION_REVISION=.*|ECS_SERVICE_TASK_DEFINITION_REVISION=\"\"|" \
    "$ENV_FILE" 2>/dev/null || true
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

echo ""
echo -e "${GREEN}========================================"
echo -e "Service Task Definition Destroyed!"
echo -e "========================================${NC}"
echo ""
echo -e "${YELLOW}Notes:${NC}"
echo -e "  - Task definitions are now INACTIVE (not deleted)"
echo -e "  - INACTIVE task definitions don't appear in normal listings"
echo -e "  - To recreate: ./scripts/infra/create-ecs-service-task-definition.sh"
echo ""
