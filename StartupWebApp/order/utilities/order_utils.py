from order.models import (
    Ordersku, Orderdiscount, Orderstatus, Ordershippingmethod
)
from order.models import (
    Orderconfiguration, Skuprice, Skuimage, Cart, Cartsku, Cartdiscount,
    Productsku, Productimage, Cartshippingmethod
)
from StartupWebApp.utilities import random
from django.conf import settings
import stripe
import logging
stripe.api_key = settings.STRIPE_SERVER_SECRET_KEY
stripe.log = settings.STRIPE_LOG_LEVEL

logger = logging.getLogger(__name__)


def checkout_allowed(request):
    an_ct_values_allowed_to_checkout = Orderconfiguration.objects.get(
        key='an_ct_values_allowed_to_checkout').string_value
    if an_ct_values_allowed_to_checkout is not None:
        an_ct_values_allowed_to_checkout_arr = an_ct_values_allowed_to_checkout.split(',')
    else:
        an_ct_values_allowed_to_checkout_arr = []
    usernames_allowed_to_checkout = Orderconfiguration.objects.get(
        key='usernames_allowed_to_checkout').string_value
    if usernames_allowed_to_checkout is not None:
        usernames_allowed_to_checkout_arr = usernames_allowed_to_checkout.split(',')
    else:
        usernames_allowed_to_checkout_arr = []

    checkout_allowed = False
    if request.user.is_authenticated:
        for username in usernames_allowed_to_checkout_arr:
            if username == "*":
                checkout_allowed = True
                break
            elif str(username) == str(request.user.username):
                checkout_allowed = True
                break
    else:
        signed_cookie = request.get_signed_cookie(
            key='an_ct', default=False, salt='anonymouscartcookieisthis')
        for an_ct in an_ct_values_allowed_to_checkout_arr:
            if str(an_ct) == "*":
                checkout_allowed = True
                break
            elif str(an_ct) == str(signed_cookie):
                checkout_allowed = True
                break

    return checkout_allowed


def get_cart_items(request, cart):
    cart_item_dict = {}

    if cart is not None:
        product_sku_dict = {}
        counter = 0
        for cartsku in Cartsku.objects.filter(cart=cart):
            if cartsku.sku.sku_type.title == 'product':
                sku_data = {}
                sku_data['sku_id'] = cartsku.sku.id
                sku_data['sku_type__title'] = cartsku.sku.sku_type.title
                sku_data['sku_inventory__title'] = cartsku.sku.sku_inventory.title
                sku_data['sku_inventory__identifier'] = cartsku.sku.sku_inventory.identifier
                sku_data['color'] = cartsku.sku.color
                sku_data['size'] = cartsku.sku.size
                sku_data['description'] = cartsku.sku.description
                sku_data['price'] = Skuprice.objects.filter(
                    sku=cartsku.sku).latest('created_date_time').price
                sku_data['quantity'] = cartsku.quantity
                sku_data['parent_product__title'] = Productsku.objects.get(
                    sku=cartsku.sku).product.title
                sku_data['parent_product__title_url'] = Productsku.objects.get(
                    sku=cartsku.sku).product.title_url
                sku_data['parent_product__identifier'] = Productsku.objects.get(
                    sku=cartsku.sku).product.identifier
                sku_image_main_exists = Skuimage.objects.filter(
                    sku=cartsku.sku, main_image=True).exists()
                sku_image_url = None
                if sku_image_main_exists is True:
                    sku_image_url = Skuimage.objects.get(sku=cartsku.sku, main_image=True).image_url
                else:
                    sku_image_url = Productimage.objects.get(
                        product=Productsku.objects.get(
                            sku=cartsku.sku).product, main_image=True).image_url
                sku_data['sku_image_url'] = sku_image_url
                product_sku_dict[counter] = sku_data
                counter += 1
        cart_item_dict['product_sku_data'] = product_sku_dict
    return cart_item_dict


def create_cart(request):
    if request.user.is_authenticated:
        cart = Cart.objects.create(member=request.user.member)
    else:
        cart = Cart.objects.create()
    return cart


