#!/bin/bash

##############################################################################
# Create ECS Auto-Scaling for StartupWebApp
#
# This script creates:
# - Application Auto Scaling target for ECS service
# - CPU-based scaling policy (target: 70%)
# - Memory-based scaling policy (target: 80%)
#
# Auto-scaling allows the ECS service to automatically adjust the number of
# tasks based on CPU and memory utilization. This helps handle traffic spikes
# while minimizing costs during low-traffic periods.
#
# Configuration:
# - Minimum tasks: 1 (cost optimization during low traffic)
# - Maximum tasks: 4 (handle traffic spikes)
# - Scale-out cooldown: 60 seconds (quick response to load)
# - Scale-in cooldown: 300 seconds (avoid flapping)
#
# Prerequisites:
# - ECS service must exist (run create-ecs-service.sh)
# - ECS cluster must exist
#
# Usage: ./scripts/infra/create-ecs-autoscaling.sh
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

# Auto-scaling configuration
MIN_CAPACITY="1"      # Minimum tasks (cost optimization)
MAX_CAPACITY="4"      # Maximum tasks (handle traffic spikes)
CPU_TARGET="70"       # Target CPU utilization (%)
MEMORY_TARGET="80"    # Target memory utilization (%)
SCALE_OUT_COOLDOWN="60"   # Seconds before next scale-out
SCALE_IN_COOLDOWN="300"   # Seconds before next scale-in (5 min to avoid flapping)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create ECS Auto-Scaling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify prerequisites
echo -e "${YELLOW}Verifying prerequisites...${NC}"

if [ -z "${ECS_CLUSTER_NAME:-}" ]; then
    echo -e "${RED}Error: ECS_CLUSTER_NAME not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-ecs-cluster.sh first${NC}"
    exit 1
fi

if [ -z "${ECS_SERVICE_NAME:-}" ]; then
    echo -e "${RED}Error: ECS_SERVICE_NAME not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-ecs-service.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites verified${NC}"
echo ""

# Construct resource ID for Application Auto Scaling
# Format: service/<cluster-name>/<service-name>
RESOURCE_ID="service/${ECS_CLUSTER_NAME}/${ECS_SERVICE_NAME}"

# Check if scalable target already exists
echo -e "${YELLOW}Checking for existing auto-scaling configuration...${NC}"
EXISTING_TARGET=$(aws application-autoscaling describe-scalable-targets \
    --service-namespace ecs \
    --resource-ids "${RESOURCE_ID}" \
    --region "${AWS_REGION}" \
    --query 'ScalableTargets[0].ResourceId' \
    --output text 2>/dev/null || echo "None")

if [ "$EXISTING_TARGET" != "None" ] && [ -n "$EXISTING_TARGET" ]; then
    echo -e "${GREEN}✓ Auto-scaling already configured for ${ECS_SERVICE_NAME}${NC}"

    # Show current configuration
    CURRENT_CONFIG=$(aws application-autoscaling describe-scalable-targets \
        --service-namespace ecs \
        --resource-ids "${RESOURCE_ID}" \
        --region "${AWS_REGION}" \
        --query 'ScalableTargets[0].{Min: MinCapacity, Max: MaxCapacity}' \
        --output json)

    CURRENT_MIN=$(echo "$CURRENT_CONFIG" | jq -r '.Min')
    CURRENT_MAX=$(echo "$CURRENT_CONFIG" | jq -r '.Max')

    echo -e "  Current Min Capacity: ${CURRENT_MIN}"
    echo -e "  Current Max Capacity: ${CURRENT_MAX}"
    echo ""
    echo -e "${YELLOW}To update configuration, destroy first: ./scripts/infra/destroy-ecs-autoscaling.sh${NC}"
    exit 0
fi

echo -e "${YELLOW}No existing auto-scaling found. Creating new configuration...${NC}"
echo ""

# Display configuration
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  ECS Cluster:            ${ECS_CLUSTER_NAME}"
echo -e "  ECS Service:            ${ECS_SERVICE_NAME}"
echo -e "  Resource ID:            ${RESOURCE_ID}"
echo ""
echo -e "${YELLOW}Scaling Limits:${NC}"
echo -e "  Minimum Tasks:          ${MIN_CAPACITY}"
echo -e "  Maximum Tasks:          ${MAX_CAPACITY}"
echo ""
echo -e "${YELLOW}Scaling Policies:${NC}"
echo -e "  CPU Target:             ${CPU_TARGET}%"
echo -e "  Memory Target:          ${MEMORY_TARGET}%"
echo -e "  Scale-Out Cooldown:     ${SCALE_OUT_COOLDOWN} seconds"
echo -e "  Scale-In Cooldown:      ${SCALE_IN_COOLDOWN} seconds"
echo ""
echo -e "${YELLOW}Cost Impact:${NC}"
echo -e "  Minimum (1 task):       ~\$20/month"
echo -e "  Maximum (4 tasks):      ~\$78/month"
echo -e "  Auto-scaling itself:    \$0 (free)"
echo ""

