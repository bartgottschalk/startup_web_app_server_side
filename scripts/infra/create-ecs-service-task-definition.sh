#!/bin/bash

##############################################################################
# Create ECS Service Task Definition for StartupWebApp
#
# This script creates:
# - ECS task definition for running the Django web service (gunicorn)
# - Configured for Fargate launch type (0.5 vCPU, 1 GB RAM)
# - Exposes port 8000 for ALB health checks
# - Pulls database credentials from AWS Secrets Manager
# - Logs to CloudWatch
#
# This is different from the MIGRATION task definition:
# - Migration task: one-time, runs migrate command, exits
# - Service task: long-running, runs gunicorn, serves HTTP traffic
#
# Prerequisites:
# - ECS cluster must exist (run create-ecs-cluster.sh)
# - IAM roles must exist (run create-ecs-task-role.sh)
# - ECR repository must exist with image (run create-ecr.sh)
#
# Usage: ./scripts/infra/create-ecs-service-task-definition.sh
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
TASK_FAMILY="${PROJECT_NAME}-service-task"
TASK_CPU="512"   # 0.5 vCPU
TASK_MEMORY="1024"  # 1 GB
CONTAINER_PORT="8000"
GUNICORN_WORKERS="3"  # 2 × CPU cores + 1

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create ECS Service Task Definition${NC}"
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
if [ -n "${ECS_SERVICE_TASK_DEFINITION_ARN:-}" ]; then
    echo -e "${YELLOW}Checking if service task definition exists...${NC}"
    EXISTING_TASK_DEF=$(aws ecs describe-task-definition \
        --task-definition "${TASK_FAMILY}" \
        --region "${AWS_REGION}" \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text 2>/dev/null || echo "")

    if [ -n "$EXISTING_TASK_DEF" ] && [ "$EXISTING_TASK_DEF" != "None" ]; then
        echo -e "${GREEN}✓ Service task definition already exists: ${EXISTING_TASK_DEF}${NC}"
        echo -e "${YELLOW}Note: Registering a new revision will create version :2, :3, etc.${NC}"
        echo -e "${YELLOW}To start fresh, run ./scripts/infra/destroy-ecs-service-task-definition.sh first${NC}"
        echo ""
        read -p "Register a new revision? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Aborted."
            exit 0
        fi
    fi
fi

echo -e "${YELLOW}This will create an ECS task definition for the web service${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Task Family:    ${TASK_FAMILY}"
echo -e "  CPU:            ${TASK_CPU} (0.5 vCPU)"
echo -e "  Memory:         ${TASK_MEMORY} MB (1 GB)"
echo -e "  Container Port: ${CONTAINER_PORT}"
echo -e "  Command:        gunicorn StartupWebApp.wsgi:application"
echo -e "  Workers:        ${GUNICORN_WORKERS}"
echo -e "  Image:          ${ECR_REPOSITORY_URI}:latest"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Create CloudWatch log group for service (if not exists)
SERVICE_LOG_GROUP="/ecs/${PROJECT_NAME}-service"
echo ""
echo -e "${YELLOW}Step 1: Creating CloudWatch log group (if not exists)...${NC}"

# Check if log group exists
LOG_GROUP_EXISTS=$(aws logs describe-log-groups \
    --log-group-name-prefix "${SERVICE_LOG_GROUP}" \
    --region "${AWS_REGION}" \
    --query "logGroups[?logGroupName=='${SERVICE_LOG_GROUP}'].logGroupName" \
    --output text 2>/dev/null || echo "")

if [ -z "$LOG_GROUP_EXISTS" ]; then
    aws logs create-log-group \
        --log-group-name "${SERVICE_LOG_GROUP}" \
        --region "${AWS_REGION}"

    # Set retention policy (7 days to match migration logs)
    aws logs put-retention-policy \
        --log-group-name "${SERVICE_LOG_GROUP}" \
        --retention-in-days 7 \
        --region "${AWS_REGION}"

    # Tag the log group (tags must be comma-separated, no spaces)
    aws logs tag-log-group \
        --log-group-name "${SERVICE_LOG_GROUP}" \
        --tags "Name=${PROJECT_NAME}-service-logs,Environment=${ENVIRONMENT},Project=${PROJECT_NAME}" \
        --region "${AWS_REGION}"

    echo -e "${GREEN}✓ Log group created: ${SERVICE_LOG_GROUP}${NC}"
else
    echo -e "${GREEN}✓ Log group already exists: ${SERVICE_LOG_GROUP}${NC}"
fi

