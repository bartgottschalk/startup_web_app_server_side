#!/bin/bash

##############################################################################
# Create Bastion Host for RDS Access
#
# This script creates:
# - IAM role with SSM permissions for Session Manager access
# - EC2 instance (t3.micro) in public subnet
# - Amazon Linux 2023 with SSM agent pre-installed
# - PostgreSQL client pre-installed via user data
#
# Usage: ./scripts/infra/create-bastion.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# Access via: aws ssm start-session --target <instance-id>
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
PROJECT_NAME="startupwebapp"
ENVIRONMENT="production"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Creating Bastion Host${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if bastion already exists
if [ -n "${BASTION_INSTANCE_ID:-}" ]; then
    echo -e "${YELLOW}Checking if bastion instance exists...${NC}"
    INSTANCE_STATE=$(aws ec2 describe-instances \
        --instance-ids "$BASTION_INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text 2>/dev/null || echo "not-found")

    if [ "$INSTANCE_STATE" != "not-found" ]; then
        echo -e "${YELLOW}Bastion instance already exists: ${BASTION_INSTANCE_ID}${NC}"
        echo -e "${YELLOW}State: ${INSTANCE_STATE}${NC}"

        if [ "$INSTANCE_STATE" == "stopped" ]; then
            echo -e "${YELLOW}Starting stopped instance...${NC}"
            aws ec2 start-instances --instance-ids "$BASTION_INSTANCE_ID"
            echo -e "${GREEN}✓ Instance starting${NC}"
        fi

        echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-bastion.sh first${NC}"
        exit 0
    fi
fi

# Step 1: Create IAM role for SSM access
echo -e "${YELLOW}Step 1: Creating IAM role for SSM access...${NC}"

# Check if role already exists
ROLE_EXISTS=$(aws iam get-role --role-name "${PROJECT_NAME}-bastion-role" 2>/dev/null || echo "not-found")

if [ "$ROLE_EXISTS" == "not-found" ]; then
    # Create trust policy for EC2
    TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
)

    # Create IAM role
    aws iam create-role \
        --role-name "${PROJECT_NAME}-bastion-role" \
        --assume-role-policy-document "$TRUST_POLICY" \
        --description "IAM role for bastion host with SSM access" \
        --tags "Key=Name,Value=${PROJECT_NAME}-bastion-role" \
               "Key=Environment,Value=${ENVIRONMENT}" \
               "Key=Application,Value=StartupWebApp" \
               "Key=ManagedBy,Value=InfrastructureAsCode"

    # Attach AWS managed policy for SSM
    aws iam attach-role-policy \
        --role-name "${PROJECT_NAME}-bastion-role" \
        --policy-arn "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"

    # Create instance profile
    aws iam create-instance-profile \
        --instance-profile-name "${PROJECT_NAME}-bastion-profile"

    # Add role to instance profile
    aws iam add-role-to-instance-profile \
        --instance-profile-name "${PROJECT_NAME}-bastion-profile" \
        --role-name "${PROJECT_NAME}-bastion-role"

    # Wait for instance profile to propagate (AWS eventual consistency)
    echo -e "${YELLOW}Waiting for instance profile to propagate...${NC}"
    sleep 10

    echo -e "${GREEN}✓ IAM role and instance profile created${NC}"
else
    echo -e "${GREEN}✓ IAM role already exists${NC}"
fi

# Step 2: Get latest Amazon Linux 2023 AMI
echo -e "${YELLOW}Step 2: Getting latest Amazon Linux 2023 AMI...${NC}"
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023.*-x86_64" \
              "Name=state,Values=available" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text)
echo -e "${GREEN}✓ Using AMI: ${AMI_ID}${NC}"

# Step 3: Create user data script to install PostgreSQL client
echo -e "${YELLOW}Step 3: Creating user data script...${NC}"
USER_DATA=$(cat <<'EOF'
#!/bin/bash
set -x  # Enable debug logging
exec > >(tee /var/log/user-data.log) 2>&1

echo "Starting user-data script..."

# Ensure SSM agent is installed and running (should be pre-installed on AL2023)
echo "Checking SSM agent..."
if ! systemctl is-active --quiet amazon-ssm-agent; then
    echo "SSM agent not running, attempting to start..."
    systemctl start amazon-ssm-agent
    systemctl enable amazon-ssm-agent
fi

# Wait a moment for SSM agent to initialize
sleep 5

# Verify SSM agent is running
systemctl status amazon-ssm-agent

# Install PostgreSQL client
echo "Installing PostgreSQL client..."
dnf install -y postgresql15

# Install jq for JSON parsing
echo "Installing jq..."
dnf install -y jq

# Create a welcome message
cat > /etc/motd << 'WELCOME'
=====================================
StartupWebApp Bastion Host
=====================================
PostgreSQL client installed.

Connect to RDS:
  psql -h startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com -U postgres -d postgres

Get password from Secrets Manager:
  aws secretsmanager get-secret-value --secret-id rds/startupwebapp/multi-tenant/master --region us-east-1 --query SecretString --output text | jq -r '.password'

=====================================
WELCOME

# Signal completion
echo "Bastion host setup complete" > /tmp/setup-complete.txt
echo "User-data script finished successfully"
EOF
)

# Step 4: Launch EC2 instance
echo -e "${YELLOW}Step 4: Launching bastion host...${NC}"
BASTION_INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type t3.micro \
    --subnet-id "$PUBLIC_SUBNET_1_ID" \
    --security-group-ids "$BASTION_SECURITY_GROUP_ID" \
    --iam-instance-profile "Name=${PROJECT_NAME}-bastion-profile" \
    --associate-public-ip-address \
    --user-data "$USER_DATA" \
    --tag-specifications "ResourceType=instance,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-bastion},
        {Key=Environment,Value=${ENVIRONMENT}},
        {Key=Application,Value=StartupWebApp},
        {Key=ManagedBy,Value=InfrastructureAsCode}
    ]" \
    --metadata-options "HttpTokens=required,HttpPutResponseHopLimit=2" \
    --monitoring "Enabled=false" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo -e "${GREEN}✓ Bastion instance launched: ${BASTION_INSTANCE_ID}${NC}"

