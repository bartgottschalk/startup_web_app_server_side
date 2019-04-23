# startup_web_app_server_side
I'm co-founder of a startup which

1. Produces and sells a relatively small quantity of a relatively high number of customizable physical products, and
2. Has future plans to build a complementary digital product. 

Soon after jumping into this idea it was clear we would need a web application to support our product's discovery, selection, customization, purchase and interactive experiences. We looked at using existing marketplaces and web-site building platforms such as Squarespace or Wix. These didn't work for us for a couple of reasons

1. The customizable nature of our products
2. The large number of individual skus we would be managing
3. Our customers can create skus dynamically.

This made using “off-the-shelf” solutions unworkable, even for early prototyping and experimentation, and meant we needed to build a custom web application. Among our non-functional requirements were things like

1. The ability to iterate quickly
2. Security
3. Reliability
4. Support growth and scalability (reasonably)
5. Support future iterative exploration of our digital product
6. Can’t be so costly that it sinks the business. 

As the only technical co-founder, it landed on me to "figure this out." 

This repository contains a simplified version of the server side application I built to launch our startup. To learn more about this project you can check out [slides from a talk I gave about this project](https://docs.google.com/presentation/d/18Y_G3asKbeys7s5618N_VJkXCI0ePwJ0vKB_06c-P3w/edit#slide=id.g5820c97b01_0_114) 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for experimentation and/or development purposes. 

### Prerequisites

You will need the following python packages and tools installed:

#### For the Server application to function
- [Python 3.x](https://www.python.org/downloads/)
- A database to use with Django. [MySQL](https://dev.mysql.com/doc/refman/8.0/en/installing.html), [Postgres](https://www.postgresql.org/docs/11/tutorial-install.html), [SqlLite](https://sqlite.org/download.html) or other of your choice.
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [configparser](https://pypi.org/project/configparser/)
- [django](https://docs.djangoproject.com/en/2.2/topics/install/)
- [django-cors-headers](https://pypi.org/project/django-cors-headers/)
- [django-import-export](https://pypi.org/project/django-import-export/)
- [titlecase](https://pypi.org/project/titlecase/)
- [stripe](https://stripe.com/docs/libraries#python)

#### For the Selenium functional tests and unit test coverage report to function
- [SqlLite](https://sqlite.org/download.html)
- [firefox](https://support.mozilla.org/en-US/products/firefox/install-and-update-firefox)
- [geckodriver](https://github.com/mozilla/geckodriver/releases)
- [coverage](https://coverage.readthedocs.io/en/v4.5.x/install.html)
- [selenium](https://pypi.org/project/selenium/)

### Installing the Application

#### Install from Github
Note: These instructions assume that you will install the application at `~/StartupWebApp`. If you select another location you will need to adjust all other commands accordingly.  

```
cd ~/StartupWebApp
git clone `https://github.com/bartgottschalk/startup_web_app_server_side.git`
cd ~/StartupWebApp/startup_web_app_server_side
```

#### Configure Hosts File
Configure hosts file to route 
- localapi.startupwebapp.com to 127.0.0.1
- localliveservertestcaseapi.startupwebapp.com to 127.0.0.1 (this will be used to run Selenium functional tests)

#### Database Setup
1. Create local DB (Note: Commands are for MySQL)
```
CREATE DATABASE startupwebapp CHARACTER SET latin1 COLLATE latin1_swedish_ci;
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, REFERENCES, INDEX, ALTER ON `startupwebapp `.* TO 'django_super'@'localhost';
```
2. Run Migrations
```
cd ~/StartupWebApp/startup_web_app_server_side/StartupWebApp
python3 manage.py migrate
```
3. Create data records that are required for application to function. 
These are all included in the file [db_inserts.sql](./db_inserts.sql) in this repository. Run these inserts against the database you created in step 1 above. 

4. OPTIONAL: Create admin user. You need to do this to access the Django Admin site which is referenced below.
Follow the instructions in the [Django documentation to create this user](https://docs.djangoproject.com/en/2.2/intro/tutorial02/#creating-an-admin-user)
```
python3 manage.py createsuperuser
```

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
Config is in settings.py
Token is acquired from api server via GET request to http://localapi.startupwebapp.com/user/token
This GET request returns both a token embedded in JSON as well as a cookie containing a token. The application uses the cookie token in javascript and returns it in a Request header "X-CSRFToken". The token returned in JSON is ignored. 

##### settings_secret.py from settings_secret.py.template
```
cp settings_secret.py.template settings_secret.py
```
edit values in setting_secret.py to match your environment, database and 3rd party integrations
review and edit values in settings.py to match your environment and 3rd party integrations

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
```
cd ~/StartupWebApp/startup_web_app_server_side/StartupWebApp
```
- run all tests
`python3 manage.py test functional_tests`
- run one module of tests
`python3 manage.py test functional_tests/home`
- run one specific test
`python3 manage.py test functional_tests.global.test_global_elements.AnonymousGlobalNavigationTests.test_header`

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
	6. From address: me@startupwebapp.com
	7. Bcc address: me@startupwebapp.com
3. Select Checkbox next to Draft status email and in Actions select "Populate Email Codes". This will populate the em_cd value for any selected email whose value is unset/null. This is required for link tracking to work correctly. 
4. Select Checkbox next to Draft status email and in Actions select "Send Draft Email". This will send a draft version of this email to 'me@startupwebapp.com'. 
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

## Authors

* **Bart Gottschalk** - *Initial work* - [BartGottschalk](https://github.com/BartGottschalk)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE.md](LICENSE.md) file for details