# Create task definition JSON
echo ""
echo -e "${YELLOW}Step 2: Registering task definition...${NC}"

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
      "name": "web",
      "image": "${ECR_REPOSITORY_URI}:latest",
      "essential": true,
      "command": [
        "gunicorn",
        "StartupWebApp.wsgi:application",
        "--bind", "0.0.0.0:${CONTAINER_PORT}",
        "--workers", "${GUNICORN_WORKERS}",
        "--timeout", "30",
        "--access-logfile", "-",
        "--error-logfile", "-"
      ],
      "portMappings": [
        {
          "containerPort": ${CONTAINER_PORT},
          "hostPort": ${CONTAINER_PORT},
          "protocol": "tcp"
        }
      ],
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
        },
        {
          "name": "DATABASE_NAME",
          "value": "startupwebapp_prod"
        },
        {
          "name": "ENVIRONMENT_DOMAIN",
          "value": "https://startupwebapp.mosaicmeshai.com"
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
          "awslogs-group": "${SERVICE_LOG_GROUP}",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "web"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:${CONTAINER_PORT}/order/products || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
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
echo ""
echo -e "${YELLOW}Step 3: Updating aws-resources.env...${NC}"

# Check if variables exist, add or update
if grep -q "^ECS_SERVICE_TASK_DEFINITION_FAMILY=" "$ENV_FILE"; then
    sed -i.bak \
        -e "s|^ECS_SERVICE_TASK_DEFINITION_FAMILY=.*|ECS_SERVICE_TASK_DEFINITION_FAMILY=\"${TASK_FAMILY}\"|" \
        -e "s|^ECS_SERVICE_TASK_DEFINITION_ARN=.*|ECS_SERVICE_TASK_DEFINITION_ARN=\"${TASK_DEF_ARN}\"|" \
        -e "s|^ECS_SERVICE_TASK_DEFINITION_REVISION=.*|ECS_SERVICE_TASK_DEFINITION_REVISION=\"${TASK_DEF_REVISION}\"|" \
        -e "s|^ECS_SERVICE_LOG_GROUP=.*|ECS_SERVICE_LOG_GROUP=\"${SERVICE_LOG_GROUP}\"|" \
        "$ENV_FILE"
else
    # Add new variables
    echo "" >> "$ENV_FILE"
    echo "# ECS Service Task Definition (Phase 5.15)" >> "$ENV_FILE"
    echo "ECS_SERVICE_TASK_DEFINITION_FAMILY=\"${TASK_FAMILY}\"" >> "$ENV_FILE"
    echo "ECS_SERVICE_TASK_DEFINITION_ARN=\"${TASK_DEF_ARN}\"" >> "$ENV_FILE"
    echo "ECS_SERVICE_TASK_DEFINITION_REVISION=\"${TASK_DEF_REVISION}\"" >> "$ENV_FILE"
    echo "ECS_SERVICE_LOG_GROUP=\"${SERVICE_LOG_GROUP}\"" >> "$ENV_FILE"
fi
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Service Task Definition Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  Family:              ${TASK_FAMILY}"
echo -e "  ARN:                 ${TASK_DEF_ARN}"
echo -e "  Revision:            ${TASK_DEF_REVISION}"
echo -e "  Launch Type:         Fargate"
echo -e "  CPU:                 ${TASK_CPU} (0.5 vCPU)"
echo -e "  Memory:              ${TASK_MEMORY} MB (1 GB)"
echo -e "  Network Mode:        awsvpc"
echo -e "  Container Name:      web"
echo -e "  Container Port:      ${CONTAINER_PORT}"
echo -e "  Image:               ${ECR_REPOSITORY_URI}:latest"
echo ""
echo -e "${GREEN}Gunicorn Configuration:${NC}"
echo -e "  Workers:             ${GUNICORN_WORKERS}"
echo -e "  Timeout:             30 seconds"
echo -e "  Bind:                0.0.0.0:${CONTAINER_PORT}"
echo ""
echo -e "${GREEN}Container Health Check:${NC}"
echo -e "  Command:             curl -f http://localhost:${CONTAINER_PORT}/order/products"
echo -e "  Interval:            30 seconds"
echo -e "  Timeout:             5 seconds"
echo -e "  Retries:             3"
echo -e "  Start Period:        60 seconds"
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
echo -e "  DATABASE_NAME:           startupwebapp_prod"
echo ""
echo -e "${GREEN}CloudWatch Logs:${NC}"
echo -e "  Log Group:           ${SERVICE_LOG_GROUP}"
echo -e "  Stream Prefix:       web"
echo ""
echo -e "${GREEN}Cost Estimate:${NC}"
echo -e "  Per task (running):  ~\$0.027/hour"
echo -e "  0.5 vCPU:            ~\$0.0247/hour"
echo -e "  1 GB memory:         ~\$0.0027/hour"
echo -e "  2 tasks monthly:     ~\$39/month"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Create ECS Service: ./scripts/infra/create-ecs-service.sh"
echo -e "  2. Configure Auto-Scaling: ./scripts/infra/create-ecs-autoscaling.sh"
echo ""
echo -e "${YELLOW}Phase 5.15 Progress:${NC}"
echo -e "  ✓ Step 1: Create Application Load Balancer (ALB)"
echo -e "  ✓ Step 2: Create ACM Certificate"
echo -e "  ✓ Step 3: Create HTTPS Listener"
echo -e "  ✓ Step 4: Configure Namecheap DNS"
echo -e "  ✓ Step 5: Create ECS Service Task Definition"
echo -e "  → Step 6: Create ECS Service"
echo ""
