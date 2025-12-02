#!/bin/bash

##############################################################################
# Create HTTPS Listener for ALB - StartupWebApp
#
# This script creates:
# - HTTPS listener (port 443) on the ALB
# - Associates the ACM certificate for SSL/TLS termination
# - Routes traffic to the existing target group
#
# Prerequisites:
# - ALB must exist (./scripts/infra/create-alb.sh)
# - ACM certificate must be ISSUED (./scripts/infra/create-acm-certificate.sh)
#
# After running this script:
# - HTTPS traffic will be properly terminated at ALB
# - HTTP (port 80) continues to redirect to HTTPS
# - Backend receives plain HTTP on port 8000
#
# Usage: ./scripts/infra/create-alb-https-listener.sh
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
echo -e "${BLUE}Create HTTPS Listener for ALB${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify prerequisites
if [ -z "${ALB_ARN:-}" ]; then
    echo -e "${RED}Error: ALB_ARN not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please create ALB first: ./scripts/infra/create-alb.sh${NC}"
    exit 1
fi

if [ -z "${TARGET_GROUP_ARN:-}" ]; then
    echo -e "${RED}Error: TARGET_GROUP_ARN not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please create ALB first: ./scripts/infra/create-alb.sh${NC}"
    exit 1
fi

if [ -z "${ACM_CERTIFICATE_ARN:-}" ]; then
    echo -e "${RED}Error: ACM_CERTIFICATE_ARN not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please create certificate first: ./scripts/infra/create-acm-certificate.sh${NC}"
    exit 1
fi

# Check certificate status
CERT_STATUS=$(aws acm describe-certificate \
    --certificate-arn "${ACM_CERTIFICATE_ARN}" \
    --region "${AWS_REGION}" \
    --query 'Certificate.Status' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$CERT_STATUS" != "ISSUED" ]; then
    echo -e "${RED}Error: Certificate is not ISSUED (status: ${CERT_STATUS})${NC}"
    echo -e "${YELLOW}Wait for DNS validation to complete, then try again.${NC}"
    exit 1
fi

# Check if HTTPS listener already exists
if [ -n "${HTTPS_LISTENER_ARN:-}" ]; then
    echo -e "${YELLOW}Checking if HTTPS listener exists...${NC}"
    LISTENER_EXISTS=$(aws elbv2 describe-listeners \
        --listener-arns "${HTTPS_LISTENER_ARN}" \
        --region "${AWS_REGION}" \
        --query 'Listeners[0].ListenerArn' \
        --output text 2>/dev/null || echo "")

    if [ -n "$LISTENER_EXISTS" ] && [ "$LISTENER_EXISTS" != "None" ]; then
        echo -e "${GREEN}✓ HTTPS listener already exists: ${HTTPS_LISTENER_ARN}${NC}"
        echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-alb-https-listener.sh first${NC}"
        exit 0
    else
        echo -e "${YELLOW}HTTPS listener ARN in env file but not found in AWS, creating new...${NC}"
    fi
fi

echo -e "${YELLOW}This will create an HTTPS listener on the ALB${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  ALB ARN:         ${ALB_ARN}"
echo -e "  Target Group:    ${TARGET_GROUP_ARN}"
echo -e "  Certificate:     ${ACM_CERTIFICATE_ARN}"
echo -e "  Certificate Status: ${CERT_STATUS}"
echo ""
echo -e "${YELLOW}Traffic flow after setup:${NC}"
echo -e "  HTTPS (443) → ALB → Target Group → ECS Tasks (8000)"
echo -e "  HTTP (80) → Redirect to HTTPS"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Create HTTPS Listener
echo ""
echo -e "${YELLOW}Step 1: Creating HTTPS Listener (port 443)...${NC}"

HTTPS_LISTENER_ARN=$(aws elbv2 create-listener \
    --load-balancer-arn "${ALB_ARN}" \
    --protocol HTTPS \
    --port 443 \
    --certificates "CertificateArn=${ACM_CERTIFICATE_ARN}" \
    --ssl-policy "ELBSecurityPolicy-TLS13-1-2-2021-06" \
    --default-actions "Type=forward,TargetGroupArn=${TARGET_GROUP_ARN}" \
    --region "${AWS_REGION}" \
    --tags "Key=Name,Value=${PROJECT_NAME}-https-listener" "Key=Environment,Value=${ENVIRONMENT}" \
    --query 'Listeners[0].ListenerArn' \
    --output text)

echo -e "${GREEN}✓ HTTPS Listener created: ${HTTPS_LISTENER_ARN}${NC}"

# Step 2: Save to env file
echo ""
echo -e "${YELLOW}Step 2: Updating aws-resources.env...${NC}"

sed -i.bak \
    -e "s|^HTTPS_LISTENER_ARN=.*|HTTPS_LISTENER_ARN=\"${HTTPS_LISTENER_ARN}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env updated${NC}"

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns "${ALB_ARN}" \
    --region "${AWS_REGION}" \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}HTTPS Listener Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  HTTPS Listener ARN: ${HTTPS_LISTENER_ARN}"
echo -e "  SSL Policy:         ELBSecurityPolicy-TLS13-1-2-2021-06"
echo -e "  Certificate:        ${ACM_CERTIFICATE_ARN}"
echo ""
echo -e "${GREEN}Traffic Flow:${NC}"
echo -e "  HTTP (80)  → 301 Redirect to HTTPS"
echo -e "  HTTPS (443) → Forward to Target Group → ECS Tasks (8000)"
echo ""
echo -e "${GREEN}Test HTTPS (will show certificate error until DNS is configured):${NC}"
echo -e "  curl -I https://${ALB_DNS}"
echo ""
echo -e "${GREEN}Test with certificate verification disabled:${NC}"
echo -e "  curl -Ik https://${ALB_DNS}"
echo ""
echo -e "${YELLOW}════════════════════════════════════════${NC}"
echo -e "${YELLOW}  NEXT: Configure DNS in Namecheap${NC}"
echo -e "${YELLOW}════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Add these CNAME records in Namecheap:${NC}"
echo ""
echo -e "  ${GREEN}Backend API:${NC}"
echo -e "    Host:  startupwebapp-api"
echo -e "    Value: ${ALB_DNS}"
echo -e "    Type:  CNAME"
echo ""
echo -e "${YELLOW}After DNS propagation (5-15 minutes):${NC}"
echo -e "  curl -I https://startupwebapp-api.mosaicmeshai.com"
echo ""
echo -e "${YELLOW}Phase 5.15 Progress:${NC}"
echo -e "  ✓ Step 1: Create Application Load Balancer (ALB)"
echo -e "  ✓ Step 2: Create ACM Certificate"
echo -e "  ✓ Step 3: Create HTTPS Listener"
echo -e "  → Next: Step 4 - Configure Namecheap DNS (manual)"
echo ""
