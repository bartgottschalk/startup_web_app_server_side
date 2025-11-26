#!/bin/bash

##############################################################################
# Create NAT Gateway for StartupWebApp Private Subnets
#
# This script creates:
# - Elastic IP for NAT Gateway
# - NAT Gateway in public subnet (us-east-1a)
# - Route in private subnet route table (0.0.0.0/0 → NAT Gateway)
#
# Why NAT Gateway?
# - ECS tasks in private subnets need outbound internet access for:
#   - Pulling Docker images from ECR
#   - Fetching secrets from Secrets Manager
#   - Writing logs to CloudWatch
#   - Calling external APIs (Stripe, etc.)
# - NAT Gateway provides secure one-way internet access (outbound only)
# - Industry standard for production workloads in private subnets
#
# Cost: ~$32/month ($0.045/hour + minimal data transfer charges)
#
# Usage: ./scripts/infra/create-nat-gateway.sh
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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create NAT Gateway${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify prerequisites
if [ -z "${VPC_ID:-}" ]; then
    echo -e "${RED}Error: VPC_ID not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please create VPC first${NC}"
    exit 1
fi

if [ -z "${PUBLIC_SUBNET_1_ID:-}" ]; then
    echo -e "${RED}Error: PUBLIC_SUBNET_1_ID not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please create public subnets first${NC}"
    exit 1
fi

if [ -z "${PRIVATE_RT_ID:-}" ]; then
    echo -e "${RED}Error: PRIVATE_RT_ID not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please create private route table first${NC}"
    exit 1
fi

# Check if NAT Gateway already exists
if [ -n "${NAT_GATEWAY_ID:-}" ]; then
    echo -e "${YELLOW}Checking if NAT Gateway exists...${NC}"
    NAT_STATE=$(aws ec2 describe-nat-gateways \
        --nat-gateway-ids "${NAT_GATEWAY_ID}" \
        --region "${AWS_REGION}" \
        --query 'NatGateways[0].State' \
        --output text 2>/dev/null || echo "")

    if [ "$NAT_STATE" == "available" ] || [ "$NAT_STATE" == "pending" ]; then
        echo -e "${GREEN}✓ NAT Gateway already exists: ${NAT_GATEWAY_ID} (${NAT_STATE})${NC}"
        echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-nat-gateway.sh first${NC}"
        exit 0
    else
        echo -e "${YELLOW}NAT Gateway ID in env file but not found in AWS, creating new...${NC}"
    fi
fi

echo -e "${YELLOW}This will create a NAT Gateway for secure outbound internet access${NC}"
echo -e "${YELLOW}from private subnets (ECS tasks, RDS, etc.)${NC}"
echo ""
echo -e "${YELLOW}Cost Impact: ~\$32/month (\$0.045/hour + data transfer)${NC}"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Allocate Elastic IP for NAT Gateway
echo ""
echo -e "${YELLOW}Step 1: Allocating Elastic IP for NAT Gateway...${NC}"
ELASTIC_IP_ALLOCATION=$(aws ec2 allocate-address \
    --domain vpc \
    --region "${AWS_REGION}" \
    --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat-eip},{Key=Environment,Value=${ENVIRONMENT}},{Key=Application,Value=StartupWebApp},{Key=ManagedBy,Value=InfrastructureAsCode}]" \
    --query 'AllocationId' \
    --output text)

ELASTIC_IP_ADDRESS=$(aws ec2 describe-addresses \
    --allocation-ids "${ELASTIC_IP_ALLOCATION}" \
    --region "${AWS_REGION}" \
    --query 'Addresses[0].PublicIp' \
    --output text)

echo -e "${GREEN}✓ Elastic IP allocated: ${ELASTIC_IP_ADDRESS} (${ELASTIC_IP_ALLOCATION})${NC}"

# Step 2: Create NAT Gateway in public subnet
echo ""
echo -e "${YELLOW}Step 2: Creating NAT Gateway in public subnet (us-east-1a)...${NC}"
NAT_GATEWAY_ID=$(aws ec2 create-nat-gateway \
    --subnet-id "${PUBLIC_SUBNET_1_ID}" \
    --allocation-id "${ELASTIC_IP_ALLOCATION}" \
    --region "${AWS_REGION}" \
    --tag-specifications "ResourceType=natgateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat-gateway},{Key=Environment,Value=${ENVIRONMENT}},{Key=Application,Value=StartupWebApp},{Key=ManagedBy,Value=InfrastructureAsCode}]" \
    --query 'NatGateway.NatGatewayId' \
    --output text)

echo -e "${GREEN}✓ NAT Gateway created: ${NAT_GATEWAY_ID}${NC}"

# Step 3: Wait for NAT Gateway to become available
echo ""
echo -e "${YELLOW}Step 3: Waiting for NAT Gateway to become available (this may take 2-3 minutes)...${NC}"
aws ec2 wait nat-gateway-available \
    --nat-gateway-ids "${NAT_GATEWAY_ID}" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✓ NAT Gateway is now available${NC}"

