#!/bin/bash

##############################################################################
# Create Application Load Balancer (ALB) for StartupWebApp
#
# This script creates:
# - ALB Security Group (allow HTTP/HTTPS from internet)
# - Target Group for ECS service (port 8000, health check /order/products)
# - Application Load Balancer in public subnets
# - HTTP listener (port 80 -> redirect to HTTPS)
# - Updates Backend Security Group to allow traffic from ALB
#
# Health Check Endpoint: /order/products
# Why this endpoint?
# - Validates Django is running (returns HTML/JSON response)
# - Validates database connectivity (queries Product table)
# - Does NOT require authentication (public product listing)
# - Lightweight query suitable for frequent health checks (every 30s)
#
# Why ALB?
# - HTTPS termination (SSL/TLS handled at load balancer level)
# - Health checks (automatically replace unhealthy ECS tasks)
# - Traffic distribution across multiple ECS tasks
# - Integration with ECS Fargate for auto-scaling
# - HTTP to HTTPS redirect for security
#
# NOTE: HTTPS listener requires ACM certificate (created in Step 2)
# Run ./scripts/infra/create-alb-https-listener.sh after ACM cert is validated
#
# Cost: ~$16/month (ALB) + ~$0.008/LCU-hour (traffic-based)
#
# Usage: ./scripts/infra/create-alb.sh
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
echo -e "${BLUE}Create Application Load Balancer (ALB)${NC}"
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
    echo -e "${YELLOW}Please create VPC first: ./scripts/infra/create-vpc.sh${NC}"
    exit 1
fi

if [ -z "${PUBLIC_SUBNET_1_ID:-}" ] || [ -z "${PUBLIC_SUBNET_2_ID:-}" ]; then
    echo -e "${RED}Error: Public subnet IDs not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please create VPC with public subnets first${NC}"
    exit 1
fi

# Check if ALB already exists
if [ -n "${ALB_ARN:-}" ]; then
    echo -e "${YELLOW}Checking if ALB exists...${NC}"
    ALB_STATE=$(aws elbv2 describe-load-balancers \
        --load-balancer-arns "${ALB_ARN}" \
        --region "${AWS_REGION}" \
        --query 'LoadBalancers[0].State.Code' \
        --output text 2>/dev/null || echo "")

    if [ "$ALB_STATE" == "active" ] || [ "$ALB_STATE" == "provisioning" ]; then
        echo -e "${GREEN}✓ ALB already exists: ${ALB_ARN} (${ALB_STATE})${NC}"
        echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-alb.sh first${NC}"
        exit 0
    else
        echo -e "${YELLOW}ALB ARN in env file but not found in AWS, creating new...${NC}"
    fi
fi

echo -e "${YELLOW}This will create an Application Load Balancer for production traffic${NC}"
echo ""
echo -e "${YELLOW}Components to be created:${NC}"
echo -e "  - ALB Security Group (allow 80/443 from internet)"
echo -e "  - Target Group (port 8000, health check /order/products)"
echo -e "  - Application Load Balancer (in public subnets)"
echo -e "  - HTTP Listener (port 80 -> redirect to HTTPS)"
echo ""
echo -e "${YELLOW}Cost Impact: ~\$16/month (ALB) + traffic-based charges${NC}"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Create ALB Security Group
echo ""
echo -e "${YELLOW}Step 1: Creating ALB Security Group...${NC}"

# Check if ALB security group already exists
EXISTING_ALB_SG=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${PROJECT_NAME}-alb-sg" "Name=vpc-id,Values=${VPC_ID}" \
    --region "${AWS_REGION}" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_ALB_SG" ] && [ "$EXISTING_ALB_SG" != "None" ]; then
    ALB_SECURITY_GROUP_ID="$EXISTING_ALB_SG"
    echo -e "${GREEN}✓ ALB Security Group already exists: ${ALB_SECURITY_GROUP_ID}${NC}"
else
    ALB_SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --group-name "${PROJECT_NAME}-alb-sg" \
        --description "Security group for StartupWebApp ALB - allows HTTP/HTTPS from internet" \
        --vpc-id "${VPC_ID}" \
        --region "${AWS_REGION}" \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${PROJECT_NAME}-alb-sg},{Key=Environment,Value=${ENVIRONMENT}},{Key=Application,Value=StartupWebApp},{Key=ManagedBy,Value=InfrastructureAsCode}]" \
        --query 'GroupId' \
        --output text)

    echo -e "${GREEN}✓ ALB Security Group created: ${ALB_SECURITY_GROUP_ID}${NC}"

    # Add inbound rules for HTTP (80) and HTTPS (443)
    echo -e "${YELLOW}  Adding inbound rule: HTTP (80) from anywhere...${NC}"
    aws ec2 authorize-security-group-ingress \
        --group-id "${ALB_SECURITY_GROUP_ID}" \
        --protocol tcp \
        --port 80 \
        --cidr "0.0.0.0/0" \
        --region "${AWS_REGION}" > /dev/null

    echo -e "${YELLOW}  Adding inbound rule: HTTPS (443) from anywhere...${NC}"
    aws ec2 authorize-security-group-ingress \
        --group-id "${ALB_SECURITY_GROUP_ID}" \
        --protocol tcp \
        --port 443 \
        --cidr "0.0.0.0/0" \
        --region "${AWS_REGION}" > /dev/null

    echo -e "${GREEN}✓ ALB Security Group rules configured${NC}"