def set_anonymous_cart_cookie(request, response, cart):
    if not request.user.is_authenticated:
        from django.conf import settings
        cookie_value = random.getRandomString(20, 20)
        cart.anonymous_cart_id = cookie_value
        cart.save()
        # Only set domain in production (DEBUG=False) to allow cookies to work with localhost
        domain = '.startupwebapp.com' if not settings.DEBUG else None
        response.set_signed_cookie(
            key='an_ct',
            value=cookie_value,
            salt='anonymouscartcookieisthis',
            max_age=31536000,
            expires=None,
            path='/',
            domain=domain,
            secure=None,
            httponly=False)


def look_up_cart(request):
    cart = None
    logger.debug(f'User authenticated status: {request.user.is_authenticated}')
    if request.user.is_authenticated:
        member_cart_exists = Cart.objects.filter(member=request.user.member).exists()
        if member_cart_exists is True:
            cart = Cart.objects.get(member=request.user.member)
    else:
        signed_cookie = request.get_signed_cookie(
            key='an_ct', default=False, salt='anonymouscartcookieisthis')
        anonymous_cart_exists = Cart.objects.filter(anonymous_cart_id=signed_cookie).exists()
        if anonymous_cart_exists is True:
            cart = Cart.objects.get(anonymous_cart_id=signed_cookie)
    return cart


def look_up_member_cart(request):
    cart = None
    member_cart_exists = Cart.objects.filter(member=request.user.member).exists()
    if member_cart_exists is True:
        cart = Cart.objects.get(member=request.user.member)
    return cart


def look_up_anonymous_cart(request):
    cart = None
    signed_cookie = request.get_signed_cookie(
        key='an_ct', default=False, salt='anonymouscartcookieisthis')
    anonymous_cart_exists = Cart.objects.filter(anonymous_cart_id=signed_cookie).exists()
    if anonymous_cart_exists is True:
        cart = Cart.objects.get(anonymous_cart_id=signed_cookie)
    return cart


def get_cart_discount_codes(cart):
    noncombinable_found = False
    discount_code_dict = {}
    if cart is not None:
        for cartdiscount in Cartdiscount.objects.filter(cart=cart):
            discount_code_data = {}
            discount_code_data['discount_code_id'] = cartdiscount.discountcode.id
            discount_code_data['code'] = cartdiscount.discountcode.code
            discount_code_data['description'] = cartdiscount.discountcode.description
            discount_code_data['start_date_time'] = cartdiscount.discountcode.start_date_time
            discount_code_data['end_date_time'] = cartdiscount.discountcode.end_date_time
            discount_code_data['combinable'] = cartdiscount.discountcode.combinable
            discount_code_data['discount_amount'] = cartdiscount.discountcode.discount_amount
            discount_code_data['order_minimum'] = cartdiscount.discountcode.order_minimum
            discount_code_data['discounttype__title'] = cartdiscount.discountcode.discounttype.title
            discount_code_data['discounttype__description'] = cartdiscount.discountcode.discounttype.description
            discount_code_data['discounttype__applies_to'] = cartdiscount.discountcode.discounttype.applies_to
            discount_code_data['discounttype__action'] = cartdiscount.discountcode.discounttype.action

            if cartdiscount.discountcode.combinable:
                if calculate_item_subtotal(cart) >= cartdiscount.discountcode.order_minimum:
                    discount_code_data['discount_applied'] = True
                else:
                    discount_code_data['discount_applied'] = False
            else:  # non-combinable discount
                if noncombinable_found:
                    discount_code_data['discount_applied'] = False
                else:
                    noncombinable_found = True
                    if calculate_item_subtotal(cart) >= cartdiscount.discountcode.order_minimum:
                        discount_code_data['discount_applied'] = True
                    else:
                        discount_code_data['discount_applied'] = False

            discount_code_dict[cartdiscount.discountcode.id] = discount_code_data
    return discount_code_dict


