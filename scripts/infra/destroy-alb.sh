#!/bin/bash

##############################################################################
# Destroy Application Load Balancer (ALB) for StartupWebApp
#
# This script deletes (in reverse order):
# - HTTPS Listener (if exists)
# - HTTP Listener
# - Application Load Balancer
# - Target Group
# - ALB Security Group
# - Backend Security Group rule (port 8000 from ALB)
#
# WARNING: After running this script:
# - Production traffic will NOT be routed to ECS tasks
# - The custom domain will return DNS errors
# - You must recreate the ALB before production can work
#
# Usage: ./scripts/infra/destroy-alb.sh
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
echo -e "${RED}DESTROY Application Load Balancer${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if ALB exists
if [ -z "${ALB_ARN:-}" ]; then
    echo -e "${YELLOW}No ALB ARN found in aws-resources.env${NC}"
    echo -e "${GREEN}Nothing to delete.${NC}"
    exit 0
fi

# Confirm destruction
echo -e "${RED}WARNING: This will delete the Application Load Balancer!${NC}"
echo -e "${RED}Production traffic will NOT be routed to ECS tasks.${NC}"
echo ""
echo -e "${YELLOW}Resources to be deleted:${NC}"
if [ -n "${HTTPS_LISTENER_ARN:-}" ]; then
    echo -e "  - HTTPS Listener: ${HTTPS_LISTENER_ARN}"
fi
if [ -n "${HTTP_LISTENER_ARN:-}" ]; then
    echo -e "  - HTTP Listener:  ${HTTP_LISTENER_ARN}"
fi
echo -e "  - ALB:            ${ALB_ARN}"
if [ -n "${TARGET_GROUP_ARN:-}" ]; then
    echo -e "  - Target Group:   ${TARGET_GROUP_ARN}"
fi
if [ -n "${ALB_SECURITY_GROUP_ID:-}" ]; then
    echo -e "  - ALB SG:         ${ALB_SECURITY_GROUP_ID}"
fi
echo ""
echo -e "${YELLOW}Cost Savings: ~\$16-20/month${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

# Step 1: Delete HTTPS Listener (if exists)
echo ""
echo -e "${YELLOW}Step 1: Deleting HTTPS Listener...${NC}"

if [ -n "${HTTPS_LISTENER_ARN:-}" ]; then
    aws elbv2 delete-listener \
        --listener-arn "${HTTPS_LISTENER_ARN}" \
        --region "${AWS_REGION}" > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ HTTPS Listener deleted${NC}"
else
    echo -e "${YELLOW}No HTTPS Listener found, skipping...${NC}"
fi

# Step 2: Delete HTTP Listener
echo ""
echo -e "${YELLOW}Step 2: Deleting HTTP Listener...${NC}"

if [ -n "${HTTP_LISTENER_ARN:-}" ]; then
    aws elbv2 delete-listener \
        --listener-arn "${HTTP_LISTENER_ARN}" \
        --region "${AWS_REGION}" > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ HTTP Listener deleted${NC}"
else
    echo -e "${YELLOW}No HTTP Listener found, skipping...${NC}"
fi

# Step 3: Delete Application Load Balancer
echo ""
echo -e "${YELLOW}Step 3: Deleting Application Load Balancer...${NC}"

aws elbv2 delete-load-balancer \
    --load-balancer-arn "${ALB_ARN}" \
    --region "${AWS_REGION}" > /dev/null 2>&1 || true

echo -e "${GREEN}✓ ALB deletion initiated${NC}"

# Step 4: Wait for ALB to be deleted
echo ""
echo -e "${YELLOW}Step 4: Waiting for ALB to be deleted (this may take 1-2 minutes)...${NC}"

