#!/bin/bash

##############################################################################
# Show All AWS Resources for StartupWebApp
#
# This script displays all created AWS resources and their current status
#
# Usage: ./scripts/infra/show-resources.sh
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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}StartupWebApp AWS Resources${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Display configuration
echo -e "${GREEN}Configuration:${NC}"
echo -e "  AWS Region:        ${AWS_REGION}"
echo -e "  AWS Account:       ${AWS_ACCOUNT_ID:-Not set}"
echo -e "  Project:           ${PROJECT_NAME}"
echo -e "  Environment:       ${ENVIRONMENT}"
echo ""

# VPC Resources
echo -e "${GREEN}VPC Resources:${NC}"
if [ -n "$VPC_ID" ]; then
    echo -e "  ${GREEN}✓${NC} VPC:                  ${VPC_ID}"
    echo -e "  ${GREEN}✓${NC} Internet Gateway:     ${IGW_ID}"

    # NAT Gateway with state check
    if [ -n "${NAT_GATEWAY_ID:-}" ]; then
        NAT_STATE=$(aws ec2 describe-nat-gateways \
            --nat-gateway-ids "${NAT_GATEWAY_ID}" \
            --region "${AWS_REGION}" \
            --query 'NatGateways[0].State' \
            --output text 2>/dev/null || echo "not-found")

        # Get Elastic IP public address
        ELASTIC_IP_PUBLIC=""
        if [ -n "${ELASTIC_IP_ID:-}" ]; then
            ELASTIC_IP_PUBLIC=$(aws ec2 describe-addresses \
                --allocation-ids "${ELASTIC_IP_ID}" \
                --region "${AWS_REGION}" \
                --query 'Addresses[0].PublicIp' \
                --output text 2>/dev/null || echo "")
        fi

        if [ "$NAT_STATE" == "available" ]; then
            echo -e "  ${GREEN}✓${NC} NAT Gateway:          ${NAT_GATEWAY_ID} (${NAT_STATE})"
            if [ -n "$ELASTIC_IP_PUBLIC" ]; then
                echo -e "  ${GREEN}✓${NC} Elastic IP:           ${ELASTIC_IP_ID} (${ELASTIC_IP_PUBLIC})"
            else
                echo -e "  ${GREEN}✓${NC} Elastic IP:           ${ELASTIC_IP_ID}"
            fi
        elif [ "$NAT_STATE" == "pending" ]; then
            echo -e "  ${YELLOW}⚠${NC} NAT Gateway:          ${NAT_GATEWAY_ID} (${NAT_STATE} - wait 2-3 min)"
            echo -e "  ${GREEN}✓${NC} Elastic IP:           ${ELASTIC_IP_ID}"
        else
            echo -e "  ${YELLOW}⚠${NC} NAT Gateway:          ${NAT_GATEWAY_ID} (${NAT_STATE})"
            echo -e "  ${YELLOW}⚠${NC} Elastic IP:           ${ELASTIC_IP_ID}"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} NAT Gateway:          Not created (./scripts/infra/create-nat-gateway.sh)"
        echo -e "  ${YELLOW}⚠${NC} Elastic IP:           Not allocated"
    fi

    echo -e "  ${GREEN}✓${NC} Public Subnet 1:      ${PUBLIC_SUBNET_1_ID}"
    echo -e "  ${GREEN}✓${NC} Public Subnet 2:      ${PUBLIC_SUBNET_2_ID}"
    echo -e "  ${GREEN}✓${NC} Private Subnet 1:     ${PRIVATE_SUBNET_1_ID}"
    echo -e "  ${GREEN}✓${NC} Private Subnet 2:     ${PRIVATE_SUBNET_2_ID}"
    echo -e "  ${GREEN}✓${NC} DB Subnet Group:      ${DB_SUBNET_GROUP_NAME}"
else
    echo -e "  ${YELLOW}⚠${NC} VPC not created (run: ./scripts/infra/create-vpc.sh)"
fi
echo ""

# Security Groups
echo -e "${GREEN}Security Groups:${NC}"
if [ -n "${RDS_SECURITY_GROUP_ID:-}" ]; then
    echo -e "  ${GREEN}✓${NC} RDS Security Group:   ${RDS_SECURITY_GROUP_ID}"
    echo -e "  ${GREEN}✓${NC} Bastion SG:           ${BASTION_SECURITY_GROUP_ID}"
    echo -e "  ${GREEN}✓${NC} Backend SG:           ${BACKEND_SECURITY_GROUP_ID}"
