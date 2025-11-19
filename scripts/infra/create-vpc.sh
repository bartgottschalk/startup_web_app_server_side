#!/bin/bash

##############################################################################
# Create VPC and Networking Infrastructure for StartupWebApp
#
# This script creates:
# - VPC (10.0.0.0/16)
# - 2 Public Subnets (for bastion/NAT)
# - 2 Private Subnets (for RDS)
# - Internet Gateway
# - NAT Gateway (for private subnet internet access)
# - Route Tables
# - DB Subnet Group (required for RDS)
#
# Usage: ./scripts/infra/create-vpc.sh
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
PROJECT_NAME="startupwebapp"
ENVIRONMENT="production"
AWS_REGION="us-east-1"

# Initialize environment file
source "${SCRIPT_DIR}/init-env.sh"

# VPC Configuration
VPC_CIDR="10.0.0.0/16"
PUBLIC_SUBNET_1_CIDR="10.0.1.0/24"
PUBLIC_SUBNET_2_CIDR="10.0.2.0/24"
PRIVATE_SUBNET_1_CIDR="10.0.10.0/24"
PRIVATE_SUBNET_2_CIDR="10.0.11.0/24"
AZ_1="${AWS_REGION}a"
AZ_2="${AWS_REGION}b"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Creating VPC Infrastructure${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Source existing resource IDs if file exists
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

# Get AWS Account ID
echo -e "${YELLOW}Getting AWS Account ID...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account: ${AWS_ACCOUNT_ID}${NC}"
echo ""

# Check if VPC already exists
if [ -n "${VPC_ID:-}" ]; then
    echo -e "${YELLOW}VPC already exists: ${VPC_ID}${NC}"
    echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-vpc.sh first${NC}"
    exit 0
fi

# Ask about NAT Gateway (default: no)
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}NAT Gateway Configuration${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "${YELLOW}Do you need a NAT Gateway?${NC}"
echo ""
echo -e "A NAT Gateway allows private subnets to access the internet."
echo -e "Cost: ~\$32/month"
echo ""
echo -e "${GREEN}You NEED a NAT Gateway if:${NC}"
echo -e "  - Backend services will be in private subnets AND need internet access"
echo -e "  - Lambda functions in private subnets need internet access"
echo ""
echo -e "${GREEN}You DON'T need a NAT Gateway if:${NC}"
echo -e "  - Backend services will be in public subnets (most common)"
echo -e "  - RDS only (databases don't need outbound internet access)"
echo -e "  - You want to minimize costs"
echo ""
read -p "Create NAT Gateway? (yes/no) [default: no]: " create_nat
create_nat=${create_nat:-no}

if [ "$create_nat" != "yes" ]; then
    echo -e "${GREEN}Skipping NAT Gateway (saves ~\$32/month)${NC}"
    echo -e "${YELLOW}Note: Deploy backend services to public subnets for internet access${NC}"
    CREATE_NAT=false
else
    echo -e "${YELLOW}NAT Gateway will be created${NC}"
    CREATE_NAT=true
fi
echo ""

# Create VPC
echo -e "${YELLOW}Creating VPC (${VPC_CIDR})...${NC}"
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block "$VPC_CIDR" \
    --tag-specifications "ResourceType=vpc,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-vpc},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp},
        {Key=ManagedBy,Value=InfrastructureAsCode}
    ]" \
    --query 'Vpc.VpcId' \
    --output text)
echo -e "${GREEN}✓ VPC created: ${VPC_ID}${NC}"

# Enable DNS hostnames
echo -e "${YELLOW}Enabling DNS hostnames...${NC}"
aws ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-hostnames
echo -e "${GREEN}✓ DNS hostnames enabled${NC}"

# Create Internet Gateway
echo -e "${YELLOW}Creating Internet Gateway...${NC}"
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications "ResourceType=internet-gateway,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-igw},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp}
    ]" \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)
echo -e "${GREEN}✓ Internet Gateway created: ${IGW_ID}${NC}"

# Attach Internet Gateway to VPC
echo -e "${YELLOW}Attaching Internet Gateway to VPC...${NC}"
aws ec2 attach-internet-gateway --vpc-id "$VPC_ID" --internet-gateway-id "$IGW_ID"
echo -e "${GREEN}✓ Internet Gateway attached${NC}"

