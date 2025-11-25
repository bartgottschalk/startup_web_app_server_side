#!/bin/bash

##############################################################################
# Infrastructure Deployment Status and Next Steps
#
# This script shows what's been deployed and what's next
#
# Usage: ./scripts/infra/status.sh
##############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Initialize environment file
source "${SCRIPT_DIR}/init-env.sh"
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Infrastructure Deployment Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    echo -e "${YELLOW}Have you run any infrastructure scripts yet?${NC}"
    echo ""
    echo -e "${CYAN}Start here:${NC}"
    echo -e "  ./scripts/infra/create-vpc.sh"
    exit 1
fi

source "$ENV_FILE"

# Track overall progress
TOTAL_STEPS=7
COMPLETED_STEPS=0

# Helper function to get Name tag from a resource
get_name_tag() {
    local resource_type=$1
    local resource_id=$2
    local name=""

    case $resource_type in
        vpc|subnet|igw|route-table|nat-gateway)
            name=$(aws ec2 describe-tags \
                --filters "Name=resource-id,Values=${resource_id}" "Name=key,Values=Name" \
                --query 'Tags[0].Value' \
                --output text 2>/dev/null || echo "None")
            ;;
        security-group)
            name=$(aws ec2 describe-security-groups \
                --group-ids "${resource_id}" \
                --query 'SecurityGroups[0].Tags[?Key==`Name`].Value' \
                --output text 2>/dev/null || echo "None")
            ;;
        elastic-ip)
            name=$(aws ec2 describe-addresses \
                --allocation-ids "${resource_id}" \
                --query 'Addresses[0].Tags[?Key==`Name`].Value' \
                --output text 2>/dev/null || echo "None")
            ;;
    esac

    if [ -z "$name" ] || [ "$name" = "None" ]; then
        echo -e "${RED}NONE${NC}"
    else
        echo "$name"
    fi
}

# Step 1: VPC
echo -e "${CYAN}Step 1/7: VPC and Networking${NC}"
if [ -n "${VPC_ID:-}" ]; then
    echo -e "  ${GREEN}✓ COMPLETED${NC} - VPC and networking created"
    COMPLETED_STEPS=$((COMPLETED_STEPS + 1))
    echo ""
    echo -e "  VPC:               ${VPC_ID} ($(get_name_tag vpc ${VPC_ID}))"
    echo -e "  Internet Gateway:  ${IGW_ID} ($(get_name_tag igw ${IGW_ID}))"
    echo -e "  Public Subnet 1:   ${PUBLIC_SUBNET_1_ID} ($(get_name_tag subnet ${PUBLIC_SUBNET_1_ID}))"
    echo -e "  Public Subnet 2:   ${PUBLIC_SUBNET_2_ID} ($(get_name_tag subnet ${PUBLIC_SUBNET_2_ID}))"
    echo -e "  Private Subnet 1:  ${PRIVATE_SUBNET_1_ID} ($(get_name_tag subnet ${PRIVATE_SUBNET_1_ID}))"
    echo -e "  Private Subnet 2:  ${PRIVATE_SUBNET_2_ID} ($(get_name_tag subnet ${PRIVATE_SUBNET_2_ID}))"
    echo -e "  Public Route Tbl:  ${PUBLIC_RT_ID} ($(get_name_tag route-table ${PUBLIC_RT_ID}))"
    echo -e "  Private Route Tbl: ${PRIVATE_RT_ID} ($(get_name_tag route-table ${PRIVATE_RT_ID}))"
    if [ -n "${NAT_GATEWAY_ID:-}" ]; then
        echo -e "  NAT Gateway:       ${NAT_GATEWAY_ID} ($(get_name_tag nat-gateway ${NAT_GATEWAY_ID}))"
        echo -e "  Elastic IP:        ${ELASTIC_IP_ID} ($(get_name_tag elastic-ip ${ELASTIC_IP_ID}))"
    fi
else
    echo -e "  ${RED}✗ NOT STARTED${NC}"
    echo -e "  ${YELLOW}→ Next: ./scripts/infra/create-vpc.sh${NC}"
    echo -e "  ${YELLOW}   Time: ~10-15 minutes${NC}"
fi
echo ""