fi

# Step 2: Update Backend Security Group to allow traffic from ALB
echo ""
echo -e "${YELLOW}Step 2: Updating Backend Security Group...${NC}"

if [ -n "${BACKEND_SECURITY_GROUP_ID:-}" ]; then
    # Check if rule already exists
    EXISTING_RULE=$(aws ec2 describe-security-groups \
        --group-ids "${BACKEND_SECURITY_GROUP_ID}" \
        --region "${AWS_REGION}" \
        --query "SecurityGroups[0].IpPermissions[?FromPort==\`8000\` && ToPort==\`8000\` && UserIdGroupPairs[?GroupId==\`${ALB_SECURITY_GROUP_ID}\`]]" \
        --output text 2>/dev/null || echo "")

    if [ -z "$EXISTING_RULE" ]; then
        echo -e "${YELLOW}  Adding inbound rule: Port 8000 from ALB Security Group...${NC}"
        aws ec2 authorize-security-group-ingress \
            --group-id "${BACKEND_SECURITY_GROUP_ID}" \
            --protocol tcp \
            --port 8000 \
            --source-group "${ALB_SECURITY_GROUP_ID}" \
            --region "${AWS_REGION}" > /dev/null
        echo -e "${GREEN}✓ Backend Security Group updated: Allow port 8000 from ALB${NC}"
    else
        echo -e "${GREEN}✓ Backend Security Group already allows port 8000 from ALB${NC}"
    fi
else
    echo -e "${YELLOW}Warning: BACKEND_SECURITY_GROUP_ID not found, skipping...${NC}"
fi

# Step 3: Create Target Group
echo ""
echo -e "${YELLOW}Step 3: Creating Target Group...${NC}"

# Check if target group already exists
EXISTING_TG=$(aws elbv2 describe-target-groups \
    --names "${PROJECT_NAME}-tg" \
    --region "${AWS_REGION}" \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_TG" ] && [ "$EXISTING_TG" != "None" ]; then
    TARGET_GROUP_ARN="$EXISTING_TG"
    echo -e "${GREEN}✓ Target Group already exists: ${TARGET_GROUP_ARN}${NC}"
else
    TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
        --name "${PROJECT_NAME}-tg" \
        --protocol HTTP \
        --port 8000 \
        --vpc-id "${VPC_ID}" \
        --target-type ip \
        --health-check-enabled \
        --health-check-protocol HTTP \
        --health-check-path "/order/products" \
        --health-check-interval-seconds 30 \
        --health-check-timeout-seconds 5 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 3 \
        --matcher "HttpCode=200" \
        --region "${AWS_REGION}" \
        --tags "Key=Name,Value=${PROJECT_NAME}-tg" "Key=Environment,Value=${ENVIRONMENT}" "Key=Application,Value=StartupWebApp" "Key=ManagedBy,Value=InfrastructureAsCode" \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)

    echo -e "${GREEN}✓ Target Group created: ${TARGET_GROUP_ARN}${NC}"
fi

echo -e "${GREEN}  Target Group Configuration:${NC}"
echo -e "    Protocol: HTTP"
echo -e "    Port: 8000"
echo -e "    Target Type: IP (for Fargate)"
echo -e "    Health Check: /order/products (HTTP 200)"
echo -e "    Interval: 30s, Timeout: 5s"
echo -e "    Thresholds: 2 healthy, 3 unhealthy"

# Step 4: Create Application Load Balancer
echo ""
echo -e "${YELLOW}Step 4: Creating Application Load Balancer...${NC}"

