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
    echo -e "  ${GREEN}✓${NC} NAT Gateway:          ${NAT_GATEWAY_ID}"
    echo -e "  ${GREEN}✓${NC} Elastic IP:           ${ELASTIC_IP_ID}"
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
fi

echo -e "${BLUE}========================================${NC}"
echo ""
