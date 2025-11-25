# Selenium Functional Tests (from the perspective of the user)

import os

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from datetime import timedelta

from django.utils import timezone
from django.test import LiveServerTestCase
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from user.models import Member, Termsofuse, Emailtype, Emailstatus, Adtype, Adstatus
from order.models import Orderconfiguration, Cart, Cartsku, Skutype, Skuinventory, Product, Sku, Skuprice, Productsku, Status, Orderstatus, Shippingmethod, Discounttype, Discountcode

class BaseFunctionalTest(LiveServerTestCase):
	# class variables
	options = Options()
	if "HEADLESS" in os.environ and os.environ['HEADLESS'] == 'TRUE':
		options.headless = True
	host = '0.0.0.0'  # Bind to all interfaces so test server is accessible via Docker network hostname 'backend'
	port = 60767 # hardcoding the port so that I can access the LiveServerTestCase API from the staticically deployed client at a predictable url:port combo
	yesterday = start_date_time=timezone.now() - timedelta(days=1)
	tomorrow = start_date_time=timezone.now() + timedelta(days=1)
	# Use localliveservertestcase.startupwebapp.com for cookie sharing between frontend and backend
	# Two environments supported:
	# 1. CI (CI_ENV=true): Frontend on port 8080, backend on port 60767 (like local dev)
	# 2. Docker (DOCKER_ENV=true): Frontend on port 80 (internal), backend on port 60767
	if os.environ.get('CI_ENV'):
		static_home_page_url = "http://localliveservertestcase.startupwebapp.com:8080/"
	elif os.environ.get('DOCKER_ENV'):
		static_home_page_url = "http://localliveservertestcase.startupwebapp.com/"
	else:
		# Fallback for local development outside Docker (port 8080)
		static_home_page_url = "http://localliveservertestcase.startupwebapp.com:8080/"

	def setUp(self):
		self.browser = webdriver.Firefox(options=self.options)
		self._test_passed = True  # Track test success for debugging

		# Debug: Verify LiveServerTestCase backend is running (CI only)
		if os.environ.get('CI_ENV'):
			import socket
			print(f"\n[DEBUG] Testing LiveServerTestCase connectivity...")
			print(f"[DEBUG] Host: {self.host}, Port: {self.port}")
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.settimeout(2)
				result = sock.connect_ex(('127.0.0.1', self.port))
				sock.close()
				if result == 0:
					print(f"[DEBUG] ✓ Port {self.port} is open and accepting connections")
				else:
					print(f"[DEBUG] ✗ Port {self.port} is NOT accepting connections (error code: {result})")
			except Exception as e:
				print(f"[DEBUG] ✗ Socket test failed: {e}")

		# Setup necessary DB Objects
		ClientEventConfiguration.objects.create(id=1, log_client_events=True)

		Group.objects.create(name='Members')
		Termsofuse.objects.create(version='1', version_note='Specifically, we\'ve modified our <a class=\"raw-link\" href=\"/privacy-policy\">Privacy Policy</a> and <a class=\"raw-link\" href=\"/terms-of-sale\">Terms of Sale</a>. Modifications include...', publication_date_time=timezone.now())

		Emailtype.objects.create(title='Member')
		Emailtype.objects.create(title='Prospect')
		Emailstatus.objects.create(title='Draft')
		Emailstatus.objects.create(title='Ready')
		Emailstatus.objects.create(title='Sent')

		Adtype.objects.create(title='Google AdWords')
		Adtype.objects.create(title='Facebook')
		Adstatus.objects.create(title='Draft')
		Adstatus.objects.create(title='Ready')
		Adstatus.objects.create(title='Running')
		Adstatus.objects.create(title='Stopped')

		Status.objects.create(identifier='accepted', title='Accepted', description='The order has been accepted and is being processed.')
		Status.objects.create(identifier='manufacturing', title='Manufacturing', description='Custom items in the order are being manufactured.')
		Status.objects.create(identifier='packing', title='Packing', description='The order is being packed for shipment.')
		Status.objects.create(identifier='shipped', title='Shipped', description='The order has been shipped.')

		Shippingmethod.objects.create(carrier='USPS Priority Mail 2-Day', shipping_cost='13.65', tracking_code_base_url='https://tools.usps.com/go/TrackConfirmAction.action?tRef=fullpage&tLc=1&text28777=&tLabels=', active=True, identifier='USPSPriorityMail2Day')
		Shippingmethod.objects.create(carrier='USPS Retail Ground', shipping_cost='9.56', tracking_code_base_url='https://tools.usps.com/go/TrackConfirmAction.action?tRef=fullpage&tLc=1&text28777=&tLabels=', active=True, identifier='USPSRetailGround')
		Shippingmethod.objects.create(carrier='FedEx Ground', shipping_cost='10.85', tracking_code_base_url='https://www.fedex.com/apps/fedextrack/?action=track&cntry_code=us&trackingnumber=', active=True, identifier='FedExGround')
		Shippingmethod.objects.create(carrier='UPS Ground', shipping_cost='11.34', tracking_code_base_url='https://wwwapps.ups.com/WebTracking/track?&track.x=Track&trackNums=', active=True, identifier='UPSGround')
		Shippingmethod.objects.create(carrier='None', shipping_cost='0.00', tracking_code_base_url='none', active=True, identifier='None')

		Discounttype.objects.create(title='Save Percent Off Your Item Total', description='Take {}% off your item total', applies_to='item_total', action='percent-off')
		Discounttype.objects.create(title='Save Dollar Amount Off Your Item Total', description='Save ${} on your item total', applies_to='item_total', action='dollar-amt-off')
		Discounttype.objects.create(title='Free Months Digital Subscription', description='Get {} months of free digital subscription with your order', applies_to='subscription', action='free-digital-months')
		Discounttype.objects.create(title='Free USPS Retail Ground Shipping', description='Free USPS Retail Ground shipping on your order', applies_to='shipping', action='free-usps-ground-shipping')

		Discountcode.objects.create(code='APRIL50PERCENT', description='50% off your item total in April', start_date_time=self.yesterday, end_date_time=self.tomorrow, combinable=False, discount_amount='50', discounttype=Discounttype.objects.get(action='percent-off'), order_minimum='0')
		Discountcode.objects.create(code='APRILSAVER', description='Get $10 off your order of $20 or more in April', start_date_time=self.yesterday, end_date_time=self.tomorrow, combinable=False, discount_amount='10', discounttype=Discounttype.objects.get(action='dollar-amt-off'), order_minimum='20')
		Discountcode.objects.create(code='FREE3MONTHS', description='Get 3 free months subscription to our digital services', start_date_time=self.yesterday, end_date_time=self.tomorrow, combinable=True, discount_amount='3', discounttype=Discounttype.objects.get(action='free-digital-months'), order_minimum='0')
		Discountcode.objects.create(code='FREESHIPPING', description='Get free USPS Retail Ground shipping on all orders', start_date_time=self.yesterday, end_date_time=self.tomorrow, combinable=True, discount_amount='100', discounttype=Discounttype.objects.get(action='free-usps-ground-shipping'), order_minimum='0')
		Discountcode.objects.create(code='AUG50PERCENT', description='50% off your item total in August!', start_date_time=self.yesterday, end_date_time=self.tomorrow, combinable=False, discount_amount='50', discounttype=Discounttype.objects.get(action='percent-off'), order_minimum='0')
		Discountcode.objects.create(code='AUGSAVER', description='Get $10 off your order of $20 or more in August!', start_date_time=self.yesterday, end_date_time=self.tomorrow, combinable=False, discount_amount='10', discounttype=Discounttype.objects.get(action='dollar-amt-off'), order_minimum='20')
		Discountcode.objects.create(code='SEPT50PERCENT', description='50% off your item total in September!', start_date_time=self.yesterday, end_date_time=self.tomorrow, combinable=False, discount_amount='50', discounttype=Discounttype.objects.get(action='percent-off'), order_minimum='0')
		Discountcode.objects.create(code='SEPTSAVER', description='Get $10 off your order of $20 or more in September!', start_date_time=self.yesterday, end_date_time=self.tomorrow, combinable=False, discount_amount='10', discounttype=Discounttype.objects.get(action='dollar-amt-off'), order_minimum='20')

		Skutype.objects.create(id=1, title='product')
		Skuinventory.objects.create(id=1, title='In Stock', identifier='in-stock', description='In Stock items are available to purchase.')
		Skuinventory.objects.create(id=2, title='Back Ordered', identifier='back-ordered', description='Back Ordered items are not available to purchase at this time.')
		Skuinventory.objects.create(id=3, title='Out of Stock', identifier='out-of-stock', description='Out of Stock items are not available to purchase.')

		Product.objects.create(id=1, title='Paper Clips', title_url='PaperClips', identifier='bSusp6dBHm', headline='Paper clips can hold up to 20 pieces of paper together!', description_part_1='Made out of high quality metal and folded to exact specifications.', description_part_2='Use paperclips for all your paper binding needs!')
		Sku.objects.create(id=1, color='Silver', size='Medium', sku_type_id=1, description='Left Sided Paperclip', sku_inventory_id=1)
		Skuprice.objects.create(id=1, price=3.5, created_date_time=timezone.now(), sku_id=1)
		Productsku.objects.create(id=1, product_id=1, sku_id=1)

		# Debug: Verify backend API is responding (CI only)
		if os.environ.get('CI_ENV'):
			import urllib.request
			import urllib.error
			api_url = f"http://localliveservertestcaseapi.startupwebapp.com:{self.port}/user/logged-in"
			print(f"\n[DEBUG] Testing backend API endpoint: {api_url}")
			try:
				req = urllib.request.Request(api_url)
				response = urllib.request.urlopen(req, timeout=5)
				print(f"[DEBUG] ✓ Backend API responding (status: {response.status})")
				response_data = response.read().decode('utf-8')
				print(f"[DEBUG] Response preview: {response_data[:200]}")
			except urllib.error.HTTPError as e:
				print(f"[DEBUG] ✗ Backend API returned HTTP error: {e.code} {e.reason}")
			except urllib.error.URLError as e:
				print(f"[DEBUG] ✗ Backend API connection failed: {e.reason}")
			except Exception as e:
				print(f"[DEBUG] ✗ Backend API test failed: {e}")



	def run(self, result=None):
		"""Override run to capture test failure status"""
		test_result = super().run(result)
		# If test had errors or failures, mark as failed for tearDown
		if result and (result.errors or result.failures):
			self._test_passed = False
		return test_result

	def _capture_debug_info(self):
		"""Capture browser console logs and take screenshot on test failure"""
		if not self._test_passed and os.environ.get('CI_ENV'):
			print("\n" + "="*80)
			print("DEBUG INFO - Test Failed in CI Environment")
			print("="*80)

			# Capture current URL
			try:
				print(f"Current URL: {self.browser.current_url}")
			except Exception as e:
				print(f"Could not get current URL: {e}")

			# Capture page title
			try:
				print(f"Page Title: {self.browser.title}")
			except Exception as e:
				print(f"Could not get page title: {e}")

			# Capture browser console logs
			try:
				print("\n--- Browser Console Logs ---")
				logs = self.browser.get_log('browser')
				if logs:
					for log in logs:
						print(f"[{log['level']}] {log['message']}")
				else:
					print("No browser console logs found")
			except Exception as e:
				print(f"Could not retrieve browser logs: {e}")

			# Capture page source (first 1000 chars)
			try:
				print("\n--- Page Source (first 1000 chars) ---")
				page_source = self.browser.page_source
				print(page_source[:1000])
			except Exception as e:
				print(f"Could not get page source: {e}")

			# Check if cart element exists in DOM
			try:
				print("\n--- Cart Element Check ---")
				cart_wrapper = self.browser.find_elements_by_id('cart-item-count-wrapper')
				if cart_wrapper:
					print(f"cart-item-count-wrapper FOUND: {cart_wrapper[0].get_attribute('outerHTML')}")
				else:
					print("cart-item-count-wrapper NOT FOUND in DOM")
					# Check if header-shopping-cart exists
					header_cart = self.browser.find_elements_by_id('header-shopping-cart')
					if header_cart:
						print(f"header-shopping-cart exists: {header_cart[0].get_attribute('innerHTML')[:200]}")
					else:
						print("header-shopping-cart NOT FOUND either")
			except Exception as e:
				print(f"Could not check cart element: {e}")

			# Take screenshot
			try:
				test_name = self.id().split('.')[-1]
				screenshot_path = f"/tmp/test_failure_{test_name}.png"
				self.browser.save_screenshot(screenshot_path)
				print(f"\nScreenshot saved to: {screenshot_path}")
			except Exception as e:
				print(f"Could not save screenshot: {e}")

			print("="*80 + "\n")

	def tearDown(self):
		self._capture_debug_info()
		self.browser.quit()


