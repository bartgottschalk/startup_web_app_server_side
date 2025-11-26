#!/bin/bash

##############################################################################
# Destroy NAT Gateway for StartupWebApp
#
# This script deletes:
# - Route from private subnet route table (0.0.0.0/0 → NAT Gateway)
# - NAT Gateway
# - Elastic IP allocation
#
# WARNING: After running this script, ECS tasks in private subnets will NOT
# be able to reach the internet (ECR, Secrets Manager, CloudWatch, external APIs)
#
# Usage: ./scripts/infra/destroy-nat-gateway.sh
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

echo -e "${RED}========================================${NC}"
echo -e "${RED}DESTROY NAT Gateway${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if NAT Gateway exists
if [ -z "${NAT_GATEWAY_ID:-}" ]; then
    echo -e "${YELLOW}No NAT Gateway ID found in aws-resources.env${NC}"
    echo -e "${GREEN}Nothing to delete.${NC}"
    exit 0
fi

# Confirm destruction
echo -e "${RED}WARNING: This will delete the NAT Gateway!${NC}"
echo -e "${RED}ECS tasks will NOT be able to reach the internet after deletion.${NC}"
echo ""
echo -e "${YELLOW}NAT Gateway ID: ${NAT_GATEWAY_ID}${NC}"
if [ -n "${ELASTIC_IP_ID:-}" ]; then
    ELASTIC_IP=$(aws ec2 describe-addresses \
        --allocation-ids "${ELASTIC_IP_ID}" \
        --region "${AWS_REGION}" \
        --query 'Addresses[0].PublicIp' \
        --output text 2>/dev/null || echo "unknown")
    echo -e "${YELLOW}Elastic IP: ${ELASTIC_IP} (${ELASTIC_IP_ID})${NC}"
fi
echo ""
echo -e "${YELLOW}Cost Savings: ~\$32/month${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

# Step 1: Delete route from private route table
echo ""
echo -e "${YELLOW}Step 1: Deleting 0.0.0.0/0 route from private route table...${NC}"

if [ -n "${PRIVATE_RT_ID:-}" ]; then
    aws ec2 delete-route \
        --route-table-id "${PRIVATE_RT_ID}" \
        --destination-cidr-block "0.0.0.0/0" \
        --region "${AWS_REGION}" > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ Route deleted from private route table${NC}"
else
    echo -e "${YELLOW}No private route table ID found, skipping...${NC}"
fi

# Step 2: Delete NAT Gateway
echo ""
echo -e "${YELLOW}Step 2: Deleting NAT Gateway...${NC}"

aws ec2 delete-nat-gateway \
    --nat-gateway-id "${NAT_GATEWAY_ID}" \
    --region "${AWS_REGION}" > /dev/null 2>&1 || true

echo -e "${GREEN}✓ NAT Gateway deletion initiated${NC}"

# Step 3: Wait for NAT Gateway to be deleted (takes a few minutes)
echo ""
echo -e "${YELLOW}Step 3: Waiting for NAT Gateway to be deleted (this may take 2-3 minutes)...${NC}"

# Poll NAT Gateway state until deleted
MAX_WAIT=300  # 5 minutes
WAIT_INTERVAL=10
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    NAT_STATE=$(aws ec2 describe-nat-gateways \
        --nat-gateway-ids "${NAT_GATEWAY_ID}" \
        --region "${AWS_REGION}" \
        --query 'NatGateways[0].State' \
        --output text 2>/dev/null || echo "deleted")

    if [ "$NAT_STATE" == "deleted" ] || [ "$NAT_STATE" == "None" ]; then
        echo -e "${GREEN}✓ NAT Gateway deleted${NC}"
        break
    fi

    echo -e "${YELLOW}  NAT Gateway state: ${NAT_STATE} (waiting ${WAIT_INTERVAL}s...)${NC}"
    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}Warning: NAT Gateway deletion timed out after 5 minutes${NC}"
    echo -e "${YELLOW}The NAT Gateway may still be deleting. Check AWS Console.${NC}"
fi

# Step 4: Release Elastic IP
echo ""
echo -e "${YELLOW}Step 4: Releasing Elastic IP...${NC}"

if [ -n "${ELASTIC_IP_ID:-}" ]; then
    aws ec2 release-address \
        --allocation-id "${ELASTIC_IP_ID}" \
        --region "${AWS_REGION}" > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ Elastic IP released${NC}"
else
    echo -e "${YELLOW}No Elastic IP ID found, skipping...${NC}"
fi

# Step 5: Clear environment file
echo ""
echo -e "${YELLOW}Step 5: Clearing aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^NAT_GATEWAY_ID=.*|NAT_GATEWAY_ID=\"\"|" \
    -e "s|^ELASTIC_IP_ID=.*|ELASTIC_IP_ID=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}NAT Gateway Deleted!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo -e "  • ECS tasks in private subnets can NO LONGER reach the internet"
echo -e "  • GitHub Actions workflow will FAIL until NAT Gateway is recreated"
echo -e "  • To recreate: ./scripts/infra/create-nat-gateway.sh"
echo -e "  • Cost savings: ~\$32/month"
echo ""