# Step 2: Security Groups
echo -e "${CYAN}Step 2/7: Security Groups${NC}"
if [ -n "${RDS_SECURITY_GROUP_ID:-}" ]; then
    echo -e "  ${GREEN}✓ COMPLETED${NC} - Security groups created"
    COMPLETED_STEPS=$((COMPLETED_STEPS + 1))
    echo ""
    echo -e "  RDS SG:      ${RDS_SECURITY_GROUP_ID} ($(get_name_tag security-group ${RDS_SECURITY_GROUP_ID}))"
    echo -e "  Bastion SG:  ${BASTION_SECURITY_GROUP_ID} ($(get_name_tag security-group ${BASTION_SECURITY_GROUP_ID}))"
    echo -e "  Backend SG:  ${BACKEND_SECURITY_GROUP_ID} ($(get_name_tag security-group ${BACKEND_SECURITY_GROUP_ID}))"
elif [ -n "${VPC_ID:-}" ]; then
    echo -e "  ${RED}✗ NOT STARTED${NC}"
    echo -e "  ${YELLOW}→ Next: ./scripts/infra/create-security-groups.sh${NC}"
    echo -e "  ${YELLOW}   Time: ~1 minute${NC}"
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Requires VPC (Step 1)"
fi
echo ""

# Step 3: Secrets Manager
echo -e "${CYAN}Step 3/7: Secrets Manager${NC}"
if [ -n "${DB_SECRET_ARN:-}" ]; then
    echo -e "  ${GREEN}✓ COMPLETED${NC} - Secret created: ${DB_SECRET_NAME}"
    COMPLETED_STEPS=$((COMPLETED_STEPS + 1))
elif [ -n "${VPC_ID:-}" ]; then
    echo -e "  ${RED}✗ NOT STARTED${NC}"
    echo -e "  ${YELLOW}→ Next: ./scripts/infra/create-secrets.sh${NC}"
    echo -e "  ${YELLOW}   Time: ~1 minute${NC}"
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Requires VPC (Step 1)"
fi
echo ""

# Step 4: RDS PostgreSQL
echo -e "${CYAN}Step 4/7: RDS PostgreSQL Instance${NC}"
if [ -n "${RDS_ENDPOINT:-}" ]; then
    # Check RDS status
    RDS_STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier "${RDS_INSTANCE_ID}" \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text 2>/dev/null || echo "unknown")

    if [ "$RDS_STATUS" == "available" ]; then
        echo -e "  ${GREEN}✓ COMPLETED${NC} - RDS instance available: ${RDS_ENDPOINT}"
        COMPLETED_STEPS=$((COMPLETED_STEPS + 1))
    else
        echo -e "  ${YELLOW}⏳ IN PROGRESS${NC} - RDS status: ${RDS_STATUS}"
        echo -e "  ${YELLOW}   Wait for status to become 'available'${NC}"
    fi
elif [ -n "${DB_SECRET_ARN:-}" ] && [ -n "${RDS_SECURITY_GROUP_ID:-}" ]; then
    echo -e "  ${RED}✗ NOT STARTED${NC}"
    echo -e "  ${YELLOW}→ Next: ./scripts/infra/create-rds.sh${NC}"
    echo -e "  ${YELLOW}   Time: ~10-15 minutes${NC}"
    echo -e "  ${YELLOW}   Cost: ~\$28/month (RDS + monitoring)${NC}"
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Requires Steps 1-3 complete"
fi
echo ""