else
    echo -e "  ${YELLOW}⚠${NC} Security Groups not created (run: ./scripts/infra/create-security-groups.sh)"
fi
echo ""

# Secrets Manager
echo -e "${GREEN}Secrets Manager:${NC}"
if [ -n "${DB_SECRET_ARN:-}" ]; then
    echo -e "  ${GREEN}✓${NC} Secret Name:          ${DB_SECRET_NAME}"
    echo -e "  ${GREEN}✓${NC} Secret ARN:           ${DB_SECRET_ARN}"
else
    echo -e "  ${YELLOW}⚠${NC} Secret not created (run: ./scripts/infra/create-secrets.sh)"
fi
echo ""

# Bastion Host
echo -e "${GREEN}Bastion Host (EC2):${NC}"
if [ -n "${BASTION_INSTANCE_ID:-}" ]; then
    # Get bastion status
    BASTION_STATUS=$(aws ec2 describe-instances \
        --instance-ids "$BASTION_INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text 2>/dev/null || echo "not-found")

    if [ "$BASTION_STATUS" != "not-found" ]; then
        echo -e "  ${GREEN}✓${NC} Instance ID:          ${BASTION_INSTANCE_ID}"
        echo -e "  ${GREEN}✓${NC} Status:               ${BASTION_STATUS}"
        echo -e "  ${GREEN}✓${NC} Connect:              aws ssm start-session --target ${BASTION_INSTANCE_ID}"
    else
        echo -e "  ${YELLOW}⚠${NC} Instance not found (may be terminated)"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Bastion not created (run: ./scripts/infra/create-bastion.sh)"
fi
echo ""

# RDS Resources
echo -e "${GREEN}RDS PostgreSQL:${NC}"
if [ -n "${RDS_ENDPOINT:-}" ]; then
    # Get RDS status
    RDS_STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier "$RDS_INSTANCE_ID" \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text 2>/dev/null || echo "unknown")

    echo -e "  ${GREEN}✓${NC} Instance ID:          ${RDS_INSTANCE_ID}"
    echo -e "  ${GREEN}✓${NC} Endpoint:             ${RDS_ENDPOINT}"
    echo -e "  ${GREEN}✓${NC} Port:                 ${RDS_PORT}"
    echo -e "  ${GREEN}✓${NC} Status:               ${RDS_STATUS}"
else
    echo -e "  ${YELLOW}⚠${NC} RDS not created (run: ./scripts/infra/create-rds.sh)"
fi
echo ""

# CloudWatch Monitoring
echo -e "${GREEN}CloudWatch Monitoring:${NC}"
if [ -n "${SNS_TOPIC_ARN:-}" ]; then
    echo -e "  ${GREEN}✓${NC} SNS Topic:            ${SNS_TOPIC_ARN}"
    echo -e "  ${GREEN}✓${NC} Dashboard:            ${CLOUDWATCH_DASHBOARD_NAME}"
    echo -e "  ${GREEN}✓${NC} Alarms:               4 alarms configured"
else
    echo -e "  ${YELLOW}⚠${NC} Monitoring not configured (run: ./scripts/infra/create-monitoring.sh <email>)"
fi
echo ""

# ECR Repository (Phase 5.14)
echo -e "${GREEN}ECR Repository (Phase 5.14):${NC}"
if [ -n "${ECR_REPOSITORY_URI:-}" ]; then
    echo -e "  ${GREEN}✓${NC} Repository Name:      ${ECR_REPOSITORY_NAME:-startupwebapp-backend}"
    echo -e "  ${GREEN}✓${NC} Repository URI:       ${ECR_REPOSITORY_URI}"

    # Count images in repository
    IMAGE_COUNT=$(aws ecr list-images \
        --repository-name "${ECR_REPOSITORY_NAME:-startupwebapp-backend}" \
        --region "${AWS_REGION}" \
        --query 'length(imageIds)' \
        --output text 2>/dev/null || echo "0")

    echo -e "  ${GREEN}✓${NC} Images:               ${IMAGE_COUNT} image(s)"
else
    echo -e "  ${YELLOW}⚠${NC} ECR not created (run: ./scripts/infra/create-ecr.sh)"
fi
echo ""