MAX_WAIT=180  # 3 minutes
WAIT_INTERVAL=10
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    ALB_STATE=$(aws elbv2 describe-load-balancers \
        --load-balancer-arns "${ALB_ARN}" \
        --region "${AWS_REGION}" \
        --query 'LoadBalancers[0].State.Code' \
        --output text 2>/dev/null || echo "deleted")

    if [ "$ALB_STATE" == "deleted" ] || [ "$ALB_STATE" == "" ]; then
        echo -e "${GREEN}✓ ALB deleted${NC}"
        break
    fi

    echo -e "${YELLOW}  ALB state: ${ALB_STATE} (waiting ${WAIT_INTERVAL}s...)${NC}"
    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${YELLOW}ALB deletion in progress, continuing...${NC}"
fi

# Step 5: Delete Target Group
echo ""
echo -e "${YELLOW}Step 5: Deleting Target Group...${NC}"

if [ -n "${TARGET_GROUP_ARN:-}" ]; then
    # Wait a moment for ALB to fully release target group
    sleep 5
    aws elbv2 delete-target-group \
        --target-group-arn "${TARGET_GROUP_ARN}" \
        --region "${AWS_REGION}" > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ Target Group deleted${NC}"
else
    echo -e "${YELLOW}No Target Group found, skipping...${NC}"
fi

# Step 6: Remove Backend Security Group rule
echo ""
echo -e "${YELLOW}Step 6: Removing Backend Security Group rule...${NC}"

if [ -n "${BACKEND_SECURITY_GROUP_ID:-}" ] && [ -n "${ALB_SECURITY_GROUP_ID:-}" ]; then
    aws ec2 revoke-security-group-ingress \
        --group-id "${BACKEND_SECURITY_GROUP_ID}" \
        --protocol tcp \
        --port 8000 \
        --source-group "${ALB_SECURITY_GROUP_ID}" \
        --region "${AWS_REGION}" > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ Backend Security Group rule removed${NC}"
else
    echo -e "${YELLOW}No Backend Security Group rule to remove, skipping...${NC}"
fi

# Step 7: Delete ALB Security Group
echo ""
echo -e "${YELLOW}Step 7: Deleting ALB Security Group...${NC}"

if [ -n "${ALB_SECURITY_GROUP_ID:-}" ]; then
    # Wait a moment for ALB to fully release security group
    sleep 5
    aws ec2 delete-security-group \
        --group-id "${ALB_SECURITY_GROUP_ID}" \
        --region "${AWS_REGION}" > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ ALB Security Group deleted${NC}"
else
    echo -e "${YELLOW}No ALB Security Group found, skipping...${NC}"
fi

# Step 8: Clear environment file
echo ""
echo -e "${YELLOW}Step 8: Clearing aws-resources.env...${NC}"

sed -i.bak \
    -e "s|^ALB_ARN=.*|ALB_ARN=\"\"|" \
    -e "s|^ALB_DNS_NAME=.*|ALB_DNS_NAME=\"\"|" \
    -e "s|^ALB_SECURITY_GROUP_ID=.*|ALB_SECURITY_GROUP_ID=\"\"|" \
    -e "s|^TARGET_GROUP_ARN=.*|TARGET_GROUP_ARN=\"\"|" \
    -e "s|^HTTP_LISTENER_ARN=.*|HTTP_LISTENER_ARN=\"\"|" \
    -e "s|^HTTPS_LISTENER_ARN=.*|HTTPS_LISTENER_ARN=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ALB Deleted!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo -e "  - Production traffic will NOT reach ECS tasks"
echo -e "  - Custom domain will return errors until ALB is recreated"
echo -e "  - To recreate: ./scripts/infra/create-alb.sh"
echo -e "  - Cost savings: ~\$16-20/month"
echo ""
echo -e "${YELLOW}If you need to restore production:${NC}"
echo -e "  1. Run: ./scripts/infra/create-alb.sh"
echo -e "  2. Run: ./scripts/infra/create-alb-https-listener.sh (after ACM cert)"
echo -e "  3. Update DNS CNAME if ALB DNS changed"
echo ""