def get_cart_totals(cart):
    cart_totals_dict = {}

    item_subtotal = calculate_item_subtotal(cart)

    if Cartshippingmethod.objects.filter(cart=cart).exists():
        shipping_subtotal = Cartshippingmethod.objects.get(cart=cart).shippingmethod.shipping_cost
    else:
        shipping_subtotal = 0

    item_discount = calculate_cart_item_discount(cart, item_subtotal)
    shipping_discount = calculate_shipping_discount(cart, item_subtotal)
    cart_total = item_subtotal - item_discount + shipping_subtotal - \
        (shipping_discount if shipping_discount is not None else 0)

    cart_totals_dict['item_subtotal'] = item_subtotal
    cart_totals_dict['item_discount'] = item_discount
    cart_totals_dict['shipping_subtotal'] = shipping_subtotal
    cart_totals_dict['shipping_discount'] = shipping_discount
    cart_totals_dict['cart_total'] = cart_total

    return cart_totals_dict


def get_stripe_customer_payment_data(customer, shipping_address, card_id):
    customer_payment_dict = {}
    if card_id is None:
        card_id = customer.default_source
    for source in customer.sources.data:
        if source.id == card_id:
            args = {}
            token = {}

            if shipping_address is not None:
                args['shipping_name'] = shipping_address['name']
                args['shipping_address_line1'] = shipping_address['address_line1']
                args['shipping_address_city'] = shipping_address['city']
                args['shipping_address_state'] = shipping_address['state']
                args['shipping_address_zip'] = shipping_address['zip']
                args['shipping_address_country'] = shipping_address['country']
                args['shipping_address_country_code'] = shipping_address['country_code']
            else:
                args['shipping_name'] = source.name
                args['shipping_address_line1'] = source.address_line1
                args['shipping_address_city'] = source.address_city
                args['shipping_address_state'] = source.address_state
                args['shipping_address_zip'] = source.address_zip
                args['shipping_address_country'] = source.address_country
                args['shipping_address_country_code'] = source.country
            args['billing_name'] = source.name
            args['billing_address_line1'] = source.address_line1
            args['billing_address_city'] = source.address_city
            args['billing_address_state'] = source.address_state
            args['billing_address_zip'] = source.address_zip
            args['billing_address_country'] = source.address_country
            args['billing_address_country_code'] = source.country
            card = {}
            card['name'] = source.name
            card['brand'] = source.brand
            card['last4'] = source.last4
            card['exp_month'] = source.exp_month
            card['exp_year'] = source.exp_year
            card['address_zip'] = source.address_zip
            token['card'] = card
            token['email'] = customer.email
            token['type'] = source.object
            customer_payment_dict['token'] = token
            customer_payment_dict['args'] = args
            break

    return customer_payment_dict


def load_address_dict(address):
    address_dict = {}
    address_dict['name'] = address.name
    address_dict['address_line1'] = address.address_line1
    address_dict['city'] = address.city
    address_dict['state'] = address.state
    address_dict['zip'] = address.zip
    address_dict['country'] = address.country
    address_dict['country_code'] = address.country_code
    return address_dict


def calculate_cart_item_discount(cart, item_subtotal):
    noncombinable_found = False
    item_discount = 0
    for cartdiscount in Cartdiscount.objects.filter(cart=cart):
        if cartdiscount.discountcode.discounttype.applies_to == 'item_total':
            if not cartdiscount.discountcode.combinable:
                if noncombinable_found:
                    pass
                else:
                    if item_subtotal >= cartdiscount.discountcode.order_minimum:
                        if cartdiscount.discountcode.discounttype.action == 'percent-off':
                            item_discount += item_subtotal * \
                                (cartdiscount.discountcode.discount_amount / 100)
                        if cartdiscount.discountcode.discounttype.action == 'dollar-amt-off':
                            item_discount += item_discount + cartdiscount.discountcode.discount_amount
                    else:
                        pass
                noncombinable_found = True
            elif cartdiscount.discountcode.combinable:
                pass
    return item_discount


