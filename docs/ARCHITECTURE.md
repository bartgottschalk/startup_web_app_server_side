# System Architecture

**Purpose**: High-level overview of how StartupWebApp components fit together

---

## 🚧 TODO (Next Session): Fill in full content

**This is a STUB file created during documentation reorganization.**

**Planned Outline** (~300 lines when complete):

### 1. System Components
- **Frontend**: jQuery/React on S3 + CloudFront (static files)
- **Backend API**: Django REST on ECS Fargate (Python 3.12)
- **Database**: PostgreSQL 16 on RDS (multi-tenant architecture)
- **Payment Processing**: Stripe Checkout Sessions (webhooks)
- **Email**: Django templates + SMTP (SES or SendGrid)
- **Infrastructure**: AWS VPC, ALB, ECR, CloudWatch, Secrets Manager

### 2. Data Models
- **User Models**: User, Member, Prospect
- **Product Models**: Product, SKU, SKUPrice, ProductSKU, SKUInventory
- **Order Models**: Order, OrderSKU, OrderPayment, OrderShipping, OrderStatus
- **Cart Models**: Cart, CartSKU, CartDiscount
- **Email Models**: Email, EmailType, EmailSent
- **Client Event Models**: ClientEvent, Configuration
- Diagram showing relationships and foreign keys

### 3. Key Flows

**Checkout Flow**:
1. Anonymous/Member adds items to cart
2. Cart calculates totals (items + shipping - discounts)
3. User clicks checkout → Redirects to Stripe Checkout Session
4. Stripe processes payment
5. Webhook triggers `handle_checkout_session_completed`
6. **Transaction-protected order creation** (9 database objects atomic)
7. Email confirmation sent
8. Cart deleted

**User Registration Flow**:
1. User submits create-account form
2. Django password validators enforce strength
3. Custom validators (capital letter, special char, length)
4. Member record created
5. User logged in automatically
6. Welcome email sent

**Email Campaign Flow**:
1. Admin creates Email in Django admin (Draft status)
2. Populate email codes (tracking)
3. Send draft email to test address
4. Change status to Ready
5. Bulk send to Members/Prospects
6. Track opens/clicks via email codes

### 4. Security Features
- **CSRF Protection**: Token-based with cookie storage
- **Rate Limiting**: django-ratelimit on login, register, password reset (local-memory cache)
- **Transaction Protection**: `@transaction.atomic()` on order creation (Phase 1-7 complete)
- **Password Validation**: Django validators (username similarity, common passwords) + custom validators
- **Authentication**: Session-based with @login_required decorators
- **Input Sanitization**: XSS protection via `.text()` escaping in frontend
- **HTTPS**: Enforced in production (ALB → ECS, CloudFront → S3)
- **Secrets Management**: AWS Secrets Manager (no credentials in code)

### 5. Multi-Tenant Architecture
- Single PostgreSQL instance with multiple databases
- Experimental forks use separate databases (`startupwebapp_dev`, `healthtech_dev`, `fintech_dev`)
- Switch via `DATABASE_NAME` environment variable in docker-compose
- Isolated data, shared infrastructure

---

**Next Session**: Fill in this content with diagrams, code examples, and deployment architecture visuals.
