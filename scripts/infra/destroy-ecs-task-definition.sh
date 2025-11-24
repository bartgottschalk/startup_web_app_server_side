#!/bin/bash

##############################################################################
# Destroy AWS ECS Task Definition
#
# This script deregisters all revisions of the ECS task definition.
# Note: Task definitions cannot be truly "deleted" in AWS, only deregistered.
# Deregistered task definitions remain in AWS but cannot be used.
#
# Usage: ./scripts/infra/destroy-ecs-task-definition.sh
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
TASK_FAMILY="${PROJECT_NAME}-migration-task"

echo -e "${RED}========================================${NC}"
echo -e "${RED}DESTROY ECS Task Definition${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if task definition exists
if [ -z "${ECS_TASK_DEFINITION_FAMILY:-}" ]; then
    echo -e "${YELLOW}No task definition found in aws-resources.env${NC}"
    exit 0
fi

echo -e "${YELLOW}WARNING: This will deregister all revisions of the task definition!${NC}"
echo -e "${YELLOW}Task Family: ${TASK_FAMILY}${NC}"
echo ""
echo -e "${YELLOW}Note: Deregistered task definitions remain in AWS but cannot be used.${NC}"
echo -e "${YELLOW}Running ECS tasks will not be affected.${NC}"
echo ""
read -p "Are you sure you want to deregister the task definition? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Get all task definition revisions
echo -e "${YELLOW}Finding all task definition revisions...${NC}"
TASK_DEF_ARNS=$(aws ecs list-task-definitions \
    --family-prefix "${TASK_FAMILY}" \
    --region "${AWS_REGION}" \
    --query 'taskDefinitionArns[]' \
    --output text 2>/dev/null || echo "")

if [ -z "$TASK_DEF_ARNS" ]; then
    echo -e "${YELLOW}No active task definitions found for family: ${TASK_FAMILY}${NC}"
    echo -e "${GREEN}Task definition may already be deregistered${NC}"
else
    # Deregister each revision
    REVISION_COUNT=0
    for TASK_DEF_ARN in $TASK_DEF_ARNS; do
        echo -e "${YELLOW}Deregistering: ${TASK_DEF_ARN}...${NC}"
        aws ecs deregister-task-definition \
            --task-definition "$TASK_DEF_ARN" \
            --region "${AWS_REGION}" > /dev/null 2>&1 || true
        echo -e "${GREEN}✓ Deregistered: ${TASK_DEF_ARN}${NC}"
        REVISION_COUNT=$((REVISION_COUNT + 1))
    done

    echo ""
    echo -e "${GREEN}✓ Deregistered ${REVISION_COUNT} task definition revision(s)${NC}"
fi

# Update environment file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^ECS_TASK_DEFINITION_FAMILY=.*|ECS_TASK_DEFINITION_FAMILY=\"\"|" \
    -e "s|^ECS_TASK_DEFINITION_ARN=.*|ECS_TASK_DEFINITION_ARN=\"\"|" \
    -e "s|^ECS_TASK_DEFINITION_REVISION=.*|ECS_TASK_DEFINITION_REVISION=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Task Definition Deregistered${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "All revisions of task definition '${TASK_FAMILY}' have been deregistered."
echo ""
echo -e "${YELLOW}Note:${NC}"
echo -e "  - Deregistered task definitions remain in AWS but cannot be used"
echo -e "  - Running ECS tasks are not affected"
echo -e "  - You can register a new task definition with the same family name"
echo ""