# Create Public Subnet 1
echo -e "${YELLOW}Creating Public Subnet 1 (${PUBLIC_SUBNET_1_CIDR} in ${AZ_1})...${NC}"
PUBLIC_SUBNET_1_ID=$(aws ec2 create-subnet \
    --vpc-id "$VPC_ID" \
    --cidr-block "$PUBLIC_SUBNET_1_CIDR" \
    --availability-zone "$AZ_1" \
    --tag-specifications "ResourceType=subnet,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-public-subnet-1},
        {Key=Type,Value=Public},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp}
    ]" \
    --query 'Subnet.SubnetId' \
    --output text)
echo -e "${GREEN}✓ Public Subnet 1 created: ${PUBLIC_SUBNET_1_ID}${NC}"

# Create Public Subnet 2
echo -e "${YELLOW}Creating Public Subnet 2 (${PUBLIC_SUBNET_2_CIDR} in ${AZ_2})...${NC}"
PUBLIC_SUBNET_2_ID=$(aws ec2 create-subnet \
    --vpc-id "$VPC_ID" \
    --cidr-block "$PUBLIC_SUBNET_2_CIDR" \
    --availability-zone "$AZ_2" \
    --tag-specifications "ResourceType=subnet,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-public-subnet-2},
        {Key=Type,Value=Public},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp}
    ]" \
    --query 'Subnet.SubnetId' \
    --output text)
echo -e "${GREEN}✓ Public Subnet 2 created: ${PUBLIC_SUBNET_2_ID}${NC}"

# Create Private Subnet 1 (for RDS)
echo -e "${YELLOW}Creating Private Subnet 1 (${PRIVATE_SUBNET_1_CIDR} in ${AZ_1})...${NC}"
PRIVATE_SUBNET_1_ID=$(aws ec2 create-subnet \
    --vpc-id "$VPC_ID" \
    --cidr-block "$PRIVATE_SUBNET_1_CIDR" \
    --availability-zone "$AZ_1" \
    --tag-specifications "ResourceType=subnet,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-private-subnet-1},
        {Key=Type,Value=Private},
        {Key=Purpose,Value=RDS},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp}
    ]" \
    --query 'Subnet.SubnetId' \
    --output text)
echo -e "${GREEN}✓ Private Subnet 1 created: ${PRIVATE_SUBNET_1_ID}${NC}"

# Create Private Subnet 2 (for RDS Multi-AZ)
echo -e "${YELLOW}Creating Private Subnet 2 (${PRIVATE_SUBNET_2_CIDR} in ${AZ_2})...${NC}"
PRIVATE_SUBNET_2_ID=$(aws ec2 create-subnet \
    --vpc-id "$VPC_ID" \
    --cidr-block "$PRIVATE_SUBNET_2_CIDR" \
    --availability-zone "$AZ_2" \
    --tag-specifications "ResourceType=subnet,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-private-subnet-2},
        {Key=Type,Value=Private},
        {Key=Purpose,Value=RDS},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp}
    ]" \
    --query 'Subnet.SubnetId' \
    --output text)
echo -e "${GREEN}✓ Private Subnet 2 created: ${PRIVATE_SUBNET_2_ID}${NC}"

# Create Public Route Table
echo -e "${YELLOW}Creating Public Route Table...${NC}"
PUBLIC_RT_ID=$(aws ec2 create-route-table \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=route-table,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-public-rt},
        {Key=Type,Value=Public},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp}
    ]" \
    --query 'RouteTable.RouteTableId' \
    --output text)
echo -e "${GREEN}✓ Public Route Table created: ${PUBLIC_RT_ID}${NC}"

# Add route to Internet Gateway in public route table
echo -e "${YELLOW}Adding route to Internet Gateway...${NC}"
aws ec2 create-route \
    --route-table-id "$PUBLIC_RT_ID" \
    --destination-cidr-block "0.0.0.0/0" \
    --gateway-id "$IGW_ID"
echo -e "${GREEN}✓ Route to Internet Gateway added${NC}"

# Associate Public Subnets with Public Route Table
echo -e "${YELLOW}Associating public subnets with public route table...${NC}"
aws ec2 associate-route-table --route-table-id "$PUBLIC_RT_ID" --subnet-id "$PUBLIC_SUBNET_1_ID"
aws ec2 associate-route-table --route-table-id "$PUBLIC_RT_ID" --subnet-id "$PUBLIC_SUBNET_2_ID"
echo -e "${GREEN}✓ Public subnets associated${NC}"