# Optional: Bastion Host
echo -e "${CYAN}Optional: Bastion Host (for database access)${NC}"
if [ -n "${BASTION_INSTANCE_ID:-}" ]; then
    BASTION_STATUS=$(aws ec2 describe-instances \
        --instance-ids "$BASTION_INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text 2>/dev/null || echo "not-found")

    if [ "$BASTION_STATUS" != "not-found" ]; then
        echo -e "  ${GREEN}✓ CREATED${NC} - Bastion host ${BASTION_STATUS}"
        echo -e "  ${YELLOW}   Instance ID: ${BASTION_INSTANCE_ID}${NC}"
        echo -e "  ${YELLOW}   Connect: aws ssm start-session --target ${BASTION_INSTANCE_ID}${NC}"
        echo -e "  ${YELLOW}   Cost: ~\$7/month running, ~\$1/month stopped${NC}"
    else
        echo -e "  ${YELLOW}⚠ Instance not found (may be terminated)${NC}"
        echo -e "  ${YELLOW}   Create new: ./scripts/infra/create-bastion.sh${NC}"
    fi
elif [ -n "${RDS_ENDPOINT:-}" ]; then
    echo -e "  ${YELLOW}⚠ NOT CREATED${NC} (optional but recommended)"
    echo -e "  ${YELLOW}→ To create: ./scripts/infra/create-bastion.sh${NC}"
    echo -e "  ${YELLOW}   Needed for: Direct database access (Step 5)${NC}"
    echo -e "  ${YELLOW}   Cost: ~\$7/month running, ~\$1/month stopped${NC}"
    echo -e "  ${YELLOW}   Alternative: SSH tunnel from EC2 or local machine${NC}"
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Requires RDS (Step 4)"
fi
echo ""

# Step 5: Multi-Tenant Databases
echo -e "${CYAN}Step 5/7: Multi-Tenant Databases${NC}"
if [ -n "${RDS_ENDPOINT:-}" ]; then
    RDS_STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier "${RDS_INSTANCE_ID}" \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text 2>/dev/null || echo "unknown")

    if [ "$RDS_STATUS" == "available" ]; then
        echo -e "  ${YELLOW}⚠ MANUAL STEP REQUIRED${NC}"
        echo -e "  ${YELLOW}→ Next: ./scripts/infra/create-databases.sh${NC}"
        echo -e "  ${YELLOW}   This script generates SQL - you must execute it manually${NC}"
        echo -e "  ${YELLOW}   Requires: Bastion host or SSH tunnel to connect to RDS${NC}"
        echo -e "  ${YELLOW}   Creates: startupwebapp_prod, healthtech_experiment, fintech_experiment${NC}"
        # Note: We can't automatically detect if databases exist
    else
        echo -e "  ${RED}✗ BLOCKED${NC} - RDS must be 'available' (currently: ${RDS_STATUS})"
    fi
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Requires RDS (Step 4)"
fi
echo ""

# Step 6: CloudWatch Monitoring
echo -e "${CYAN}Step 6/7: CloudWatch Monitoring${NC}"
if [ -n "${SNS_TOPIC_ARN:-}" ]; then
    echo -e "  ${GREEN}✓ COMPLETED${NC} - Monitoring configured"

    # Check if subscription is confirmed
    if [ "${SNS_SUBSCRIPTION_ARN:-}" == "pending confirmation" ]; then
        echo -e "  ${YELLOW}⚠ ACTION REQUIRED${NC} - Check your email and confirm SNS subscription!"
    else
        echo -e "  ${GREEN}✓${NC} SNS subscription confirmed"
        COMPLETED_STEPS=$((COMPLETED_STEPS + 1))
    fi
elif [ -n "${RDS_ENDPOINT:-}" ]; then
    echo -e "  ${RED}✗ NOT STARTED${NC}"
    echo -e "  ${YELLOW}→ Next: ./scripts/infra/create-monitoring.sh <your-email@domain.com>${NC}"
    echo -e "  ${YELLOW}   Time: ~2 minutes${NC}"
    echo -e "  ${YELLOW}   Cost: ~\$1/month${NC}"
    echo -e "  ${YELLOW}   Note: You'll need to confirm email subscription${NC}"
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Requires RDS (Step 4)"
fi
echo ""

# Step 7: Verification
echo -e "${CYAN}Step 7/7: Verify Deployment${NC}"
if [ -n "${RDS_ENDPOINT:-}" ] && [ -n "${SNS_TOPIC_ARN:-}" ]; then
    RDS_STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier "$RDS_INSTANCE_ID" \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text 2>/dev/null || echo "unknown")

    if [ "$RDS_STATUS" == "available" ]; then
        echo -e "  ${GREEN}✓ READY FOR VERIFICATION${NC}"
        COMPLETED_STEPS=$((COMPLETED_STEPS + 1))
        echo -e "  ${YELLOW}→ Next: ./scripts/infra/show-resources.sh${NC}"
        echo -e "  ${YELLOW}   View all resources and get connection details${NC}"
    else
        echo -e "  ${RED}✗ BLOCKED${NC} - RDS status: ${RDS_STATUS}"
    fi
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Complete all previous steps first"
fi
echo ""

