# ⚠️ Important Domain Notice
I no longer control the domain startupwebapp.com and am not responsible for the content that is currently served from that domain. Use caution if you go there.

# startup_web_app_server_side

A Django REST API backend for an e-commerce startup, featuring comprehensive test coverage, Docker containerization, and Python 3.12 compatibility.

## Current Status (December 2025)

✅ **Production Live** - Full-stack deployed to AWS (ECS Fargate + S3/CloudFront)
✅ **753 Tests Passing** - Comprehensive test coverage (722 unit + 31 functional) with PostgreSQL
✅ **CI/CD Pipeline** - Auto-deploy on merge to master with PR validation
✅ **PostgreSQL 16** - Production-ready database with multi-tenant architecture
✅ **Python 3.12 Compatible** - Fully modernized for latest Python
✅ **Docker Containerized** - Easy setup with Docker Compose
✅ **Django 4.2.16 LTS** - Modern Django with security support until April 2026
✅ **Code Quality Tools** - Zero linting errors (backend + frontend)

**Production URLs:**
- Backend API: `https://startupwebapp-api.mosaicmeshai.com`
- Frontend: `https://startupwebapp.mosaicmeshai.com`

### Test Coverage Breakdown
- **User App**: 299 tests (authentication, profiles, email management, Stripe error handling, admin actions)
- **Order App**: 322 tests (products, cart, checkout, payments via Stripe, Checkout Sessions)
- **ClientEvent App**: 51 tests (analytics event tracking)
- **Validators**: 50 tests (input validation)
- **Functional Tests**: 31 Selenium tests (full user journey testing, Django Admin)

### Code Quality
- **Backend**: pylint 4.0.2, flake8 7.3.0 (runs in Docker)
- **Frontend**: ESLint 9.39.1 with Node.js 25.1.0 (runs on host)
- **Analysis**: 9,313 issues catalogued with prioritized recommendations
- See `docs/technical-notes/2025-11-09-code-linting-analysis.md` for details

📚 **See [docs/PROJECT_HISTORY.md](docs/PROJECT_HISTORY.md) for detailed project timeline and completed phases.**

## ⚠️ Important: Demo Project - TEST Mode Only

**This is a demonstration/template project, not a real business.**

**Stripe Configuration:**
- Production uses **TEST mode keys** (pk_test_..., sk_test_...) - NOT live keys
- Deployed site accepts **test credit cards only** (4242 4242 4242 4242)
- **No real payment processing** occurs, even in production
- Demonstrates full e-commerce functionality without financial risk

**For Real Businesses:**
- Fork this repository for your own business
- Configure your own Stripe **LIVE mode keys** (pk_live_..., sk_live_...)
- Update AWS Secrets Manager with your keys
- You'll inherit battle-tested payment infrastructure

**Why This Architecture?**
- Safe demonstration of complete checkout flow
- Template for real businesses to customize
- Allows public deployment without payment liability
- Forks can use real Stripe accounts for actual transactions

## About This Project

I'm co-founder of a startup which:

1. Produces and sells a relatively small quantity of a relatively high number of customizable physical products, and
2. Has future plans to build a complementary digital product.

Soon after jumping into this idea it was clear we would need a web application to support our product's discovery, selection, customization, purchase and interactive experiences. We looked at using existing marketplaces and web-site building platforms such as Squarespace or Wix. These didn't work for us for a couple of reasons:

1. The customizable nature of our products
2. The large number of individual skus we would be managing
3. Our customers can create skus dynamically

This made using "off-the-shelf" solutions unworkable, even for early prototyping and experimentation, and meant we needed to build a custom web application. Among our non-functional requirements were things like:

1. The ability to iterate quickly
2. Security
3. Reliability
4. Support growth and scalability (reasonably)
5. Support future iterative exploration of our digital product
6. Can't be so costly that it sinks the business

As the only technical co-founder, it landed on me to "figure this out."