# Step 4: Update private route table to route internet traffic through NAT Gateway
echo ""
echo -e "${YELLOW}Step 4: Updating private subnet route table...${NC}"

# Check if route already exists
EXISTING_ROUTE=$(aws ec2 describe-route-tables \
    --route-table-ids "${PRIVATE_RT_ID}" \
    --region "${AWS_REGION}" \
    --query 'RouteTables[0].Routes[?DestinationCidrBlock==`0.0.0.0/0`].NatGatewayId' \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_ROUTE" ]; then
    echo -e "${YELLOW}Replacing existing 0.0.0.0/0 route in private route table...${NC}"
    aws ec2 replace-route \
        --route-table-id "${PRIVATE_RT_ID}" \
        --destination-cidr-block "0.0.0.0/0" \
        --nat-gateway-id "${NAT_GATEWAY_ID}" \
        --region "${AWS_REGION}" > /dev/null
    echo -e "${GREEN}✓ Route replaced: 0.0.0.0/0 → ${NAT_GATEWAY_ID}${NC}"
else
    echo -e "${YELLOW}Creating 0.0.0.0/0 route in private route table...${NC}"
    aws ec2 create-route \
        --route-table-id "${PRIVATE_RT_ID}" \
        --destination-cidr-block "0.0.0.0/0" \
        --nat-gateway-id "${NAT_GATEWAY_ID}" \
        --region "${AWS_REGION}" > /dev/null
    echo -e "${GREEN}✓ Route created: 0.0.0.0/0 → ${NAT_GATEWAY_ID}${NC}"
fi

# Step 5: Save to env file
echo ""
echo -e "${YELLOW}Step 5: Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^NAT_GATEWAY_ID=.*|NAT_GATEWAY_ID=\"${NAT_GATEWAY_ID}\"|" \
    -e "s|^ELASTIC_IP_ID=.*|ELASTIC_IP_ID=\"${ELASTIC_IP_ALLOCATION}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}NAT Gateway Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  NAT Gateway ID:      ${NAT_GATEWAY_ID}"
echo -e "  Elastic IP:          ${ELASTIC_IP_ADDRESS}"
echo -e "  Allocation ID:       ${ELASTIC_IP_ALLOCATION}"
echo -e "  Public Subnet:       ${PUBLIC_SUBNET_1_ID} (us-east-1a)"
echo -e "  Private Route Table: ${PRIVATE_RT_ID}"
echo -e "  Route:               0.0.0.0/0 → ${NAT_GATEWAY_ID}"
echo ""
echo -e "${GREEN}What This Enables:${NC}"
echo -e "  ✓ ECS tasks can pull Docker images from ECR"
echo -e "  ✓ ECS tasks can fetch secrets from Secrets Manager"
echo -e "  ✓ ECS tasks can write logs to CloudWatch"
echo -e "  ✓ ECS tasks can call external APIs (Stripe, etc.)"
echo -e "  ✓ All resources in private subnets remain private (no inbound access)"
echo ""
echo -e "${GREEN}Cost Estimate:${NC}"
echo -e "  NAT Gateway:         \$0.045/hour = \$32.85/month"
echo -e "  Data Processing:     \$0.045/GB"
echo -e "  Typical usage:       ~\$33/month total"
echo ""
echo -e "${GREEN}Network Architecture:${NC}"
echo -e "  Private Subnet → NAT Gateway → Internet Gateway → Internet"
echo -e "  (Outbound only, inbound blocked for security)"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Test ECS task connectivity:"
echo -e "     Trigger GitHub Actions workflow to run migrations"
echo -e "     Expected: ECS task successfully pulls image and fetches secrets"
echo ""
echo -e "  2. Verify route table configuration:"
echo -e "     aws ec2 describe-route-tables --route-table-ids ${PRIVATE_RT_ID}"
echo ""
echo -e "  3. Monitor NAT Gateway metrics in CloudWatch:"
echo -e "     - BytesInFromSource (data from private subnets)"
echo -e "     - BytesOutToDestination (data to internet)"
echo -e "     - ActiveConnectionCount"
echo ""
echo -e "${YELLOW}Phase 5.14 Progress:${NC}"
echo -e "  ✓ Step 1: Multi-Stage Dockerfile"
echo -e "  ✓ Step 2: Create AWS ECR Repository"
echo -e "  ✓ Step 3: Create ECS Cluster and IAM Roles"
echo -e "  ✓ Step 4: Create ECS Task Definition"
echo -e "  ✓ Step 5: Create GitHub Actions CI/CD Workflow"
echo -e "  ✓ Step 6: Configure GitHub Secrets"
echo -e "  ✓ Step 7a: Create NAT Gateway"
echo -e "  → Next: Test workflow and run migrations (Step 7b)"
echo ""
