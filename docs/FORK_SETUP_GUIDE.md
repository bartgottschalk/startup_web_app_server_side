# Fork Setup Guide

**Purpose**: Step-by-step guide for customizing StartupWebApp for your business

---

## Table of Contents

1. [Before You Fork](#1-before-you-fork)
2. [Customize the Code](#2-customize-the-code)
3. [Deploy to AWS](#3-deploy-to-aws)
4. [Configure Your Products](#4-configure-your-products)
5. [Launch Checklist](#5-launch-checklist)

---

## 1. Before You Fork

### Prerequisites

Before forking StartupWebApp for your business, ensure you have:

**Required Accounts:**
- **GitHub Account** - To fork and host your repository
- **AWS Account** - For hosting infrastructure (RDS, ECS, S3, CloudFront)
- **Stripe Account** - For payment processing ([stripe.com](https://stripe.com))
- **Domain Name** - Your business domain (e.g., `yourbusiness.com`)

**Technical Skills:**
- Basic command-line usage (bash, Docker)
- Git fundamentals (clone, commit, push, pull requests)
- Basic understanding of environment variables and secrets management
- Familiarity with Django admin interface (for product management)

**Development Tools:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop) - Required for local development
- [Git](https://git-scm.com/) - Required for version control
- Text editor or IDE (VS Code, PyCharm, etc.)

### Cost Expectations

**AWS Infrastructure (Production):**
- **RDS PostgreSQL 16** (db.t3.micro): ~$15-20/month
- **ECS Fargate** (1 task, 0.5 vCPU, 1GB RAM): ~$15-20/month
- **Application Load Balancer**: ~$16/month + data transfer
- **NAT Gateway**: ~$32/month + data transfer
- **S3 + CloudFront** (frontend hosting): ~$1-5/month (traffic-dependent)
- **CloudWatch Logs/Metrics**: ~$5-10/month
- **Secrets Manager**: ~$1/month (2-3 secrets)
- **Data Transfer**: Variable, typically $5-20/month for low traffic

**Baseline: ~$98-120/month for low-traffic production environment**

**Stripe Fees:**
- 2.9% + $0.30 per successful transaction (US)
- No monthly fees, pay only for successful charges

**Scaling Costs:**
- Higher traffic will increase ECS Fargate tasks, ALB data transfer, CloudFront costs
- Database can scale to db.t3.small (~$30/month), db.t3.medium (~$60/month)
- Auto-scaling can be configured for ECS tasks (see `docs/reference/ecs-cicd-migrations.md`)

### What You're Getting

StartupWebApp is a production-ready e-commerce template with:

**Backend (Django REST API):**
- Django 5.2 LTS + Python 3.12
- PostgreSQL 16 database
- Comprehensive test coverage (818 tests)
- Transaction-protected order creation
- Rate limiting on authentication endpoints
- CSRF protection, password validation, input sanitization

**Frontend (jQuery/React Template):**
- Static files served via Nginx (dev) or CloudFront (production)
- jQuery-based SPA with React components
- Responsive design
- Stripe Checkout integration

**Infrastructure:**
- Docker Compose for local development
- AWS deployment scripts for production
- GitHub Actions CI/CD pipelines
- CloudWatch monitoring and alerting

**Security Hardening:**
- Battle-tested authentication flows
- XSS protection via input escaping
- Transaction atomicity on order creation
- Rate limiting on sensitive endpoints
- Secrets management via AWS Secrets Manager

### Tech Stack Overview

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend Framework** | Django | 5.2 LTS | REST API, admin interface |
| **Backend Language** | Python | 3.12 | Application code |
| **Database** | PostgreSQL | 16 | Primary data store |
| **Frontend** | jQuery + React | 3.x + 18.x | UI/UX |
| **Payment** | Stripe Checkout | Latest API | Payment processing |
| **Email** | Django SMTP | Built-in | Transactional emails |
| **Containerization** | Docker | Latest | Local dev + production |
| **Cloud** | AWS | - | ECS, RDS, S3, CloudFront, ALB |
| **CI/CD** | GitHub Actions | - | Automated deployments |
| **Monitoring** | CloudWatch | - | Logs, metrics, alarms |

**Multi-Tenant Architecture:**
- Single PostgreSQL instance supports multiple databases
- Experimental forks use separate databases (`startupwebapp_dev`, `healthtech_dev`, `fintech_dev`)
- Switch via `DATABASE_NAME` environment variable
- Isolated data, shared infrastructure

---

## 2. Customize the Code

### Fork the Repository

1. **Fork on GitHub:**
   - Navigate to [github.com/bartgottschalk/startup_web_app_server_side](https://github.com/bartgottschalk/startup_web_app_server_side)
   - Click "Fork" in the top-right
   - Choose your GitHub account as the destination
   - Optionally rename to `yourbusiness-backend`

2. **Fork the frontend:**
   - Navigate to [github.com/bartgottschalk/startup_web_app_client_side](https://github.com/bartgottschalk/startup_web_app_client_side)
   - Click "Fork"
   - Optionally rename to `yourbusiness-frontend`

3. **Clone your forks locally:**
   ```bash
   cd ~/Projects
   git clone https://github.com/YOUR_USERNAME/yourbusiness-backend.git
   git clone https://github.com/YOUR_USERNAME/yourbusiness-frontend.git
   cd yourbusiness-backend
   ```

### Update Stripe Keys

**CRITICAL: Switch from TEST to LIVE mode for real business**

1. **Get Stripe LIVE keys:**
   - Log in to [dashboard.stripe.com](https://dashboard.stripe.com)
   - Toggle "Viewing test data" to **LIVE mode**
   - Navigate to Developers → API Keys
   - Copy your **Publishable key** (`pk_live_...`) and **Secret key** (`sk_live_...`)

2. **Update local secrets:**
   ```bash
   # Create settings_secret.py from template
   cp StartupWebApp/StartupWebApp/settings_secret.py.template \
      StartupWebApp/StartupWebApp/settings_secret.py

   # Edit settings_secret.py
   nano StartupWebApp/StartupWebApp/settings_secret.py
   ```

3. **Set your Stripe keys:**
   ```python
   # StartupWebApp/settings_secret.py
   STRIPE_PUBLISHABLE_KEY = 'pk_live_YOUR_PUBLISHABLE_KEY'
   STRIPE_SECRET_KEY = 'sk_live_YOUR_SECRET_KEY'
   ```

4. **Production secrets (AWS Secrets Manager):**
   - These will be updated during deployment (Section 3)
   - Stored in AWS Secrets Manager: `startupwebapp/production`

**Important:** NEVER commit `settings_secret.py` to git (already in `.gitignore`)

### Customize Data Migrations

Data migrations automatically seed your database with reference data. Customize these for YOUR business:

**1. Email Templates (`user/migrations/0002_seed_user_data.py`):**

```python
# Line ~80: Email templates
Email.objects.get_or_create(
    em_cd='welcome-member',
    defaults={
        'subject': 'Welcome to YOUR BUSINESS!',  # Change this
        'from_address': 'contact@yourbusiness.com',  # Change this
        'bcc_address': 'contact@yourbusiness.com',
        'body_text': '''Hi {recipient_first_name},

Welcome to YOUR BUSINESS! We're excited to have you.

[Customize this welcome message for your brand]

Questions? Reply to this email.

Best regards,
YOUR BUSINESS Team
''',  # Customize your message
    }
)
```

**2. Sample Products (`order/migrations/0004_seed_order_data.py`):**

Replace the sample products (Paper Clips, Binder Clips, Rubber Bands) with YOUR products:

```python
# Line ~200: Sample products
product1, created = Product.objects.get_or_create(
    identifier='YOUR-PRODUCT-001',
    defaults={
        'title': 'Your Product Name',
        'title_url': 'your-product-name',
        'headline': 'Short catchy headline',
        'description_part_1': 'Detailed product description...',
        'description_part_2': 'Additional details...',
    }
)

# Create SKU for your product
sku1, created = Sku.objects.get_or_create(
    color='Blue',
    size='Medium',
    description='Blue, Medium size',
    defaults={
        'sku_type': sku_type_product,
        'sku_inventory': inventory_in_stock,
    }
)

# Set price
Skuprice.objects.get_or_create(
    sku=sku1,
    defaults={
        'price': Decimal('29.99'),  # Your price
        'created_date_time': datetime.now(datetime.UTC),
    }
)

# Link product to SKU
Productsku.objects.get_or_create(
    product=product1,
    sku=sku1
)
```

**3. Shipping Methods (`order/migrations/0004_seed_order_data.py`):**

```python
# Line ~150: Shipping methods
Shippingmethod.objects.get_or_create(
    title='Standard Shipping',
    defaults={
        'cost': Decimal('5.99'),  # Your shipping cost
        'description': '5-7 business days',
        'display_order': 1,
    }
)

Shippingmethod.objects.get_or_create(
    title='Express Shipping',
    defaults={
        'cost': Decimal('12.99'),
        'description': '2-3 business days',
        'display_order': 2,
    }
)
```

**4. Terms of Use (`user/migrations/0002_seed_user_data.py`):**

```python
# Line ~50: Terms of Use
Termsofuse.objects.get_or_create(
    defaults={
        'terms_of_use_text': '''
YOUR BUSINESS TERMS OF USE

Last Updated: [Date]

1. Acceptance of Terms
By using yourbusiness.com, you agree to these Terms of Use.

2. Products and Services
[Describe your offerings]

3. Payment Terms
[Your payment terms]

4. Shipping and Returns
[Your policies]

[Continue with standard terms - consult a lawyer!]
''',
        'created_date_time': datetime.now(datetime.UTC),
    }
)
```

### Update Email Templates

Email templates control all transactional emails (order confirmations, account creation, password resets).

**1. Order Confirmation Email:**

Edit `order/migrations/0004_seed_order_data.py` (around line 250):

```python
Email.objects.get_or_create(
    em_cd='order-confirmation-member',
    defaults={
        'subject': 'Your YOUR BUSINESS Order Confirmation',
        'from_address': 'orders@yourbusiness.com',
        'bcc_address': 'orders@yourbusiness.com',
        'body_text': '''Hi {recipient_first_name},

Thank you for your order from YOUR BUSINESS!

{order_information}

{product_information}

{shipping_information}

{discount_information}

{order_total_information}

{payment_information}

{shipping_address_information}

Questions? Reply to this email or visit https://yourbusiness.com/contact

Best regards,
YOUR BUSINESS Team
''',
    }
)
```

**2. Password Reset Email:**

Edit `user/migrations/0002_seed_user_data.py`:

```python
Email.objects.get_or_create(
    em_cd='password-reset',
    defaults={
        'subject': 'YOUR BUSINESS Password Reset',
        'from_address': 'support@yourbusiness.com',
        'body_text': '''Hi {recipient_first_name},

You requested a password reset for your YOUR BUSINESS account.

Click here to reset: https://yourbusiness.com/reset-password?token={reset_token}

This link expires in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
YOUR BUSINESS Team
''',
    }
)
```

### Change Domain Names

Replace `startupwebapp.com` with `yourbusiness.com` throughout the codebase:

**1. Backend settings:**

```bash
# settings.py
ALLOWED_HOSTS = ['api.yourbusiness.com', 'yourbusiness.com']
ENVIRONMENT_DOMAIN = 'https://yourbusiness.com'

# CORS settings (settings_secret.py)
CORS_ORIGIN_WHITELIST = (
    'https://yourbusiness.com',
    'http://localhost:8080',  # Local dev
)

# CSRF settings
CSRF_COOKIE_DOMAIN = '.yourbusiness.com'
```

**2. Frontend configuration:**

Edit `startup_web_app_client_side/js/config.js`:

```javascript
const API_BASE_URL = 'https://api.yourbusiness.com';
const DOMAIN = 'yourbusiness.com';
```

**3. Search and replace:**

```bash
# In backend repository
grep -r "startupwebapp.com" . --exclude-dir=.git

# Replace in all files (review carefully!)
find . -type f -not -path "./.git/*" \
  -exec sed -i 's/startupwebapp\.com/yourbusiness.com/g' {} \;
```

### Update Privacy Policy & Terms

**1. Create legal documents:**

Consult a lawyer to draft:
- Terms of Use / Terms of Service
- Privacy Policy
- Return/Refund Policy
- Shipping Policy

**2. Add to frontend:**

```bash
cd ../yourbusiness-frontend
# Create new pages
cp privacy privacy.yourbusiness
# Edit content in your editor
```

**3. Update database:**

Terms of Use is stored in the database (created via migration above). Update via Django admin after deployment.

### Customize Product Images

**1. Prepare product images:**
- High-resolution product photos (1000x1000px minimum)
- Multiple angles if applicable
- Transparent backgrounds for product shots (optional)

**2. Upload to S3:**

During deployment, you'll create an S3 bucket for images:

```bash
aws s3 cp product-image.jpg s3://yourbusiness-product-images/products/your-product-001.jpg
```

**3. Update image URLs in data migrations:**

```python
# order/migrations/0004_seed_order_data.py
Productimage.objects.get_or_create(
    product=product1,
    image_url='https://img.yourbusiness.com/products/your-product-001.jpg',
    defaults={
        'main_image': True,
        'caption': 'Your Product - Front View',
    }
)
```

**Note:** Set up CloudFront distribution for `img.yourbusiness.com` (see Section 3).

### Configure Email Sending

**Option 1: Gmail (Development/Low Volume)**

1. Create Gmail App Password:
   - Go to Google Account settings → Security → 2-Step Verification → App passwords
   - Generate password for "Mail"

2. Update settings:
   ```python
   # settings_secret.py
   EMAIL_HOST_USER = 'your-gmail@gmail.com'
   EMAIL_HOST_PASSWORD = 'your-app-password'
   ```

**Option 2: AWS SES (Production - Recommended)**

1. Verify your domain in SES:
   ```bash
   aws ses verify-domain-identity --domain yourbusiness.com
   ```

2. Add DNS records (provided by AWS)

3. Request production access (if not in sandbox)

4. Update settings:
   ```python
   # settings_secret.py
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = 'YOUR_SES_SMTP_USERNAME'
   EMAIL_HOST_PASSWORD = 'YOUR_SES_SMTP_PASSWORD'
   ```

**Option 3: SendGrid (Alternative)**

Similar to SES but with SendGrid SMTP credentials.

---

## 3. Deploy to AWS

### Prerequisites

1. **AWS CLI installed and configured:**
   ```bash
   aws --version
   aws configure
   # Enter your Access Key ID, Secret Access Key, region (us-east-1)
   ```

2. **Environment variables file:**
   ```bash
   cd scripts/infra
   cp aws-resources.env.template aws-resources.env
   ```

3. **Edit `aws-resources.env`:**
   ```bash
   nano aws-resources.env
   ```

   Update values:
   ```bash
   PROJECT_NAME="yourbusiness"
   AWS_REGION="us-east-1"
   ENVIRONMENT="production"
   DOMAIN_NAME="yourbusiness.com"
   API_DOMAIN="api.yourbusiness.com"
   ```

### Infrastructure Deployment

**Execute scripts in order** (each script is idempotent - safe to run multiple times):

**1. Create VPC and Networking:**
```bash
./create-vpc.sh
# Creates: VPC, subnets (public/private), route tables, internet gateway
```

**2. Create Security Groups:**
```bash
./create-security-groups.sh
# Creates: ALB security group, ECS security group, RDS security group
```

**3. Create NAT Gateway:**
```bash
./create-nat-gateway.sh
# Allows private subnets to access internet (for Docker image pulls, etc.)
```

**4. Create RDS PostgreSQL:**
```bash
./create-rds.sh
# Creates: PostgreSQL 16 instance (db.t3.micro, Multi-AZ optional)
```

**5. Create Secrets in AWS Secrets Manager:**
```bash
./create-secrets.sh
# Prompts for: Database password, Django secret key, Stripe keys, email credentials
```

**6. Create Application Load Balancer:**
```bash
./create-alb.sh
# Creates: ALB, target group, HTTP listener (port 80)
```

**7. Create ACM Certificate for HTTPS:**
```bash
./create-acm-certificate.sh
# Creates: SSL certificate for api.yourbusiness.com
# ACTION REQUIRED: Add DNS validation records to your domain registrar
```

**8. Create HTTPS Listener:**
```bash
./create-alb-https-listener.sh
# Adds: HTTPS listener (port 443) to ALB, redirects HTTP → HTTPS
```

**9. Create ECS Cluster:**
```bash
./create-ecs-cluster.sh
# Creates: ECS Fargate cluster
```

**10. Create ECR Repository:**
```bash
./create-ecr.sh
# Creates: Docker image repository for backend
```

**11. Build and Push Docker Image:**
```bash
# From backend repository root
docker build -t yourbusiness-backend .

# Tag for ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker tag yourbusiness-backend:latest \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/yourbusiness-backend:latest

docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/yourbusiness-backend:latest
```

**12. Create ECS Task Definition:**
```bash
./create-ecs-task-definition.sh
# Creates: Task definition with environment variables from Secrets Manager
```

**13. Create ECS Service:**
```bash
./create-ecs-service.sh
# Creates: ECS service, runs tasks, registers with ALB
```

**14. Create Auto-Scaling:**
```bash
./create-ecs-autoscaling.sh
# Creates: Auto-scaling policies for ECS tasks (CPU/Memory based)
```

**15. Deploy Frontend to S3 + CloudFront:**
```bash
./create-frontend-hosting.sh
# Creates: S3 bucket, CloudFront distribution for yourbusiness.com
# Uploads static files from frontend repository
```

**16. Create Monitoring:**
```bash
./create-monitoring.sh
# Creates: CloudWatch dashboards, log groups, alarms (5xx errors, CPU, memory)
```

**17. Create Email Failure Monitoring:**
```bash
./create-order-email-failures-sns-topic.sh
# Creates: SNS topic for order email failure alerts

./create-order-email-failure-alarm.sh
# Creates: CloudWatch alarm that triggers when order emails fail
```

### Configure GitHub Secrets for CI/CD

1. **Navigate to your repository:**
   - Go to Settings → Secrets and variables → Actions

2. **Add secrets:**
   ```
   AWS_ACCESS_KEY_ID=<your-access-key>
   AWS_SECRET_ACCESS_KEY=<your-secret-key>
   AWS_REGION=us-east-1
   ECR_REPOSITORY=yourbusiness-backend
   ECS_CLUSTER=yourbusiness-cluster
   ECS_SERVICE=yourbusiness-service
   ECS_TASK_DEFINITION=yourbusiness-task
   ```

3. **GitHub Actions workflows:**
   - `.github/workflows/deploy.yml` - Auto-deploys on merge to `master`
   - `.github/workflows/test.yml` - Runs tests on pull requests

### Run Database Migrations

**Connect to bastion host:**
```bash
./create-bastion.sh  # If not already created
ssh -i ~/.ssh/yourbusiness-bastion.pem ec2-user@BASTION_IP
```

**SSH to ECS task (or use ECS Exec):**
```bash
# From bastion, SSH to ECS task private IP
ssh -i ~/.ssh/key.pem ubuntu@TASK_PRIVATE_IP

# Or use ECS Exec (easier)
aws ecs execute-command \
  --cluster yourbusiness-cluster \
  --task TASK_ID \
  --container yourbusiness-backend \
  --interactive \
  --command "/bin/bash"
```

**Run migrations:**
```bash
python manage.py migrate
# This creates tables AND seeds all reference data via data migrations
```

**Create superuser:**
```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@yourbusiness.com
# Password: <secure-password>
```

### Update DNS Records

**Point your domain to AWS:**

1. **API subdomain (ALB):**
   ```
   Type: CNAME
   Name: api.yourbusiness.com
   Value: yourbusiness-alb-123456789.us-east-1.elb.amazonaws.com
   ```

2. **Main domain (CloudFront):**
   ```
   Type: CNAME
   Name: yourbusiness.com (or @)
   Value: d1234567890abc.cloudfront.net
   ```

3. **Wait for propagation:**
   ```bash
   dig api.yourbusiness.com
   dig yourbusiness.com
   ```

---

## 4. Configure Your Products

### Access Django Admin

1. **Navigate to admin:**
   ```
   https://api.yourbusiness.com/admin/
   ```

2. **Login with superuser credentials** (created in Section 3)

### Add Products

**1. Create Product:**
- Navigate to **Home → Order → Products**
- Click **Add Product**
- Fill in:
  - Title: "Your Product Name"
  - Title URL: "your-product-name" (URL slug)
  - Identifier: Generate 10-character code at [random.org](https://www.random.org/strings/?num=1&len=10&digits=on&upperalpha=on&loweralpha=on&unique=on&format=html&rnd=new)
  - Headline: "Catchy one-liner"
  - Description Part 1: Main product description
  - Description Part 2: Additional details (optional)
- Save

**2. Add Product Image:**
- Navigate to **Home → Order → Product Images**
- Click **Add Product Image**
- Select your product
- Image URL: `https://img.yourbusiness.com/products/your-image.jpg`
- Main Image: ✓ (check for primary image)
- Caption: "Product name - front view"
- Save

**3. Create SKU:**
- Navigate to **Home → Order → Skus**
- Click **Add Sku**
- Fill in:
  - SKU Type: "Product"
  - SKU Inventory: "In Stock"
  - Color: "Blue" (if applicable)
  - Size: "Medium" (if applicable)
  - Description: "Blue, Medium"
- Save

**4. Set SKU Price:**
- Navigate to **Home → Order → SKU Prices**
- Click **Add SKU Price**
- Select your SKU
- Price: 29.99
- Created Date Time: (auto-filled with current time)
- Save

**5. Link Product to SKU:**
- Navigate to **Home → Order → Product SKUs**
- Click **Add Product SKU**
- Select your product
- Select your SKU
- Save

**6. Add SKU Image (optional):**
- Navigate to **Home → Order → SKU Images**
- Similar to Product Images, but for specific SKU variants

### Configure Shipping Methods

**Navigate to Home → Order → Shipping Methods:**

**Standard Shipping:**
- Title: "Standard Shipping"
- Cost: 5.99
- Description: "5-7 business days"
- Display Order: 1

**Express Shipping:**
- Title: "Express Shipping"
- Cost: 12.99
- Description: "2-3 business days"
- Display Order: 2

### Create Discount Codes

**Navigate to Home → Order → Discount Codes:**

**Example: WELCOME10**
- Code: WELCOME10
- Description: "10% off your first order"
- Start Date Time: (today)
- End Date Time: (1 year from now)
- Combinable: False
- Discount Amount: 10 (percentage)
- Discount Type: "Percent Off"
- Order Minimum: 0.00

**Example: FREESHIP**
- Code: FREESHIP
- Description: "Free standard shipping"
- Discount Amount: 5.99
- Discount Type: "Dollar Amount Off"
- Order Minimum: 25.00

### Test Checkout Flow

1. **Add product to cart:**
   - Navigate to https://yourbusiness.com/products
   - Click "Add to Cart"

2. **View cart:**
   - Click cart icon
   - Verify product, price, quantity

3. **Apply discount code:**
   - Enter WELCOME10
   - Verify discount applied

4. **Checkout:**
   - Click "Checkout"
   - Redirects to Stripe Checkout
   - Use Stripe test card: 4242 4242 4242 4242, any future expiry, any CVC

5. **Verify order confirmation:**
   - Check email for order confirmation
   - Verify order appears in Django admin (Home → Order → Orders)

---

## 5. Launch Checklist

### Pre-Launch Testing

- [ ] **Test complete checkout flow** (anonymous + signed-in)
  - [ ] Add product to cart
  - [ ] Apply discount code
  - [ ] Complete Stripe checkout
  - [ ] Verify order confirmation email received
  - [ ] Verify order appears in Django admin
- [ ] **Test account creation**
  - [ ] Create new account
  - [ ] Verify welcome email received
  - [ ] Verify email verification link works
- [ ] **Test password reset**
  - [ ] Request password reset
  - [ ] Verify reset email received
  - [ ] Reset password successfully
- [ ] **Test email unsubscribe**
  - [ ] Click unsubscribe link in email
  - [ ] Verify unsubscribed status in admin
- [ ] **Load test critical flows**
  - [ ] 100 concurrent users (use tools like Apache Bench, Locust)
  - [ ] Verify no 5xx errors
  - [ ] Verify ECS auto-scaling works

### Switch Stripe to LIVE Mode

**CRITICAL: Do this LAST, only when ready for real transactions**

1. **Update AWS Secrets Manager:**
   ```bash
   aws secretsmanager update-secret \
     --secret-id startupwebapp/production \
     --secret-string '{
       "stripe_publishable_key": "pk_live_YOUR_KEY",
       "stripe_secret_key": "sk_live_YOUR_KEY",
       "database_password": "...",
       "django_secret_key": "...",
       "email_host_password": "..."
     }'
   ```

2. **Restart ECS tasks:**
   ```bash
   aws ecs update-service \
     --cluster yourbusiness-cluster \
     --service yourbusiness-service \
     --force-new-deployment
   ```

3. **Verify LIVE mode:**
   - Complete test checkout with REAL credit card
   - Check Stripe dashboard → Payments (should show in LIVE mode)
   - **IMPORTANT:** Refund test transaction immediately

### Configure Production Email

- [ ] **AWS SES setup:**
  - [ ] Verify domain in SES
  - [ ] Add SPF/DKIM DNS records
  - [ ] Request production access (move out of sandbox)
  - [ ] Update secrets with SES SMTP credentials
- [ ] **Test email delivery:**
  - [ ] Send test order confirmation
  - [ ] Send test password reset
  - [ ] Check spam folders
  - [ ] Verify SPF/DKIM pass (check email headers)

### Set Up Monitoring & Alerts

- [ ] **CloudWatch Alarms:**
  - [ ] ALB 5xx errors > 10 in 5 minutes → Email/SMS
  - [ ] ECS CPU > 80% for 5 minutes → Email
  - [ ] RDS storage < 20% free → Email
  - [ ] Order email failures > 0 in 5 minutes → Email
- [ ] **Subscribe to SNS topics:**
  ```bash
  aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:ACCOUNT:yourbusiness-alerts \
    --protocol email \
    --notification-endpoint alerts@yourbusiness.com
  ```
- [ ] **Test alerts:**
  - [ ] Manually trigger alarm
  - [ ] Verify email/SMS received

### Security Audit

- [ ] **SSL Certificate:**
  - [ ] Verify HTTPS working on api.yourbusiness.com
  - [ ] Verify HTTPS working on yourbusiness.com
  - [ ] Check certificate validity at [ssllabs.com](https://www.ssllabs.com/ssltest/)
- [ ] **Security Headers:**
  - [ ] HSTS enabled
  - [ ] X-Frame-Options: DENY
  - [ ] X-Content-Type-Options: nosniff
- [ ] **Secrets Management:**
  - [ ] No secrets in git history
  - [ ] All secrets in AWS Secrets Manager
  - [ ] IAM roles use least privilege
- [ ] **Rate Limiting:**
  - [ ] Test login rate limit (10/hour per IP)
  - [ ] Test account creation limit (5/hour per IP)
  - [ ] Test password reset limit (5/hour per username)

### GDPR Compliance

- [ ] **Privacy Policy:**
  - [ ] Posted on website
  - [ ] Covers data collection, storage, usage
  - [ ] Explains cookies
  - [ ] Provides contact email for data requests
- [ ] **Cookie Consent:**
  - [ ] Cookie banner on homepage
  - [ ] Accept/Decline options
  - [ ] Non-essential cookies blocked until consent
- [ ] **Data Export:**
  - [ ] Implement user data export endpoint
  - [ ] Test export functionality
- [ ] **Data Deletion:**
  - [ ] Implement account deletion
  - [ ] Cascade deletes for user data
  - [ ] Retain order records (legal requirement)

### Configure Custom Domain (CloudFront)

- [ ] **Alternate Domain Names:**
  - [ ] Add yourbusiness.com to CloudFront distribution
  - [ ] Add www.yourbusiness.com (optional)
- [ ] **ACM Certificate:**
  - [ ] Request certificate in us-east-1 for CloudFront
  - [ ] Validate via DNS
  - [ ] Attach to CloudFront distribution
- [ ] **Update DNS:**
  - [ ] Point yourbusiness.com → CloudFront distribution
  - [ ] Wait for propagation

### Final Checks

- [ ] **Run all tests:**
  ```bash
  docker-compose exec backend python manage.py test --parallel=4
  ```
- [ ] **Zero linting errors:**
  ```bash
  docker-compose exec backend flake8 --max-line-length=120
  ```
- [ ] **Database backups:**
  - [ ] Verify RDS automated backups enabled (7 days retention)
  - [ ] Test manual snapshot creation
  - [ ] Document restore procedure
- [ ] **Incident response plan:**
  - [ ] Document rollback procedure
  - [ ] Document database restore procedure
  - [ ] Contact list for emergencies
- [ ] **Legal review:**
  - [ ] Terms of Use approved by lawyer
  - [ ] Privacy Policy approved by lawyer
  - [ ] Return/Refund policy compliant with local laws

### Go Live! 🚀

- [ ] **Announce launch:**
  - [ ] Social media posts
  - [ ] Email existing prospects (if any)
  - [ ] Press release (optional)
- [ ] **Monitor for 48 hours:**
  - [ ] Watch CloudWatch logs for errors
  - [ ] Monitor Stripe dashboard for transactions
  - [ ] Check email delivery rates
  - [ ] Review customer support emails
- [ ] **Celebrate! 🎉**

---

## Troubleshooting

### Common Issues

**"CSRF verification failed"**
- Ensure `CSRF_COOKIE_DOMAIN` matches your domain
- Verify frontend and backend share same parent domain
- Check browser cookies are enabled

**"No order confirmation email received"**
- Check CloudWatch logs for `[ORDER_EMAIL_FAILURE]`
- Verify email credentials in Secrets Manager
- Check spam folder
- Test SMTP connection manually

**"Stripe checkout fails"**
- Verify Stripe keys are LIVE mode (not test)
- Check Stripe webhook is configured
- Review Stripe dashboard → Developers → Webhooks → Events

**"ECS tasks keep restarting"**
- Check CloudWatch logs for errors
- Verify Secrets Manager secrets are correct
- Ensure RDS security group allows ECS task connections

**"Database connection refused"**
- Verify RDS is in same VPC as ECS tasks
- Check security group rules
- Test connection from bastion host

---

## Next Steps

After launch:

1. **Monitor metrics** - Watch CloudWatch dashboards for anomalies
2. **Gather feedback** - Survey customers, iterate on UX
3. **Scale infrastructure** - Upgrade RDS/ECS as traffic grows
4. **Add features** - Refer to `docs/PROJECT_ROADMAP_2026.md` for ideas
5. **Stay updated** - Pull upstream changes from StartupWebApp for security fixes

---

## Support

- **StartupWebApp Issues**: [github.com/bartgottschalk/startup_web_app_server_side/issues](https://github.com/bartgottschalk/startup_web_app_server_side/issues)
- **AWS Documentation**: [docs.aws.amazon.com](https://docs.aws.amazon.com)
- **Stripe Documentation**: [stripe.com/docs](https://stripe.com/docs)
- **Django Documentation**: [docs.djangoproject.com](https://docs.djangoproject.com)

**Good luck with your launch!** 🚀