This repository contains a simplified version of the server side application I built to launch our startup. To learn more about this project you can check out [slides from a talk I gave about the technical aspects of this project](https://docs.google.com/presentation/d/18Y_G3asKbeys7s5618N_VJkXCI0ePwJ0vKB_06c-P3w/edit#slide=id.g5820c97b01_0_114) or [slides from a talk I gave demoing use of the project for startup idea validation](https://docs.google.com/presentation/d/1O80AyN6jpFxfooDz8ILfYE1PyYlm917mP2EqYuMf5SE/edit#slide=id.g5820c97b01_0_90).

## Quick Start with Docker (Recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) - Required
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) - Required
- [Node.js](https://nodejs.org/) (v25+) - Optional, for JavaScript linting only

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/bartgottschalk/startup_web_app_server_side.git
cd startup_web_app_server_side
```

2. **Build and start the Docker containers** (PostgreSQL + Backend + Frontend)
```bash
docker-compose build
docker-compose up -d
```

This starts three services:
- **PostgreSQL 16**: Database server with multi-tenant support (3 databases created automatically)
- **Backend**: Django REST API
- **Frontend**: Nginx serving static files

3. **Configure local domain names** (Required for full-stack development)

The application uses custom domain names to enable proper CSRF cookie sharing between frontend and backend. Add these entries to your **host machine's** `/etc/hosts` file:

```bash
# Mac/Linux: Add entries to /etc/hosts
echo "127.0.0.1    localhost.startupwebapp.com" | sudo tee -a /etc/hosts
echo "127.0.0.1    localapi.startupwebapp.com" | sudo tee -a /etc/hosts
```

**Why is this needed?**
- Frontend runs on `http://localhost.startupwebapp.com:8080`
- Backend API runs on `http://localapi.startupwebapp.com:8000`
- Both domains share the `.startupwebapp.com` suffix, allowing CSRF cookies to work across subdomains
- Without this, you'll get CSRF and CORS errors when the frontend tries to call the backend

4. **Initialize the PostgreSQL database**
```bash
docker-compose exec backend python manage.py migrate
```

**What happens during initialization:**
- PostgreSQL automatically creates 3 databases: `startupwebapp_dev`, `healthtech_dev`, `fintech_dev`
- Django migrations create 57 tables in the `startupwebapp_dev` database
- **Data migrations automatically seed** all required reference data including:
  - ClientEvent configuration
  - Auth groups, Terms of Use, Email templates
  - Order statuses, shipping methods, discount types
  - Sample products (Paper Clips, Binder Clips, Rubber Bands)

See [Seed Data & Data Migrations](#seed-data--data-migrations) section for details.

**Multi-tenant architecture**: The setup supports multiple "forks" (experimental variants) by changing the `DATABASE_NAME` environment variable in `docker-compose.yml`. Each fork uses its own isolated database on the shared PostgreSQL instance.

5. **Access the application**
- **Frontend**: http://localhost.startupwebapp.com:8080
- **Backend API**: http://localapi.startupwebapp.com:8000
- **Django Admin**: http://localapi.startupwebapp.com:8000/admin/

### Run Tests

**Run all unit tests** (722 tests with PostgreSQL):
```bash
docker-compose exec backend python manage.py test order.tests user.tests clientevent.tests StartupWebApp.tests --parallel=4
```

**Note**: Tests use PostgreSQLTestCase (TransactionTestCase with `reset_sequences=True`) to handle PostgreSQL's sequence management correctly.

**Run functional tests** (31 tests):
```bash
# IMPORTANT: Setup hosts file first (required after each container restart)
docker-compose exec backend bash /app/setup_docker_test_hosts.sh

# Then run functional tests
docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests
```

### Code Quality & Linting

**Run Python linting** (backend):
```bash
docker-compose exec backend flake8 user order clientevent StartupWebApp --max-line-length=120 --statistics
```

**Run JavaScript linting** (frontend - requires Node.js on host):
```bash
cd ../startup_web_app_client_side
npx eslint js/**/*.js --ignore-pattern "js/jquery/**"
```

**Note**: Linting identifies code quality issues. Run before committing to maintain code standards. See `docs/technical-notes/2025-11-09-code-linting-analysis.md` for baseline and priorities.

### Access Django Admin
```bash
# Create admin user
docker-compose exec backend python manage.py createsuperuser

# Access at http://localapi.startupwebapp.com:8000/admin/
```

### PostgreSQL Configuration

**Connection Details:**
- Host: `localhost` (from host machine) or `db` (from within Docker)
- Port: `5432`
- Default Database: `startupwebapp_dev`
- User: `django_app`
- Password: `dev_password_change_in_prod` (change for production!)

**Multi-Tenant Setup:**
To switch between forks (experimental variants), change the `DATABASE_NAME` environment variable in `docker-compose.yml`:
```yaml
backend:
  environment:
    DATABASE_NAME: healthtech_dev  # or fintech_dev
```

**Database Access:**
```bash
# Connect to PostgreSQL via psql
docker-compose exec db psql -U django_app -d startupwebapp_dev

# List all databases
docker-compose exec db psql -U django_app -d postgres -c "\l"

# View database tables
docker-compose exec db psql -U django_app -d startupwebapp_dev -c "\dt"
```

**Data Persistence:**
PostgreSQL data is stored in a Docker volume (`postgres_data`). To completely reset:
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Recreate with fresh data
docker-compose exec backend python manage.py migrate  # Creates tables + seeds data
```

### Stop the containers
```bash
docker-compose down
```

---

## Seed Data & Data Migrations

This application uses **Django data migrations** to automatically create required seed data when migrations run. This ensures that new deployments (including forks) have all the reference data needed for the application to function.

### How It Works

When you run `python manage.py migrate`, the following data migrations execute automatically:

| Migration | App | Data Created |
|-----------|-----|--------------|
| `0002_seed_configuration.py` | clientevent | Configuration record (enables/disables client event logging) |
| `0002_seed_user_data.py` | user | Auth Group (Members), Terms of Use, Email Types/Statuses, Ad Types/Statuses, Email Templates |
| `0002_add_default_inventory_statuses.py` | order | SKU Inventory statuses (In Stock, Back Ordered, Out of Stock) |
| `0004_seed_order_data.py` | order | Order Statuses, SKU Types, Order Configuration, Discount Types, Shipping Methods, Sample Products |

### Why Data Migrations?

Previously, seed data was loaded via:
- `db_inserts.sql` - Manual SQL file (MySQL syntax)
- `load_sample_data` - Django management command

These required manual execution after migrations, which caused issues:
- Production deployments forgot to run them → 500 errors
- Different environments had inconsistent data
- Forks had no clear guidance on required data

Data migrations solve this by:
- Running automatically with `migrate`
- Using `get_or_create` for idempotency (safe to run multiple times)
- Skipping during test runs (tests create their own data)
- Being part of version control

### For Projects That Fork This Repository

If you fork StartupWebApp for your own project, you'll want to customize the seed data:

1. **Modify the data migrations** in:
   - `StartupWebApp/clientevent/migrations/0002_seed_configuration.py`
   - `StartupWebApp/user/migrations/0002_seed_user_data.py`
   - `StartupWebApp/order/migrations/0004_seed_order_data.py`

2. **Key items to customize**:
   - Email templates (subject, body, from_address)
   - Terms of Use content
   - Sample products (replace Paper Clips, Binder Clips, etc.)
   - Shipping methods and costs
   - Discount codes

3. **Items typically kept as-is**:
   - Auth Group (Members)
   - Email Types/Statuses (Member, Prospect / Draft, Ready, Sent)
   - Order Statuses (Accepted, Manufacturing, Packing, Shipped)
   - SKU Inventory statuses

### Legacy: load_sample_data Command

The `python manage.py load_sample_data` command still exists for convenience during development. It creates the same data as the migrations but can be run manually with a `--flush` flag to reset data.

```bash
# Load sample data (idempotent - safe to run multiple times)
docker-compose exec backend python manage.py load_sample_data

# Reset and reload sample data
docker-compose exec backend python manage.py load_sample_data --flush
```

**Note**: For new deployments, you don't need to run this command - migrations handle it automatically.

---

## Full-Stack Development with Docker Compose

The backend and frontend can be run together using Docker Compose for a complete development environment with functional tests.

### Prerequisites
- Docker Desktop installed
- Frontend repository cloned as a sibling directory:
  ```bash
  cd /path/to/projects
  git clone https://github.com/bartgottschalk/startup_web_app_client_side.git
  git clone https://github.com/bartgottschalk/startup_web_app_server_side.git
  ```
- `settings_secret.py` configured (see CORS Configuration below)

### Quick Start

1. **Start both services**
   ```bash
   cd startup_web_app_server_side
   docker-compose up -d
   ```

2. **Initialize the database** (first time only)
   ```bash
   docker-compose exec backend python manage.py migrate
   ```
   Note: Migrations automatically create all required seed data. See [Seed Data & Data Migrations](#seed-data--data-migrations).

3. **Start the backend API server**
   ```bash
   docker-compose exec -d backend python manage.py runserver 0.0.0.0:8000
   ```

4. **Access the application**
   - Frontend: http://localhost.startupwebapp.com:8080
   - Backend API: http://localapi.startupwebapp.com:8000
   - Admin interface: http://localapi.startupwebapp.com:8000/admin/

   **Note**: Remember to configure your /etc/hosts file first (see Quick Start guide above)

### Architecture

The `docker-compose.yml` orchestrates three services:
- **db**: PostgreSQL 16-alpine database with multi-tenant support
- **backend**: Django REST API (Python 3.12)
- **frontend**: Nginx serving static HTML/CSS/JavaScript

**Database**: PostgreSQL 16 with three pre-configured databases (`startupwebapp_dev`, `healthtech_dev`, `fintech_dev`) for multi-tenant experimentation. Connection pooling enabled (`CONN_MAX_AGE=600`).

**Docker Networking**: Services communicate via a custom bridge network (`startupwebapp`), enabling:
- Browser → Frontend (localhost.startupwebapp.com:8080)
- Browser → Backend API (localapi.startupwebapp.com:8000)
- Frontend (Docker) → Backend API (Docker network)
- Functional tests → Both services

Custom domain names (`.startupwebapp.com`) enable proper CSRF cookie sharing between frontend and backend during development.

### Nginx Configuration

The `nginx.conf` file configures nginx to properly serve extensionless HTML files (e.g., `/about`, `/contact`, `/cart`) with the correct MIME type (`text/html`).

**Why this is needed**: Without this configuration, browsers will download these files instead of rendering them, because nginx defaults to `application/octet-stream` for files without extensions.

**Key configuration features**:
- `absolute_redirect off` - Uses relative redirects to preserve port numbers (e.g., keeps `:8080` when navigating)
- `try_files $uri $uri.html $uri/ =404` - Attempts to find files with or without `.html` extension
- `default_type text/html` - Sets HTML as default MIME type
- Gzip compression enabled
- Static asset caching with 1-year expiration

### CORS Configuration

For Docker development, add these origins to `StartupWebApp/StartupWebApp/settings_secret.py`:

```python
CORS_ORIGIN_WHITELIST = (
    'http://localhost:8080',  # Docker Compose frontend (browser access - legacy)
    'http://frontend',  # Docker Compose frontend (internal Docker network)
    'http://localliveservertestcase.startupwebapp.com',  # Functional tests
    'http://localhost.startupwebapp.com:8080',  # Local development (recommended)
)
```

**Important Notes:**
- `settings_secret.py` is gitignored and must be created manually. See `settings_secret.py.template` for reference.
- The `:8080` port must be included in `http://localhost.startupwebapp.com:8080` for the frontend to communicate with the backend
- CSRF cookies require matching domain suffixes (`.startupwebapp.com`) to work properly

### Running Functional Tests

Functional tests use Selenium with headless Firefox to test the full stack from a user's perspective.

**⚠️ IMPORTANT: Setup Required Before First Run**

Before running functional tests, you must configure the Docker container's `/etc/hosts` file to enable cookie sharing between frontend and backend:

```bash
docker-compose exec backend bash /app/setup_docker_test_hosts.sh
```

This script maps `localliveservertestcase.startupwebapp.com` and `localliveservertestcaseapi.startupwebapp.com` hostnames to the Docker container IPs, allowing CSRF cookies to be shared across subdomains.

**Note**: This setup is required after each container restart/rebuild.

**Run all functional tests**:
```bash
docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests --verbosity=2
```

**Run specific test suites**:
```bash
# Home page tests
docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests.home --verbosity=2

# About page tests
docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests.about --verbosity=2

# Contact page tests
docker-compose exec -e HEADLESS=TRUE backend python manage.py test functional_tests.contact --verbosity=2
```

**How it works**:
- The `DOCKER_ENV=true` environment variable enables Docker-specific networking
- Tests access frontend at `http://frontend/` (Docker service name)
- LiveServerTestCase provides test API at `http://backend:60767`
- Selenium controls Firefox in headless mode

### Troubleshooting

**Frontend pages download instead of displaying:**
- Verify `nginx.conf` is mounted in docker-compose.yml
- Restart frontend: `docker-compose restart frontend`

**CORS errors in browser console:**
- Add required origins to `CORS_ORIGIN_WHITELIST` in `settings_secret.py`
- Restart backend server

**Functional tests hang or fail with CSRF/cookie errors:**
- **IMPORTANT**: Run the hosts setup script first: `docker-compose exec backend bash /app/setup_docker_test_hosts.sh`
- This is required after each container restart/rebuild
- Ensure both backend and frontend containers are running: `docker-compose ps`
- Check nginx is serving files correctly: `curl -I http://localhost:8080/about`
- Verify CORS configuration includes Docker origins

**Can't connect to API:**
- Ensure backend server is running: `docker-compose exec backend ps aux | grep manage.py`
- Check API responds: `curl http://localapi.startupwebapp.com:8000/user/logged-in`
- Verify /etc/hosts has the required domain entries (see Quick Start guide)

---

## Advanced: Manual Installation

<details>
<summary>Click to expand manual installation instructions (legacy method)</summary>

**⚠️ Note**: The Docker setup (above) is strongly recommended. Manual installation requires PostgreSQL configuration and is primarily for advanced use cases.

### Prerequisites

You will need the following python packages and tools installed:

#### For the Server application to function
- [Python 3.12](https://www.python.org/downloads/)
- [PostgreSQL 16.x](https://www.postgresql.org/download/) - **Required** (application is configured for PostgreSQL)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Python packages: see `requirements.txt` (includes `psycopg2-binary==2.9.9`)

#### For the Selenium functional tests
- [SQLite](https://sqlite.org/download.html)
- [Firefox](https://support.mozilla.org/en-US/products/firefox/install-and-update-firefox)
- [geckodriver](https://github.com/mozilla/geckodriver/releases)

### Installing the Application Manually

#### Install from Github
Note: These instructions assume that you will install the application at `~/StartupWebApp`. If you select another location you will need to adjust all other commands accordingly.

```bash
cd ~/StartupWebApp
git clone https://github.com/bartgottschalk/startup_web_app_server_side.git
cd ~/StartupWebApp/startup_web_app_server_side
```

#### Install Python dependencies
```bash
pip install -r requirements.txt
```

#### Configure Hosts File
Configure hosts file to route 
- localapi.startupwebapp.com to 127.0.0.1
- localliveservertestcaseapi.startupwebapp.com to 127.0.0.1 (this will be used to run Selenium functional tests)

#### Secrets and Passwords
Using this approach described in [How to Scrub Sensitive Information From Django settings.py Files](http://fearofcode.github.io/blog/2013/01/15/how-to-scrub-sensitive-information-from-django-settings-dot-py-files/)
1. Remove secrets from settings.py
2. Place in settings_secret.py
3. Add settings_secret.py to .gitignore
4. Put dummy values in settings_secret.py.template

##### Django CORS Config
See [django-cors-headers documentation](https://github.com/ottoyiu/django-cors-headers)
Config is in settings.py and settings_secret.py

##### Django CRSF Config
Config is in settings_secret.py and settings.py

Token is acquired from api server via GET request (js/utilities/utilities-0.0.1.js->$.get_token) to http://localapi.startupwebapp.com/user/token 

This GET request returns both a token embedded in JSON as well as a cookie containing a token - csrftoken cookie is set automatically by Django. The token explicitly returned in the view response is ignored and discarded by the client in favor of using the cookie value. The application uses the cookie token in javascript and returns it in a Request header "X-CSRFToken". The token returned in JSON is ignored. 

See [Django CSRF Documentation](https://docs.djangoproject.com/en/4.2/ref/csrf/)

##### settings_secret.py from settings_secret.py.template
```
cp settings_secret.py.template settings_secret.py
```
edit values in setting_secret.py to match your environment, database and 3rd party integrations
review and edit values in settings.py to match your environment and 3rd party integrations

#### Database Setup
1. Create local PostgreSQL database:
```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database and user
CREATE DATABASE startupwebapp_dev;
CREATE USER django_app WITH PASSWORD 'dev_password_change_in_prod';
GRANT ALL PRIVILEGES ON DATABASE startupwebapp_dev TO django_app;
```

2. Configure environment variables in `settings_secret.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'startupwebapp_dev',
        'USER': 'django_app',
        'PASSWORD': 'dev_password_change_in_prod',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
    }
}
```

3. Run Migrations
```
cd ~/StartupWebApp/startup_web_app_server_side/StartupWebApp
python3 manage.py migrate
```

**Note**: The migrations automatically create required Skuinventory reference records (In Stock, Back Ordered, Out of Stock). See migration `0002_add_default_inventory_statuses.py` for details.

3. Load sample data (recommended for development/testing):
```
python3 manage.py load_sample_data
```

This management command creates:
- 3 sample products (Paper Clips, Binder Clips, Rubber Bands)
- 6 SKUs with prices and images
- Shipping methods, discount codes, order configuration
- User data (terms of use, email types, ad types)
- Client event configuration

**Alternative**: You can manually load data from [db_inserts.sql](./db_inserts.sql) (legacy MySQL format), but the management command is recommended as it's database-agnostic and includes all required data.

4. OPTIONAL: Create admin user. You need to do this to access the Django Admin site which is referenced below.
Follow the instructions in the [Django documentation to create this user](https://docs.djangoproject.com/en/4.2/intro/tutorial02/#creating-an-admin-user)
```
python3 manage.py createsuperuser
```

**Important**: When creating users via `createsuperuser`, you must also create an associated Member record for the user to avoid application errors. See the codebase or use the Django admin interface to create Member records.

### Running the Local Server
```
cd ~/StartupWebApp/startup_web_app_server_side/StartupWebApp
python3 manage.py runserver
```

#### Access the Django Admin Site
Go to http://localapi.startupwebapp.com:8000/admin/

#### Test that the API is responding: 
Go to http://localapi.startupwebapp.com:8000/user/logged-in
Expected result: {"logged_in": false, "log_client_events": true, "client_event_id": "null", "cart_item_count": 0, "user-api-version": "0.0.1"}

## Running tests

This application contains Selenium functional tests and python/Django unit tests.

### Run Selenium Functional Tests

**Note**: All functional tests should be run with `HEADLESS=TRUE` to run Firefox in headless mode.

```
cd ~/StartupWebApp/startup_web_app_server_side/StartupWebApp
```
- run all tests
```
HEADLESS=TRUE python3 manage.py test functional_tests
```
- run one module of tests
```
HEADLESS=TRUE python3 manage.py test functional_tests/home
```
- run one specific test
```
HEADLESS=TRUE python3 manage.py test functional_tests.global.test_global_elements.AnonymousGlobalNavigationTests.test_header
HEADLESS=TRUE python3 manage.py test functional_tests.pythonabot.test_pythonabot.PythonABotPageFunctionalTests
```

### Run Unit Tests
```
cd ~/StartupWebApp/startup_web_app_server_side/StartupWebApp
python3 manage.py test user order clientevent
```

### Run Code Coverage Stats
```
cd ~/StartupWebApp/startup_web_app_server_side/StartupWebApp
coverage run --source='.' manage.py test StartupWebApp
coverage report
```

## Application Funtional Instructions

### Sending Member and Prospect Emails
Members will only receive emails if: 
1. Newsletter subscriber is True
2. Email unsubscribed is False

Prospects will only receive emails if:
1. Email unsubscribed is False

Steps to create a Prospect:
1. In Django Admin go to Home->User->Prospects
2. Add new prospect
3. Select Checkbox next to Prospect and in Actions select "Populate Prospect Codes". This will populate the pr_cd value for any selected prospect whose value is unset/null. This is required for email and ad link tracking to work correctly. 

Steps to send email: 
1. In Django Admin go to Home->User->Emails
2. Create a new Email instance
	1. Subject: Text that will show in the subject of the email
	2. Email Type: Select Prospect or Member as appropriate
	3. Email Status: Start with Draft. 
	4. Body html: Paste in the html version of the email. 
	5. Body html: Paste in the text version of the email. 
	6. From address: contact@startupwebapp.com
	7. Bcc address: contact@startupwebapp.com
3. Select Checkbox next to Draft status email and in Actions select "Populate Email Codes". This will populate the em_cd value for any selected email whose value is unset/null. This is required for link tracking to work correctly. 
4. Select Checkbox next to Draft status email and in Actions select "Send Draft Email". This will send a draft version of this email to 'contact@startupwebapp.com'. 
5. Change the email status to "Ready" once testing of the email is complete. 
	1. Make sure to test link tracking and unsubscribe. 
	2. Test all links in the email for tracking. 
6. Select Checkbox next to Ready status email and in Actions select "Send Ready Email to Recipients". This will send a real email to recipients and the Bcc email from the From email address for that email. 
7. Confirm that the email status changed to "Sent"
8. Confirm that the Bcc email address received the emails as expected. 

### Using Discount Codes
Create a new record in table order_discount_code
- id: auto-increment
- code: This is the discount code users and members will actually see and type into the shopping cart page
- description: This is the "Value" that users see when they've successfully entered a discount code on the shopping cart page
- start_date_time: This is the time at which the discount code will become valid and apply to cart and order
- end_date_time: This is the time at which the discount code will no longer be valid and will not apply to cart and order
- combinable: boolean. True means that this discount can be combined with any other discount. False means that this discount can't be combined with any other discount which is also NOT combinable. 
- discount_amount: The meaning of this field depends on the discount type. If type is "percent-off" then this field is the percent discount. If type is "dollar-amt-off" then this field is the dollar amount discount. 
- discounttype_id: FK to order_discount_type
- order_minimum: Discount will not apply unless the item_subtotal is >= to this amount

### Setting Up Products and Skus
1. Create order_product records. 
	- All fields except for description_part_2 are required. 
	- Use this link to [generate 10 character (upper, lower, digit) random identifiers](https://www.random.org/strings/?num=10&len=10&digits=on&upperalpha=on&loweralpha=on&unique=on&format=html&rnd=new)
2. Create order_product_image records. 
	- Select the product 
	- Provide the relative `/img/` or full image path `https://img.startupwebapp.com/product/...`
	- Select if this is the main image for this product. There can only be one main image. The DB doesn't enforce this constraint so make sure you don't screw this up. 
	- Provide an optional caption for the image.
3. Create order_sku records. 
	- Sku type will be 'product'
	- Select appropriate sku inventory value
	- Color, Size and Description are all optional but recommended.
4. Create order_sku_price record for each sku.
	- Select appropriate sku
	- Set price
	- select today and now for Created date time (the last date is used to determine price)
5. Create order_product_sku record for each sku.
	- Select the appropriate product
	- Select the appropriate sku
	- Note that DB enforces unique combos. 
6. Create order_sku_image record for each sku (optional)
	- Select Sku
	- Provide the relative `/img/` or full image path `https://img.startupwebapp.com/product/sku/...`
	- Select if this is the main image for this sku. There can only be one main image. The DB doesn't enforce this constraint so make sure you don't screw this up.
	- Provide an optional caption for the image.

</details>

---

## Authors

* **Bart Gottschalk** - *Initial work* - [BartGottschalk](https://github.com/BartGottschalk)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE.md](LICENSE.md) file for details
