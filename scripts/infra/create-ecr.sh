#!/bin/bash

##############################################################################
# Create AWS ECR Repository for StartupWebApp Backend
#
# This script creates:
# - ECR repository for Docker images
# - Image scanning configuration (scan on push)
# - Lifecycle policy (keep last 10 images)
# - Encryption at rest (AES256)
#
# Usage: ./scripts/infra/create-ecr.sh
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
REPOSITORY_NAME="${PROJECT_NAME}-backend"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create AWS ECR Repository${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if repository already exists
if [ -n "${ECR_REPOSITORY_URI:-}" ]; then
    echo -e "${YELLOW}Checking if ECR repository exists...${NC}"
    EXISTING_REPO=$(aws ecr describe-repositories \
        --repository-names "${REPOSITORY_NAME}" \
        --region "${AWS_REGION}" \
        --query 'repositories[0].repositoryUri' \
        --output text 2>/dev/null || echo "")

    if [ -n "$EXISTING_REPO" ]; then
        echo -e "${GREEN}✓ ECR repository already exists: ${EXISTING_REPO}${NC}"
        echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-ecr.sh first${NC}"
        exit 0
    else
        echo -e "${YELLOW}Repository URI in env file but not found in AWS, creating new...${NC}"
    fi
fi

# Create ECR repository
echo -e "${YELLOW}Creating ECR repository...${NC}"
REPOSITORY_URI=$(aws ecr create-repository \
    --repository-name "${REPOSITORY_NAME}" \
    --region "${AWS_REGION}" \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256 \
    --tags Key=Name,Value="${REPOSITORY_NAME}" \
           Key=Environment,Value="${ENVIRONMENT}" \
           Key=Application,Value=StartupWebApp \
           Key=ManagedBy,Value=InfrastructureAsCode \
    --query 'repository.repositoryUri' \
    --output text)

echo -e "${GREEN}✓ ECR repository created: ${REPOSITORY_URI}${NC}"

# Set lifecycle policy (keep last 10 images)
echo -e "${YELLOW}Setting lifecycle policy...${NC}"
cat > /tmp/ecr-lifecycle-policy.json << 'EOF'
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF

aws ecr put-lifecycle-policy \
    --repository-name "${REPOSITORY_NAME}" \
    --region "${AWS_REGION}" \
    --lifecycle-policy-text file:///tmp/ecr-lifecycle-policy.json > /dev/null

rm /tmp/ecr-lifecycle-policy.json
echo -e "${GREEN}✓ Lifecycle policy set (keep last 10 images)${NC}"

# Save to env file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^ECR_REPOSITORY_URI=.*|ECR_REPOSITORY_URI=\"${REPOSITORY_URI}\"|" \
    -e "s|^ECR_REPOSITORY_NAME=.*|ECR_REPOSITORY_NAME=\"${REPOSITORY_NAME}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ECR Repository Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  Repository Name:     ${REPOSITORY_NAME}"
echo -e "  Repository URI:      ${REPOSITORY_URI}"
echo -e "  Region:              ${AWS_REGION}"
echo -e "  Image Scanning:      Enabled (scan on push)"
echo -e "  Encryption:          AES256"
echo -e "  Lifecycle Policy:    Keep last 10 images"
echo ""
echo -e "${GREEN}Cost Estimate:${NC}"
echo -e "  ECR Storage:         ~\$0.10/GB/month"
echo -e "  Typical usage:       ~\$0.10-\$0.20/month (1-2 images)"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Build production image:"
echo -e "     docker build --target production -t ${REPOSITORY_NAME}:latest ."
echo ""
echo -e "  2. Login to ECR:"
echo -e "     aws ecr get-login-password --region ${AWS_REGION} | \\"
echo -e "       docker login --username AWS --password-stdin ${REPOSITORY_URI%/*}"
echo ""
echo -e "  3. Tag image:"
echo -e "     docker tag ${REPOSITORY_NAME}:latest ${REPOSITORY_URI}:latest"
echo ""
echo -e "  4. Push image:"
echo -e "     docker push ${REPOSITORY_URI}:latest"
echo ""
echo -e "${YELLOW}Phase 5.14 Progress:${NC}"
echo -e "  ✓ Step 1: Multi-Stage Dockerfile"
echo -e "  ✓ Step 2: Create AWS ECR Repository"
echo -e "  → Next: Create ECS cluster (./scripts/infra/create-ecs-cluster.sh)"
echo ""
