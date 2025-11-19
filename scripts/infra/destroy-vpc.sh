#!/bin/bash

##############################################################################
# Destroy VPC and Networking Infrastructure for StartupWebApp
#
# This script destroys (in reverse order):
# - DB Subnet Group
# - NAT Gateway
# - Elastic IP
# - Route Tables
# - Subnets
# - Internet Gateway
# - VPC
#
# Usage: ./scripts/infra/destroy-vpc.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# WARNING: This will DELETE all networking infrastructure
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
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"

echo -e "${RED}========================================${NC}"
echo -e "${RED}Destroying VPC Infrastructure${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    echo -e "${YELLOW}Have you created the VPC infrastructure?${NC}"
    exit 1
fi

source "$ENV_FILE"

# Confirm destruction
echo -e "${RED}WARNING: This will DELETE all VPC infrastructure!${NC}"
echo -e "${YELLOW}This includes:${NC}"
echo -e "  - VPC: ${VPC_ID}"
echo -e "  - NAT Gateway: ${NAT_GATEWAY_ID}"
echo -e "  - Elastic IP: ${ELASTIC_IP_ID}"
echo -e "  - Internet Gateway: ${IGW_ID}"
echo -e "  - All Subnets and Route Tables"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting destruction...${NC}"
echo ""

# Delete DB Subnet Group
if [ -n "$DB_SUBNET_GROUP_NAME" ]; then
    echo -e "${YELLOW}Deleting DB Subnet Group...${NC}"
    aws rds delete-db-subnet-group --db-subnet-group-name "$DB_SUBNET_GROUP_NAME" 2>/dev/null || true
    echo -e "${GREEN}✓ DB Subnet Group deleted${NC}"
fi

# Delete NAT Gateway
if [ -n "$NAT_GATEWAY_ID" ]; then
    echo -e "${YELLOW}Deleting NAT Gateway (this takes ~2-3 minutes)...${NC}"
    aws ec2 delete-nat-gateway --nat-gateway-id "$NAT_GATEWAY_ID" 2>/dev/null || true
    echo -e "${GREEN}✓ NAT Gateway deletion initiated${NC}"

    echo -e "${YELLOW}Waiting for NAT Gateway to be deleted...${NC}"
    aws ec2 wait nat-gateway-deleted --nat-gateway-ids "$NAT_GATEWAY_ID" 2>/dev/null || true
    echo -e "${GREEN}✓ NAT Gateway deleted${NC}"
fi

# Release Elastic IP
if [ -n "$ELASTIC_IP_ID" ]; then
    echo -e "${YELLOW}Releasing Elastic IP...${NC}"
    aws ec2 release-address --allocation-id "$ELASTIC_IP_ID" 2>/dev/null || true
    echo -e "${GREEN}✓ Elastic IP released${NC}"
fi

# Delete Private Route Table (disassociate first)
if [ -n "$PRIVATE_RT_ID" ]; then
    echo -e "${YELLOW}Deleting Private Route Table...${NC}"

    # Get and delete associations
    ASSOCIATIONS=$(aws ec2 describe-route-tables --route-table-ids "$PRIVATE_RT_ID" \
        --query 'RouteTables[0].Associations[?!Main].RouteTableAssociationId' --output text 2>/dev/null || true)

    for assoc in $ASSOCIATIONS; do
        aws ec2 disassociate-route-table --association-id "$assoc" 2>/dev/null || true
    done

    aws ec2 delete-route-table --route-table-id "$PRIVATE_RT_ID" 2>/dev/null || true
    echo -e "${GREEN}✓ Private Route Table deleted${NC}"
fi

# Delete Public Route Table (disassociate first)
if [ -n "$PUBLIC_RT_ID" ]; then
    echo -e "${YELLOW}Deleting Public Route Table...${NC}"

    # Get and delete associations
    ASSOCIATIONS=$(aws ec2 describe-route-tables --route-table-ids "$PUBLIC_RT_ID" \
        --query 'RouteTables[0].Associations[?!Main].RouteTableAssociationId' --output text 2>/dev/null || true)

    for assoc in $ASSOCIATIONS; do
        aws ec2 disassociate-route-table --association-id "$assoc" 2>/dev/null || true
    done

    aws ec2 delete-route-table --route-table-id "$PUBLIC_RT_ID" 2>/dev/null || true
    echo -e "${GREEN}✓ Public Route Table deleted${NC}"
fi

# Delete Subnets
for subnet_id in "$PRIVATE_SUBNET_1_ID" "$PRIVATE_SUBNET_2_ID" "$PUBLIC_SUBNET_1_ID" "$PUBLIC_SUBNET_2_ID"; do
    if [ -n "$subnet_id" ]; then
        echo -e "${YELLOW}Deleting Subnet: ${subnet_id}...${NC}"
        aws ec2 delete-subnet --subnet-id "$subnet_id" 2>/dev/null || true
        echo -e "${GREEN}✓ Subnet deleted${NC}"
    fi
done

# Detach and Delete Internet Gateway
if [ -n "$IGW_ID" ] && [ -n "$VPC_ID" ]; then
    echo -e "${YELLOW}Detaching Internet Gateway...${NC}"
    aws ec2 detach-internet-gateway --internet-gateway-id "$IGW_ID" --vpc-id "$VPC_ID" 2>/dev/null || true
    echo -e "${GREEN}✓ Internet Gateway detached${NC}"

    echo -e "${YELLOW}Deleting Internet Gateway...${NC}"
    aws ec2 delete-internet-gateway --internet-gateway-id "$IGW_ID" 2>/dev/null || true
    echo -e "${GREEN}✓ Internet Gateway deleted${NC}"
fi

# Delete VPC
if [ -n "$VPC_ID" ]; then
    echo -e "${YELLOW}Deleting VPC...${NC}"
    aws ec2 delete-vpc --vpc-id "$VPC_ID" 2>/dev/null || true
    echo -e "${GREEN}✓ VPC deleted${NC}"
fi

# Clear environment file
echo -e "${YELLOW}Clearing aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^VPC_ID=.*|VPC_ID=\"\"|" \
    -e "s|^IGW_ID=.*|IGW_ID=\"\"|" \
    -e "s|^PUBLIC_SUBNET_1_ID=.*|PUBLIC_SUBNET_1_ID=\"\"|" \
    -e "s|^PUBLIC_SUBNET_2_ID=.*|PUBLIC_SUBNET_2_ID=\"\"|" \
    -e "s|^PRIVATE_SUBNET_1_ID=.*|PRIVATE_SUBNET_1_ID=\"\"|" \
    -e "s|^PRIVATE_SUBNET_2_ID=.*|PRIVATE_SUBNET_2_ID=\"\"|" \
    -e "s|^PUBLIC_RT_ID=.*|PUBLIC_RT_ID=\"\"|" \
    -e "s|^PRIVATE_RT_ID=.*|PRIVATE_RT_ID=\"\"|" \
    -e "s|^NAT_GATEWAY_ID=.*|NAT_GATEWAY_ID=\"\"|" \
    -e "s|^ELASTIC_IP_ID=.*|ELASTIC_IP_ID=\"\"|" \
    -e "s|^DB_SUBNET_GROUP_NAME=.*|DB_SUBNET_GROUP_NAME=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}VPC Infrastructure Destroyed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
