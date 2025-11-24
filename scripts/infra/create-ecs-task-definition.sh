#!/bin/bash

##############################################################################
# Create AWS ECS Task Definition for Django Migrations
#
# This script creates:
# - ECS task definition for running Django migrations
# - Configured for Fargate launch type (0.25 vCPU, 512 MB RAM)
# - Pulls database credentials from AWS Secrets Manager
# - Logs to CloudWatch
#
# Usage: ./scripts/infra/create-ecs-task-definition.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# Prerequisites:
#   - ECS cluster must exist (run create-ecs-cluster.sh)
#   - IAM roles must exist (run create-ecs-task-role.sh)
#   - ECR repository must exist with image (run create-ecr.sh)
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
TASK_FAMILY="${PROJECT_NAME}-migration-task"
TASK_CPU="256"  # 0.25 vCPU
TASK_MEMORY="512"  # 512 MB

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create ECS Task Definition${NC}"
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

if [ -z "${ECS_TASK_EXECUTION_ROLE_ARN:-}" ]; then
    echo -e "${RED}Error: ECS_TASK_EXECUTION_ROLE_ARN not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-ecs-task-role.sh first${NC}"
    exit 1
fi

if [ -z "${ECS_TASK_ROLE_ARN:-}" ]; then
    echo -e "${RED}Error: ECS_TASK_ROLE_ARN not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-ecs-task-role.sh first${NC}"
    exit 1
fi

if [ -z "${ECR_REPOSITORY_URI:-}" ]; then
    echo -e "${RED}Error: ECR_REPOSITORY_URI not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-ecr.sh first${NC}"
    exit 1
fi

if [ -z "${DB_SECRET_ARN:-}" ]; then
    echo -e "${RED}Error: DB_SECRET_ARN not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please ensure Secrets Manager is configured${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites verified${NC}"
echo ""

# Check if task definition already exists
if [ -n "${ECS_TASK_DEFINITION_ARN:-}" ]; then
    echo -e "${YELLOW}Checking if task definition exists...${NC}"
    EXISTING_TASK_DEF=$(aws ecs describe-task-definition \
        --task-definition "${TASK_FAMILY}" \
        --region "${AWS_REGION}" \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text 2>/dev/null || echo "")

    if [ -n "$EXISTING_TASK_DEF" ] && [ "$EXISTING_TASK_DEF" != "None" ]; then
        echo -e "${GREEN}✓ Task definition already exists: ${EXISTING_TASK_DEF}${NC}"
        echo -e "${YELLOW}Note: Registering a new revision will create version :2, :3, etc.${NC}"
        echo -e "${YELLOW}To start fresh, run ./scripts/infra/destroy-ecs-task-definition.sh first${NC}"
        echo ""
        read -p "Register a new revision? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Aborted."
            exit 0
        fi
    fi
fi

# Create task definition JSON
echo -e "${YELLOW}Creating task definition...${NC}"

TASK_DEF_JSON=$(cat <<EOF
{
  "family": "${TASK_FAMILY}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "${TASK_CPU}",
  "memory": "${TASK_MEMORY}",
  "executionRoleArn": "${ECS_TASK_EXECUTION_ROLE_ARN}",
  "taskRoleArn": "${ECS_TASK_ROLE_ARN}",
  "containerDefinitions": [
    {
      "name": "migration",
      "image": "${ECR_REPOSITORY_URI}:latest",
      "essential": true,
      "command": ["python", "manage.py", "migrate"],
      "environment": [
        {
          "name": "DJANGO_SETTINGS_MODULE",
          "value": "StartupWebApp.settings_production"
        },
        {
          "name": "AWS_REGION",
          "value": "${AWS_REGION}"
        },
        {
          "name": "DB_SECRET_NAME",
          "value": "${DB_SECRET_NAME}"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_PASSWORD",
          "valueFrom": "${DB_SECRET_ARN}:password::"
        },
        {
          "name": "DATABASE_USER",
          "valueFrom": "${DB_SECRET_ARN}:username::"
        },
        {
          "name": "DATABASE_HOST",
          "valueFrom": "${DB_SECRET_ARN}:host::"
        },
        {
          "name": "DATABASE_PORT",
          "valueFrom": "${DB_SECRET_ARN}:port::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "${ECS_LOG_GROUP_NAME}",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "migration"
        }
      }
    }
  ]
}
EOF
)