# ECS Cluster (Phase 5.14)
echo -e "${GREEN}ECS Cluster (Phase 5.14):${NC}"
if [ -n "${ECS_CLUSTER_NAME:-}" ]; then
    echo -e "  ${GREEN}✓${NC} Cluster Name:         ${ECS_CLUSTER_NAME}"
    echo -e "  ${GREEN}✓${NC} Cluster ARN:          ${ECS_CLUSTER_ARN}"
    echo -e "  ${GREEN}✓${NC} Log Group:            ${ECS_LOG_GROUP_NAME}"

    # Get cluster status
    CLUSTER_STATUS=$(aws ecs describe-clusters \
        --clusters "${ECS_CLUSTER_NAME}" \
        --region "${AWS_REGION}" \
        --query 'clusters[0].status' \
        --output text 2>/dev/null || echo "UNKNOWN")

    # Count running tasks
    TASK_COUNT=$(aws ecs list-tasks \
        --cluster "${ECS_CLUSTER_NAME}" \
        --region "${AWS_REGION}" \
        --query 'length(taskArns)' \
        --output text 2>/dev/null || echo "0")

    echo -e "  ${GREEN}✓${NC} Status:               ${CLUSTER_STATUS}"
    echo -e "  ${GREEN}✓${NC} Running Tasks:        ${TASK_COUNT}"
else
    echo -e "  ${YELLOW}⚠${NC} ECS Cluster not created (run: ./scripts/infra/create-ecs-cluster.sh)"
fi
echo ""

# ECS IAM Roles (Phase 5.14)
echo -e "${GREEN}ECS IAM Roles (Phase 5.14):${NC}"
if [ -n "${ECS_TASK_EXECUTION_ROLE_ARN:-}" ]; then
    echo -e "  ${GREEN}✓${NC} Task Execution Role:  ${ECS_TASK_EXECUTION_ROLE_NAME}"
    echo -e "      ARN: ${ECS_TASK_EXECUTION_ROLE_ARN}"
    echo -e "  ${GREEN}✓${NC} Task Role:            ${ECS_TASK_ROLE_NAME}"
    echo -e "      ARN: ${ECS_TASK_ROLE_ARN}"
else
    echo -e "  ${YELLOW}⚠${NC} IAM Roles not created (run: ./scripts/infra/create-ecs-task-role.sh)"
fi
echo ""

# ECS Task Definition (Phase 5.14)
echo -e "${GREEN}ECS Task Definition (Phase 5.14):${NC}"
if [ -n "${ECS_TASK_DEFINITION_ARN:-}" ]; then
    echo -e "  ${GREEN}✓${NC} Family:               ${ECS_TASK_DEFINITION_FAMILY}"
    echo -e "  ${GREEN}✓${NC} Revision:             ${ECS_TASK_DEFINITION_REVISION}"
    echo -e "  ${GREEN}✓${NC} ARN:                  ${ECS_TASK_DEFINITION_ARN}"

    # Get task definition details
    TASK_DEF_STATUS=$(aws ecs describe-task-definition \
        --task-definition "${ECS_TASK_DEFINITION_FAMILY}:${ECS_TASK_DEFINITION_REVISION}" \
        --region "${AWS_REGION}" \
        --query 'taskDefinition.status' \
        --output text 2>/dev/null || echo "UNKNOWN")

    TASK_DEF_CPU=$(aws ecs describe-task-definition \
        --task-definition "${ECS_TASK_DEFINITION_FAMILY}:${ECS_TASK_DEFINITION_REVISION}" \
        --region "${AWS_REGION}" \
        --query 'taskDefinition.cpu' \
        --output text 2>/dev/null || echo "unknown")

    TASK_DEF_MEMORY=$(aws ecs describe-task-definition \
        --task-definition "${ECS_TASK_DEFINITION_FAMILY}:${ECS_TASK_DEFINITION_REVISION}" \
        --region "${AWS_REGION}" \
        --query 'taskDefinition.memory' \
        --output text 2>/dev/null || echo "unknown")

    echo -e "  ${GREEN}✓${NC} Status:               ${TASK_DEF_STATUS}"
    echo -e "  ${GREEN}✓${NC} CPU:                  ${TASK_DEF_CPU} (0.25 vCPU)"
    echo -e "  ${GREEN}✓${NC} Memory:               ${TASK_DEF_MEMORY} MB"
else
    echo -e "  ${YELLOW}⚠${NC} Task Definition not created (run: ./scripts/infra/create-ecs-task-definition.sh)"
fi
echo ""