read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Register scalable target
echo ""
echo -e "${YELLOW}Step 1: Registering scalable target...${NC}"

aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id "${RESOURCE_ID}" \
    --scalable-dimension "ecs:service:DesiredCount" \
    --min-capacity "${MIN_CAPACITY}" \
    --max-capacity "${MAX_CAPACITY}" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✓ Scalable target registered${NC}"
echo -e "  Min Capacity: ${MIN_CAPACITY}"
echo -e "  Max Capacity: ${MAX_CAPACITY}"

# Step 2: Create CPU scaling policy
echo ""
echo -e "${YELLOW}Step 2: Creating CPU scaling policy...${NC}"

CPU_POLICY_NAME="${PROJECT_NAME}-cpu-scaling"

aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --resource-id "${RESOURCE_ID}" \
    --scalable-dimension "ecs:service:DesiredCount" \
    --policy-name "${CPU_POLICY_NAME}" \
    --policy-type "TargetTrackingScaling" \
    --target-tracking-scaling-policy-configuration "{
        \"TargetValue\": ${CPU_TARGET},
        \"PredefinedMetricSpecification\": {
            \"PredefinedMetricType\": \"ECSServiceAverageCPUUtilization\"
        },
        \"ScaleOutCooldown\": ${SCALE_OUT_COOLDOWN},
        \"ScaleInCooldown\": ${SCALE_IN_COOLDOWN}
    }" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✓ CPU scaling policy created: ${CPU_POLICY_NAME}${NC}"
echo -e "  Target: ${CPU_TARGET}% CPU utilization"

# Step 3: Create Memory scaling policy
echo ""
echo -e "${YELLOW}Step 3: Creating Memory scaling policy...${NC}"

MEMORY_POLICY_NAME="${PROJECT_NAME}-memory-scaling"

aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --resource-id "${RESOURCE_ID}" \
    --scalable-dimension "ecs:service:DesiredCount" \
    --policy-name "${MEMORY_POLICY_NAME}" \
    --policy-type "TargetTrackingScaling" \
    --target-tracking-scaling-policy-configuration "{
        \"TargetValue\": ${MEMORY_TARGET},
        \"PredefinedMetricSpecification\": {
            \"PredefinedMetricType\": \"ECSServiceAverageMemoryUtilization\"
        },
        \"ScaleOutCooldown\": ${SCALE_OUT_COOLDOWN},
        \"ScaleInCooldown\": ${SCALE_IN_COOLDOWN}
    }" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✓ Memory scaling policy created: ${MEMORY_POLICY_NAME}${NC}"
echo -e "  Target: ${MEMORY_TARGET}% memory utilization"

# Step 4: Update aws-resources.env
echo ""
echo -e "${YELLOW}Step 4: Updating aws-resources.env...${NC}"

# Check if variables exist, add or update
if grep -q "^AUTOSCALING_MIN_CAPACITY=" "$ENV_FILE"; then
    sed -i.bak \
        -e "s|^AUTOSCALING_MIN_CAPACITY=.*|AUTOSCALING_MIN_CAPACITY=\"${MIN_CAPACITY}\"|" \
        -e "s|^AUTOSCALING_MAX_CAPACITY=.*|AUTOSCALING_MAX_CAPACITY=\"${MAX_CAPACITY}\"|" \
        -e "s|^AUTOSCALING_CPU_POLICY=.*|AUTOSCALING_CPU_POLICY=\"${CPU_POLICY_NAME}\"|" \
        -e "s|^AUTOSCALING_MEMORY_POLICY=.*|AUTOSCALING_MEMORY_POLICY=\"${MEMORY_POLICY_NAME}\"|" \
        "$ENV_FILE"
else
    # Add new variables
    echo "" >> "$ENV_FILE"
    echo "# ECS Auto-Scaling (Phase 5.15 Step 6b)" >> "$ENV_FILE"
    echo "AUTOSCALING_MIN_CAPACITY=\"${MIN_CAPACITY}\"" >> "$ENV_FILE"
    echo "AUTOSCALING_MAX_CAPACITY=\"${MAX_CAPACITY}\"" >> "$ENV_FILE"
    echo "AUTOSCALING_CPU_POLICY=\"${CPU_POLICY_NAME}\"" >> "$ENV_FILE"
    echo "AUTOSCALING_MEMORY_POLICY=\"${MEMORY_POLICY_NAME}\"" >> "$ENV_FILE"