def calculate_shipping_discount(cart, item_subtotal):
    shipping_discount = 0
    for cartdiscount in Cartdiscount.objects.filter(cart=cart):
        if cartdiscount.discountcode.discounttype.applies_to == 'shipping':
            if item_subtotal >= cartdiscount.discountcode.order_minimum:
                cart_shipping_method_exists = Cartshippingmethod.objects.filter(cart=cart).exists()
                if cart_shipping_method_exists is True:
                    cart_shipping_method = Cartshippingmethod.objects.get(cart=cart)
                    if cart_shipping_method.shippingmethod.identifier == 'USPSRetailGround':
                        shipping_discount = cart_shipping_method.shippingmethod.shipping_cost
                else:
                    shipping_discount = 0
            else:
                pass
    return shipping_discount


def calculate_item_subtotal(cart):
    item_subtotal = 0
    for cartsku in Cartsku.objects.filter(cart=cart):
        item_subtotal += (
            Skuprice.objects.filter(
                sku=cartsku.sku).latest('created_date_time').price *
            Cartsku.objects.get(
                cart=cart,
                sku=cartsku.sku).quantity)
    return item_subtotal


def count_cart_items(cart):
    item_count = 0
    for cartsku in Cartsku.objects.filter(cart=cart):
        item_count += 1
    return item_count


def get_order_data(order):
    order_data = {}
    order_data['order_attributes'] = get_order_attributes(order)
    order_data['order_items'] = get_order_items(order)
    order_data['order_shipping_method'] = get_order_shipping_method(order)
    order_data['order_discount_codes'] = get_order_discount_codes(order)
    order_data['order_totals'] = get_order_totals(order)
    order_data['order_statuses'] = get_order_statuses(order)
    order_data['order_shipping_address'] = get_order_shipping_address(order)
    order_data['order_billing_address'] = get_order_billing_address(order)
    order_data['order_payment_info'] = get_order_payment_info(order)
    return order_data


def get_order_attributes(order):
    order_attributes = {}
    order_attributes['identifier'] = order.identifier
    order_attributes['order_date_time'] = order.order_date_time
    order_attributes['sales_tax_amt'] = order.sales_tax_amt
    return order_attributes


def get_order_items(order):
    order_item_dict = {}

    product_sku_dict = {}
    counter = 0
    for ordersku in Ordersku.objects.filter(order=order):
        if ordersku.sku.sku_type.title == 'product':
            sku_data = {}
            sku_data['sku_id'] = ordersku.sku.id
            sku_data['sku_type__title'] = ordersku.sku.sku_type.title
            sku_data['sku_inventory__title'] = ordersku.sku.sku_inventory.title
            sku_data['color'] = ordersku.sku.color
            sku_data['size'] = ordersku.sku.size
            sku_data['description'] = ordersku.sku.description
            sku_data['price'] = ordersku.price_each
            sku_data['quantity'] = ordersku.quantity
            sku_data['parent_product__title'] = Productsku.objects.get(
                sku=ordersku.sku).product.title
            sku_data['parent_product__title_url'] = Productsku.objects.get(
                sku=ordersku.sku).product.title_url
            sku_data['parent_product__identifier'] = Productsku.objects.get(
                sku=ordersku.sku).product.identifier
            sku_image_main_exists = Skuimage.objects.filter(
                sku=ordersku.sku, main_image=True).exists()
            sku_image_url = None
            if sku_image_main_exists is True:
                sku_image_url = Skuimage.objects.get(sku=ordersku.sku, main_image=True).image_url
            else:
                sku_image_url = Productimage.objects.get(
                    product=Productsku.objects.get(
                        sku=ordersku.sku).product,
                    main_image=True).image_url
            sku_data['sku_image_url'] = sku_image_url
            product_sku_dict[counter] = sku_data
            counter += 1
    order_item_dict['product_sku_data'] = product_sku_dict
    return order_item_dict


