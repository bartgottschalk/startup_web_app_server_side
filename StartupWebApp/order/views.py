from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from smtplib import SMTPDataError
from django.core.signing import Signer
from django.db import transaction
from user.models import Prospect, Email, Emailsent
from order.utilities import order_utils
from order.models import (
    Orderpayment,
    Ordershippingaddress,
    Orderbillingaddress,
    Order,
    Ordersku,
    Orderdiscount,
    Orderemailfailure,
    Status,
    Orderstatus,
    Ordershippingmethod,
)
from order.models import (
    Orderconfiguration,
    Sku,
    Skuprice,
    Skuimage,
    Cart,
    Cartsku,
    Cartdiscount,
    Discountcode,
    Productsku,
    Product,
    Productimage,
    Productvideo,
    Shippingmethod,
    Cartshippingmethod,
)
from StartupWebApp.form import validator
from StartupWebApp.utilities import identifier
from django.utils import timezone
import logging
import stripe

stripe.api_key = settings.STRIPE_SERVER_SECRET_KEY
stripe.log = settings.STRIPE_LOG_LEVEL

email_unsubscribe_signer = Signer(salt='email_unsubscribe')

# from user.models import

logger = logging.getLogger(__name__)

order_api_version = '0.0.1'

# @cache_control(max_age=10) #set cache control to 10 seconds


@never_cache
def index(request):
    return HttpResponse(
        "Hello, you're at the order API (version " + order_api_version + ") root. Nothing to see here..."
    )


