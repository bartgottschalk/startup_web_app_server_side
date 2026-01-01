# System Architecture

**Purpose**: High-level overview of how StartupWebApp components fit together

---

## Table of Contents

1. [System Components](#1-system-components)
2. [Data Models](#2-data-models)
3. [Key Flows](#3-key-flows)
4. [Security Features](#4-security-features)
5. [Multi-Tenant Architecture](#5-multi-tenant-architecture)

---

## 1. System Components

### Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRODUCTION AWS                          │
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │              │         │              │                     │
│  │  CloudFront  │────────▶│      S3      │                     │
│  │ Distribution │         │  (Frontend)  │                     │
│  │              │         │              │                     │
│  └──────────────┘         └──────────────┘                     │
│         │                                                       │
│         │ Static Files                                         │
│         │ (HTML/CSS/JS)                                        │
│         ▼                                                       │
│  ┌──────────────┐                                              │
│  │    User's    │                                              │
│  │   Browser    │                                              │
│  └──────────────┘                                              │
│         │                                                       │
│         │ AJAX Requests                                        │
│         ▼                                                       │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │              │         │              │                     │
│  │  Route 53    │────────▶│     ALB      │                     │
│  │     DNS      │         │ (HTTPS:443)  │                     │
│  │              │         │              │                     │
│  └──────────────┘         └──────────────┘                     │
│                                  │                              │
│                                  │ Forward                      │
│                                  ▼                              │
│                      ┌──────────────────┐                      │
│                      │   ECS Fargate    │                      │
│                      │  Django Backend  │                      │
│                      │  (Python 3.12)   │                      │
│                      └──────────────────┘                      │
│                          │           │                          │
│                          │           │                          │
│                ┌─────────┘           └─────────┐               │
│                │                                 │               │
│                ▼                                 ▼               │
│      ┌──────────────────┐             ┌──────────────────┐     │
│      │ RDS PostgreSQL   │             │ Secrets Manager  │     │
│      │   (Database)     │             │ (Stripe, Email)  │     │
│      └──────────────────┘             └──────────────────┘     │
│                                                                 │
│                          ┌──────────────────┐                  │
│                          │   CloudWatch     │                  │
│                          │ Logs + Alarms    │                  │
│                          └──────────────────┘                  │
│                                  │                              │
│                                  ▼                              │
│                          ┌──────────────────┐                  │
│                          │   SNS Topics     │                  │
│                          │ (Email Alerts)   │                  │
│                          └──────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘

                                 │
                                 │ Webhooks
                                 ▼
                      ┌──────────────────┐
                      │  Stripe Checkout │
                      │  (External API)  │
                      └──────────────────┘
```

### Component Details

#### **Frontend: jQuery/React on S3 + CloudFront**

**Technology:**
- Static files: HTML, CSS, JavaScript
- jQuery 3.x for DOM manipulation and AJAX
- React 18.x components for interactive features
- Served via Nginx (local dev) or CloudFront (production)

**Local Development:**
- Nginx container serves static files on `http://localhost.startupwebapp.com:8080`
- Custom domain required for CSRF cookie sharing with backend

**Production:**
- S3 bucket stores static files
- CloudFront distribution provides:
  - Global CDN with edge caching
  - HTTPS via ACM certificate
  - Custom domain support (e.g., `yourbusiness.com`)
  - Gzip compression
  - Directory index function (CloudFront Functions)

**Key Files:**
- `/js/utilities/utilities-0.0.1.js` - Core AJAX, CSRF token management
- `/js/index-0.0.2.js` - Homepage, product listings
- `/js/product-0.0.1.js` - Product detail pages
- `/js/checkout/*.js` - Cart, checkout, confirmation flows
- `/js/account*.js` - User account management

#### **Backend API: Django REST on ECS Fargate**

**Technology:**
- Django 5.2 LTS (Python web framework)
- Python 3.12
- Django REST framework patterns (JSON responses)
- Gunicorn WSGI server (production)
- Built-in development server (local)

**Local Development:**
- Docker container runs Django on `http://localapi.startupwebapp.com:8000`
- Hot reload enabled via `python manage.py runserver`

**Production (ECS Fargate):**
- Docker image built via GitHub Actions CI/CD
- Pushed to ECR (Elastic Container Registry)
- ECS tasks run Gunicorn with 4 workers
- Auto-scaling based on CPU/Memory (min: 1, max: 4)
- Health checks via ALB on `/user/logged-in` endpoint
- Environment variables from Secrets Manager

**Key Apps:**
- `user` - Authentication, account management, email campaigns
- `order` - Products, cart, checkout, order management
- `clientevent` - Frontend event logging for analytics

**API Endpoints:**
- `/user/login` - User authentication
- `/user/create-account` - Account creation
- `/user/logged-in` - Check login status
- `/order/cart-contents` - Retrieve cart
- `/order/add-item-to-cart` - Add product to cart
- `/order/create-checkout-session` - Initiate Stripe checkout
- `/order/checkout-session-success` - Handle checkout completion
- `/order/stripe-webhook` - Process Stripe events

#### **Database: PostgreSQL 16 on RDS**

**Configuration:**
- PostgreSQL 16.x (latest stable)
- Instance type: db.t3.micro (production baseline)
- Storage: 20GB gp3 SSD, auto-scaling up to 100GB
- Multi-AZ: Optional (recommended for production)
- Automated backups: 7-day retention
- Connection pooling: `CONN_MAX_AGE=600` (10 minutes)

**Multi-Tenant Design:**
- Single PostgreSQL instance
- Multiple databases: `startupwebapp_dev`, `healthtech_dev`, `fintech_dev`
- Switched via `DATABASE_NAME` environment variable
- Isolated data, shared infrastructure cost savings

**Security:**
- Private subnets only (no public access)
- Security group restricts access to ECS tasks + bastion host
- Credentials stored in AWS Secrets Manager
- TLS encryption in transit

**Connection Details:**
- Host: `startupwebapp-db.xxxxx.us-east-1.rds.amazonaws.com`
- Port: 5432
- Database: `startupwebapp_dev` (configurable)
- User: `django_app`
- Password: Stored in Secrets Manager

#### **Payment Processing: Stripe Checkout Sessions**

**Integration Pattern:**
- **Frontend**: Redirects to Stripe-hosted checkout page
- **Backend**: Creates Stripe Checkout Session via API
- **Stripe**: Processes payment, calls webhook on completion

**Webhook Handling:**
- Stripe sends `checkout.session.completed` event to `/order/stripe-webhook`
- Django verifies webhook signature (security)
- Creates order atomically (transaction-protected)
- Sends order confirmation email
- Deletes cart

**Idempotency:**
- Checks for existing order via `payment_intent_id`
- Returns existing order if duplicate webhook received
- Prevents duplicate orders from webhook retries

**Test vs Live Mode:**
- Demo project uses TEST mode keys (`pk_test_...`, `sk_test_...`)
- Forks should use LIVE mode keys (`pk_live_...`, `sk_live_...`)
- Keys stored in AWS Secrets Manager

#### **Email: Django Templates + SMTP**

**Email Types:**
- Transactional: Order confirmations, password resets, email verification
- Marketing: Email campaigns to Members/Prospects (bulk send)

**Templates:**
- Stored in `user_email` database table
- Support variable substitution: `{recipient_first_name}`, `{order_identifier}`
- Text-only (HTML option available via `body_html` field)

**Sending Options:**

**Local Dev: Gmail SMTP**
- `EMAIL_HOST = 'smtp.gmail.com'`
- `EMAIL_PORT = 587` (TLS)
- Requires Gmail App Password (2FA)

**Production: AWS SES (Recommended)**
- `EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'`
- Domain verification required
- SPF/DKIM DNS records for deliverability
- Request production access (move out of sandbox)

**Alternative: SendGrid**
- Similar to SES, third-party provider

**Email Failure Handling:**
- Failures logged to CloudWatch with `[ORDER_EMAIL_FAILURE]` prefix
- `Orderemailfailure` database records track failures
- CloudWatch alarm triggers SNS notifications
- Order still saved even if email fails (customer paid!)

#### **Infrastructure: AWS VPC, ALB, ECR, CloudWatch, Secrets Manager**

**VPC Architecture:**
- CIDR: 10.0.0.0/16
- **Public Subnets** (10.0.1.0/24, 10.0.2.0/24): ALB, NAT Gateway
- **Private Subnets** (10.0.3.0/24, 10.0.4.0/24): ECS tasks, RDS
- **Internet Gateway**: Allows public subnet internet access
- **NAT Gateway**: Allows private subnet outbound internet (Docker pulls, Stripe API)

**Application Load Balancer (ALB):**
- Listeners: HTTP:80 (redirects to HTTPS), HTTPS:443
- Target Group: ECS tasks on port 8000
- Health Check: `/user/logged-in` endpoint
- SSL Certificate: AWS Certificate Manager (ACM)
- Domain: `api.yourbusiness.com`

**Security Groups:**
- **ALB**: Allow 80/443 from 0.0.0.0/0 (internet)
- **ECS**: Allow 8000 from ALB security group
- **RDS**: Allow 5432 from ECS + Bastion security groups

**ECR (Elastic Container Registry):**
- Docker image repository
- Lifecycle policy: Keep latest 10 images
- Scanned for vulnerabilities

**CloudWatch:**
- **Logs**: Backend logs, ECS task logs, ALB access logs
- **Metrics**: CPU, memory, request count, 5xx errors
- **Alarms**: Email/SMS alerts for errors, high CPU, email failures
- **Dashboards**: System health visualization

**Secrets Manager:**
- Stores: Database password, Django SECRET_KEY, Stripe keys, email credentials
- Accessed via IAM role by ECS tasks
- No secrets in code or environment variables (except secret ARN)

---

## 2. Data Models

### Entity Relationship Overview

```
User (Django Auth)
  │
  └─1:1─▶ Member
           ├─1:many─▶ Cart
           ├─1:many─▶ Order
           ├─1:many─▶ Emailsent
           └─1:1─────▶ Defaultshippingaddress

Prospect (Anonymous Users)
  ├─1:many─▶ Order
  └─1:many─▶ Emailsent

Product
  ├─1:many─▶ Productimage
  └─many:many (via Productsku)─▶ SKU
                                   ├─1:many─▶ Skuprice
                                   ├─1:many─▶ Skuimage
                                   ├─FK────▶ Skutype
                                   └─FK────▶ Skuinventory

Cart
  ├─FK─▶ Member (nullable)
  ├─FK─▶ Cartshippingaddress
  ├─FK─▶ Cartpayment
  ├─1:many─▶ Cartsku (cart items)
  ├─1:many─▶ Cartdiscount
  └─1:1────▶ Cartshippingmethod

Order
  ├─FK─▶ Member (nullable)
  ├─FK─▶ Prospect (nullable)
  ├─FK─▶ Orderpayment (Stripe payment_intent_id)
  ├─FK─▶ Ordershippingaddress
  ├─FK─▶ Orderbillingaddress
  ├─1:many─▶ Ordersku (ordered items)
  ├─1:many─▶ Orderdiscount
  ├─1:many─▶ Orderstatus (history)
  ├─1:1────▶ Ordershippingmethod
  └─1:many─▶ Orderemailfailure (tracking)

Email (template)
  ├─FK─▶ Emailtype (Member/Prospect)
  ├─FK─▶ Emailstatus (Draft/Ready/Sent)
  └─1:many─▶ Emailsent (delivery log)
```

### Core Models

#### **User Models (user app)**

**User (Django built-in)**
- `username` - Unique identifier (email is NOT username)
- `email` - User's email address
- `password` - Hashed password (Django validators + custom)
- `is_active` - Account status
- `date_joined` - Registration timestamp

**Member** (extends User)
- `user` - OneToOne to Django User
- `newsletter_subscriber` - Boolean, opt-in for marketing emails
- `email_verified` - Boolean, verified via email link
- `email_verification_string` - Token for email verification
- `email_unsubscribed` - Boolean, opt-out from all emails
- `email_unsubscribe_string` - Token for one-click unsubscribe
- `reset_password_string` - Token for password reset
- `mb_cd` - Member code (unique, for email tracking)
- `stripe_customer_token` - Stripe customer ID (for saved payment methods)
- `default_shipping_address` - FK to Defaultshippingaddress
- `use_default_shipping_and_payment_info` - Boolean, quick checkout

**Prospect** (anonymous/unconverted users)
- `first_name`, `last_name` - Optional, captured from Stripe checkout
- `email` - Unique email address
- `email_unsubscribed` - Boolean, opt-out
- `email_unsubscribe_string` - Token for one-click unsubscribe
- `prospect_comment` - Admin notes
- `swa_comment` - System notes (e.g., "Captured from Stripe order ORD-123")
- `pr_cd` - Prospect code (unique, for email tracking)
- `created_date_time` - First seen timestamp
- `converted_date_time` - When converted to Member (nullable)

#### **Product Models (order app)**

**Product**
- `title` - Product name (e.g., "Paper Clips")
- `title_url` - URL slug (e.g., "paper-clips")
- `identifier` - Unique 10-character code
- `headline` - Short catchy description
- `description_part_1` - Main product description
- `description_part_2` - Additional details (optional)

**Productimage**
- `product` - FK to Product
- `image_url` - Full or relative path (e.g., `https://img.yourbusiness.com/products/clips.jpg`)
- `main_image` - Boolean, primary product image
- `caption` - Image description

**SKU** (Stock Keeping Unit - product variants)
- `sku_type` - FK to Skutype (e.g., "Product")
- `sku_inventory` - FK to Skuinventory (e.g., "In Stock", "Back Ordered", "Out of Stock")
- `color` - Variant color (e.g., "Blue")
- `size` - Variant size (e.g., "Medium")
- `description` - Human-readable (e.g., "Blue, Medium")

**Skuprice** (price history)
- `sku` - FK to SKU
- `price` - Decimal (10, 2)
- `created_date_time` - When this price became effective
- **Note**: Latest price used via `.latest('created_date_time')`

**Productsku** (Product ↔ SKU many-to-many)
- `product` - FK to Product
- `sku` - FK to SKU
- **Unique constraint**: (product, sku) - prevents duplicate links

#### **Cart Models (order app)**

**Cart**
- `member` - FK to Member (nullable, for signed-in users)
- `anonymous_cart_id` - String, cookie-based cart ID for anonymous users
- `shipping_address` - FK to Cartshippingaddress
- `payment` - FK to Cartpayment

**Cartsku** (cart items)
- `cart` - FK to Cart
- `sku` - FK to SKU
- `quantity` - Integer (1+)
- **Unique constraint**: (cart, sku) - prevents duplicate SKUs in cart

**Cartdiscount** (applied discount codes)
- `cart` - FK to Cart
- `discountcode` - FK to Discountcode
- `applied` - Boolean (always True when in cart)

**Cartshippingmethod**
- `cart` - FK to Cart (OneToOne)
- `shippingmethod` - FK to Shippingmethod

#### **Order Models (order app)**

**Order**
- `identifier` - Unique order code (e.g., "ORD-abc123def4")
- `member` - FK to Member (nullable, signed-in orders)
- `prospect` - FK to Prospect (nullable, anonymous orders)
- `payment` - FK to Orderpayment
- `shipping_address` - FK to Ordershippingaddress
- `billing_address` - FK to Orderbillingaddress
- `item_subtotal` - Decimal, sum of item prices
- `item_discount_amt` - Decimal, discount on items
- `shipping_amt` - Decimal, shipping cost
- `shipping_discount_amt` - Decimal, discount on shipping
- `sales_tax_amt` - Decimal (currently 0, future enhancement)
- `order_total` - Decimal, final total
- `agreed_with_terms_of_sale` - Boolean (always True for completed orders)
- `order_date_time` - Timestamp

**Orderpayment** (Stripe payment details)
- `email` - Customer email from Stripe
- `payment_type` - String (e.g., "card")
- `card_name` - Cardholder name
- `stripe_payment_intent_id` - Unique Stripe payment ID (idempotency key)

**Ordersku** (ordered items snapshot)
- `order` - FK to Order
- `sku` - FK to SKU
- `quantity` - Integer
- `price_each` - Decimal, **snapshot of price at order time** (crucial!)

**Orderdiscount**
- `order` - FK to Order
- `discountcode` - FK to Discountcode
- `applied` - Boolean

**Orderstatus** (order lifecycle)
- `order` - FK to Order
- `status` - FK to Status (e.g., "Accepted", "Manufacturing", "Packing", "Shipped")
- `created_date_time` - When status changed
- **History**: Multiple records per order (latest = current status)

**Orderemailfailure** (monitoring)
- `order` - FK to Order
- `failure_type` - Choices: `template_lookup`, `formatting`, `smtp`, `emailsent_logging`, `cart_deletion`
- `error_message` - Text, exception message
- `customer_email` - Email address (denormalized for quick lookup)
- `is_member_order` - Boolean (denormalized)
- `phase` - String (e.g., "phase_3", "phase_6")
- `created_date_time` - Auto timestamp
- `resolved` - Boolean (for admin tracking)
- `resolved_date_time` - When issue resolved
- `resolved_by` - Admin username
- `resolution_notes` - Text

#### **Email Models (user app)**

**Email** (email templates)
- `em_cd` - Email code (unique identifier, e.g., "welcome-member")
- `subject` - Email subject line
- `emailtype` - FK to Emailtype (Member/Prospect)
- `emailstatus` - FK to Emailstatus (Draft/Ready/Sent)
- `body_text` - Plain text email body (supports variables: `{recipient_first_name}`)
- `body_html` - HTML email body (optional)
- `from_address` - Sender email
- `bcc_address` - BCC email (e.g., for admin copy)

**Emailsent** (delivery log)
- `member` - FK to Member (nullable)
- `prospect` - FK to Prospect (nullable)
- `email` - FK to Email (template used)
- `sent_date_time` - Timestamp
- **Note**: Created only after email successfully sent (not before!)

---

## 3. Key Flows

### Checkout Flow (Transaction-Protected)

**Overview:** Customer completes purchase via Stripe Checkout, order created atomically

```
┌─────────────┐
│   Browser   │
│  (Customer) │
└──────┬──────┘
       │ 1. Add to Cart
       ▼
┌─────────────────────────────────┐
│    /order/add-item-to-cart      │
│  - Create/update Cart           │
│  - Add Cartsku record           │
│  - Return cart totals           │
└──────┬──────────────────────────┘
       │ 2. View Cart
       ▼
┌─────────────────────────────────┐
│    /order/cart-contents         │
│  - Calculate totals             │
│  - Apply discount codes         │
│  - Return cart JSON             │
└──────┬──────────────────────────┘
       │ 3. Click "Checkout"
       ▼
┌─────────────────────────────────┐
│ /order/create-checkout-session  │
│  - Create Stripe Session        │
│  - Metadata: cart_id            │
│  - Return session URL           │
└──────┬──────────────────────────┘
       │ 4. Redirect to Stripe
       ▼
┌─────────────────────────────────┐
│      Stripe Checkout Page       │
│  - Customer enters card info    │
│  - Stripe processes payment     │
│  - Redirect to success_url      │
└──────┬──────────────────────────┘
       │ 5. Return to site
       ▼
┌─────────────────────────────────┐
│ /order/checkout-session-success │
│  - Retrieve session from Stripe │
│  - Wait for webhook (polling)   │
│  - Display confirmation         │
└─────────────────────────────────┘

       │ 6. Webhook (parallel)
       ▼
┌──────────────────────────────────────────────────────────────┐
│            /order/stripe-webhook                             │
│         handle_checkout_session_completed                    │
│                                                               │
│  PHASE 1: Validation (BEFORE transaction)                    │
│    - Check idempotency (existing payment_intent_id?)         │
│    - Lookup cart by cart_id (from metadata)                  │
│    - Verify payment_status = "paid"                          │
│    - Retrieve full session from Stripe API                   │
│                                                               │
│  PHASE 2: Atomic Order Creation (INSIDE transaction)         │
│    with transaction.atomic():                                │
│      1. Create Orderpayment (stripe_payment_intent_id)       │
│      2. Create Ordershippingaddress (from Stripe)            │
│      3. Create Orderbillingaddress (from Stripe)             │
│      4. Create/update Prospect (if anonymous)                │
│      5. Create Order (identifier, totals, FK to above)       │
│      6. Create Ordersku records (from Cartsku)               │
│      7. Create Orderdiscount records (from Cartdiscount)     │
│      8. Create Orderstatus (initial status: "Accepted")      │
│      9. Create Ordershippingmethod                           │
│                                                               │
│    IF ANY STEP FAILS → FULL ROLLBACK (no partial order!)    │
│                                                               │
│  PHASE 3: Email Template Lookup (AFTER transaction)          │
│    - Determine Member vs Prospect template                   │
│    - Lookup Email by em_cd                                   │
│    - If missing → log error, create Orderemailfailure        │
│                                                               │
│  PHASE 4: Email Formatting (AFTER transaction)               │
│    - Build order confirmation text sections                  │
│    - Format template with order data                         │
│    - Create EmailMultiAlternatives object                    │
│    - If fails → log error, create Orderemailfailure          │
│                                                               │
│  PHASE 5: Cart Cleanup (AFTER transaction)                   │
│    - cart.delete()                                           │
│    - If fails → log warning (orphaned cart OK)              │
│                                                               │
│  PHASE 6: Email Send (AFTER transaction - LAST!)             │
│    - email_message.send() via SMTP                           │
│    - Create Emailsent record (only if send succeeds!)        │
│    - If fails → log [ORDER_EMAIL_FAILURE], trigger alarm     │
│                                                               │
│  Return HTTP 200 with order_identifier                       │
│    - Even if email failed, order saved (customer paid!)      │
└──────────────────────────────────────────────────────────────┘
```

**Critical Design Decisions:**

1. **Transaction Boundary:**
   - ALL 9 database writes in Phase 2 are atomic
   - Either complete order is created, or nothing (rollback)
   - Prevents partial orders if database fails mid-process

2. **Email AFTER Transaction:**
   - Email template lookup, formatting, sending all happen AFTER order saved
   - Email failures CANNOT block order creation
   - Customer has paid → order MUST be saved

3. **Idempotency:**
   - Stripe can retry webhooks
   - Check `payment_intent_id` before creating order
   - Return existing order if found (HTTP 200)

4. **Error Handling:**
   - Phase 1-2 failures → return error, no order created
   - Phase 3-6 failures → order saved, log error, return success
   - CloudWatch alarm triggers on `[ORDER_EMAIL_FAILURE]` log

### User Registration Flow

**Overview:** New user creates account with strong password validation

```
┌─────────────┐
│   Browser   │
│    (User)   │
└──────┬──────┘
       │ 1. Submit create-account form
       │    (username, email, password, password2, newsletter)
       ▼
┌─────────────────────────────────────────────────────────────┐
│                /user/create-account                         │
│                                                              │
│  1. Validate input:                                         │
│     - Username not already taken                            │
│     - Email not already taken                               │
│     - password == password2                                 │
│                                                              │
│  2. Django password validators:                             │
│     - UserAttributeSimilarityValidator                      │
│       → Reject if password similar to username             │
│     - CommonPasswordValidator                               │
│       → Reject if password in common password list         │
│     - MinimumLengthValidator (8 characters)                 │
│                                                              │
│  3. Custom password validators:                             │
│     - Capital letter required                               │
│     - Special character required                            │
│     - Length 8-50 characters                                │
│                                                              │
│  4. Create User (Django auth):                              │
│     - user = User.objects.create_user(username, email, pwd) │
│     - Password automatically hashed                         │
│                                                              │
│  5. Create Member:                                          │
│     - member = Member.objects.create(                       │
│         user=user,                                          │
│         newsletter_subscriber=form_value,                   │
│         email_verified=False,                               │
│         email_verification_string=generate_token(),         │
│         mb_cd=getNewMemberCode()                            │
│       )                                                     │
│                                                              │
│  6. Add to "Members" group (permissions):                   │
│     - user.groups.add(members_group)                        │
│                                                              │
│  7. Auto-login:                                             │
│     - login(request, user)                                  │
│                                                              │
│  8. Send welcome email (optional):                          │
│     - Email template: "welcome-member"                      │
│     - Contains email verification link                      │
│                                                              │
│  9. Return success JSON:                                    │
│     - {"endpoint": "account_created"}                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Browser redirects to:          │
│  /account (authenticated)       │
└─────────────────────────────────┘
```

**Password Strength Requirements:**
- Minimum 8 characters
- Maximum 50 characters
- At least one capital letter
- At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
- NOT similar to username
- NOT a common password (Django's built-in list)

**Rate Limiting:**
- 5 account creations per hour per IP address
- Returns HTTP 403 if limit exceeded
- Uses django-ratelimit with local-memory cache (dev) or Redis (production)

### Email Campaign Flow (Marketing Emails)

**Overview:** Admin creates and sends bulk emails to Members/Prospects

```
┌─────────────────┐
│  Django Admin   │
│  (Logged in as  │
│   superuser)    │
└────────┬────────┘
         │ 1. Create Email
         ▼
┌─────────────────────────────────────────────────────────────┐
│         Home → User → Emails → Add Email                    │
│                                                              │
│  Fields:                                                     │
│    - Subject: "New Product Launch!"                         │
│    - Email Type: Member (or Prospect)                       │
│    - Email Status: Draft                                    │
│    - Body Text: "Hi {recipient_first_name}, ..."            │
│    - Body HTML: (optional HTML version)                     │
│    - From Address: marketing@yourbusiness.com               │
│    - BCC Address: marketing@yourbusiness.com                │
│                                                              │
│  Save                                                        │
└─────────┬───────────────────────────────────────────────────┘
          │ 2. Generate email code (em_cd)
          ▼
┌─────────────────────────────────────────────────────────────┐
│    Select Email → Actions → "Populate Email Codes"          │
│    - Generates unique em_cd for tracking                    │
│    - Required for link tracking in emails                   │
└─────────┬───────────────────────────────────────────────────┘
          │ 3. Send draft email (testing)
          ▼
┌─────────────────────────────────────────────────────────────┐
│    Select Email → Actions → "Send Draft Email"              │
│    - Sends to BCC address only                              │
│    - Test: Click all links, check formatting               │
└─────────┬───────────────────────────────────────────────────┘
          │ 4. Change status to Ready
          ▼
┌─────────────────────────────────────────────────────────────┐
│    Edit Email → Email Status: Ready → Save                  │
└─────────┬───────────────────────────────────────────────────┘
          │ 5. Send to all recipients
          ▼
┌─────────────────────────────────────────────────────────────┐
│  Select Email → Actions → "Send Ready Email to Recipients"  │
│                                                              │
│  Processing:                                                 │
│    IF Email Type == Member:                                 │
│      recipients = Member.objects.filter(                    │
│        newsletter_subscriber=True,                          │
│        email_unsubscribed=False                             │
│      )                                                       │
│                                                              │
│    IF Email Type == Prospect:                               │
│      recipients = Prospect.objects.filter(                  │
│        email_unsubscribed=False                             │
│      )                                                       │
│                                                              │
│    FOR EACH recipient:                                      │
│      - Format email body with recipient data:               │
│        {recipient_first_name}, {mb_cd} or {pr_cd}           │
│      - Add tracking parameters to all links:                │
│        ?em_cd=<email_code>&mb_cd=<member_code>              │
│      - Send email via SMTP                                  │
│      - Create Emailsent record                              │
│                                                              │
│  Change Email Status: Sent                                  │
└─────────────────────────────────────────────────────────────┘
```

**Email Unsubscribe:**
- Every email includes unsubscribe link
- Link format: `/user/email-unsubscribe?email_unsubscribe_string=<token>`
- Sets `email_unsubscribed=True` on Member or Prospect
- One-click unsubscribe (no login required)

**Email Tracking:**
- `em_cd` - Tracks which email campaign
- `mb_cd` / `pr_cd` - Tracks which recipient
- Link clicks can be logged to `ClientEvent` table for analytics

---

## 4. Security Features

### CSRF Protection

**Implementation:**
- Django's built-in CSRF middleware enabled
- Token stored in `csrftoken` cookie
- Frontend sends token in `X-CSRFToken` header on all POST/PUT/DELETE requests

**Cookie Configuration:**
```python
# settings.py
CSRF_COOKIE_DOMAIN = '.startupwebapp.com'  # Shared subdomain
CSRF_COOKIE_HTTPONLY = False  # JavaScript needs access
CSRF_COOKIE_SECURE = True  # HTTPS only (production)
```

**Frontend Flow:**
1. Page load: Backend sets `csrftoken` cookie
2. AJAX request: Frontend reads cookie, adds `X-CSRFToken` header
3. Backend validates token matches cookie
4. If mismatch → HTTP 403 Forbidden

**Files:**
- `js/utilities/utilities-0.0.1.js` - `$.get_token()` fetches token from `/user/token`
- All AJAX calls use `beforeSend` to add header

### Rate Limiting

**Protected Endpoints:**

| Endpoint | Limit | Key | Response |
|----------|-------|-----|----------|
| `/user/login` | 10/hour | IP address | HTTP 403 |
| `/user/create-account` | 5/hour | IP address | HTTP 403 |
| `/user/reset-password` | 5/hour | Username | HTTP 403 |

**Implementation:**
- Library: `django-ratelimit==4.1.0`
- Cache backend: Local-memory (dev), Redis (production - future)
- Decorator: `@ratelimit(key='ip', rate='10/h', method='POST')`

**Configuration:**
```python
# settings.py
RATELIMIT_ENABLE = 'test' not in sys.argv  # Disabled during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ratelimit-cache',
    }
}
```

**Behavior:**
- If limit exceeded → HTTP 403 response
- "Fail open" mode: If cache unavailable, requests succeed (availability > strict limiting)

**Future Enhancement:**
- ElastiCache Redis for production (shared cache across ECS tasks)

### Transaction Protection on Order Creation

**Problem:**
- Order creation involves 9+ database writes
- If any write fails mid-process → partial order (data corruption)
- Customer has paid via Stripe, but order incomplete

**Solution:**
- `@transaction.atomic()` decorator wraps all 9 database operations
- Either ALL succeed (commit) or ALL fail (rollback)
- Atomic guarantee from PostgreSQL

**Protected Operations:**
1. `Orderpayment.objects.create()`
2. `Ordershippingaddress.objects.create()`
3. `Orderbillingaddress.objects.create()`
4. `Prospect.objects.get_or_create()` (if anonymous)
5. `Order.objects.create()`
6. `Ordersku.objects.create()` (loop, multiple SKUs)
7. `Orderdiscount.objects.create()` (loop, multiple discounts)
8. `Orderstatus.objects.create()`
9. `Ordershippingmethod.objects.create()`

**Email Handling:**
- Email sending happens OUTSIDE transaction (Phase 6)
- Email failure CANNOT rollback order (customer paid!)
- Logged to CloudWatch, triggers alarm

**Files:**
- `order/views.py:1416` - `handle_checkout_session_completed()`
- `order/views.py:1016` - `checkout_session_success()`

**Tests:**
- `order/tests/test_transaction_rollback.py` - 9 tests verify atomicity

### Password Validation

**Django Built-In Validators:**

1. **UserAttributeSimilarityValidator:**
   - Rejects passwords similar to username, first name, last name, email
   - Example: Username "john123" → Password "john456" rejected

2. **CommonPasswordValidator:**
   - Rejects passwords from common password list (20,000+ passwords)
   - Examples: "password", "123456", "qwerty" rejected

3. **MinimumLengthValidator:**
   - Rejects passwords < 8 characters

**Custom Validators:**

1. **Capital Letter Required:**
   - Regex: `[A-Z]`
   - Error: "Password must contain at least one capital letter"

2. **Special Character Required:**
   - Regex: `[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]`
   - Error: "Password must contain at least one special character"

3. **Length 8-50:**
   - Min: 8, Max: 50
   - Prevents excessively long passwords (DoS)

**Configuration:**
```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'user.validators.CapitalLetterValidator'},
    {'NAME': 'user.validators.SpecialCharacterValidator'},
    {'NAME': 'user.validators.MaximumLengthValidator', 'OPTIONS': {'max_length': 50}},
]
```

**Applied On:**
- Account creation (`/user/create-account`)
- Password change (`/user/change-password`)
- Password reset (`/user/reset-password`)

### Authentication & Authorization

**Session-Based Authentication:**
- Django's built-in sessions (not JWT tokens)
- Session cookie: `sessionid` (HttpOnly, Secure in production)
- Backend checks `request.user.is_authenticated`

**@login_required Decorator:**
- Protects endpoints requiring authentication
- Redirects to login page if unauthenticated (HTTP 302)
- Used sparingly for AJAX endpoints (manual checks preferred)

**Manual Authentication Checks:**
- Most AJAX endpoints check `request.user.is_anonymous`
- Return JSON error: `{"endpoint": "user_not_authenticated"}`
- Frontend handles gracefully (doesn't try to parse HTML as JSON)

**Protected Endpoints:**
- `/user/account-content` - View account details
- `/user/update-my-information` - Update profile
- `/user/change-my-password` - Change password
- `/order/my-orders` - View order history
- All Django admin URLs (`/admin/`)

### Input Sanitization (XSS Protection)

**Frontend (JavaScript):**
- **Never use `.html()` with user input** (XSS risk!)
- **Always use `.text()`** for user-provided data
- `.text()` escapes HTML entities: `<script>` → `&lt;script&gt;`

**Example:**
```javascript
// UNSAFE (XSS vulnerable)
$('#username').html(data.username);

// SAFE (XSS protected)
$('#username').text(data.username);
```

**Sanitized Fields:**
- Product names, descriptions
- User names, emails
- Cart item titles
- Order details
- Error messages

**Backend (Django):**
- Django templates auto-escape by default
- `{{ user.username }}` → HTML entities escaped
- Admin-provided content (e.g., email templates) trusted (no escaping)

**Files Fixed (Session 16):**
- `/js/index-0.0.2.js` - Product listings
- `/js/checkout/confirm-0.0.1.js` - Checkout confirmation
- `/js/account-0.0.1.js` - Account page
- `/js/account/order-0.0.1.js` - Order history
- `/js/product-0.0.1.js` - Product details

### HTTPS Enforcement

**Production:**
- ALB redirects HTTP:80 → HTTPS:443
- CloudFront serves frontend over HTTPS only
- SSL certificates from AWS Certificate Manager (ACM)

**Security Headers:**
```python
# settings.py
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True  # Redirect HTTP → HTTPS
SESSION_COOKIE_SECURE = True  # HTTPS only
CSRF_COOKIE_SECURE = True  # HTTPS only
```

### Secrets Management

**AWS Secrets Manager:**
- Secret name: `startupwebapp/production`
- Contains: Database password, Django SECRET_KEY, Stripe keys, email credentials
- Accessed via IAM role (ECS task role)
- Rotated manually (future: auto-rotation)

**Environment Variables:**
- `SECRET_ARN` - ARN of Secrets Manager secret
- ECS task retrieves secrets at startup
- No secrets in code or Dockerfile

**Local Development:**
- `settings_secret.py` - Gitignored file
- Never committed to repository
- Created from `settings_secret.py.template`

---

## 5. Multi-Tenant Architecture

### Design Pattern

**Single Database Instance, Multiple Databases:**
```
PostgreSQL Instance (RDS)
  ├─ startupwebapp_dev (main project)
  ├─ healthtech_dev (experimental fork)
  └─ fintech_dev (experimental fork)
```

**Switching Databases:**
```yaml
# docker-compose.yml
backend:
  environment:
    DATABASE_NAME: healthtech_dev  # Switch here
```

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'startupwebapp_dev'),
        'USER': 'django_app',
        'PASSWORD': get_secret('database_password'),
        'HOST': 'db',  # Docker service name (local) or RDS endpoint (prod)
        'PORT': '5432',
    }
}
```

### Use Cases

**1. Fork Experimentation:**
- Fork StartupWebApp for new business (e.g., "HealthTech Co")
- Create new database: `healthtech_dev`
- Customize products, branding, domain
- Deploy to production with separate ECS service
- Share infrastructure costs (single RDS instance)

**2. A/B Testing:**
- Create experimental database with different pricing
- Switch `DATABASE_NAME` for specific customer segment
- Compare conversion rates
- Migrate successful experiments to main database

**3. Development Branches:**
- Feature branch uses separate database
- Test migrations, data changes in isolation
- Merge code + migrate main database when ready

### Database Isolation

**Isolated:**
- User accounts (Members, Prospects)
- Products, SKUs, prices
- Orders, payments
- Cart data
- Email templates

**Shared:**
- PostgreSQL server resources (CPU, memory)
- Backup schedule
- Network connectivity

### Migration Strategy

**Creating New Database:**
```sql
-- On PostgreSQL instance
CREATE DATABASE healthtech_dev;
GRANT ALL PRIVILEGES ON DATABASE healthtech_dev TO django_app;
```

**Running Migrations:**
```bash
# Set database in environment
export DATABASE_NAME=healthtech_dev

# Run migrations (creates tables + seeds data)
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

**Data Migration Customization:**
- Edit `user/migrations/0002_seed_user_data.py` - Email templates, terms
- Edit `order/migrations/0004_seed_order_data.py` - Products, shipping, discounts
- Migrations are idempotent (`get_or_create`) - safe to run multiple times

### Production Considerations

**Cost Savings:**
- Single RDS instance: ~$15-20/month
- Multiple databases on same instance: No additional cost
- Scales to ~10-20 small databases before hitting resource limits

**Performance:**
- Each database has separate connection pool
- `CONN_MAX_AGE=600` keeps connections alive
- PostgreSQL handles multiple databases efficiently

**Scaling:**
- When databases grow large, migrate to separate RDS instances
- Use RDS read replicas for read-heavy workloads
- Upgrade instance type (db.t3.small → db.t3.medium)

---

## Diagrams

### Deployment Architecture (Production)

```
                      ┌─────────────────────────┐
                      │      Route 53 DNS       │
                      │  api.yourbusiness.com   │
                      │  yourbusiness.com       │
                      └────────┬────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
    ┌──────────────────┐          ┌──────────────────┐
    │   CloudFront     │          │       ALB        │
    │  (Frontend CDN)  │          │  (Backend HTTPS) │
    │                  │          │                  │
    │  - Edge caching  │          │  - SSL term.     │
    │  - Gzip compress │          │  - Health checks │
    │  - ACM cert      │          │  - Target groups │
    └────────┬─────────┘          └────────┬─────────┘
             │                              │
             ▼                              ▼
    ┌──────────────────┐          ┌──────────────────┐
    │    S3 Bucket     │          │   ECS Fargate    │
    │  (Static files)  │          │  (Django tasks)  │
    │                  │          │                  │
    │  - HTML/CSS/JS   │          │  - Auto-scaling  │
    │  - Versioned     │          │  - Secrets Mgr   │
    └──────────────────┘          └────────┬─────────┘
                                           │
                            ┌──────────────┼──────────────┐
                            │              │              │
                            ▼              ▼              ▼
                   ┌─────────────┐ ┌─────────────┐ ┌──────────┐
                   │     RDS     │ │   Secrets   │ │CloudWatch│
                   │ PostgreSQL  │ │   Manager   │ │Logs/Alarm│
                   │             │ │             │ │          │
                   │ - Multi-AZ  │ │ - Stripe    │ │ - SNS    │
                   │ - Backups   │ │ - Email     │ │ - Metrics│
                   └─────────────┘ └─────────────┘ └──────────┘
```

### Request Flow (Checkout)

```
User Browser                Frontend (S3)              Backend (ECS)           Stripe              Database (RDS)
     │                           │                          │                    │                       │
     │ 1. GET /products          │                          │                    │                       │
     ├──────────────────────────▶│                          │                    │                       │
     │ 2. HTML/JS                │                          │                    │                       │
     │◀──────────────────────────┤                          │                    │                       │
     │                           │                          │                    │                       │
     │ 3. GET /order/cart-contents                          │                    │                       │
     ├──────────────────────────────────────────────────────▶│                    │                       │
     │                           │                          │ 4. SELECT cart... │                       │
     │                           │                          ├───────────────────────────────────────────▶│
     │                           │                          │ 5. Cart data      │                       │
     │                           │                          │◀───────────────────────────────────────────┤
     │ 6. Cart JSON              │                          │                    │                       │
     │◀──────────────────────────────────────────────────────┤                    │                       │
     │                           │                          │                    │                       │
     │ 7. POST /order/create-checkout-session                                     │                       │
     ├──────────────────────────────────────────────────────▶│                    │                       │
     │                           │                          │ 8. Create session  │                       │
     │                           │                          ├───────────────────▶│                       │
     │                           │                          │ 9. Session URL     │                       │
     │                           │                          │◀───────────────────┤                       │
     │ 10. Session URL           │                          │                    │                       │
     │◀──────────────────────────────────────────────────────┤                    │                       │
     │                           │                          │                    │                       │
     │ 11. Redirect to Stripe    │                          │                    │                       │
     ├───────────────────────────────────────────────────────────────────────────▶│                       │
     │                           │                          │                    │                       │
     │ 12. Enter card, pay       │                          │                    │                       │
     ├───────────────────────────────────────────────────────────────────────────▶│                       │
     │                           │                          │                    │                       │
     │                           │                          │ 13. Webhook: checkout.session.completed      │
     │                           │                          │◀───────────────────┤                       │
     │                           │                          │                    │                       │
     │                           │                          │ 14. BEGIN TRANSACTION                      │
     │                           │                          ├───────────────────────────────────────────▶│
     │                           │                          │ 15. INSERT Orderpayment                    │
     │                           │                          ├───────────────────────────────────────────▶│
     │                           │                          │ 16. INSERT Ordershippingaddress             │
     │                           │                          ├───────────────────────────────────────────▶│
     │                           │                          │ ... (7 more INSERTs)                        │
     │                           │                          │ 17. COMMIT TRANSACTION                     │
     │                           │                          ├───────────────────────────────────────────▶│
     │                           │                          │                    │                       │
     │                           │                          │ 18. Send email     │                       │
     │                           │                          │ (SMTP)             │                       │
     │                           │                          │                    │                       │
     │                           │                          │ 19. DELETE cart    │                       │
     │                           │                          ├───────────────────────────────────────────▶│
     │                           │                          │                    │                       │
     │ 20. Redirect to success_url                          │                    │                       │
     │◀──────────────────────────────────────────────────────────────────────────┤                       │
     │                           │                          │                    │                       │
     │ 21. GET /order/checkout-session-success?session_id=...                     │                       │
     ├──────────────────────────────────────────────────────▶│                    │                       │
     │ 22. Order confirmation    │                          │                    │                       │
     │◀──────────────────────────────────────────────────────┤                    │                       │
```

---

## Summary

StartupWebApp is a **production-ready, security-hardened e-commerce platform** designed for easy forking and customization. Key architectural strengths:

1. **Battle-tested infrastructure**: AWS VPC, ECS Fargate, RDS, CloudFront
2. **Comprehensive test coverage**: 818 tests ensure reliability
3. **Transaction protection**: Atomic order creation prevents data corruption
4. **Security-first**: CSRF, rate limiting, password validation, XSS protection, HTTPS
5. **Multi-tenant capable**: Single database instance, multiple isolated databases
6. **Fork-friendly**: Data migrations seed customizable reference data
7. **Monitoring & alerting**: CloudWatch logs, metrics, alarms, SNS notifications

**For business owners:** Fork, customize products/branding, deploy to AWS, launch your business!

**For developers:** Well-architected Django backend, clean separation of concerns, extensive documentation.

---

## Additional Resources

- **Fork Setup Guide**: `docs/FORK_SETUP_GUIDE.md` - Step-by-step customization guide
- **Disaster Recovery**: `docs/DISASTER_RECOVERY.md` - Production recovery procedures
- **AWS Deployment**: `docs/reference/production-deployment.md` - Infrastructure details
- **ECS CI/CD**: `docs/reference/ecs-cicd-migrations.md` - Deployment pipeline
- **Security Fixes**: `docs/archive/2025-modernization-history/PRE_FORK_SECURITY_FIXES.md` - Security hardening history

**Questions?** Open an issue at [github.com/bartgottschalk/startup_web_app_server_side/issues](https://github.com/bartgottschalk/startup_web_app_server_side/issues)