fi
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env updated${NC}"

# Step 5: Verify configuration
echo ""
echo -e "${YELLOW}Step 5: Verifying auto-scaling configuration...${NC}"

# Get current service desired count
CURRENT_DESIRED=$(aws ecs describe-services \
    --cluster "${ECS_CLUSTER_NAME}" \
    --services "${ECS_SERVICE_NAME}" \
    --region "${AWS_REGION}" \
    --query 'services[0].desiredCount' \
    --output text)

echo -e "  Current desired count: ${CURRENT_DESIRED}"

# List scaling policies
POLICIES=$(aws application-autoscaling describe-scaling-policies \
    --service-namespace ecs \
    --resource-id "${RESOURCE_ID}" \
    --region "${AWS_REGION}" \
    --query 'ScalingPolicies[*].PolicyName' \
    --output text)

echo -e "  Active policies: ${POLICIES}"

echo -e "${GREEN}✓ Auto-scaling configuration verified${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ECS Auto-Scaling Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Scalable Target:${NC}"
echo -e "  Resource ID:            ${RESOURCE_ID}"
echo -e "  Min Capacity:           ${MIN_CAPACITY} task(s)"
echo -e "  Max Capacity:           ${MAX_CAPACITY} task(s)"
echo ""
echo -e "${GREEN}Scaling Policies:${NC}"
echo -e "  CPU Policy:             ${CPU_POLICY_NAME}"
echo -e "    Target:               ${CPU_TARGET}% CPU utilization"
echo -e "    Scale-out cooldown:   ${SCALE_OUT_COOLDOWN}s"
echo -e "    Scale-in cooldown:    ${SCALE_IN_COOLDOWN}s"
echo ""
echo -e "  Memory Policy:          ${MEMORY_POLICY_NAME}"
echo -e "    Target:               ${MEMORY_TARGET}% memory utilization"
echo -e "    Scale-out cooldown:   ${SCALE_OUT_COOLDOWN}s"
echo -e "    Scale-in cooldown:    ${SCALE_IN_COOLDOWN}s"
echo ""
echo -e "${GREEN}How It Works:${NC}"
echo -e "  • When CPU > ${CPU_TARGET}% for 3 data points → add task(s)"
echo -e "  • When Memory > ${MEMORY_TARGET}% for 3 data points → add task(s)"
echo -e "  • When both metrics below target for 15 data points → remove task(s)"
echo -e "  • CloudWatch evaluates metrics every 1 minute"
echo ""
echo -e "${GREEN}Cost Impact:${NC}"
echo -e "  • Current: ${CURRENT_DESIRED} task(s) running"
echo -e "  • Min cost: ~\$20/month (1 task × 730 hours × \$0.027/hour)"
echo -e "  • Max cost: ~\$78/month (4 tasks × 730 hours × \$0.027/hour)"
echo ""
echo -e "${GREEN}Useful Commands:${NC}"
echo -e "  View scaling targets:   aws application-autoscaling describe-scalable-targets --service-namespace ecs"
echo -e "  View scaling policies:  aws application-autoscaling describe-scaling-policies --service-namespace ecs --resource-id ${RESOURCE_ID}"
echo -e "  View scaling activity:  aws application-autoscaling describe-scaling-activities --service-namespace ecs --resource-id ${RESOURCE_ID}"
echo -e "  View service:           aws ecs describe-services --cluster ${ECS_CLUSTER_NAME} --services ${ECS_SERVICE_NAME}"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Monitor task count over the next hour (should scale down to ${MIN_CAPACITY} if low traffic)"
echo -e "  2. Setup S3 + CloudFront for frontend: ./scripts/infra/create-frontend-hosting.sh"
echo ""
echo -e "${YELLOW}Note: Auto-scaling takes effect immediately. Task count will adjust based on metrics.${NC}"
echo -e "${YELLOW}During low traffic, expect tasks to scale down to ${MIN_CAPACITY} within 15-30 minutes.${NC}"
echo ""
echo -e "${YELLOW}Phase 5.15 Progress:${NC}"
echo -e "  ✓ Step 1: Create Application Load Balancer (ALB)"
echo -e "  ✓ Step 2: Create ACM Certificate"
echo -e "  ✓ Step 3: Create HTTPS Listener"
echo -e "  ✓ Step 4: Configure Namecheap DNS"
echo -e "  ✓ Step 5: Create ECS Service Task Definition"
echo -e "  ✓ Step 6: Create ECS Service"
echo -e "  ✓ Step 6b: Configure Auto-Scaling"
echo -e "  → Step 7: Setup S3 + CloudFront"
echo ""