ALB_ARN=$(aws elbv2 create-load-balancer \
    --name "${PROJECT_NAME}-alb" \
    --subnets "${PUBLIC_SUBNET_1_ID}" "${PUBLIC_SUBNET_2_ID}" \
    --security-groups "${ALB_SECURITY_GROUP_ID}" \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --region "${AWS_REGION}" \
    --tags "Key=Name,Value=${PROJECT_NAME}-alb" "Key=Environment,Value=${ENVIRONMENT}" "Key=Application,Value=StartupWebApp" "Key=ManagedBy,Value=InfrastructureAsCode" \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

ALB_DNS_NAME=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns "${ALB_ARN}" \
    --region "${AWS_REGION}" \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo -e "${GREEN}✓ Application Load Balancer created${NC}"
echo -e "    ARN: ${ALB_ARN}"
echo -e "    DNS: ${ALB_DNS_NAME}"

# Step 5: Wait for ALB to be active
echo ""
echo -e "${YELLOW}Step 5: Waiting for ALB to become active (this may take 1-2 minutes)...${NC}"

aws elbv2 wait load-balancer-available \
    --load-balancer-arns "${ALB_ARN}" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✓ ALB is now active${NC}"

# Step 6: Create HTTP Listener (redirect to HTTPS)
echo ""
echo -e "${YELLOW}Step 6: Creating HTTP Listener (port 80 -> redirect to HTTPS)...${NC}"

HTTP_LISTENER_ARN=$(aws elbv2 create-listener \
    --load-balancer-arn "${ALB_ARN}" \
    --protocol HTTP \
    --port 80 \
    --default-actions "Type=redirect,RedirectConfig={Protocol=HTTPS,Port=443,StatusCode=HTTP_301}" \
    --region "${AWS_REGION}" \
    --tags "Key=Name,Value=${PROJECT_NAME}-http-listener" "Key=Environment,Value=${ENVIRONMENT}" \
    --query 'Listeners[0].ListenerArn' \
    --output text)

echo -e "${GREEN}✓ HTTP Listener created (redirects to HTTPS)${NC}"
echo -e "    ARN: ${HTTP_LISTENER_ARN}"

# Step 7: Save to env file
echo ""
echo -e "${YELLOW}Step 7: Updating aws-resources.env...${NC}"

sed -i.bak \
    -e "s|^ALB_ARN=.*|ALB_ARN=\"${ALB_ARN}\"|" \
    -e "s|^ALB_DNS_NAME=.*|ALB_DNS_NAME=\"${ALB_DNS_NAME}\"|" \
    -e "s|^ALB_SECURITY_GROUP_ID=.*|ALB_SECURITY_GROUP_ID=\"${ALB_SECURITY_GROUP_ID}\"|" \
    -e "s|^TARGET_GROUP_ARN=.*|TARGET_GROUP_ARN=\"${TARGET_GROUP_ARN}\"|" \
    -e "s|^HTTP_LISTENER_ARN=.*|HTTP_LISTENER_ARN=\"${HTTP_LISTENER_ARN}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ALB Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  ALB ARN:             ${ALB_ARN}"
echo -e "  ALB DNS:             ${ALB_DNS_NAME}"
echo -e "  ALB Security Group:  ${ALB_SECURITY_GROUP_ID}"
echo -e "  Target Group:        ${TARGET_GROUP_ARN}"
echo -e "  HTTP Listener:       ${HTTP_LISTENER_ARN}"
echo ""
echo -e "${GREEN}Traffic Flow:${NC}"
echo -e "  Internet -> ALB (80/443) -> Target Group -> ECS Tasks (8000)"
echo ""
echo -e "${GREEN}Health Check Configuration:${NC}"
echo -e "  Endpoint:    /order/products"
echo -e "  Protocol:    HTTP"
echo -e "  Port:        8000"
echo -e "  Interval:    30 seconds"
echo -e "  Timeout:     5 seconds"
echo -e "  Healthy:     2 consecutive successes"
echo -e "  Unhealthy:   3 consecutive failures"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: HTTPS Listener Not Yet Created${NC}"
echo -e "${YELLOW}The ALB is ready but HTTPS is not yet configured.${NC}"
echo -e "${YELLOW}HTTP traffic will redirect to HTTPS but HTTPS will fail until:${NC}"
echo -e "  1. ACM Certificate is created (Step 2)"
echo -e "  2. ACM Certificate is validated via DNS"
echo -e "  3. HTTPS Listener is added to ALB"
echo ""
echo -e "${GREEN}Cost Estimate:${NC}"
echo -e "  ALB:                 ~\$16/month (fixed)"
echo -e "  LCU (traffic):       ~\$0.008/LCU-hour (variable)"
echo -e "  Typical startup:     ~\$18-20/month total"
echo ""
echo -e "${GREEN}Test the ALB (HTTP only):${NC}"
echo -e "  curl -I http://${ALB_DNS_NAME}"
echo -e "  Expected: HTTP 301 redirect to https://"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Create ACM Certificate: ./scripts/infra/create-acm-certificate.sh"
echo -e "  2. Validate certificate via Namecheap DNS (manual CNAME)"
echo -e "  3. Create HTTPS Listener: ./scripts/infra/create-alb-https-listener.sh"
echo -e "  4. Configure DNS: CNAME startupwebapp-api.mosaicmeshai.com -> ${ALB_DNS_NAME}"
echo ""
echo -e "${YELLOW}Phase 5.15 Progress:${NC}"
echo -e "  ✓ Step 1: Create Application Load Balancer (ALB)"
echo -e "  → Next: Step 2 - Request ACM Certificate"
echo ""