# Create Private Route Table (always needed for RDS in private subnets)
echo -e "${YELLOW}Creating Private Route Table...${NC}"
PRIVATE_RT_ID=$(aws ec2 create-route-table \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=route-table,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-private-rt},
        {Key=Type,Value=Private},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp}
    ]" \
    --query 'RouteTable.RouteTableId' \
    --output text)
echo -e "${GREEN}✓ Private Route Table created: ${PRIVATE_RT_ID}${NC}"

# NAT Gateway setup (optional)
if [ "$CREATE_NAT" = true ]; then
    # Allocate Elastic IP for NAT Gateway
    echo -e "${YELLOW}Allocating Elastic IP for NAT Gateway...${NC}"
    ELASTIC_IP_ALLOC=$(aws ec2 allocate-address \
        --domain vpc \
        --tag-specifications "ResourceType=elastic-ip,Tags=[
            {Key=Name,Value=${PROJECT_NAME}-nat-eip},
            {Key=Environment,Value=${ENVIRONMENT}},
            {Key=Application,Value=StartupWebApp}
        ]")
    ELASTIC_IP_ID=$(echo "$ELASTIC_IP_ALLOC" | jq -r '.AllocationId')
    ELASTIC_IP=$(echo "$ELASTIC_IP_ALLOC" | jq -r '.PublicIp')
    echo -e "${GREEN}✓ Elastic IP allocated: ${ELASTIC_IP} (${ELASTIC_IP_ID})${NC}"

    # Create NAT Gateway (in Public Subnet 1)
    echo -e "${YELLOW}Creating NAT Gateway (this takes ~2-3 minutes)...${NC}"
    NAT_GATEWAY_ID=$(aws ec2 create-nat-gateway \
        --subnet-id "$PUBLIC_SUBNET_1_ID" \
        --allocation-id "$ELASTIC_IP_ID" \
        --tag-specifications "ResourceType=natgateway,Tags=[
            {Key=Name,Value=${PROJECT_NAME}-nat-gw},
            {Key=Environment,Value=${ENVIRONMENT}},
            {Key=Application,Value=StartupWebApp}
        ]" \
        --query 'NatGateway.NatGatewayId' \
        --output text)
    echo -e "${GREEN}✓ NAT Gateway created: ${NAT_GATEWAY_ID}${NC}"

    # Wait for NAT Gateway to become available
    echo -e "${YELLOW}Waiting for NAT Gateway to become available...${NC}"
    aws ec2 wait nat-gateway-available --nat-gateway-ids "$NAT_GATEWAY_ID"
    echo -e "${GREEN}✓ NAT Gateway is available${NC}"

    # Add route to NAT Gateway in private route table
    echo -e "${YELLOW}Adding route to NAT Gateway in private route table...${NC}"
    aws ec2 create-route \
        --route-table-id "$PRIVATE_RT_ID" \
        --destination-cidr-block "0.0.0.0/0" \
        --nat-gateway-id "$NAT_GATEWAY_ID"
    echo -e "${GREEN}✓ Route to NAT Gateway added${NC}"
else
    # No NAT Gateway - private subnets have no internet access (RDS doesn't need it)
    echo -e "${YELLOW}Skipping NAT Gateway creation${NC}"
    echo -e "${GREEN}✓ Private subnets will have no internet access (suitable for RDS)${NC}"
    ELASTIC_IP_ID=""
    NAT_GATEWAY_ID=""
fi

# Associate Private Subnets with Private Route Table
echo -e "${YELLOW}Associating private subnets with private route table...${NC}"
aws ec2 associate-route-table --route-table-id "$PRIVATE_RT_ID" --subnet-id "$PRIVATE_SUBNET_1_ID"
aws ec2 associate-route-table --route-table-id "$PRIVATE_RT_ID" --subnet-id "$PRIVATE_SUBNET_2_ID"
echo -e "${GREEN}✓ Private subnets associated${NC}"