def get_order_shipping_method(order):
    shipping_method = {}
    if Ordershippingmethod.objects.filter(order=order).exists():
        shipping_method_selected = Ordershippingmethod.objects.get(order=order).shippingmethod
        shipping_method['identifier'] = shipping_method_selected.identifier
        shipping_method['carrier'] = shipping_method_selected.carrier
        shipping_method['shipping_cost'] = shipping_method_selected.shipping_cost
        shipping_method['tracking_code_base_url'] = shipping_method_selected.tracking_code_base_url
    return shipping_method


def get_order_discount_codes(order):
    discount_code_dict = {}
    for orderdiscount in Orderdiscount.objects.filter(order=order):
        discount_code_data = {}
        discount_code_data['discount_code_id'] = orderdiscount.discountcode.id
        discount_code_data['code'] = orderdiscount.discountcode.code
        discount_code_data['description'] = orderdiscount.discountcode.description
        discount_code_data['start_date_time'] = orderdiscount.discountcode.start_date_time
        discount_code_data['end_date_time'] = orderdiscount.discountcode.end_date_time
        discount_code_data['combinable'] = orderdiscount.discountcode.combinable
        discount_code_data['discount_amount'] = orderdiscount.discountcode.discount_amount
        discount_code_data['order_minimum'] = orderdiscount.discountcode.order_minimum
        discount_code_data['discounttype__title'] = orderdiscount.discountcode.discounttype.title
        discount_code_data['discounttype__description'] = orderdiscount.discountcode.discounttype.description
        discount_code_data['discounttype__applies_to'] = orderdiscount.discountcode.discounttype.applies_to
        discount_code_data['discounttype__action'] = orderdiscount.discountcode.discounttype.action
        discount_code_data['discount_applied'] = orderdiscount.applied
        discount_code_dict[orderdiscount.discountcode.id] = discount_code_data
    return discount_code_dict


def get_order_totals(order):
    order_totals_dict = {}
    order_totals_dict['item_subtotal'] = order.item_subtotal
    order_totals_dict['item_discount'] = order.item_discount_amt
    order_totals_dict['shipping_subtotal'] = order.shipping_amt
    order_totals_dict['shipping_discount'] = order.shipping_discount_amt
    order_totals_dict['order_total'] = order.order_total
    return order_totals_dict


def get_order_statuses(order):
    statuses_dict = {}
    counter = 0
    for orderstatus in Orderstatus.objects.filter(order=order).order_by('-created_date_time'):
        status_data = {}
        status_data['identifier'] = orderstatus.status.identifier
        status_data['title'] = orderstatus.status.title
        status_data['description'] = orderstatus.status.description
        status_data['created_date_time'] = orderstatus.created_date_time
        statuses_dict[counter] = status_data
        counter += 1
    return statuses_dict


def get_order_shipping_address(order):
    shipping_address_dict = {}
    if order.shipping_address is not None:
        shipping_address_dict['name'] = order.shipping_address.name
        shipping_address_dict['address_line1'] = order.shipping_address.address_line1
        shipping_address_dict['city'] = order.shipping_address.city
        shipping_address_dict['state'] = order.shipping_address.state
        shipping_address_dict['zip'] = order.shipping_address.zip
        shipping_address_dict['country'] = order.shipping_address.country
        shipping_address_dict['country_code'] = order.shipping_address.country_code
    return shipping_address_dict


def get_order_billing_address(order):
    billing_address_dict = {}
    if order.billing_address is not None:
        billing_address_dict['name'] = order.billing_address.name
        billing_address_dict['address_line1'] = order.billing_address.address_line1
        billing_address_dict['city'] = order.billing_address.city
        billing_address_dict['state'] = order.billing_address.state
        billing_address_dict['zip'] = order.billing_address.zip
        billing_address_dict['country'] = order.billing_address.country
        billing_address_dict['country_code'] = order.billing_address.country_code
    return billing_address_dict


