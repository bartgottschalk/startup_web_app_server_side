from django.conf import settings
import time
# import boto3  # Commented out - not used in any tests
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

MAX_WAIT = 10

def wait_for_element_by_id_text_value(context, id, expected_value):
	start_time = time.time()
	while True:
		new_value = context.browser.find_element(By.ID, id).text
		if expected_value == new_value:
			return True
		else:
			if time.time() - start_time > MAX_WAIT: 
				raise TimeoutError('The text value equality was not found before MAX_WAIT reached! expected_value=' + expected_value + ' - new_value=' + str(new_value))
			time.sleep(0.5)

def wait_for_element_by_class_name_text_value(context, class_name, expected_value):
	start_time = time.time()
	while True:
		new_value = context.browser.find_element(By.CLASS_NAME, class_name).text
		if expected_value == new_value:
			return True
		else:
			if time.time() - start_time > MAX_WAIT: 
				raise TimeoutError('The text value equality was not found before MAX_WAIT reached! expected_value=' + expected_value + ' - new_value=' + str(new_value))
			time.sleep(0.5)

def wait_for_page_title(context, expected_value):
	start_time = time.time()
	while True:
		if expected_value == context.browser.title:
			return True
		else:
			if time.time() - start_time > MAX_WAIT: 
				raise TimeoutError('The page title was not found before MAX_WAIT reached!')
			time.sleep(0.5)

def wait_for_element_to_display_by_id(context, id):
	start_time = time.time()
	while True:
		display_val = context.browser.find_element(By.ID, id).value_of_css_property('display')
		if display_val == 'block':
			return True
		else:
			if time.time() - start_time > MAX_WAIT: 
				raise TimeoutError('The display property was not set to block before MAX_WAIT reached! expected_value=' + expected_value + ' - new_value=' + str(new_value))
			time.sleep(0.5)

def wait_for_element_to_load_by_id(context, id):
	start_time = time.time()
	while True:
		try:
			context.browser.find_element(By.ID, id)
			return
		except (AssertionError, WebDriverException) as e:
			if time.time() - start_time > MAX_WAIT: 
				raise e
			time.sleep(0.5)

def wait_for_element_to_load_by_class_name(context, class_name):
	start_time = time.time()
	while True:
		try:
			context.browser.find_element(By.CLASS_NAME, class_name)
			return
		except (AssertionError, WebDriverException) as e:
			if time.time() - start_time > MAX_WAIT: 
				raise e
			time.sleep(0.5)

def wait_click_by_id(context, id):
	start_time = time.time()
	while True:
		try:
			context.browser.find_element(By.ID, id).click()
			return
		except (AssertionError, WebDriverException) as e:
			if time.time() - start_time > MAX_WAIT: 
				raise e
			time.sleep(0.5)

def wait_click_by_class_name(context, class_name):
	start_time = time.time()
	while True:
		try:
			context.browser.find_element(By.CLASS_NAME, class_name).click()
			return
		except (AssertionError, WebDriverException) as e:
			if time.time() - start_time > MAX_WAIT: 
				raise e
			time.sleep(0.5)

def wait_for_shopping_cart_count(context, count_val, count_text):
	start_time = time.time()
	while True:
		try:
			shopping_cart_element = context.browser.find_element(By.ID, 'header-shopping-cart')
			context.assertEqual(shopping_cart_element.find_element(By.ID, 'cart-item-count-wrapper').get_attribute("title"), count_text)
			context.assertEqual(shopping_cart_element.find_element(By.ID, 'cart-item-count-wrapper').text, count_val)
			return
		except (AssertionError, WebDriverException) as e:
			if time.time() - start_time > MAX_WAIT: 
				raise e
			time.sleep(0.5)

def wait_for_welcome_image_carousel(context, href_val, text_val, src_val):
	start_time = time.time()
	while True:
		try:
			context.assertIn(href_val, context.browser.find_element(By.ID, 'welcome-image-carousel-link').get_attribute("href"))
			context.assertEqual(context.browser.find_elements(By.CLASS_NAME, 'welcome-image-carousel-quote-container')[0].text, text_val)
			context.assertEqual(context.browser.find_elements(By.CLASS_NAME, 'welcome-image-carousel-image')[0].get_attribute("alt"), text_val)
			context.assertEqual(context.browser.find_elements(By.CLASS_NAME, 'welcome-image-carousel-image')[0].get_attribute("src"), src_val)
			return
		except (AssertionError, WebDriverException) as e:
			if time.time() - start_time > MAX_WAIT: 
				raise e
			time.sleep(0.5)

def wait_for_new_window_handle(context, previous_window_handles):
	start_time = time.time()
	while True:
		new_window_handles = context.browser.window_handles
		if previous_window_handles == new_window_handles:
			if time.time() - start_time > MAX_WAIT: 
				raise TimeoutError('The new window handler was not found before MAX_WAIT reached!')
			time.sleep(0.5)
		else:
			return list(set(new_window_handles) - set(previous_window_handles))[0]

# These S3 functions are not used in any functional tests (only commented out reference exists)
# If needed in the future, uncomment and add boto3 to requirements.txt
#
# def setupS3Connection():
#     session = boto3.Session(profile_name='aws-sdk-user')
#     # Any clients created from this session will use credentials
#     # from the [dev] section of ~/.aws/credentials.
#     s3 = session.resource('s3')
#     return s3
#
# def putPDFOnS3(file_path, file_name):
#     #print('setup S3 Connection')
#     s3 = setupS3Connection()
#
#     # put PDF On S3
#     data = open(file_path + file_name, 'rb')
#     s3.Bucket(settings.S3_FUNCTIONAL_TESTING_BUCKET_NAME).put_object(Key=settings.S3_FUNCTIONAL_TESTING_BUCKET_PATH + file_name, Body=data, ContentType='image/png', CacheControl='max-age=1')
#
#     location = settings.S3_FUNCTIONAL_TESTING_DOMAIN + "/" + settings.S3_FUNCTIONAL_TESTING_BUCKET_NAME + file_name
#     print('location is: ' + location)