# Additional Infrastructure: ECR Repository (Phase 5.14 - ECS/CI/CD)
echo -e "${CYAN}════════════════════════════════════════${NC}"
echo -e "${CYAN}Phase 5.14: ECS/CI/CD Infrastructure${NC}"
echo -e "${CYAN}════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}ECR Repository (Docker Registry)${NC}"
if [ -n "${ECR_REPOSITORY_URI:-}" ]; then
    # Check if repository actually exists
    ECR_EXISTS=$(aws ecr describe-repositories \
        --repository-names "${ECR_REPOSITORY_NAME:-startupwebapp-backend}" \
        --region "${AWS_REGION}" \
        --query 'repositories[0].repositoryUri' \
        --output text 2>/dev/null || echo "")

    if [ -n "$ECR_EXISTS" ]; then
        echo -e "  ${GREEN}✓ COMPLETED${NC} - ECR repository created"
        echo ""
        echo -e "  Repository URI:  ${ECR_REPOSITORY_URI}"
        echo -e "  Repository Name: ${ECR_REPOSITORY_NAME:-startupwebapp-backend}"
    else
        echo -e "  ${YELLOW}⚠ URI in env file but repository not found in AWS${NC}"
        echo -e "  ${YELLOW}→ Recreate: ./scripts/infra/create-ecr.sh${NC}"
    fi
elif [ -n "${RDS_ENDPOINT:-}" ]; then
    echo -e "  ${RED}✗ NOT STARTED${NC}"
    echo ""
    echo -e "  ${YELLOW}Phase 5.14 builds on Phase 5.13 (RDS Infrastructure)${NC}"
    echo -e "  ${YELLOW}Purpose: Container orchestration and CI/CD for deployments${NC}"
    echo ""
    echo -e "  ${YELLOW}→ Next: ./scripts/infra/create-ecr.sh${NC}"
    echo -e "  ${YELLOW}   Time: ~2 minutes${NC}"
    echo -e "  ${YELLOW}   Cost: ~\$0.10-\$0.20/month (ECR storage)${NC}"
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Requires RDS deployment complete (Steps 1-7 above)"
fi
echo ""

# ECS Cluster
echo -e "${CYAN}ECS Cluster (Container Orchestration)${NC}"
if [ -n "${ECS_CLUSTER_NAME:-}" ]; then
    # Check if cluster actually exists
    ECS_EXISTS=$(aws ecs describe-clusters \
        --clusters "${ECS_CLUSTER_NAME}" \
        --region "${AWS_REGION}" \
        --query 'clusters[0].clusterName' \
        --output text 2>/dev/null || echo "")

    if [ -n "$ECS_EXISTS" ] && [ "$ECS_EXISTS" != "None" ]; then
        echo -e "  ${GREEN}✓ COMPLETED${NC} - ECS cluster created"
        echo ""
        echo -e "  Cluster Name:    ${ECS_CLUSTER_NAME}"
        echo -e "  Log Group:       ${ECS_LOG_GROUP_NAME:-/ecs/${PROJECT_NAME}-migrations}"
    else
        echo -e "  ${YELLOW}⚠ Cluster in env file but not found in AWS${NC}"
        echo -e "  ${YELLOW}→ Recreate: ./scripts/infra/create-ecs-cluster.sh${NC}"
    fi
elif [ -n "${ECR_REPOSITORY_URI:-}" ]; then
    echo -e "  ${RED}✗ NOT STARTED${NC}"
    echo -e "  ${YELLOW}→ Next: ./scripts/infra/create-ecs-cluster.sh${NC}"
    echo -e "  ${YELLOW}   Time: ~2 minutes${NC}"
    echo -e "  ${YELLOW}   Cost: \$0 (cluster itself is free, pay-per-use for tasks)${NC}"
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Requires ECR repository"
fi
echo ""