# Create DB Subnet Group (required for RDS)
echo -e "${YELLOW}Creating DB Subnet Group...${NC}"
DB_SUBNET_GROUP_NAME="${PROJECT_NAME}-db-subnet-group"
aws rds create-db-subnet-group \
    --db-subnet-group-name "$DB_SUBNET_GROUP_NAME" \
    --db-subnet-group-description "Subnet group for ${PROJECT_NAME} RDS multi-tenant instance" \
    --subnet-ids "$PRIVATE_SUBNET_1_ID" "$PRIVATE_SUBNET_2_ID" \
    --tags "Key=Name,Value=${DB_SUBNET_GROUP_NAME}" \
           "Key=Environment,Value=${ENVIRONMENT}" \
           "Key=Application,Value=StartupWebApp"
echo -e "${GREEN}✓ DB Subnet Group created: ${DB_SUBNET_GROUP_NAME}${NC}"

# Update environment file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^AWS_ACCOUNT_ID=.*|AWS_ACCOUNT_ID=\"${AWS_ACCOUNT_ID}\"|" \
    -e "s|^VPC_ID=.*|VPC_ID=\"${VPC_ID}\"|" \
    -e "s|^IGW_ID=.*|IGW_ID=\"${IGW_ID}\"|" \
    -e "s|^PUBLIC_SUBNET_1_ID=.*|PUBLIC_SUBNET_1_ID=\"${PUBLIC_SUBNET_1_ID}\"|" \
    -e "s|^PUBLIC_SUBNET_2_ID=.*|PUBLIC_SUBNET_2_ID=\"${PUBLIC_SUBNET_2_ID}\"|" \
    -e "s|^PRIVATE_SUBNET_1_ID=.*|PRIVATE_SUBNET_1_ID=\"${PRIVATE_SUBNET_1_ID}\"|" \
    -e "s|^PRIVATE_SUBNET_2_ID=.*|PRIVATE_SUBNET_2_ID=\"${PRIVATE_SUBNET_2_ID}\"|" \
    -e "s|^PUBLIC_RT_ID=.*|PUBLIC_RT_ID=\"${PUBLIC_RT_ID}\"|" \
    -e "s|^PRIVATE_RT_ID=.*|PRIVATE_RT_ID=\"${PRIVATE_RT_ID}\"|" \
    -e "s|^NAT_GATEWAY_ID=.*|NAT_GATEWAY_ID=\"${NAT_GATEWAY_ID}\"|" \
    -e "s|^ELASTIC_IP_ID=.*|ELASTIC_IP_ID=\"${ELASTIC_IP_ID}\"|" \
    -e "s|^DB_SUBNET_GROUP_NAME=.*|DB_SUBNET_GROUP_NAME=\"${DB_SUBNET_GROUP_NAME}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}VPC Infrastructure Created Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  VPC ID:                ${VPC_ID}"
echo -e "  VPC CIDR:              ${VPC_CIDR}"
echo -e "  Internet Gateway:      ${IGW_ID}"
if [ "$CREATE_NAT" = true ]; then
    echo -e "  NAT Gateway:           ${NAT_GATEWAY_ID}"
    echo -e "  Elastic IP:            ${ELASTIC_IP}"
else
    echo -e "  NAT Gateway:           Not created (saves ~\$32/month)"
fi
echo -e "  Public Subnet 1:       ${PUBLIC_SUBNET_1_ID} (${AZ_1})"
echo -e "  Public Subnet 2:       ${PUBLIC_SUBNET_2_ID} (${AZ_2})"
echo -e "  Private Subnet 1:      ${PRIVATE_SUBNET_1_ID} (${AZ_1})"
echo -e "  Private Subnet 2:      ${PRIVATE_SUBNET_2_ID} (${AZ_2})"
echo -e "  DB Subnet Group:       ${DB_SUBNET_GROUP_NAME}"
echo ""
if [ "$CREATE_NAT" = false ]; then
    echo -e "${YELLOW}Important: No NAT Gateway created${NC}"
    echo -e "  - Private subnets (RDS) have no internet access (this is fine for databases)"
    echo -e "  - Deploy backend services to public subnets for internet access"
    echo -e "  - To add NAT Gateway later: destroy and recreate VPC, or manually add via AWS Console"
    echo ""
fi
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Run: ./scripts/infra/create-security-groups.sh"
echo -e "  2. Run: ./scripts/infra/create-secrets.sh"
echo -e "  3. Run: ./scripts/infra/create-rds.sh"
echo ""