def get_order_payment_info(order):
    payment_dict = {}
    if order.payment is not None:
        payment_dict['email'] = order.payment.email
        payment_dict['payment_type'] = order.payment.payment_type
        payment_dict['card_name'] = order.payment.card_name
        payment_dict['card_brand'] = order.payment.card_brand
        payment_dict['card_last4'] = order.payment.card_last4
        payment_dict['card_exp_month'] = order.payment.card_exp_month
        payment_dict['card_exp_year'] = order.payment.card_exp_year
        payment_dict['card_zip'] = order.payment.card_zip
    return payment_dict


def get_confirmation_email_order_info_text_format(order_identifier):
    order_information = 'Order Identifier: ' + order_identifier
    return order_information


def get_confirmation_email_product_information_text_format(order_item_dict):
    product_information_text = ''
    for product_sku_id in order_item_dict['product_sku_data']:
        sku_title_str = order_item_dict['product_sku_data'][product_sku_id]['parent_product__title']
        if order_item_dict['product_sku_data'][product_sku_id]['description'] is not None:
            sku_title_str += ', ' + \
                order_item_dict['product_sku_data'][product_sku_id]['description']
        if order_item_dict['product_sku_data'][product_sku_id]['color'] is not None:
            sku_title_str += ', ' + order_item_dict['product_sku_data'][product_sku_id]['color']
        if order_item_dict['product_sku_data'][product_sku_id]['size'] is not None:
            sku_title_str += ', ' + order_item_dict['product_sku_data'][product_sku_id]['size']
        item_each_formatted = '${:,.2f}'.format(
            float(order_item_dict['product_sku_data'][product_sku_id]['price']))
        item_subtotal_formatted = '${:,.2f}'.format(
            float(
                order_item_dict['product_sku_data'][product_sku_id]['price']) * int(
                order_item_dict['product_sku_data'][product_sku_id]['quantity']))
        product_information_text += (
            sku_title_str + ', ' + item_each_formatted + ' each, Quantity: ' +
            str(order_item_dict['product_sku_data'][product_sku_id]['quantity']) +
            ', Subtotal: ' + item_subtotal_formatted
        )
        product_information_text += '\r\n'

    product_information_text = product_information_text[:-2]
    return product_information_text


def get_confirmation_email_shipping_information_text_format(shipping_method):
    shipping_cost_formatted = '${:,.2f}'.format(shipping_method.shipping_cost)
    shipping_information = shipping_method.carrier + ' ' + shipping_cost_formatted
    return shipping_information


def get_confirmation_email_discount_code_text_format(discount_code_dict):
    discount_code_text = ''
    for discount_code_id in discount_code_dict:
        combinable_str = 'No'
        if discount_code_dict[discount_code_id]['combinable']:
            combinable_str = 'Yes'

        value_str = discount_code_dict[discount_code_id]['description']
        value_str = value_str.replace(
            '{}', str(discount_code_dict[discount_code_id]['discount_amount']))

        wont_be_applied_str = ''
        if not discount_code_dict[discount_code_id]['discount_applied']:
            wont_be_applied_str = ' [This code cannot be combined or does not qualify for your order.]'

        discount_code_text += 'Code: ' + discount_code_dict[discount_code_id]['code'] + \
            wont_be_applied_str + ', ' + value_str + ', Combinable: ' + combinable_str
        discount_code_text += '\r\n'

    if discount_code_text == '':
        discount_code_text = 'None'
    else:
        discount_code_text = discount_code_text[:-2]

    return discount_code_text


def get_confirmation_email_order_totals_text_format(cart_totals_dict):
    item_subtotal_formatted = '${:,.2f}'.format(cart_totals_dict['item_subtotal'])
    item_discount_formatted = '${:,.2f}'.format(cart_totals_dict['item_discount'])
    shipping_subtotal_formatted = '${:,.2f}'.format(cart_totals_dict['shipping_subtotal'])
    shipping_discount_formatted = '${:,.2f}'.format(cart_totals_dict['shipping_discount'])
    cart_total_formatted = '${:,.2f}'.format(cart_totals_dict['cart_total'])
    order_total_information = 'Item Subtotal: ' + item_subtotal_formatted + '\r\n'
    if cart_totals_dict['item_discount'] > 0:
        order_total_information += 'Item Discount: (' + item_discount_formatted + ')\r\n'
    order_total_information += 'Shipping: ' + shipping_subtotal_formatted + '\r\n'
    if cart_totals_dict['shipping_discount'] > 0:
        order_total_information += 'Shipping Discount: (' + shipping_discount_formatted + ')\r\n'
    order_total_information += 'Order Total: ' + cart_total_formatted + '\r\n'
    return order_total_information