# ECS IAM Roles
echo -e "${CYAN}ECS IAM Roles (Task Permissions)${NC}"
if [ -n "${ECS_TASK_EXECUTION_ROLE_ARN:-}" ]; then
    # Check if roles actually exist
    EXEC_ROLE_EXISTS=$(aws iam get-role \
        --role-name "${ECS_TASK_EXECUTION_ROLE_NAME}" \
        --query 'Role.RoleName' \
        --output text 2>/dev/null || echo "")

    TASK_ROLE_EXISTS=$(aws iam get-role \
        --role-name "${ECS_TASK_ROLE_NAME}" \
        --query 'Role.RoleName' \
        --output text 2>/dev/null || echo "")

    if [ -n "$EXEC_ROLE_EXISTS" ] && [ -n "$TASK_ROLE_EXISTS" ]; then
        echo -e "  ${GREEN}✓ COMPLETED${NC} - IAM roles created"
        echo ""
        echo -e "  Task Execution Role: ${ECS_TASK_EXECUTION_ROLE_NAME}"
        echo -e "  Task Role:           ${ECS_TASK_ROLE_NAME}"
    else
        echo -e "  ${YELLOW}⚠ Roles in env file but not found in AWS${NC}"
        echo -e "  ${YELLOW}→ Recreate: ./scripts/infra/create-ecs-task-role.sh${NC}"
    fi
elif [ -n "${ECS_CLUSTER_NAME:-}" ]; then
    echo -e "  ${RED}✗ NOT STARTED${NC}"
    echo -e "  ${YELLOW}→ Next: ./scripts/infra/create-ecs-task-role.sh${NC}"
    echo -e "  ${YELLOW}   Time: ~2 minutes${NC}"
    echo -e "  ${YELLOW}   Cost: \$0 (IAM roles are free)${NC}"
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Requires ECS cluster"
fi
echo ""

# ECS Task Definition
echo -e "${CYAN}ECS Task Definition (Migration Task)${NC}"
if [ -n "${ECS_TASK_DEFINITION_ARN:-}" ]; then
    # Check if task definition actually exists
    TASK_DEF_EXISTS=$(aws ecs describe-task-definition \
        --task-definition "${ECS_TASK_DEFINITION_FAMILY}" \
        --region "${AWS_REGION}" \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text 2>/dev/null || echo "")

    if [ -n "$TASK_DEF_EXISTS" ]; then
        echo -e "  ${GREEN}✓ COMPLETED${NC} - Task definition registered"
        echo ""
        echo -e "  Family:              ${ECS_TASK_DEFINITION_FAMILY}"
        echo -e "  Revision:            ${ECS_TASK_DEFINITION_REVISION}"
    else
        echo -e "  ${YELLOW}⚠ Task definition in env file but not found in AWS${NC}"
        echo -e "  ${YELLOW}→ Recreate: ./scripts/infra/create-ecs-task-definition.sh${NC}"
    fi
elif [ -n "${ECS_TASK_EXECUTION_ROLE_ARN:-}" ]; then
    echo -e "  ${RED}✗ NOT STARTED${NC}"
    echo -e "  ${YELLOW}→ Next: ./scripts/infra/create-ecs-task-definition.sh${NC}"
    echo -e "  ${YELLOW}   Time: ~2 minutes${NC}"
    echo -e "  ${YELLOW}   Cost: \$0 (task definition itself is free)${NC}"
    echo -e "  ${YELLOW}   Note: Requires Docker image in ECR first${NC}"
else
    echo -e "  ${RED}✗ BLOCKED${NC} - Requires ECS IAM roles"
fi
echo ""

# Phase 5.14 Progress Summary
if [ -n "${ECR_REPOSITORY_URI:-}" ] || [ -n "${ECS_CLUSTER_NAME:-}" ] || [ -n "${ECS_TASK_EXECUTION_ROLE_ARN:-}" ]; then
    echo -e "${YELLOW}Phase 5.14 Progress Summary:${NC}"

    if [ -n "${ECR_REPOSITORY_URI:-}" ]; then
        echo -e "  ✓ Step 1: Multi-Stage Dockerfile"
        echo -e "  ✓ Step 2: ECR Repository"
    else
        echo -e "  ✓ Step 1: Multi-Stage Dockerfile"
        echo -e "  → Step 2: ECR Repository"
    fi

    if [ -n "${ECS_CLUSTER_NAME:-}" ]; then
        echo -e "  ✓ Step 3: ECS Cluster"
    else
        echo -e "  → Step 3: ECS Cluster"
    fi

    if [ -n "${ECS_TASK_DEFINITION_ARN:-}" ]; then
        echo -e "  ✓ Step 3: ECS Infrastructure (cluster + IAM roles)"
        echo -e "  ✓ Step 4: ECS Task Definition"
        echo -e "  → Step 5: Create GitHub Actions Workflow"
        echo -e "  → Step 6: Configure GitHub Secrets"
        echo -e "  → Step 7: Run Migrations & Documentation"
    elif [ -n "${ECS_TASK_EXECUTION_ROLE_ARN:-}" ]; then
        echo -e "  ✓ Step 3: ECS Infrastructure (cluster + IAM roles)"
        echo -e "  → Step 4: Create ECS Task Definition (./scripts/infra/create-ecs-task-definition.sh)"
        echo -e "  → Step 5: Create GitHub Actions Workflow"
        echo -e "  → Step 6: Configure GitHub Secrets"
        echo -e "  → Step 7: Run Migrations & Documentation"
    else
        echo -e "  → Step 3: ECS Infrastructure (cluster + IAM roles)"
    fi
    echo ""