# Application Load Balancer (Phase 5.15)
echo -e "${GREEN}Application Load Balancer (Phase 5.15):${NC}"
if [ -n "${ALB_ARN:-}" ]; then
    # Get ALB status
    ALB_STATE=$(aws elbv2 describe-load-balancers \
        --load-balancer-arns "${ALB_ARN}" \
        --region "${AWS_REGION}" \
        --query 'LoadBalancers[0].State.Code' \
        --output text 2>/dev/null || echo "unknown")

    echo -e "  ${GREEN}✓${NC} ALB DNS:              ${ALB_DNS_NAME:-unknown}"
    echo -e "  ${GREEN}✓${NC} ALB ARN:              ${ALB_ARN}"
    echo -e "  ${GREEN}✓${NC} Status:               ${ALB_STATE}"
    echo -e "  ${GREEN}✓${NC} ALB Security Group:   ${ALB_SECURITY_GROUP_ID:-unknown}"
    echo -e "  ${GREEN}✓${NC} Target Group:         ${TARGET_GROUP_ARN:-unknown}"
    echo -e "  ${GREEN}✓${NC} HTTP Listener:        ${HTTP_LISTENER_ARN:-unknown}"
    if [ -n "${HTTPS_LISTENER_ARN:-}" ]; then
        echo -e "  ${GREEN}✓${NC} HTTPS Listener:       ${HTTPS_LISTENER_ARN}"
    else
        echo -e "  ${YELLOW}⚠${NC} HTTPS Listener:       Not configured (needs ACM certificate)"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} ALB not created (run: ./scripts/infra/create-alb.sh)"
fi
echo ""

# ACM Certificate (Phase 5.15)
echo -e "${GREEN}ACM Certificate (Phase 5.15):${NC}"
if [ -n "${ACM_CERTIFICATE_ARN:-}" ]; then
    # Get certificate status
    CERT_STATUS=$(aws acm describe-certificate \
        --certificate-arn "${ACM_CERTIFICATE_ARN}" \
        --region "${AWS_REGION}" \
        --query 'Certificate.Status' \
        --output text 2>/dev/null || echo "unknown")

    CERT_DOMAIN=$(aws acm describe-certificate \
        --certificate-arn "${ACM_CERTIFICATE_ARN}" \
        --region "${AWS_REGION}" \
        --query 'Certificate.DomainName' \
        --output text 2>/dev/null || echo "unknown")

    echo -e "  ${GREEN}✓${NC} Certificate ARN:      ${ACM_CERTIFICATE_ARN}"
    echo -e "  ${GREEN}✓${NC} Domain:               ${CERT_DOMAIN}"
    echo -e "  ${GREEN}✓${NC} Status:               ${CERT_STATUS}"
else
    echo -e "  ${YELLOW}⚠${NC} ACM Certificate not created (run: ./scripts/infra/create-acm-certificate.sh)"
fi
echo ""

# ECS Service Task Definition (Phase 5.15)
echo -e "${GREEN}ECS Service Task Definition (Phase 5.15):${NC}"
if [ -n "${ECS_SERVICE_TASK_DEFINITION_ARN:-}" ]; then
    # Get task definition details
    SERVICE_TASK_DEF_STATUS=$(aws ecs describe-task-definition \
        --task-definition "${ECS_SERVICE_TASK_DEFINITION_FAMILY:-startupwebapp-service-task}" \
        --region "${AWS_REGION}" \
        --query 'taskDefinition.status' \
        --output text 2>/dev/null || echo "UNKNOWN")

    SERVICE_TASK_DEF_CPU=$(aws ecs describe-task-definition \
        --task-definition "${ECS_SERVICE_TASK_DEFINITION_FAMILY:-startupwebapp-service-task}" \
        --region "${AWS_REGION}" \
        --query 'taskDefinition.cpu' \
        --output text 2>/dev/null || echo "unknown")

    SERVICE_TASK_DEF_MEMORY=$(aws ecs describe-task-definition \
        --task-definition "${ECS_SERVICE_TASK_DEFINITION_FAMILY:-startupwebapp-service-task}" \
        --region "${AWS_REGION}" \
        --query 'taskDefinition.memory' \
        --output text 2>/dev/null || echo "unknown")

    echo -e "  ${GREEN}✓${NC} Family:               ${ECS_SERVICE_TASK_DEFINITION_FAMILY:-startupwebapp-service-task}"
    echo -e "  ${GREEN}✓${NC} Revision:             ${ECS_SERVICE_TASK_DEFINITION_REVISION:-1}"
    echo -e "  ${GREEN}✓${NC} ARN:                  ${ECS_SERVICE_TASK_DEFINITION_ARN}"
    echo -e "  ${GREEN}✓${NC} Status:               ${SERVICE_TASK_DEF_STATUS}"
    echo -e "  ${GREEN}✓${NC} CPU:                  ${SERVICE_TASK_DEF_CPU} (0.5 vCPU)"
    echo -e "  ${GREEN}✓${NC} Memory:               ${SERVICE_TASK_DEF_MEMORY} MB"
    echo -e "  ${GREEN}✓${NC} Log Group:            ${ECS_SERVICE_LOG_GROUP:-/ecs/startupwebapp-service}"
