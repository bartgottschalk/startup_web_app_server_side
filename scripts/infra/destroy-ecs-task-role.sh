#!/bin/bash

##############################################################################
# Destroy IAM Roles for ECS Tasks
#
# This script destroys:
# - ECS Task Execution Role
# - ECS Task Role
#
# Usage: ./scripts/infra/destroy-ecs-task-role.sh
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
TASK_EXECUTION_ROLE_NAME="ecsTaskExecutionRole-${PROJECT_NAME}"
TASK_ROLE_NAME="ecsTaskRole-${PROJECT_NAME}"

echo -e "${RED}========================================${NC}"
echo -e "${RED}DESTROY IAM Roles for ECS Tasks${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if roles exist
if [ -z "${ECS_TASK_EXECUTION_ROLE_ARN:-}" ]; then
    echo -e "${YELLOW}No ECS IAM roles found in aws-resources.env${NC}"
    exit 0
fi

echo -e "${YELLOW}WARNING: This will delete ECS IAM roles!${NC}"
echo -e "${YELLOW}Task Execution Role: ${TASK_EXECUTION_ROLE_NAME}${NC}"
echo -e "${YELLOW}Task Role: ${TASK_ROLE_NAME}${NC}"
echo ""
read -p "Are you sure you want to delete these IAM roles? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

#############################################
# Delete Task Execution Role
#############################################

echo -e "${YELLOW}Deleting Task Execution Role...${NC}"

# Detach managed policies
echo -e "${YELLOW}Detaching managed policy...${NC}"
aws iam detach-role-policy \
    --role-name "${TASK_EXECUTION_ROLE_NAME}" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" \
    2>/dev/null || true

# Delete inline policies
echo -e "${YELLOW}Deleting inline policies...${NC}"
INLINE_POLICIES=$(aws iam list-role-policies \
    --role-name "${TASK_EXECUTION_ROLE_NAME}" \
    --query 'PolicyNames[]' \
    --output text 2>/dev/null || echo "")

if [ -n "$INLINE_POLICIES" ]; then
    for POLICY_NAME in $INLINE_POLICIES; do
        aws iam delete-role-policy \
            --role-name "${TASK_EXECUTION_ROLE_NAME}" \
            --policy-name "$POLICY_NAME" 2>/dev/null || true
        echo -e "${GREEN}✓ Deleted inline policy: ${POLICY_NAME}${NC}"
    done
fi

# Delete the role
aws iam delete-role \
    --role-name "${TASK_EXECUTION_ROLE_NAME}" 2>/dev/null || true

echo -e "${GREEN}✓ Task Execution Role deleted${NC}"

#############################################
# Delete Task Role
#############################################

echo -e "${YELLOW}Deleting Task Role...${NC}"

# Delete inline policies
INLINE_POLICIES=$(aws iam list-role-policies \
    --role-name "${TASK_ROLE_NAME}" \
    --query 'PolicyNames[]' \
    --output text 2>/dev/null || echo "")

if [ -n "$INLINE_POLICIES" ]; then
    for POLICY_NAME in $INLINE_POLICIES; do
        aws iam delete-role-policy \
            --role-name "${TASK_ROLE_NAME}" \
            --policy-name "$POLICY_NAME" 2>/dev/null || true
        echo -e "${GREEN}✓ Deleted inline policy: ${POLICY_NAME}${NC}"
    done
fi

# Delete the role
aws iam delete-role \
    --role-name "${TASK_ROLE_NAME}" 2>/dev/null || true

echo -e "${GREEN}✓ Task Role deleted${NC}"

# Update environment file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^ECS_TASK_EXECUTION_ROLE_ARN=.*|ECS_TASK_EXECUTION_ROLE_ARN=\"\"|" \
    -e "s|^ECS_TASK_EXECUTION_ROLE_NAME=.*|ECS_TASK_EXECUTION_ROLE_NAME=\"\"|" \
    -e "s|^ECS_TASK_ROLE_ARN=.*|ECS_TASK_ROLE_ARN=\"\"|" \
    -e "s|^ECS_TASK_ROLE_NAME=.*|ECS_TASK_ROLE_NAME=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}IAM Roles Destroyed${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "ECS IAM roles have been deleted."
echo ""
