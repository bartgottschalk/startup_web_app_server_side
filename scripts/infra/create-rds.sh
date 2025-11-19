#!/bin/bash

##############################################################################
# Create AWS RDS PostgreSQL Instance for StartupWebApp
#
# This script creates:
# - RDS PostgreSQL 16.x instance (db.t4g.small)
# - Multi-tenant ready (supports multiple databases)
# - Automated backups (7-day retention)
# - Enhanced monitoring
# - Performance Insights
#
# Usage: ./scripts/infra/create-rds.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# Prerequisites: VPC, Security Groups, and Secrets must be created first
# Estimated time: 10-15 minutes (AWS provisioning time)
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
PROJECT_NAME="startupwebapp"
ENVIRONMENT="production"

# RDS Configuration
DB_INSTANCE_CLASS="db.t4g.small"
DB_ENGINE="postgres"
DB_ENGINE_VERSION="16"  # Will use latest 16.x
DB_STORAGE=20  # GB
DB_MAX_STORAGE=100  # GB (auto-scaling limit)
DB_BACKUP_RETENTION=7  # days

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Creating RDS PostgreSQL Instance${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if [ -z "$DB_SUBNET_GROUP_NAME" ]; then
    echo -e "${RED}Error: DB_SUBNET_GROUP_NAME not found${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-vpc.sh first${NC}"
    exit 1
fi

if [ -z "$RDS_SECURITY_GROUP_ID" ]; then
    echo -e "${RED}Error: RDS_SECURITY_GROUP_ID not found${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-security-groups.sh first${NC}"
    exit 1
fi

if [ -z "$DB_SECRET_ARN" ]; then
    echo -e "${RED}Error: DB_SECRET_ARN not found${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-secrets.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Check if RDS instance already exists
RDS_EXISTS=$(aws rds describe-db-instances \
    --db-instance-identifier "$RDS_INSTANCE_ID" \
    --query 'DBInstances[0].DBInstanceIdentifier' \
    --output text 2>/dev/null || echo "None")

if [ "$RDS_EXISTS" != "None" ]; then
    echo -e "${YELLOW}RDS instance already exists: ${RDS_INSTANCE_ID}${NC}"
    echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-rds.sh first${NC}"
    exit 0
fi

# Get database password from Secrets Manager
echo -e "${YELLOW}Retrieving database password from Secrets Manager...${NC}"
DB_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id "$DB_SECRET_NAME" \
    --query 'SecretString' \
    --output text | jq -r '.password')
echo -e "${GREEN}✓ Password retrieved${NC}"

# Create RDS instance
echo -e "${YELLOW}Creating RDS PostgreSQL instance...${NC}"
echo -e "${YELLOW}Instance ID: ${RDS_INSTANCE_ID}${NC}"
echo -e "${YELLOW}Instance Class: ${DB_INSTANCE_CLASS}${NC}"
echo -e "${YELLOW}Engine: PostgreSQL ${DB_ENGINE_VERSION}.x${NC}"
echo -e "${YELLOW}Storage: ${DB_STORAGE} GB (auto-scaling to ${DB_MAX_STORAGE} GB)${NC}"
echo ""
echo -e "${YELLOW}This will take 10-15 minutes...${NC}"
echo ""

aws rds create-db-instance \
    --db-instance-identifier "$RDS_INSTANCE_ID" \
    --db-instance-class "$DB_INSTANCE_CLASS" \
    --engine "$DB_ENGINE" \
    --engine-version "$DB_ENGINE_VERSION" \
    --master-username "postgres" \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage "$DB_STORAGE" \
    --storage-type "gp3" \
    --max-allocated-storage "$DB_MAX_STORAGE" \
    --vpc-security-group-ids "$RDS_SECURITY_GROUP_ID" \
    --db-subnet-group-name "$DB_SUBNET_GROUP_NAME" \
    --backup-retention-period "$DB_BACKUP_RETENTION" \
    --preferred-backup-window "03:00-04:00" \
    --preferred-maintenance-window "sun:04:00-sun:05:00" \
    --enable-cloudwatch-logs-exports "postgresql" \
    --monitoring-interval 60 \
    --enable-performance-insights \
    --performance-insights-retention-period 7 \
    --no-publicly-accessible \
    --auto-minor-version-upgrade \
    --deletion-protection \
    --tags "Key=Name,Value=${RDS_INSTANCE_ID}" \
           "Key=Environment,Value=${ENVIRONMENT}" \
           "Key=Application,Value=StartupWebApp" \
           "Key=ManagedBy,Value=InfrastructureAsCode" \
    > /dev/null