# Register task definition
TASK_DEF_ARN=$(aws ecs register-task-definition \
    --region "${AWS_REGION}" \
    --cli-input-json "$TASK_DEF_JSON" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo -e "${GREEN}✓ Task definition registered: ${TASK_FAMILY}${NC}"
echo -e "  ARN: ${TASK_DEF_ARN}"

# Extract revision number
TASK_DEF_REVISION=$(echo "$TASK_DEF_ARN" | awk -F: '{print $NF}')
echo -e "  Revision: ${TASK_DEF_REVISION}"

# Save to env file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^ECS_TASK_DEFINITION_FAMILY=.*|ECS_TASK_DEFINITION_FAMILY=\"${TASK_FAMILY}\"|" \
    -e "s|^ECS_TASK_DEFINITION_ARN=.*|ECS_TASK_DEFINITION_ARN=\"${TASK_DEF_ARN}\"|" \
    -e "s|^ECS_TASK_DEFINITION_REVISION=.*|ECS_TASK_DEFINITION_REVISION=\"${TASK_DEF_REVISION}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Task Definition Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  Family:              ${TASK_FAMILY}"
echo -e "  ARN:                 ${TASK_DEF_ARN}"
echo -e "  Revision:            ${TASK_DEF_REVISION}"
echo -e "  Launch Type:         Fargate"
echo -e "  CPU:                 ${TASK_CPU} (0.25 vCPU)"
echo -e "  Memory:              ${TASK_MEMORY} MB"
echo -e "  Network Mode:        awsvpc"
echo -e "  Container:           migration"
echo -e "  Image:               ${ECR_REPOSITORY_URI}:latest"
echo -e "  Command:             python manage.py migrate"
echo -e "  Execution Role:      ${ECS_TASK_EXECUTION_ROLE_NAME}"
echo -e "  Task Role:           ${ECS_TASK_ROLE_NAME}"
echo -e "  Log Group:           ${ECS_LOG_GROUP_NAME}"
echo ""
echo -e "${GREEN}Secrets (from Secrets Manager):${NC}"
echo -e "  DATABASE_PASSWORD:   ${DB_SECRET_NAME}:password"
echo -e "  DATABASE_USER:       ${DB_SECRET_NAME}:username"
echo -e "  DATABASE_HOST:       ${DB_SECRET_NAME}:host"
echo -e "  DATABASE_PORT:       ${DB_SECRET_NAME}:port"
echo ""
echo -e "${GREEN}Environment Variables:${NC}"
echo -e "  DJANGO_SETTINGS_MODULE:  StartupWebApp.settings_production"
echo -e "  AWS_REGION:              ${AWS_REGION}"
echo -e "  DB_SECRET_NAME:          ${DB_SECRET_NAME}"
echo ""
echo -e "${GREEN}Cost Estimate:${NC}"
echo -e "  Per task run (5 min):    ~\$0.001"
echo -e "  0.25 vCPU:               ~\$0.01235/hour"
echo -e "  0.5 GB memory:           ~\$0.00135/hour"
echo -e "  Total hourly:            ~\$0.0137/hour"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Test task manually (replace DATABASE_NAME):"
echo -e "     aws ecs run-task \\"
echo -e "       --cluster ${ECS_CLUSTER_NAME} \\"
echo -e "       --task-definition ${TASK_FAMILY} \\"
echo -e "       --launch-type FARGATE \\"
echo -e "       --network-configuration \"awsvpcConfiguration={subnets=[${PRIVATE_SUBNET_1_ID},${PRIVATE_SUBNET_2_ID}],securityGroups=[${BACKEND_SECURITY_GROUP_ID}]}\" \\"
echo -e "       --overrides '{\"containerOverrides\":[{\"name\":\"migration\",\"environment\":[{\"name\":\"DATABASE_NAME\",\"value\":\"startupwebapp_prod\"}]}]}'"
echo ""
echo -e "  2. Create GitHub Actions workflow:"
echo -e "     .github/workflows/run-migrations.yml"
echo ""
echo -e "${YELLOW}Phase 5.14 Progress:${NC}"
echo -e "  ✓ Step 1: Multi-Stage Dockerfile"
echo -e "  ✓ Step 2: Create AWS ECR Repository"
echo -e "  ✓ Step 3: Create ECS Infrastructure"
echo -e "  ✓ Step 4: Create ECS Task Definition"
echo -e "  → Step 5: Create GitHub Actions Workflow"
echo ""
