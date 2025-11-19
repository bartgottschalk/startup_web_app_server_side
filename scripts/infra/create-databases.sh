#!/bin/bash

##############################################################################
# Create Multi-Tenant Databases on RDS PostgreSQL Instance
#
# This script creates:
# - startupwebapp_prod (main application database)
# - healthtech_experiment (fork database)
# - fintech_experiment (fork database)
# - django_app user with permissions
#
# Usage: ./scripts/infra/create-databases.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# Prerequisites: RDS instance must be created, bastion host or SSH tunnel required
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

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Creating Multi-Tenant Databases${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify RDS endpoint exists
if [ -z "$RDS_ENDPOINT" ]; then
    echo -e "${RED}Error: RDS_ENDPOINT not found${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-rds.sh first${NC}"
    exit 1
fi

# Get database credentials from Secrets Manager
echo -e "${YELLOW}Retrieving database credentials...${NC}"
DB_CREDS=$(aws secretsmanager get-secret-value \
    --secret-id "$DB_SECRET_NAME" \
    --query 'SecretString' \
    --output text)

DB_PASSWORD=$(echo "$DB_CREDS" | jq -r '.password')
DB_USER=$(echo "$DB_CREDS" | jq -r '.username')
echo -e "${GREEN}✓ Credentials retrieved${NC}"

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Database Connection Information${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "  Host: ${RDS_ENDPOINT}"
echo -e "  Port: 5432"
echo -e "  Master User: postgres"
echo ""
echo -e "${YELLOW}Connection options:${NC}"
echo -e "  1. From bastion host in same VPC"
echo -e "  2. Via SSH tunnel: ssh -L 5432:${RDS_ENDPOINT}:5432 user@bastion-host"
echo -e "  3. From AWS Cloud9 environment"
echo ""

# Create SQL script
SQL_SCRIPT="/tmp/create-databases-${RDS_INSTANCE_ID}.sql"
echo -e "${YELLOW}Creating SQL script...${NC}"

cat > "$SQL_SCRIPT" <<EOF
-- Create application user
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';

-- Create databases with proper encoding
CREATE DATABASE startupwebapp_prod
  WITH ENCODING='UTF8'
  LC_COLLATE='en_US.UTF-8'
  LC_CTYPE='en_US.UTF-8'
  OWNER=${DB_USER};

CREATE DATABASE healthtech_experiment
  WITH ENCODING='UTF8'
  LC_COLLATE='en_US.UTF-8'
  LC_CTYPE='en_US.UTF-8'
  OWNER=${DB_USER};

CREATE DATABASE fintech_experiment
  WITH ENCODING='UTF8'
  LC_COLLATE='en_US.UTF-8'
  LC_CTYPE='en_US.UTF-8'
  OWNER=${DB_USER};

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE startupwebapp_prod TO ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE healthtech_experiment TO ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE fintech_experiment TO ${DB_USER};

-- List databases to confirm
\l
EOF

echo -e "${GREEN}✓ SQL script created: ${SQL_SCRIPT}${NC}"
echo ""

# Display script for manual execution
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Manual Execution Required${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "${YELLOW}This script cannot automatically connect to the database.${NC}"
echo -e "${YELLOW}You need to execute the SQL commands manually.${NC}"
echo ""
echo -e "${GREEN}Option 1: Execute via psql (from bastion or via tunnel)${NC}"
echo -e "  psql -h ${RDS_ENDPOINT} -U postgres -d postgres -f ${SQL_SCRIPT}"
echo ""
echo -e "${GREEN}Option 2: Copy and paste SQL commands${NC}"
echo -e "  psql -h ${RDS_ENDPOINT} -U postgres -d postgres"
echo -e "  Then paste the following SQL:"
echo ""
cat "$SQL_SCRIPT"
echo ""
echo -e "${GREEN}Option 3: Use DBeaver or pgAdmin${NC}"
echo -e "  Connection details:"
echo -e "    Host: ${RDS_ENDPOINT}"
echo -e "    Port: 5432"
echo -e "    Database: postgres"
echo -e "    Username: postgres"
echo -e "    Password: [Get from Secrets Manager: ${DB_SECRET_NAME}]"
echo ""
echo -e "${YELLOW}After creating databases, verify with:${NC}"
echo -e "  psql -h ${RDS_ENDPOINT} -U ${DB_USER} -d startupwebapp_prod -c '\\dt'"
echo ""
echo -e "${YELLOW}SQL script saved to: ${SQL_SCRIPT}${NC}"
echo ""