echo -e "${GREEN}✓ RDS instance creation initiated${NC}"
echo ""

# Wait for RDS instance to become available
echo -e "${YELLOW}Waiting for RDS instance to become available (10-15 minutes)...${NC}"
echo -e "${YELLOW}You can monitor progress in the AWS Console:${NC}"
echo -e "${YELLOW}https://console.aws.amazon.com/rds/home?region=${AWS_REGION}#database:id=${RDS_INSTANCE_ID}${NC}"
echo ""

aws rds wait db-instance-available --db-instance-identifier "$RDS_INSTANCE_ID"

echo -e "${GREEN}✓ RDS instance is available!${NC}"
echo ""

# Get RDS endpoint
echo -e "${YELLOW}Getting RDS endpoint...${NC}"
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier "$RDS_INSTANCE_ID" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)
echo -e "${GREEN}✓ RDS Endpoint: ${RDS_ENDPOINT}${NC}"

# Update Secrets Manager with actual RDS endpoint
echo -e "${YELLOW}Updating Secrets Manager with RDS endpoint...${NC}"
aws secretsmanager update-secret \
    --secret-id "$DB_SECRET_NAME" \
    --secret-string "{
        \"engine\": \"postgresql\",
        \"host\": \"${RDS_ENDPOINT}\",
        \"port\": 5432,
        \"username\": \"django_app\",
        \"password\": \"${DB_PASSWORD}\",
        \"dbClusterIdentifier\": \"${RDS_INSTANCE_ID}\"
    }" > /dev/null
echo -e "${GREEN}✓ Secrets Manager updated${NC}"

# Update environment file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^RDS_ENDPOINT=.*|RDS_ENDPOINT=\"${RDS_ENDPOINT}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RDS Instance Created Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  Instance ID:        ${RDS_INSTANCE_ID}"
echo -e "  Endpoint:           ${RDS_ENDPOINT}"
echo -e "  Port:               5432"
echo -e "  Engine:             PostgreSQL ${DB_ENGINE_VERSION}.x"
echo -e "  Instance Class:     ${DB_INSTANCE_CLASS}"
echo -e "  Storage:            ${DB_STORAGE} GB (auto-scaling to ${DB_MAX_STORAGE} GB)"
echo -e "  Backup Retention:   ${DB_BACKUP_RETENTION} days"
echo -e "  Master Username:    postgres"
echo -e "  Master Password:    [Stored in Secrets Manager]"
echo ""
echo -e "${GREEN}Security:${NC}"
echo -e "  - Private subnets only (no public access)"
echo -e "  - Security Group: ${RDS_SECURITY_GROUP_ID}"
echo -e "  - Deletion protection: Enabled"
echo -e "  - SSL/TLS: Required"
echo ""
echo -e "${GREEN}Monitoring:${NC}"
echo -e "  - Enhanced monitoring: 60-second intervals"
echo -e "  - Performance Insights: 7-day retention"
echo -e "  - CloudWatch Logs: PostgreSQL logs exported"
echo ""
echo -e "${GREEN}Connection Information:${NC}"
echo -e "  Secret Name: ${DB_SECRET_NAME}"
echo -e "  Secret ARN:  ${DB_SECRET_ARN}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Run: ./scripts/infra/create-databases.sh"
echo -e "     (Creates multi-tenant databases: startupwebapp_prod, healthtech_experiment, fintech_experiment)"
echo -e "  2. Run: ./scripts/infra/create-monitoring.sh"
echo -e "     (Sets up CloudWatch alarms and SNS notifications)"
echo -e "  3. Test database connectivity from bastion host"
echo ""