# Update environment file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^BASTION_INSTANCE_ID=.*|BASTION_INSTANCE_ID=\"${BASTION_INSTANCE_ID}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

# Wait for instance to be running
echo -e "${YELLOW}Waiting for instance to be running (this takes ~30 seconds)...${NC}"
aws ec2 wait instance-running --instance-ids "$BASTION_INSTANCE_ID"
echo -e "${GREEN}✓ Instance is running${NC}"

# Wait for instance profile association to be fully ready
echo -e "${YELLOW}Waiting for IAM instance profile to be fully associated (30 seconds)...${NC}"
sleep 30
echo -e "${GREEN}✓ Instance profile should be ready${NC}"

# Verify instance profile is attached
ATTACHED_PROFILE=$(aws ec2 describe-instances \
    --instance-ids "$BASTION_INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].IamInstanceProfile.Arn' \
    --output text)
echo -e "${GREEN}✓ Instance profile attached: ${ATTACHED_PROFILE}${NC}"

# Reboot the instance to force credential refresh
echo -e "${YELLOW}Rebooting instance to ensure IAM credentials are properly loaded...${NC}"
aws ec2 reboot-instances --instance-ids "$BASTION_INSTANCE_ID"
sleep 10
aws ec2 wait instance-running --instance-ids "$BASTION_INSTANCE_ID"
echo -e "${GREEN}✓ Instance rebooted and running${NC}"

# Wait for SSM agent to be ready
echo -e "${YELLOW}Waiting for SSM agent to be ready (this takes ~2 minutes)...${NC}"
echo -e "${YELLOW}Checking SSM status every 10 seconds...${NC}"

for i in {1..24}; do
    SSM_STATUS=$(aws ssm describe-instance-information \
        --filters "Key=InstanceIds,Values=$BASTION_INSTANCE_ID" \
        --query 'InstanceInformationList[0].PingStatus' \
        --output text 2>/dev/null || echo "not-ready")

    if [ "$SSM_STATUS" == "Online" ]; then
        echo -e "${GREEN}✓ SSM agent is online${NC}"
        break
    fi

    if [ $i -eq 24 ]; then
        echo -e "${YELLOW}⚠ SSM agent not ready yet, but continuing...${NC}"
        echo -e "${YELLOW}  You may need to wait a few more minutes before connecting${NC}"
    else
        echo -n "."
        sleep 10
    fi
done
echo ""

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Bastion Host Created Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Instance Details:${NC}"
echo -e "  Instance ID:  ${BASTION_INSTANCE_ID}"
echo -e "  Instance Type: t3.micro (~\$0.01/hour = ~\$7/month)"
echo -e "  OS:           Amazon Linux 2023"
echo -e "  PostgreSQL:   Version 15 client installed"
echo ""
echo -e "${GREEN}Connect via AWS Systems Manager Session Manager:${NC}"
echo -e "  aws ssm start-session --target ${BASTION_INSTANCE_ID}"
echo ""
echo -e "${GREEN}Once connected, you can:${NC}"
echo -e "  1. Get RDS password:"
echo -e "     aws secretsmanager get-secret-value \\"
echo -e "       --secret-id rds/startupwebapp/multi-tenant/master \\"
echo -e "       --region us-east-1 --query SecretString --output text | jq -r '.password'"
echo ""
echo -e "  2. Connect to RDS PostgreSQL:"
echo -e "     psql -h startupwebapp-multi-tenant-prod.cqbgoe8omhyh.us-east-1.rds.amazonaws.com \\"
echo -e "          -U postgres -d postgres"
echo ""
echo -e "  3. Run the database creation SQL:"
echo -e "     (Copy and paste from /tmp/create-databases-startupwebapp-multi-tenant-prod.sql)"
echo ""
echo -e "${YELLOW}Cost Management:${NC}"
echo -e "  - Stop when not in use:     aws ec2 stop-instances --instance-ids ${BASTION_INSTANCE_ID}"
echo -e "  - Start when needed:        aws ec2 start-instances --instance-ids ${BASTION_INSTANCE_ID}"
echo -e "  - Terminate permanently:    ./scripts/infra/destroy-bastion.sh"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Connect via SSM: aws ssm start-session --target ${BASTION_INSTANCE_ID}"
echo -e "  2. Create databases using the SQL script"
echo -e "  3. Verify database creation"
echo ""