else
    echo -e "  ${YELLOW}⚠${NC} Service Task Definition not created (run: ./scripts/infra/create-ecs-service-task-definition.sh)"
fi
echo ""

# ECS Service (Phase 5.15)
echo -e "${GREEN}ECS Service (Phase 5.15):${NC}"
if [ -n "${ECS_SERVICE_NAME:-}" ]; then
    # Get service status
    SERVICE_STATUS=$(aws ecs describe-services \
        --cluster "${ECS_CLUSTER_NAME:-startupwebapp-cluster}" \
        --services "${ECS_SERVICE_NAME}" \
        --region "${AWS_REGION}" \
        --query 'services[0].{status: status, running: runningCount, desired: desiredCount, pending: pendingCount}' \
        --output json 2>/dev/null || echo '{}')

    SERVICE_STATE=$(echo "$SERVICE_STATUS" | jq -r '.status // "UNKNOWN"')
    SERVICE_RUNNING=$(echo "$SERVICE_STATUS" | jq -r '.running // "0"')
    SERVICE_DESIRED=$(echo "$SERVICE_STATUS" | jq -r '.desired // "0"')
    SERVICE_PENDING=$(echo "$SERVICE_STATUS" | jq -r '.pending // "0"')

    echo -e "  ${GREEN}✓${NC} Service Name:         ${ECS_SERVICE_NAME}"
    echo -e "  ${GREEN}✓${NC} Service ARN:          ${ECS_SERVICE_ARN:-unknown}"
    echo -e "  ${GREEN}✓${NC} Status:               ${SERVICE_STATE}"
    echo -e "  ${GREEN}✓${NC} Running Tasks:        ${SERVICE_RUNNING}/${SERVICE_DESIRED}"
    if [ "$SERVICE_PENDING" != "0" ]; then
        echo -e "  ${YELLOW}⚠${NC} Pending Tasks:        ${SERVICE_PENDING}"
    fi

    # Get target health
    if [ -n "${TARGET_GROUP_ARN:-}" ]; then
        HEALTHY_TARGETS=$(aws elbv2 describe-target-health \
            --target-group-arn "${TARGET_GROUP_ARN}" \
            --region "${AWS_REGION}" \
            --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`] | length(@)' \
            --output text 2>/dev/null || echo "0")
        TOTAL_TARGETS=$(aws elbv2 describe-target-health \
            --target-group-arn "${TARGET_GROUP_ARN}" \
            --region "${AWS_REGION}" \
            --query 'TargetHealthDescriptions | length(@)' \
            --output text 2>/dev/null || echo "0")
        echo -e "  ${GREEN}✓${NC} Target Health:        ${HEALTHY_TARGETS}/${TOTAL_TARGETS} healthy"
    fi

    echo ""
    echo -e "  ${GREEN}Access URLs:${NC}"
    echo -e "    HTTPS:              https://startupwebapp-api.mosaicmeshai.com"
    echo -e "    Health Check:       https://startupwebapp-api.mosaicmeshai.com/order/products"
else
    echo -e "  ${YELLOW}⚠${NC} ECS Service not created (run: ./scripts/infra/create-ecs-service.sh)"
fi
echo ""

# Cost Estimate
echo -e "${GREEN}Estimated Monthly Cost:${NC}"
TOTAL_COST=0
if [ -n "${NAT_GATEWAY_ID:-}" ]; then
    echo -e "  NAT Gateway:          ~\$32/month"
    TOTAL_COST=$((TOTAL_COST + 32))
else
    echo -e "  NAT Gateway:          \$0 (not created)"
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
        echo -e "  Bastion t3.micro:     \$0 (stopped - only EBS storage ~\$1/month)"
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
if [ -n "${ALB_ARN:-}" ]; then
    echo -e "  ALB:                  ~\$16/month (+ traffic)"
    TOTAL_COST=$((TOTAL_COST + 16))
fi
if [ -n "${ECS_SERVICE_NAME:-}" ]; then
    # Get actual running task count for cost estimate
    SERVICE_RUNNING=$(aws ecs describe-services \
        --cluster "${ECS_CLUSTER_NAME:-startupwebapp-cluster}" \
        --services "${ECS_SERVICE_NAME}" \
        --region "${AWS_REGION}" \
        --query 'services[0].runningCount' \
        --output text 2>/dev/null || echo "0")
    if [ "$SERVICE_RUNNING" != "0" ] && [ "$SERVICE_RUNNING" != "None" ]; then
        TASK_COST=$((SERVICE_RUNNING * 20))  # ~$20/task/month at 0.5 vCPU, 1GB
        echo -e "  ECS Service Tasks:    ~\$${TASK_COST}/month (${SERVICE_RUNNING} tasks @ ~\$20/task)"
        TOTAL_COST=$((TOTAL_COST + TASK_COST))
    else
        echo -e "  ECS Service Tasks:    \$0 (no running tasks)"
    fi
fi
if [ $TOTAL_COST -gt 0 ]; then
    echo -e "  ${GREEN}─────────────────────────────${NC}"
    echo -e "  ${GREEN}Total:                ~\$${TOTAL_COST}/month${NC}"
else
    echo -e "  ${YELLOW}No resources created yet${NC}"
fi
echo ""

# Quick Links
if [ -n "${RDS_ENDPOINT:-}" ] || [ -n "${ECR_REPOSITORY_URI:-}" ]; then
    echo -e "${GREEN}Quick Links:${NC}"

    if [ -n "${RDS_ENDPOINT:-}" ]; then
        echo -e "  RDS Console:"
        echo -e "    https://console.aws.amazon.com/rds/home?region=${AWS_REGION}#database:id=${RDS_INSTANCE_ID}"
        echo ""
        echo -e "  CloudWatch Dashboard:"
        echo -e "    https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#dashboards:name=${CLOUDWATCH_DASHBOARD_NAME}"
        echo ""
        echo -e "  Secrets Manager:"
        echo -e "    https://console.aws.amazon.com/secretsmanager/home?region=${AWS_REGION}#!/secret?name=${DB_SECRET_NAME}"
        echo ""
    fi

    if [ -n "${ECR_REPOSITORY_URI:-}" ]; then
        echo -e "  ECR Repository:"
        echo -e "    https://console.aws.amazon.com/ecr/repositories/private/${AWS_ACCOUNT_ID}/${ECR_REPOSITORY_NAME:-startupwebapp-backend}?region=${AWS_REGION}"
        echo ""
    fi

    if [ -n "${ECS_CLUSTER_NAME:-}" ]; then
        echo -e "  ECS Cluster:"
        echo -e "    https://console.aws.amazon.com/ecs/home?region=${AWS_REGION}#/clusters/${ECS_CLUSTER_NAME}"
        echo ""
        echo -e "  ECS CloudWatch Logs:"
        echo -e "    https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#logsV2:log-groups/log-group/${ECS_LOG_GROUP_NAME}"
        echo ""
    fi

    if [ -n "${ALB_ARN:-}" ]; then
        echo -e "  Application Load Balancer:"
        echo -e "    https://console.aws.amazon.com/ec2/home?region=${AWS_REGION}#LoadBalancers:"
        echo ""
        echo -e "  ALB Target Group:"
        echo -e "    https://console.aws.amazon.com/ec2/home?region=${AWS_REGION}#TargetGroups:"
        echo ""
    fi

    if [ -n "${ACM_CERTIFICATE_ARN:-}" ]; then
        echo -e "  ACM Certificates:"
        echo -e "    https://console.aws.amazon.com/acm/home?region=${AWS_REGION}#/certificates"
        echo ""
    fi

    if [ -n "${ECS_SERVICE_LOG_GROUP:-}" ]; then
        echo -e "  ECS Service Logs:"
        echo -e "    https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#logsV2:log-groups/log-group/${ECS_SERVICE_LOG_GROUP}"
        echo ""
    fi

    if [ -n "${ECS_SERVICE_NAME:-}" ]; then
        echo -e "  ECS Service:"
        echo -e "    https://console.aws.amazon.com/ecs/home?region=${AWS_REGION}#/clusters/${ECS_CLUSTER_NAME:-startupwebapp-cluster}/services/${ECS_SERVICE_NAME}"
        echo ""
    fi
fi

echo -e "${BLUE}========================================${NC}"
echo ""