def order_detail(request, order_identifier):
    # raise ValueError('A very specific bad thing happened.')
    try:
        order = Order.objects.get(identifier=order_identifier)
        if request.user.is_anonymous:
            logger.warning('AnonymousUser found when authenticated user expected')
            if order.member is None:
                order_data = order_utils.get_order_data(order)
                response = JsonResponse(
                    {'order_detail': 'success', 'order_data': order_data, 'order-api-version': order_api_version},
                    safe=False,
                )
            else:
                error_dict = {"error": 'log-in-required-to-view-order'}
                response = JsonResponse(
                    {
                        'order_detail': 'error',
                        'errors': error_dict,
                        'order_identifier': order_identifier,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
        else:
            if order.member == request.user.member:
                order_data = order_utils.get_order_data(order)
                response = JsonResponse(
                    {'order_detail': 'success', 'order_data': order_data, 'order-api-version': order_api_version},
                    safe=False,
                )
            else:
                error_dict = {"error": 'order-not-in-account'}
                response = JsonResponse(
                    {
                        'order_detail': 'error',
                        'errors': error_dict,
                        'order_identifier': order_identifier,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
    except (ObjectDoesNotExist, ValueError):
        order = None
        error_dict = {"error": 'order-not-found'}
        response = JsonResponse(
            {
                'order_detail': 'error',
                'errors': error_dict,
                'order_identifier': order_identifier,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    return response


def products(request):
    # raise ValueError('A very specific bad thing happened.')
    products_dict = {}
    for product in Product.objects.all():
        product_data = {}
        product_data['title'] = product.title
        product_data['title_url'] = product.title_url
        product_data['identifier'] = product.identifier
        product_data['headline'] = product.headline
        product_data['description_part_1'] = product.description_part_1
        product_data['description_part_2'] = product.description_part_2
        price_low = None
        price_high = None
        for product_sku in Productsku.objects.filter(product=product):
            if (
                price_low is None
                or Skuprice.objects.filter(sku=product_sku.sku).latest('created_date_time').price < price_low
            ):
                price_low = Skuprice.objects.filter(sku=product_sku.sku).latest('created_date_time').price
            if (
                price_high is None
                or Skuprice.objects.filter(sku=product_sku.sku).latest('created_date_time').price > price_high
            ):
                price_high = Skuprice.objects.filter(sku=product_sku.sku).latest('created_date_time').price
        product_data['price_low'] = price_low
        product_data['price_high'] = price_high

        product_image_main_exists = Productimage.objects.filter(product=product, main_image=True).exists()
        product_image_url = None
        if product_image_main_exists is True:
            product_image_url = Productimage.objects.get(product=product, main_image=True).image_url
        product_data['product_image_url'] = product_image_url
        products_dict[product.identifier] = product_data

    response = JsonResponse({'products_data': products_dict, 'order-api-version': order_api_version}, safe=False)
    return response


def product(request, product_identifier):
    # raise ValueError('A very specific bad thing happened.')
    try:
        product = Product.objects.get(identifier=product_identifier)

        product_data = {}
        product_data['title'] = product.title
        product_data['title_url'] = product.title_url
        product_data['identifier'] = product.identifier
        product_data['headline'] = product.headline
        product_data['description_part_1'] = product.description_part_1
        product_data['description_part_2'] = product.description_part_2

        product_images = {}
        for product_image in Productimage.objects.filter(product=product).order_by('-main_image'):
            product_image_data = {}
            product_image_data['image_url'] = product_image.image_url
            product_image_data['main'] = product_image.main_image
            product_image_data['caption'] = product_image.caption
            product_images[product_image.id] = product_image_data
        product_data['product_images'] = product_images

        product_videos = {}
        for product_video in Productvideo.objects.filter(product=product).order_by('-id'):
            product_video_data = {}
            product_video_data['video_url'] = product_video.video_url
            product_video_data['video_thumbnail_url'] = product_video.video_thumbnail_url
            product_video_data['caption'] = product_video.caption
            product_videos[product_video.id] = product_video_data
        product_data['product_videos'] = product_videos

        product_skus = {}
        for product_sku in Productsku.objects.filter(product=product).order_by('sku__id'):
            product_sku_data = {}
            product_sku_data['color'] = product_sku.sku.color
            product_sku_data['size'] = product_sku.sku.size
            product_sku_data['description'] = product_sku.sku.description
            product_sku_data['price'] = Skuprice.objects.filter(sku=product_sku.sku).latest('created_date_time').price
            product_sku_data['inventory_status_identifier'] = product_sku.sku.sku_inventory.identifier
            product_sku_data['inventory_status_title'] = product_sku.sku.sku_inventory.title
            product_sku_data['inventory_status_description'] = product_sku.sku.sku_inventory.description

            sku_images = {}
            for sku_image in Skuimage.objects.filter(sku=product_sku.sku).order_by('-main_image'):
                sku_image_data = {}
                sku_image_data['image_url'] = sku_image.image_url
                sku_image_data['main'] = sku_image.main_image
                sku_image_data['caption'] = sku_image.caption
                sku_images[sku_image.id] = sku_image_data
            product_sku_data['sku_images'] = sku_images

            product_skus[product_sku.sku.id] = product_sku_data
        product_data['skus'] = product_skus

        response = JsonResponse(
            {
                'product': 'success',
                'product_identifier': product_identifier,
                'product_data': product_data,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    except (ObjectDoesNotExist, ValueError) as e:
        logger.warning(f'Product not found for identifier {product_identifier}: {e}')
        error_dict = {"error": 'product-identifier-not-found'}
        response = JsonResponse(
            {
                'product': 'error',
                'errors': error_dict,
                'product_identifier': product_identifier,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    return response


def checkout_allowed(request):
    # raise ValueError('A very specific bad thing happened.')
    checkout_allowed = order_utils.checkout_allowed(request)
    response = JsonResponse({'checkout_allowed': checkout_allowed, 'order-api-version': order_api_version}, safe=False)
    return response


def cart_items(request):
    # raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    cart_item_dict = order_utils.get_cart_items(request, cart)
    response = JsonResponse(
        {
            'cart_found': (True if cart is not None else False),
            'item_data': cart_item_dict,
            'order-api-version': order_api_version,
        },
        safe=False,
    )
    return response


def confirm_items(request):
    # raise ValueError('A very specific bad thing happened.')
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        cart = order_utils.look_up_cart(request)
        confirm_item_dict = order_utils.get_cart_items(request, cart)
        response = JsonResponse(
            {
                'checkout_allowed': checkout_allowed,
                'cart_found': (True if cart is not None else False),
                'item_data': confirm_item_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    else:
        response = JsonResponse(
            {'checkout_allowed': checkout_allowed, 'order-api-version': order_api_version}, safe=False
        )
    return response


def cart_shipping_methods(request):
    # raise ValueError('A very specific bad thing happened.')
    shipping_methods = {}
    shipping_method_selected = None
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        if Cartshippingmethod.objects.filter(cart=cart).exists():
            shipping_method_selected = Cartshippingmethod.objects.get(cart=cart).shippingmethod.identifier
        else:
            Cartshippingmethod.objects.create(
                cart=cart,
                shippingmethod=Shippingmethod.objects.get(
                    identifier=Orderconfiguration.objects.get(key='default_shipping_method').string_value
                ),
            )
            shipping_method_selected = Orderconfiguration.objects.get(key='default_shipping_method').string_value

        shipping_method_arr = Shippingmethod.objects.filter(
            active=True,
        ).order_by('-shipping_cost')

        counter = 0
        for shippingmethod in shipping_method_arr:
            shipping_method_data = {}
            shipping_method_data['identifier'] = shippingmethod.identifier
            shipping_method_data['carrier'] = shippingmethod.carrier
            shipping_method_data['shipping_cost'] = shippingmethod.shipping_cost
            shipping_method_data['tracking_code_base_url'] = shippingmethod.tracking_code_base_url
            shipping_methods[counter] = shipping_method_data
            counter += 1

    response = JsonResponse(
        {
            'cart_found': (True if cart is not None else False),
            'cart_shipping_methods': shipping_methods,
            'shipping_method_selected': shipping_method_selected,
            'order-api-version': order_api_version,
        },
        safe=False,
    )
    return response


def confirm_shipping_method(request):
    # raise ValueError('A very specific bad thing happened.')
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        cart = order_utils.look_up_cart(request)
        shipping_method = {}
        if cart is not None:
            if Cartshippingmethod.objects.filter(cart=cart).exists():
                shipping_method_selected = Cartshippingmethod.objects.get(cart=cart).shippingmethod
                shipping_method['identifier'] = shipping_method_selected.identifier
                shipping_method['carrier'] = shipping_method_selected.carrier
                shipping_method['shipping_cost'] = shipping_method_selected.shipping_cost
                shipping_method['tracking_code_base_url'] = shipping_method_selected.tracking_code_base_url
        response = JsonResponse(
            {
                'checkout_allowed': checkout_allowed,
                'cart_found': (True if cart is not None else False),
                'confirm_shipping_method': shipping_method,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    else:
        response = JsonResponse(
            {'checkout_allowed': checkout_allowed, 'order-api-version': order_api_version}, safe=False
        )
    return response


def cart_discount_codes(request):
    # raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    discount_code_dict = order_utils.get_cart_discount_codes(cart)
    response = JsonResponse(
        {
            'cart_found': (True if cart is not None else False),
            'discount_code_data': discount_code_dict,
            'order-api-version': order_api_version,
        },
        safe=False,
    )
    return response


def confirm_discount_codes(request):
    # raise ValueError('A very specific bad thing happened.')
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        cart = order_utils.look_up_cart(request)
        discount_code_dict = order_utils.get_cart_discount_codes(cart)
        response = JsonResponse(
            {
                'checkout_allowed': checkout_allowed,
                'cart_found': (True if cart is not None else False),
                'discount_code_data': discount_code_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    else:
        response = JsonResponse(
            {'checkout_allowed': checkout_allowed, 'order-api-version': order_api_version}, safe=False
        )
    return response


def cart_totals(request):
    # raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    cart_totals_dict = order_utils.get_cart_totals(cart)
    response = JsonResponse(
        {
            'cart_found': (True if cart is not None else False),
            'cart_totals_data': cart_totals_dict,
            'order-api-version': order_api_version,
        },
        safe=False,
    )
    return response


def confirm_totals(request):
    # raise ValueError('A very specific bad thing happened.')

    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        cart = order_utils.look_up_cart(request)
        cart_totals_dict = order_utils.get_cart_totals(cart)
        response = JsonResponse(
            {
                'checkout_allowed': checkout_allowed,
                'cart_found': (True if cart is not None else False),
                'confirm_totals_data': cart_totals_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    else:
        response = JsonResponse(
            {'checkout_allowed': checkout_allowed, 'order-api-version': order_api_version}, safe=False
        )
    return response


def cart_add_product_sku(request):
    # raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is None:
        cart = order_utils.create_cart(request)
    sku_id = None
    if request.method == 'POST' and 'sku_id' in request.POST:
        sku_id = request.POST['sku_id']
    quantity = None
    if request.method == 'POST' and 'quantity' in request.POST:
        quantity = request.POST['quantity']
    if sku_id is not None:
        try:
            quantity_valid = validator.validateSkuQuantity(quantity)
            # Validators return True or error array - must use == True
            if quantity_valid == True:  # noqa: E712
                sku = Sku.objects.get(id=sku_id)
                product_sku = Productsku.objects.get(sku=sku)
                cart_sku_exists = Cartsku.objects.filter(cart=cart, sku=product_sku.sku).exists()
                if cart_sku_exists:
                    cart_sku = Cartsku.objects.get(cart=cart, sku=product_sku.sku)
                    cart_sku.quantity = cart_sku.quantity + int(quantity)
                    cart_sku.save()
                else:
                    Cartsku.objects.create(cart=cart, sku=product_sku.sku, quantity=int(quantity))
                cart_item_count = order_utils.count_cart_items(cart)
                response = JsonResponse(
                    {
                        'cart_add_product_sku': 'success',
                        'sku_id': sku_id,
                        'cart_item_count': cart_item_count,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
                order_utils.set_anonymous_cart_cookie(request, response, cart)
            else:
                error_dict = {"quantity": quantity_valid}
                return JsonResponse(
                    {
                        'cart_add_product_sku': 'error',
                        'errors': error_dict,
                        'sku_id': sku_id,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
        except (ObjectDoesNotExist, ValueError) as e:
            logger.warning(f'Database lookup failed: {e}')
            error_dict = {"error": 'sku-not-found'}
            response = JsonResponse(
                {
                    'cart_add_product_sku': 'error',
                    'errors': error_dict,
                    'sku_id': sku_id,
                    'order-api-version': order_api_version,
                },
                safe=False,
            )
    else:
        error_dict = {"error": 'sku-id-required'}
        response = JsonResponse(
            {
                'cart_add_product_sku': 'error',
                'errors': error_dict,
                'sku_id': sku_id,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    return response


def cart_update_sku_quantity(request):
    # raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        sku_id = None
        if request.method == 'POST' and 'sku_id' in request.POST:
            sku_id = request.POST['sku_id']
        quantity_new = None
        if request.method == 'POST' and 'quantity' in request.POST:
            quantity_new = request.POST['quantity']
        if sku_id is not None:
            try:
                cart_sku = Cartsku.objects.get(cart=cart, sku=Sku.objects.get(id=sku_id))
                cart_sku.quantity = quantity_new
                cart_sku.save()
                sku_subtotal = (
                    Skuprice.objects.filter(sku=cart_sku.sku).latest('created_date_time').price
                    * Cartsku.objects.get(cart=cart, sku=cart_sku.sku).quantity
                )
                discount_code_dict = order_utils.get_cart_discount_codes(cart)
                cart_totals_dict = order_utils.get_cart_totals(cart)
                response = JsonResponse(
                    {
                        'cart_update_sku_quantity': 'success',
                        'cart_found': (True if cart is not None else False),
                        'sku_id': sku_id,
                        'sku_subtotal': sku_subtotal,
                        'discount_code_data': discount_code_dict,
                        'cart_totals_data': cart_totals_dict,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
            except (ObjectDoesNotExist, ValueError) as e:
                logger.warning(f'Database lookup failed: {e}')
                error_dict = {"error": 'cart-sku-not-found'}
                response = JsonResponse(
                    {
                        'cart_update_sku_quantity': 'error',
                        'errors': error_dict,
                        'sku_id': sku_id,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
        else:
            error_dict = {"error": 'sku-id-required'}
            response = JsonResponse(
                {'cart_update_sku_quantity': 'error', 'errors': error_dict, 'order-api-version': order_api_version},
                safe=False,
            )
    else:
        error_dict = {"error": 'cart-not-found'}
        response = JsonResponse(
            {'cart_update_sku_quantity': 'error', 'errors': error_dict, 'order-api-version': order_api_version},
            safe=False,
        )
    return response


def cart_remove_sku(request):
    # raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        sku_id = None
        if request.method == 'POST' and 'sku_id' in request.POST:
            sku_id = request.POST['sku_id']
        if sku_id is not None:
            try:
                cart_sku = Cartsku.objects.get(cart=cart, sku=Sku.objects.get(id=sku_id))
                cart_sku.delete()

                shipping_methods = {}
                shipping_method_selected = None

                if Cartshippingmethod.objects.filter(cart=cart).exists():
                    Cartshippingmethod.objects.get(cart=cart).delete()

                shipping_method_arr = Shippingmethod.objects.filter(active=True).order_by('-shipping_cost')

                counter = 0
                for shippingmethod in shipping_method_arr:
                    shipping_method_data = {}
                    shipping_method_data['identifier'] = shippingmethod.identifier
                    shipping_method_data['carrier'] = shippingmethod.carrier
                    shipping_method_data['shipping_cost'] = shippingmethod.shipping_cost
                    shipping_method_data['tracking_code_base_url'] = shippingmethod.tracking_code_base_url
                    shipping_methods[counter] = shipping_method_data
                    counter += 1

                discount_code_dict = order_utils.get_cart_discount_codes(cart)
                cart_totals_dict = order_utils.get_cart_totals(cart)
                cart_item_count = order_utils.count_cart_items(cart)
                response = JsonResponse(
                    {
                        'cart_remove_sku': 'success',
                        'cart_found': (True if cart is not None else False),
                        'sku_id': sku_id,
                        'cart_item_count': cart_item_count,
                        'cart_shipping_methods': shipping_methods,
                        'shipping_method_selected': shipping_method_selected,
                        'discount_code_data': discount_code_dict,
                        'cart_totals_data': cart_totals_dict,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
            except (ObjectDoesNotExist, ValueError) as e:
                logger.warning(f'Database lookup failed: {e}')
                error_dict = {"error": 'cart-sku-not-found'}
                response = JsonResponse(
                    {
                        'cart_remove_sku': 'error',
                        'errors': error_dict,
                        'sku_id': sku_id,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
        else:
            error_dict = {"error": 'sku-id-required'}
            response = JsonResponse(
                {'cart_remove_sku': 'error', 'errors': error_dict, 'order-api-version': order_api_version}, safe=False
            )
    else:
        error_dict = {"error": 'cart-not-found'}
        response = JsonResponse(
            {'cart_remove_sku': 'error', 'errors': error_dict, 'order-api-version': order_api_version}, safe=False
        )
    return response


def cart_apply_discount_code(request):
    # raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        discount_code_id = None
        if request.method == 'POST' and 'discount_code_id' in request.POST:
            discount_code_id = request.POST['discount_code_id']
        if discount_code_id is not None:
            try:
                discountcode = Discountcode.objects.get(code=discount_code_id)
                now = timezone.now()
                if now < discountcode.start_date_time or now > discountcode.end_date_time:
                    error_dict = {"error": 'cart-discount-code-not-active'}
                    response = JsonResponse(
                        {
                            'cart_apply_discount_code': 'error',
                            'errors': error_dict,
                            'discount_code_id': discount_code_id,
                            'order-api-version': order_api_version,
                        },
                        safe=False,
                    )
                elif Cartdiscount.objects.filter(cart=cart, discountcode=discountcode).exists():
                    error_dict = {"error": 'cart-discount-code-already-applied'}
                    response = JsonResponse(
                        {
                            'cart_apply_discount_code': 'error',
                            'errors': error_dict,
                            'discount_code_id': discount_code_id,
                            'order-api-version': order_api_version,
                        },
                        safe=False,
                    )
                else:
                    Cartdiscount.objects.create(cart=cart, discountcode=discountcode)
                    discount_code_dict = order_utils.get_cart_discount_codes(cart)
                    cart_totals_dict = order_utils.get_cart_totals(cart)
                    response = JsonResponse(
                        {
                            'cart_apply_discount_code': 'success',
                            'cart_found': (True if cart is not None else False),
                            'discount_code_id': discount_code_id,
                            'discount_code_data': discount_code_dict,
                            'cart_totals_data': cart_totals_dict,
                            'order-api-version': order_api_version,
                        },
                        safe=False,
                    )
            except (ObjectDoesNotExist, ValueError) as e:
                logger.warning(f'Database lookup failed: {e}')
                error_dict = {"error": 'cart-discount-code-not-found'}
                response = JsonResponse(
                    {
                        'cart_apply_discount_code': 'error',
                        'errors': error_dict,
                        'discount_code_id': discount_code_id,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
        else:
            error_dict = {"error": 'discount-code-required'}
            response = JsonResponse(
                {'cart_apply_discount_code': 'error', 'errors': error_dict, 'order-api-version': order_api_version},
                safe=False,
            )
    else:
        error_dict = {"error": 'cart-not-found'}
        response = JsonResponse(
            {'cart_apply_discount_code': 'error', 'errors': error_dict, 'order-api-version': order_api_version},
            safe=False,
        )
    return response


def cart_remove_discount_code(request):
    # raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        discount_code_id = None
        if request.method == 'POST' and 'discount_code_id' in request.POST:
            discount_code_id = request.POST['discount_code_id']
        if discount_code_id is not None:
            try:
                Cartdiscount.objects.filter(
                    cart=cart, discountcode=Discountcode.objects.get(id=discount_code_id)
                ).delete()
                discount_code_dict = order_utils.get_cart_discount_codes(cart)
                cart_totals_dict = order_utils.get_cart_totals(cart)
                response = JsonResponse(
                    {
                        'cart_remove_discount_code': 'success',
                        'cart_found': (True if cart is not None else False),
                        'discount_code_id': discount_code_id,
                        'discount_code_data': discount_code_dict,
                        'cart_totals_data': cart_totals_dict,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
            except (ObjectDoesNotExist, ValueError) as e:
                logger.warning(f'Database lookup failed: {e}')
                error_dict = {"error": 'cart-discount-code-not-found'}
                response = JsonResponse(
                    {
                        'cart_remove_discount_code': 'error',
                        'errors': error_dict,
                        'discount_code_id': discount_code_id,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
        else:
            error_dict = {"error": 'discount-code-required'}
            response = JsonResponse(
                {'cart_remove_discount_code': 'error', 'errors': error_dict, 'order-api-version': order_api_version},
                safe=False,
            )
    else:
        error_dict = {"error": 'cart-not-found'}
        response = JsonResponse(
            {'cart_remove_discount_code': 'error', 'errors': error_dict, 'order-api-version': order_api_version},
            safe=False,
        )
    return response


def cart_update_shipping_method(request):
    # raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        shipping_method_identifier = None
        if request.method == 'POST' and 'shipping_method_identifier' in request.POST:
            shipping_method_identifier = request.POST['shipping_method_identifier']
        if shipping_method_identifier is not None:
            try:
                # raise ValueError('A very specific bad thing happened.')
                cart_shipping_method_exists = Cartshippingmethod.objects.filter(cart=cart).exists()
                if cart_shipping_method_exists:
                    cart_shipping_method = Cartshippingmethod.objects.get(cart=cart)
                    cart_shipping_method.shippingmethod = Shippingmethod.objects.get(
                        identifier=shipping_method_identifier
                    )
                    cart_shipping_method.save()
                else:
                    Cartshippingmethod.objects.create(
                        cart=cart, shippingmethod=Shippingmethod.objects.get(identifier=shipping_method_identifier)
                    )
                discount_code_dict = order_utils.get_cart_discount_codes(cart)
                cart_totals_dict = order_utils.get_cart_totals(cart)
                response = JsonResponse(
                    {
                        'cart_update_shipping_method': 'success',
                        'cart_found': (True if cart is not None else False),
                        'shipping_method_identifier': shipping_method_identifier,
                        'discount_code_data': discount_code_dict,
                        'cart_totals_data': cart_totals_dict,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
            except (ObjectDoesNotExist, ValueError) as e:
                logger.warning(f'Database lookup failed: {e}')
                error_dict = {"error": 'error-setting-cart-shipping-method'}
                response = JsonResponse(
                    {
                        'cart_update_shipping_method': 'error',
                        'errors': error_dict,
                        'shipping_method_identifier': shipping_method_identifier,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
        else:
            error_dict = {"error": 'shipping-method-identifier-required'}
            response = JsonResponse(
                {'cart_update_shipping_method': 'error', 'errors': error_dict, 'order-api-version': order_api_version},
                safe=False,
            )
    else:
        error_dict = {"error": 'cart-not-found'}
        response = JsonResponse(
            {'cart_update_shipping_method': 'error', 'errors': error_dict, 'order-api-version': order_api_version},
            safe=False,
        )
    return response


def cart_delete_cart(request):
    # raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        cart.delete()
        response = JsonResponse({'cart_delete_cart': 'success', 'order-api-version': order_api_version}, safe=False)
    else:
        error_dict = {"error": 'cart-not-found'}
        response = JsonResponse(
            {'cart_delete_cart': 'error', 'errors': error_dict, 'order-api-version': order_api_version}, safe=False
        )
    return response


def create_checkout_session(request):
    """
    Create a Stripe Checkout Session for the user's cart.
    Returns session_id and checkout_url for frontend to redirect to Stripe.
    """
    checkout_allowed = order_utils.checkout_allowed(request)

    if not checkout_allowed:
        error_dict = {"error": 'checkout-not-allowed'}
        response = JsonResponse(
            {
                'create_checkout_session': 'error',
                'errors': error_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
        return response

    # Look up the cart
    cart = order_utils.look_up_cart(request)

    if cart is None:
        error_dict = {"error": 'cart-not-found'}
        response = JsonResponse(
            {
                'create_checkout_session': 'error',
                'errors': error_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
        return response

    # Check if cart has items
    cart_items = order_utils.get_cart_items(request, cart)
    if not cart_items.get('product_sku_data') or len(cart_items['product_sku_data']) == 0:
        error_dict = {"error": 'cart-is-empty'}
        response = JsonResponse(
            {
                'create_checkout_session': 'error',
                'errors': error_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
        return response

    try:
        # Get frontend domain for building absolute URLs
        # Use settings to get the frontend domain
        frontend_domain = getattr(settings, 'ENVIRONMENT_DOMAIN', 'http://localhost:8080')

        # Build line items for Stripe
        line_items = []
        for item_key, item_data in cart_items['product_sku_data'].items():
            # Convert price to cents (Stripe requires integer cents)
            unit_amount_cents = int(float(item_data['price']) * 100)

            # Build absolute image URL (Stripe requires absolute URLs, not relative paths)
            sku_image_url = item_data['sku_image_url']
            if sku_image_url.startswith('http://') or sku_image_url.startswith('https://'):
                # Already absolute URL (e.g., from test data)
                image_url = sku_image_url
            else:
                # Relative URL - prepend frontend domain
                image_url = f"{frontend_domain}{sku_image_url}"

            line_item = {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item_data['parent_product__title'],
                        'description': f"{item_data['color']} - {item_data['size']}",
                        'images': [image_url],
                    },
                    'unit_amount': unit_amount_cents,
                },
                'quantity': item_data['quantity'],
            }
            line_items.append(line_item)

        # Add shipping as a separate line item
        cart_totals = order_utils.get_cart_totals(cart)
        shipping_cost = float(cart_totals.get('shipping_subtotal', 0))
        if shipping_cost > 0:
            shipping_line_item = {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Shipping',
                        'description': cart_totals.get('shipping_method_carrier', 'Standard Shipping'),
                    },
                    'unit_amount': int(shipping_cost * 100),  # Convert to cents
                },
                'quantity': 1,
            }
            line_items.append(shipping_line_item)

        # Determine customer email
        customer_email = None
        if request.user.is_authenticated:
            customer_email = request.user.email
        else:
            # For anonymous users, use email from checkout form (pre-fills Stripe)
            # User can still change it at Stripe checkout page if needed
            if request.method == 'POST' and 'anonymous_email_address' in request.POST:
                customer_email = request.POST.get('anonymous_email_address')

        # Build success and cancel URLs
        success_url = f"{frontend_domain}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{frontend_domain}/checkout/confirm"

        # Create Stripe Checkout Session
        session_params = {
            'mode': 'payment',
            'line_items': line_items,
            'success_url': success_url,
            'cancel_url': cancel_url,
            'billing_address_collection': 'required',
            'shipping_address_collection': {
                'allowed_countries': ['US', 'CA'],  # Expand as needed
            },
            'phone_number_collection': {
                'enabled': True,
            },
            'metadata': {
                'cart_id': str(cart.id),  # Store cart_id for webhook handler
            },
        }

        # Add customer_email if available
        if customer_email:
            session_params['customer_email'] = customer_email

        session = stripe.checkout.Session.create(**session_params)

        response = JsonResponse(
            {
                'create_checkout_session': 'success',
                'session_id': session.id,
                'checkout_url': session.url,
                'order-api-version': order_api_version,
            },
            safe=False,
        )

    except stripe.error.StripeError as e:
        logger.error(f'Stripe error creating checkout session: {str(e)}')
        error_dict = {
            "error": 'stripe-error',
            "description": str(e)
        }
        response = JsonResponse(
            {
                'create_checkout_session': 'error',
                'errors': error_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    except Exception as e:
        logger.error(f'Unexpected error creating checkout session: {str(e)}')
        error_dict = {
            "error": 'unexpected-error',
            "description": str(e)
        }
        response = JsonResponse(
            {
                'create_checkout_session': 'error',
                'errors': error_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )

    return response


def checkout_session_success(request):
    """
    Handle successful Stripe Checkout Session completion.
    Retrieve session data, create order, and send confirmation email.
    """
    # Get session_id from query parameters
    session_id = request.GET.get('session_id')

    if not session_id:
        error_dict = {"error": 'session-id-required'}
        response = JsonResponse(
            {
                'checkout_session_success': 'error',
                'errors': error_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
        return response

    try:
        # Retrieve the Stripe Checkout Session
        session = stripe.checkout.Session.retrieve(session_id)

        # Verify payment is completed
        if session.payment_status != 'paid':
            error_dict = {"error": 'payment-not-completed'}
            response = JsonResponse(
                {
                    'checkout_session_success': 'error',
                    'errors': error_dict,
                    'order-api-version': order_api_version,
                },
                safe=False,
            )
            return response

        # Check if order already exists for this payment_intent (prevent duplicates)
        payment_intent_id = session.payment_intent
        existing_order = None
        if payment_intent_id:
            try:
                existing_payment = Orderpayment.objects.get(stripe_payment_intent_id=payment_intent_id)
                existing_order = existing_payment.order_set.first()
                if existing_order:
                    # Order already exists, return it
                    response = JsonResponse(
                        {
                            'checkout_session_success': 'success',
                            'order_identifier': existing_order.identifier,
                            'order-api-version': order_api_version,
                        },
                        safe=False,
                    )
                    return response
            except Orderpayment.DoesNotExist:
                pass  # No existing order, proceed with creation

        # Look up the cart
        cart = order_utils.look_up_cart(request)

        if cart is None:
            error_dict = {"error": 'cart-not-found'}
            response = JsonResponse(
                {
                    'checkout_session_success': 'error',
                    'errors': error_dict,
                    'order-api-version': order_api_version,
                },
                safe=False,
            )
            return response

        # Extract address information from session
        customer_details = session.customer_details
        # Stripe API change: shipping_details moved to collected_information
        shipping_details = None
        if hasattr(session, 'collected_information') and session.collected_information:
            shipping_details = getattr(session.collected_information, 'shipping_details', None)

        # Get customer name and email
        customer_name = customer_details.name if customer_details else 'Customer'
        customer_email = session.customer_email or (customer_details.email if customer_details else '')

        # Create order identifier
        order_identifier = identifier.getNewOrderIdentifier()

        # Create Payment object
        payment = Orderpayment.objects.create(
            email=customer_email,
            payment_type='card',
            card_name=customer_name,
            stripe_payment_intent_id=payment_intent_id,
            # Card details would come from payment_intent if needed, but Stripe Checkout doesn't expose them
        )

        # Create Shipping Address object
        shipping_address = Ordershippingaddress.objects.create(
            name=shipping_details.name if shipping_details else customer_name,
            address_line1=shipping_details.address.line1 if shipping_details and shipping_details.address else '',
            city=shipping_details.address.city if shipping_details and shipping_details.address else '',
            state=shipping_details.address.state if shipping_details and shipping_details.address else '',
            zip=shipping_details.address.postal_code if shipping_details and shipping_details.address else '',
            country=shipping_details.address.country if shipping_details and shipping_details.address else '',
            country_code=shipping_details.address.country if shipping_details and shipping_details.address else '',
        )

        # Create Billing Address object
        billing_address = Orderbillingaddress.objects.create(
            name=customer_name,
            address_line1=customer_details.address.line1 if customer_details and customer_details.address else '',
            city=customer_details.address.city if customer_details and customer_details.address else '',
            state=customer_details.address.state if customer_details and customer_details.address else '',
            zip=customer_details.address.postal_code if customer_details and customer_details.address else '',
            country=customer_details.address.country if customer_details and customer_details.address else '',
            country_code=customer_details.address.country if customer_details and customer_details.address else '',
        )

        # Calculate order totals from cart
        cart_totals_dict = order_utils.get_cart_totals(cart)

        # Create Order object
        now = timezone.now()
        if request.user.is_authenticated:
            order = Order.objects.create(
                identifier=order_identifier,
                member=request.user.member,
                payment=payment,
                shipping_address=shipping_address,
                billing_address=billing_address,
                sales_tax_amt=0,
                item_subtotal=cart_totals_dict['item_subtotal'],
                item_discount_amt=cart_totals_dict['item_discount'],
                shipping_amt=cart_totals_dict['shipping_subtotal'],
                shipping_discount_amt=cart_totals_dict['shipping_discount'],
                order_total=cart_totals_dict['cart_total'],
                agreed_with_terms_of_sale=True,
                order_date_time=now,
            )
        else:
            # Anonymous user - get or create prospect
            prospect, created = Prospect.objects.get_or_create(
                email=customer_email,
                defaults={
                    'pr_cd': identifier.getNewProspectCode(),
                    'created_date_time': timezone.now()
                }
            )
            order = Order.objects.create(
                identifier=order_identifier,
                prospect=prospect,
                payment=payment,
                shipping_address=shipping_address,
                billing_address=billing_address,
                sales_tax_amt=0,
                item_subtotal=cart_totals_dict['item_subtotal'],
                item_discount_amt=cart_totals_dict['item_discount'],
                shipping_amt=cart_totals_dict['shipping_subtotal'],
                shipping_discount_amt=cart_totals_dict['shipping_discount'],
                order_total=cart_totals_dict['cart_total'],
                agreed_with_terms_of_sale=True,
                order_date_time=now,
            )

        # Create Ordersku objects
        cart_item_dict = order_utils.get_cart_items(request, cart)
        for product_sku_id in cart_item_dict['product_sku_data']:
            Ordersku.objects.create(
                order=order,
                sku=Sku.objects.get(id=cart_item_dict['product_sku_data'][product_sku_id]['sku_id']),
                quantity=cart_item_dict['product_sku_data'][product_sku_id]['quantity'],
                price_each=cart_item_dict['product_sku_data'][product_sku_id]['price'],
            )

        # Create Orderdiscount records
        discount_code_dict = order_utils.get_cart_discount_codes(cart)
        for discount_code_id in discount_code_dict:
            Orderdiscount.objects.create(
                order=order,
                discountcode=Discountcode.objects.get(
                    id=discount_code_dict[discount_code_id]['discount_code_id']
                ),
                applied=discount_code_dict[discount_code_id]['discount_applied'],
            )

        # Create Orderstatus record
        Orderstatus.objects.create(
            order=order,
            status=Status.objects.get(
                identifier=Orderconfiguration.objects.get(key='initial_order_status').string_value
            ),
            created_date_time=now,
        )

        # Create Ordershippingmethod record
        order_shipping_method = Ordershippingmethod.objects.create(
            order=order,
            shippingmethod=Cartshippingmethod.objects.get(cart=cart).shippingmethod
        )

        #################################
        # Send Order Confirmation Email #
        #################################
        order_info_text = order_utils.get_confirmation_email_order_info_text_format(order_identifier)
        product_text = order_utils.get_confirmation_email_product_information_text_format(cart_item_dict)
        shipping_text = order_utils.get_confirmation_email_shipping_information_text_format(
            order_shipping_method.shippingmethod
        )
        discount_code_text = order_utils.get_confirmation_email_discount_code_text_format(discount_code_dict)
        order_totals_text = order_utils.get_confirmation_email_order_totals_text_format(cart_totals_dict)
        payment_text = order_utils.get_confirmation_email_order_payment_text_format(payment)
        shipping_address_text = order_utils.get_confirmation_email_order_address_text_format(shipping_address)
        billing_address_text = order_utils.get_confirmation_email_order_address_text_format(billing_address)

        to_address = customer_email

        if request.user.is_authenticated:
            order_confirmation_em_cd_member = Orderconfiguration.objects.get(
                key='order_confirmation_em_cd_member'
            ).string_value
            email = Email.objects.get(em_cd=order_confirmation_em_cd_member)
            order_confirmation_email_body_text = email.body_text

            order_confirmation_email_namespace = {
                'line_break': '\r\n\r\n',
                'short_line_break': '\r\n',
                'recipient_first_name': customer_name,
                'order_information': order_info_text,
                'product_information': product_text,
                'shipping_information': shipping_text,
                'discount_information': discount_code_text,
                'order_total_information': order_totals_text,
                'payment_information': payment_text,
                'shipping_address_information': shipping_address_text,
                'billing_address_information': billing_address_text,
                'ENVIRONMENT_DOMAIN': settings.ENVIRONMENT_DOMAIN,
                'identifier': order_identifier,
                'em_cd': email.em_cd,
                'mb_cd': request.user.member.mb_cd,
            }
            formatted_order_confirmation_email_body_text = order_confirmation_email_body_text.format(
                **order_confirmation_email_namespace
            )
        else:
            order_confirmation_em_cd_prospect = Orderconfiguration.objects.get(
                key='order_confirmation_em_cd_prospect'
            ).string_value
            email = Email.objects.get(em_cd=order_confirmation_em_cd_prospect)
            order_confirmation_email_body_text = email.body_text

            prospect = order.prospect
            prospect.swa_comment = f'Captured from Stripe Checkout order identifier: {order_identifier}'
            prospect.save()

            prosepct_email_unsubscribe_str = (
                'You are NOT included in our email marketing list. If you would like to be '
                'added to our marketing email list please reply to this email and let us know.'
            )

            order_confirmation_email_namespace = {
                'line_break': '\r\n\r\n',
                'short_line_break': '\r\n',
                'recipient_first_name': customer_name,
                'order_information': order_info_text,
                'product_information': product_text,
                'shipping_information': shipping_text,
                'discount_information': discount_code_text,
                'order_total_information': order_totals_text,
                'payment_information': payment_text,
                'shipping_address_information': shipping_address_text,
                'billing_address_information': billing_address_text,
                'ENVIRONMENT_DOMAIN': settings.ENVIRONMENT_DOMAIN,
                'identifier': order_identifier,
                'em_cd': email.em_cd,
                'pr_cd': prospect.pr_cd,
                'prosepct_email_unsubscribe_str': prosepct_email_unsubscribe_str,
            }
            formatted_order_confirmation_email_body_text = order_confirmation_email_body_text.format(
                **order_confirmation_email_namespace
            )

        msg = EmailMultiAlternatives(
            subject=email.subject,
            body=formatted_order_confirmation_email_body_text,
            from_email=email.from_address,
            to=[to_address],
            bcc=[email.bcc_address] if email.bcc_address else [],
            reply_to=[email.from_address],
        )

        try:
            msg.send(fail_silently=False)
            now = timezone.now()
            if request.user.is_authenticated:
                Emailsent.objects.create(
                    member=request.user.member, prospect=None, email=email, sent_date_time=now
                )
            else:
                Emailsent.objects.create(
                    member=None, prospect=prospect, email=email, sent_date_time=now
                )
        except SMTPDataError:
            logger.exception('SMTPDataError sending order confirmation email')

        #####################################
        # END Send Order Confirmation Email #
        #####################################

        # Delete the cart
        cart.delete()

        response = JsonResponse(
            {
                'checkout_session_success': 'success',
                'order_identifier': order.identifier,
                'order-api-version': order_api_version,
            },
            safe=False,
        )

    except stripe.error.InvalidRequestError as e:
        logger.error(f'Invalid Stripe session: {str(e)}')
        error_dict = {
            "error": 'invalid-session',
            "description": str(e)
        }
        response = JsonResponse(
            {
                'checkout_session_success': 'error',
                'errors': error_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    except Exception as e:
        logger.error(f'Unexpected error processing checkout session: {str(e)}')
        error_dict = {
            "error": 'unexpected-error',
            "description": str(e)
        }
        response = JsonResponse(
            {
                'checkout_session_success': 'error',
                'errors': error_dict,
                'order-api-version': order_api_version,
            },
            safe=False,
        )

    return response


@csrf_exempt
def stripe_webhook(request):
    """
    Handle incoming Stripe webhook events.
    Supports checkout.session.completed and checkout.session.expired events.
    Uses signature verification for security.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'method-not-allowed'}, status=405)

    # Get the webhook payload and signature
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    # Get webhook secret from settings
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

    if not webhook_secret:
        logger.error('STRIPE_WEBHOOK_SECRET not configured')
        return JsonResponse({'error': 'webhook-not-configured'}, status=500)

    # Verify webhook signature and construct event
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f'Invalid webhook payload: {str(e)}')
        return JsonResponse({'error': 'invalid-payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f'Invalid webhook signature: {str(e)}')
        return JsonResponse({'error': 'invalid-signature'}, status=400)

    # Handle the event
    event_type = event['type']

    if event_type == 'checkout.session.completed':
        return handle_checkout_session_completed(event)
    elif event_type == 'checkout.session.expired':
        return handle_checkout_session_expired(event)
    else:
        # Unknown event type - log and acknowledge
        logger.info(f'Unhandled webhook event type: {event_type}')
        return JsonResponse({'received': True}, status=200)


def handle_checkout_session_completed(event):
    """
    Handle checkout.session.completed webhook event.
    Creates order if it doesn't already exist (idempotency).
    """
    session = event['data']['object']
    session_id = session.get('id')
    payment_intent_id = session.get('payment_intent')

    logger.info(f'Processing checkout.session.completed for session: {session_id}')

    # Check if order already exists for this payment_intent (idempotency)
    if payment_intent_id:
        try:
            existing_payment = Orderpayment.objects.get(stripe_payment_intent_id=payment_intent_id)
            existing_order = existing_payment.order_set.first()
            if existing_order:
                logger.info(f'Order already exists: {existing_order.identifier}')
                return JsonResponse({
                    'received': True,
                    'order_identifier': existing_order.identifier
                }, status=200)
        except Orderpayment.DoesNotExist:
            pass  # No existing order, proceed with creation

    # Get cart_id from session metadata
    cart_id = session.get('metadata', {}).get('cart_id')
    if not cart_id:
        logger.error(f'No cart_id in session metadata for session: {session_id}')
        return JsonResponse({'error': 'no-cart-id'}, status=400)

    # Look up the cart
    try:
        cart = Cart.objects.get(id=cart_id)
    except Cart.DoesNotExist:
        logger.error(f'Cart not found: {cart_id}')
        return JsonResponse({'error': 'cart-not-found'}, status=400)

    # Verify payment is completed
    if session.get('payment_status') != 'paid':
        logger.warning(f'Payment not completed for session: {session_id}')
        return JsonResponse({'error': 'payment-not-completed'}, status=400)

    try:
        # Retrieve full session details from Stripe
        full_session = stripe.checkout.Session.retrieve(session_id)

        # Extract address information
        customer_details = full_session.customer_details
        # Stripe API change: shipping_details moved to collected_information
        shipping_details = None
        if hasattr(full_session, 'collected_information') and full_session.collected_information:
            shipping_details = getattr(full_session.collected_information, 'shipping_details', None)

        # Get customer name and email
        customer_name = customer_details.name if customer_details else 'Customer'
        customer_email = full_session.customer_email or (
            customer_details.email if customer_details else ''
        )

        # Create order identifier
        order_identifier = identifier.getNewOrderIdentifier()

        # CRITICAL: Wrap all database writes in atomic transaction
        # If any write fails, ALL writes are rolled back (HIGH-004)
        with transaction.atomic():
            # Create Payment object
            payment = Orderpayment.objects.create(
                email=customer_email,
                payment_type='card',
                card_name=customer_name,
                stripe_payment_intent_id=payment_intent_id,
            )

            # Create Shipping Address object
            shipping_address = Ordershippingaddress.objects.create(
                name=shipping_details.name if shipping_details else customer_name,
                address_line1=shipping_details.address.line1 if shipping_details and shipping_details.address else '',
                city=shipping_details.address.city if shipping_details and shipping_details.address else '',
                state=shipping_details.address.state if shipping_details and shipping_details.address else '',
                zip=shipping_details.address.postal_code if shipping_details and shipping_details.address else '',
                country=shipping_details.address.country if shipping_details and shipping_details.address else '',
                country_code=shipping_details.address.country if shipping_details and shipping_details.address else '',
            )

            # Create Billing Address object
            billing_address = Orderbillingaddress.objects.create(
                name=customer_name,
                address_line1=customer_details.address.line1 if customer_details and customer_details.address else '',
                city=customer_details.address.city if customer_details and customer_details.address else '',
                state=customer_details.address.state if customer_details and customer_details.address else '',
                zip=customer_details.address.postal_code if customer_details and customer_details.address else '',
                country=customer_details.address.country if customer_details and customer_details.address else '',
                country_code=customer_details.address.country if customer_details and customer_details.address else '',
            )

            # Calculate order totals from cart
            cart_totals_dict = order_utils.get_cart_totals(cart)

            # Create Order object
            now = timezone.now()

            # Determine if member or prospect
            member = None
            prospect = None
            if cart.member:
                member = cart.member
            else:
                # Anonymous checkout - get or create prospect
                prospect, created = Prospect.objects.get_or_create(
                    email=customer_email,
                    defaults={
                        'pr_cd': identifier.getNewProspectCode(),
                        'created_date_time': timezone.now()
                    }
                )

            order = Order.objects.create(
                identifier=order_identifier,
                member=member,
                prospect=prospect,
                payment=payment,
                shipping_address=shipping_address,
                billing_address=billing_address,
                sales_tax_amt=0,
                item_subtotal=cart_totals_dict['item_subtotal'],
                item_discount_amt=cart_totals_dict['item_discount'],
                shipping_amt=cart_totals_dict['shipping_subtotal'],
                shipping_discount_amt=cart_totals_dict['shipping_discount'],
                order_total=cart_totals_dict['cart_total'],
                agreed_with_terms_of_sale=True,
                order_date_time=now,
            )

            # Create Ordersku objects - need to construct proper cart_item_dict
            cart_skus = Cartsku.objects.filter(cart=cart)
            for cart_sku in cart_skus:
                Ordersku.objects.create(
                    order=order,
                    sku=cart_sku.sku,
                    quantity=cart_sku.quantity,
                    price_each=cart_sku.sku.skuprice_set.latest('created_date_time').price,
                )

            # Create Orderdiscount records
            cart_discounts = Cartdiscount.objects.filter(cart=cart)
            for cart_discount in cart_discounts:
                Orderdiscount.objects.create(
                    order=order,
                    discountcode=cart_discount.discountcode,
                    applied=True,  # If it's in the cart, it was applied
                )

            # Create Orderstatus record
            Orderstatus.objects.create(
                order=order,
                status=Status.objects.get(
                    identifier=Orderconfiguration.objects.get(key='initial_order_status').string_value
                ),
                created_date_time=now,
            )

            # Create Ordershippingmethod record
            cart_shipping_method = Cartshippingmethod.objects.get(cart=cart)
            Ordershippingmethod.objects.create(
                order=order,
                shippingmethod=cart_shipping_method.shippingmethod
            )

        # Order created successfully - now attempt post-transaction operations
        # Email sending and cart deletion are OUTSIDE the transaction (HIGH-004)
        # If these fail, the order is still saved (customer has paid!)

        # Attempt to send order confirmation email
        try:
            send_order_confirmation_email(order, customer_name, customer_email, cart)

        except Exception as email_error:
            # Email failed - log failure but order is still saved (HIGH-004)
            logger.error(f'Order confirmation email failed for order {order_identifier}: {str(email_error)}')

            # Determine failure type
            failure_type = 'formatting'
            if 'DoesNotExist' in str(type(email_error)):
                failure_type = 'template_lookup'
            elif 'SMTP' in str(type(email_error)) or 'SMTPException' in str(type(email_error)):
                failure_type = 'smtp_send'

            # Create failure record
            Orderemailfailure.objects.create(
                order=order,
                failure_type=failure_type,
                error_message=str(email_error),
                customer_email=customer_email,
                is_member_order=(member is not None),
                phase='email_send'
            )

            # Log for CloudWatch alarm
            logger.error(f'[ORDER_EMAIL_FAILURE] type={failure_type} order={order_identifier} email={customer_email}')

        # Delete cart regardless of email success/failure (consistent with existing checkout flow)
        # Customer will see order confirmation page, can contact support if email not received
        try:
            cart.delete()
        except Exception as cart_delete_error:
            # Cart deletion failed - log it but don't fail the request
            logger.error(f'Cart deletion failed for order {order_identifier}: {str(cart_delete_error)}')
            Orderemailfailure.objects.create(
                order=order,
                failure_type='cart_delete',
                error_message=str(cart_delete_error),
                customer_email=customer_email,
                is_member_order=(member is not None),
                phase='post_email'
            )
            logger.error(f'[ORDER_EMAIL_FAILURE] type=cart_delete order={order_identifier} email={customer_email}')

        logger.info(f'Order created successfully via webhook: {order_identifier}')

        return JsonResponse({
            'received': True,
            'order_identifier': order_identifier
        }, status=200)

    except Exception as e:
        logger.exception(f'Error processing checkout.session.completed webhook: {str(e)}')
        return JsonResponse({'error': 'processing-error'}, status=500)


def handle_checkout_session_expired(event):
    """
    Handle checkout.session.expired webhook event.
    Just log the expiration for monitoring purposes.
    """
    session = event['data']['object']
    session_id = session.get('id')

    logger.info(f'Checkout session expired: {session_id}')

    return JsonResponse({'received': True}, status=200)


def send_order_confirmation_email(order, customer_name, customer_email, cart):
    """
    Helper function to send order confirmation email.
    Used by both checkout_session_success and webhook handlers.
    """
    try:
        # Get cart items and totals
        cart_item_dict = order_utils.get_cart_items(None, cart)
        cart_totals_dict = order_utils.get_cart_totals(cart)
        discount_code_dict = order_utils.get_cart_discount_codes(cart)

        # Get shipping method
        order_shipping_method = Ordershippingmethod.objects.get(order=order)

        # Build email text
        order_info_text = order_utils.get_confirmation_email_order_info_text_format(order.identifier)
        product_text = order_utils.get_confirmation_email_product_information_text_format(cart_item_dict)
        shipping_text = order_utils.get_confirmation_email_shipping_information_text_format(
            order_shipping_method.shippingmethod
        )
        discount_code_text = order_utils.get_confirmation_email_discount_code_text_format(discount_code_dict)
        order_totals_text = order_utils.get_confirmation_email_order_totals_text_format(cart_totals_dict)
        payment_text = order_utils.get_confirmation_email_order_payment_text_format(order.payment)
        shipping_address_text = order_utils.get_confirmation_email_order_address_text_format(order.shipping_address)
        billing_address_text = order_utils.get_confirmation_email_order_address_text_format(order.billing_address)

        # Determine member vs prospect
        if order.member:
            order_confirmation_em_cd = Orderconfiguration.objects.get(
                key='order_confirmation_em_cd_member'
            ).string_value
            email = Email.objects.get(em_cd=order_confirmation_em_cd)

            email_namespace = {
                'line_break': '\r\n\r\n',
                'short_line_break': '\r\n',
                'recipient_first_name': customer_name,
                'order_information': order_info_text,
                'product_information': product_text,
                'shipping_information': shipping_text,
                'discount_information': discount_code_text,
                'order_total_information': order_totals_text,
                'payment_information': payment_text,
                'shipping_address_information': shipping_address_text,
                'billing_address_information': billing_address_text,
                'ENVIRONMENT_DOMAIN': settings.ENVIRONMENT_DOMAIN,
                'identifier': order.identifier,
                'em_cd': email.em_cd,
                'mb_cd': order.member.mb_cd,
            }
        else:
            order_confirmation_em_cd = Orderconfiguration.objects.get(
                key='order_confirmation_em_cd_prospect'
            ).string_value
            email = Email.objects.get(em_cd=order_confirmation_em_cd)

            prospect = order.prospect
            prospect.swa_comment = f'Captured from Stripe Checkout order identifier: {order.identifier}'
            prospect.save()

            prospect_email_unsubscribe_str = (
                'You are NOT included in our email marketing list. If you would like to be '
                'added to our marketing email list please reply to this email and let us know.'
            )

            email_namespace = {
                'line_break': '\r\n\r\n',
                'short_line_break': '\r\n',
                'recipient_first_name': customer_name,
                'order_information': order_info_text,
                'product_information': product_text,
                'shipping_information': shipping_text,
                'discount_information': discount_code_text,
                'order_total_information': order_totals_text,
                'payment_information': payment_text,
                'shipping_address_information': shipping_address_text,
                'billing_address_information': billing_address_text,
                'ENVIRONMENT_DOMAIN': settings.ENVIRONMENT_DOMAIN,
                'identifier': order.identifier,
                'em_cd': email.em_cd,
                'pr_cd': prospect.pr_cd,
                'prosepct_email_unsubscribe_str': prospect_email_unsubscribe_str,
            }

        formatted_email_body = email.body_text.format(**email_namespace)

        msg = EmailMultiAlternatives(
            subject=email.subject,
            body=formatted_email_body,
            from_email=email.from_address,
            to=[customer_email],
            bcc=[email.bcc_address] if email.bcc_address else [],
            reply_to=[email.from_address],
        )

        msg.send(fail_silently=False)

        now = timezone.now()
        if order.member:
            Emailsent.objects.create(
                member=order.member, prospect=None, email=email, sent_date_time=now
            )
        else:
            Emailsent.objects.create(
                member=None, prospect=order.prospect, email=email, sent_date_time=now
            )

        logger.info(f'Order confirmation email sent for order: {order.identifier}')

    except SMTPDataError:
        logger.exception('SMTPDataError sending order confirmation email')
        raise  # Re-raise so handle_checkout_session_completed can handle it (HIGH-004)
    except Exception as e:
        logger.exception(f'Error sending order confirmation email: {str(e)}')
        raise  # Re-raise so handle_checkout_session_completed can handle it (HIGH-004)


def anonymous_email_address_payment_lookup(request):
    # raise ValueError('A very specific bad thing happened.')
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:

        anonymous_email_address = None
        if request.method == 'POST' and 'anonymous_email_address' in request.POST:
            anonymous_email_address = request.POST['anonymous_email_address']

        if anonymous_email_address is not None:
            if User.objects.filter(email=anonymous_email_address).exists():
                error_dict = {
                    "error": 'email-address-is-associated-with-member',
                    'description': (
                        'This email address is already associated with a member account. Please <span '
                        'class="login-form-error-link"><a href=\"/login?next=checkout/confirm\">login</a>'
                        '</span> to continue.'
                    ),
                }
                response = JsonResponse(
                    {
                        'checkout_allowed': checkout_allowed,
                        'anonymous_email_address_payment_lookup': 'error',
                        'errors': error_dict,
                        'order-api-version': order_api_version,
                    },
                    safe=False,
                )
            else:
                stripe_publishable_key = settings.STRIPE_PUBLISHABLE_SECRET_KEY
                if Prospect.objects.filter(email=anonymous_email_address).exists():
                    customer_dict = None
                    response = JsonResponse(
                        {
                            'checkout_allowed': checkout_allowed,
                            'anonymous_email_address_payment_lookup': 'success',
                            'stripe_publishable_key': stripe_publishable_key,
                            'customer_data': customer_dict,
                            'order-api-version': order_api_version,
                        },
                        safe=False,
                    )
                else:
                    now = timezone.now()
                    email_unsubscribe_string = identifier.getNewProspectEmailUnsubscribeString()
                    email_unsubscribe_string_signed = email_unsubscribe_signer.sign(email_unsubscribe_string)
                    email_unsubscribe_string_signed = email_unsubscribe_string_signed.rsplit(':', 1)[1]
                    pr_cd = identifier.getNewProspectCode()
                    Prospect.objects.create(
                        email=anonymous_email_address,
                        email_unsubscribed=True,
                        email_unsubscribe_string=email_unsubscribe_string,
                        email_unsubscribe_string_signed=email_unsubscribe_string_signed,
                        swa_comment='Captured from incomplete anonymous order',
                        pr_cd=pr_cd,
                        created_date_time=now,
                    )
                    customer_dict = None
                    response = JsonResponse(
                        {
                            'checkout_allowed': checkout_allowed,
                            'anonymous_email_address_payment_lookup': 'success',
                            'stripe_publishable_key': stripe_publishable_key,
                            'customer_data': customer_dict,
                            'order-api-version': order_api_version,
                        },
                        safe=False,
                    )
        else:
            error_dict = {
                "error": 'anonymous-email-address-required',
                'description': 'Anonymous email address is required',
            }
            response = JsonResponse(
                {
                    'checkout_allowed': checkout_allowed,
                    'anonymous_email_address_payment_lookup': 'error',
                    'errors': error_dict,
                    'order-api-version': order_api_version,
                },
                safe=False,
            )
    else:
        response = JsonResponse(
            {'checkout_allowed': checkout_allowed, 'order-api-version': order_api_version}, safe=False
        )
    return response


def change_confirmation_email_address(request):
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        cart = order_utils.look_up_cart(request)
        cart.payment = None
        cart.shipping_address = None
        cart.save()
        response = JsonResponse(
            {
                'checkout_allowed': checkout_allowed,
                'change_confirmation_email_address': 'success',
                'order-api-version': order_api_version,
            },
            safe=False,
        )
    else:
        response = JsonResponse(
            {'checkout_allowed': checkout_allowed, 'order-api-version': order_api_version}, safe=False
        )
    return response