def get_confirmation_email_order_payment_text_format(payment):
    order_payment_information = str(payment.card_brand) + ': **** **** **** ' + str(
        payment.card_last4) + ', Exp: ' + str(payment.card_exp_month) + '/' + str(payment.card_exp_year)
    return order_payment_information


def get_confirmation_email_order_address_text_format(address):
    address_information = str(address.name)
    address_information += '\r\n'
    address_information += str(address.address_line1)
    address_information += '\r\n'
    address_information += str(address.city) + ', ' + str(address.state) + ' ' + str(address.zip)
    address_information += '\r\n'
    address_information += str(address.country)
    return address_information


def retrieve_stripe_customer(customer_token):
    """Wrapper for stripe.Customer.retrieve with error handling"""
    try:
        customer = stripe.Customer.retrieve(customer_token)
        return customer
    except (stripe.error.CardError, stripe.error.RateLimitError,
            stripe.error.InvalidRequestError, stripe.error.AuthenticationError,
            stripe.error.APIConnectionError, stripe.error.StripeError) as e:
        # Log the error and return None to allow graceful handling by caller
        logger.error(f"Stripe error in retrieve_stripe_customer: {type(e).__name__}: {str(e)}")
        return None


def create_stripe_customer(stripe_token, email, metadata_key, metadata_value):
    try:
        customer = stripe.Customer.create(
            source=stripe_token,
            email=email,
            metadata={metadata_key: metadata_value},
        )
        return customer
    except (stripe.error.CardError, stripe.error.RateLimitError,
            stripe.error.InvalidRequestError, stripe.error.AuthenticationError,
            stripe.error.APIConnectionError, stripe.error.StripeError) as e:
        # Log the error and return None to allow graceful handling by caller
        logger.error(f"Stripe error in create_stripe_customer: {type(e).__name__}: {str(e)}")
        return None


def stripe_customer_replace_default_payemnt(customer_token, stripe_token):
    try:
        stripe.Customer.modify(customer_token,
                               source=stripe_token,
                               )
        return True
    except (stripe.error.CardError, stripe.error.RateLimitError,
            stripe.error.InvalidRequestError, stripe.error.AuthenticationError,
            stripe.error.APIConnectionError, stripe.error.StripeError) as e:
        # Log the error and return None to indicate failure
        logger.error(
            f"Stripe error in stripe_customer_replace_default_payment: {
                type(e).__name__}: {
                str(e)}")
        return None


def stripe_customer_add_card(customer_token, stripe_token):
    try:
        customer = retrieve_stripe_customer(customer_token)
        if customer is None:
            return None
        card = customer.sources.create(source=stripe_token)
        return card
    except (stripe.error.CardError, stripe.error.RateLimitError,
            stripe.error.InvalidRequestError, stripe.error.AuthenticationError,
            stripe.error.APIConnectionError, stripe.error.StripeError) as e:
        # Log the error and return None to allow graceful handling by caller
        logger.error(f"Stripe error in stripe_customer_add_card: {type(e).__name__}: {str(e)}")
        return None


def stripe_customer_change_default_payemnt(customer_token, card_id):
    try:
        stripe.Customer.modify(customer_token,
                               default_source=card_id,
                               )
        return True
    except (stripe.error.CardError, stripe.error.RateLimitError,
            stripe.error.InvalidRequestError, stripe.error.AuthenticationError,
            stripe.error.APIConnectionError, stripe.error.StripeError) as e:
        # Log the error and return None to indicate failure
        logger.error(
            f"Stripe error in stripe_customer_change_default_payment: {
                type(e).__name__}: {
                str(e)}")
        return None