fi

# Progress summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Progress Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

PERCENT=$((COMPLETED_STEPS * 100 / TOTAL_STEPS))
echo -e "  Completed: ${COMPLETED_STEPS}/${TOTAL_STEPS} steps (${PERCENT}%)"

if [ $COMPLETED_STEPS -eq 0 ]; then
    echo -e "  Status: ${RED}Not started${NC}"
    echo ""
    echo -e "${CYAN}Getting Started:${NC}"
    echo -e "  1. Read: ./scripts/infra/README.md"
    echo -e "  2. Run:  ./scripts/infra/create-vpc.sh"
elif [ $COMPLETED_STEPS -lt 4 ]; then
    echo -e "  Status: ${YELLOW}In progress - infrastructure setup${NC}"
elif [ $COMPLETED_STEPS -lt 7 ]; then
    echo -e "  Status: ${YELLOW}In progress - database and monitoring setup${NC}"
else
    echo -e "  Status: ${GREEN}Complete! ✓${NC}"
    echo ""
    echo -e "${GREEN}Infrastructure is ready!${NC}"
    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo -e "  1. Connect to RDS via bastion/tunnel and verify databases exist"
    echo -e "  2. Update Django settings with RDS credentials"
    echo -e "  3. Run Django migrations: python manage.py migrate"
    echo -e "  4. Create superuser: python manage.py createsuperuser"
    echo -e "  5. Deploy backend application"
fi

# Cost estimate
if [ $COMPLETED_STEPS -gt 0 ]; then
    echo ""
    echo -e "${CYAN}Estimated Monthly Cost:${NC}"
    TOTAL_COST=0
    if [ -n "${VPC_ID:-}" ]; then
        if [ -n "${NAT_GATEWAY_ID:-}" ]; then
            echo -e "  NAT Gateway:          ~\$32/month"
            TOTAL_COST=$((TOTAL_COST + 32))
        else
            echo -e "  NAT Gateway:          \$0 (not created)"
        fi
    fi
    if [ -n "${RDS_ENDPOINT:-}" ]; then
        echo -e "  RDS db.t4g.small:     ~\$26/month"
        echo -e "  Enhanced Monitoring:  ~\$2/month"
        TOTAL_COST=$((TOTAL_COST + 28))
    fi
    if [ -n "${BASTION_INSTANCE_ID:-}" ]; then
        BASTION_STATUS=$(aws ec2 describe-instances \
            --instance-ids "$BASTION_INSTANCE_ID" \
            --query 'Reservations[0].Instances[0].State.Name' \
            --output text 2>/dev/null || echo "not-found")
        if [ "$BASTION_STATUS" == "running" ]; then
            echo -e "  Bastion t3.micro:     ~\$7/month (stop when not in use)"
            TOTAL_COST=$((TOTAL_COST + 7))
        elif [ "$BASTION_STATUS" == "stopped" ]; then
            echo -e "  Bastion (stopped):    ~\$1/month (EBS storage only)"
            TOTAL_COST=$((TOTAL_COST + 1))
        fi
    fi
    if [ -n "${SNS_TOPIC_ARN:-}" ]; then
        echo -e "  CloudWatch/SNS:       ~\$1/month"
        TOTAL_COST=$((TOTAL_COST + 1))
    fi
    if [ -n "${ECR_REPOSITORY_URI:-}" ]; then
        echo -e "  ECR Storage:          ~\$0.10/month (1-2 images)"
        # ECR cost is negligible, don't add to total
    fi
    echo -e "  ${CYAN}────────────────────────────${NC}"
    echo -e "  ${CYAN}Total:                ~\$${TOTAL_COST}/month${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo ""
