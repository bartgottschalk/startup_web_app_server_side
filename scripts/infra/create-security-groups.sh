#!/bin/bash

##############################################################################
# Create Security Groups for StartupWebApp Infrastructure
#
# This script creates:
# - RDS Security Group (port 5432, private access only)
# - Bastion Security Group (port 22, public access for admin)
# - Backend Security Group (for future ECS/EC2 deployment)
#
# Usage: ./scripts/infra/create-security-groups.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# Prerequisites: VPC must be created first (run create-vpc.sh)
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
ENVIRONMENT="production"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Creating Security Groups${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify VPC exists
if [ -z "$VPC_ID" ]; then
    echo -e "${RED}Error: VPC_ID not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-vpc.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}Using VPC: ${VPC_ID}${NC}"
echo ""

# Check if security groups already exist
if [ -n "${RDS_SECURITY_GROUP_ID:-}" ]; then
    echo -e "${YELLOW}Security groups already exist${NC}"
    echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-security-groups.sh first${NC}"
    exit 0
fi

# Create RDS Security Group
echo -e "${YELLOW}Creating RDS Security Group...${NC}"
RDS_SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name "${PROJECT_NAME}-rds-sg" \
    --description "PostgreSQL access for StartupWebApp multi-tenant RDS" \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-rds-sg},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp},
        {Key=Purpose,Value=RDS}
    ]" \
    --query 'GroupId' \
    --output text)
echo -e "${GREEN}✓ RDS Security Group created: ${RDS_SECURITY_GROUP_ID}${NC}"

# Create Bastion Security Group
echo -e "${YELLOW}Creating Bastion Security Group...${NC}"
BASTION_SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name "${PROJECT_NAME}-bastion-sg" \
    --description "SSH access for bastion host admin" \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-bastion-sg},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp},
        {Key=Purpose,Value=Bastion}
    ]" \
    --query 'GroupId' \
    --output text)
echo -e "${GREEN}✓ Bastion Security Group created: ${BASTION_SECURITY_GROUP_ID}${NC}"

# Create Backend Security Group
echo -e "${YELLOW}Creating Backend Security Group...${NC}"
BACKEND_SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name "${PROJECT_NAME}-backend-sg" \
    --description "Backend services (ECS/EC2) for StartupWebApp" \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-backend-sg},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp},
        {Key=Purpose,Value=Backend}
    ]" \
    --query 'GroupId' \
    --output text)
echo -e "${GREEN}✓ Backend Security Group created: ${BACKEND_SECURITY_GROUP_ID}${NC}"

# Add inbound rule to RDS SG: Allow PostgreSQL from Backend SG
echo -e "${YELLOW}Adding PostgreSQL rule (Backend -> RDS)...${NC}"
aws ec2 authorize-security-group-ingress \
    --group-id "$RDS_SECURITY_GROUP_ID" \
    --protocol tcp \
    --port 5432 \
    --source-group "$BACKEND_SECURITY_GROUP_ID" \
    --group-owner "$AWS_ACCOUNT_ID"
echo -e "${GREEN}✓ Rule added: Backend -> RDS (port 5432)${NC}"

# Add inbound rule to RDS SG: Allow PostgreSQL from Bastion SG (for admin access)
echo -e "${YELLOW}Adding PostgreSQL rule (Bastion -> RDS)...${NC}"
aws ec2 authorize-security-group-ingress \
    --group-id "$RDS_SECURITY_GROUP_ID" \
    --protocol tcp \
    --port 5432 \
    --source-group "$BASTION_SECURITY_GROUP_ID" \
    --group-owner "$AWS_ACCOUNT_ID"
echo -e "${GREEN}✓ Rule added: Bastion -> RDS (port 5432)${NC}"

# Add inbound rule to Bastion SG: Allow SSH from your IP
echo -e "${YELLOW}Getting your public IP address...${NC}"
MY_IP=$(curl -s https://checkip.amazonaws.com)
echo -e "${GREEN}✓ Your public IP: ${MY_IP}${NC}"

echo -e "${YELLOW}Adding SSH rule (Your IP -> Bastion)...${NC}"
aws ec2 authorize-security-group-ingress \
    --group-id "$BASTION_SECURITY_GROUP_ID" \
    --protocol tcp \
    --port 22 \
    --cidr "${MY_IP}/32"
echo -e "${GREEN}✓ Rule added: ${MY_IP}/32 -> Bastion (port 22)${NC}"

# Add outbound rules (allow all by default, but let's be explicit)
echo -e "${YELLOW}Configuring outbound rules...${NC}"
echo -e "${GREEN}✓ Outbound rules configured (default: allow all)${NC}"

# Update environment file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^RDS_SECURITY_GROUP_ID=.*|RDS_SECURITY_GROUP_ID=\"${RDS_SECURITY_GROUP_ID}\"|" \
    -e "s|^BASTION_SECURITY_GROUP_ID=.*|BASTION_SECURITY_GROUP_ID=\"${BASTION_SECURITY_GROUP_ID}\"|" \
    -e "s|^BACKEND_SECURITY_GROUP_ID=.*|BACKEND_SECURITY_GROUP_ID=\"${BACKEND_SECURITY_GROUP_ID}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Security Groups Created Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  RDS Security Group:      ${RDS_SECURITY_GROUP_ID}"
echo -e "    - Allows PostgreSQL (5432) from Backend SG"
echo -e "    - Allows PostgreSQL (5432) from Bastion SG"
echo ""
echo -e "  Bastion Security Group:  ${BASTION_SECURITY_GROUP_ID}"
echo -e "    - Allows SSH (22) from ${MY_IP}/32"
echo ""
echo -e "  Backend Security Group:  ${BACKEND_SECURITY_GROUP_ID}"
echo -e "    - Ready for backend services"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Run: ./scripts/infra/create-secrets.sh"
echo -e "  2. Run: ./scripts/infra/create-rds.sh"
echo ""
