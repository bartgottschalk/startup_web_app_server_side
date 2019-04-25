from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache
from django.template import loader
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.db.models import Max
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from smtplib import SMTPDataError
from django.core.signing import TimestampSigner, Signer, SignatureExpired, BadSignature
from user.models import Member, Defaultshippingaddress, Prospect, Emailunsubscribereasons, EmailunsubscribereasonsAdmin, Termsofuse, Membertermsofuseversionagreed, Emailtype, Emailstatus, Email, Emailsent, Ad, Adtype, Adstatus
from order.utilities import order_utils
from order.models import Orderpayment, Ordershippingaddress, Orderbillingaddress, Order, Ordersku, Orderdiscount, Status, Orderstatus, Ordershippingmethod
from order.models import Orderconfiguration, Sku, Skuprice, Skuimage, Skutype, Skuinventory, Cartshippingaddress, Cartpayment, Cart, Cartsku, Cartdiscount, Discountcode, Discounttype, Productsku, Product, Productimage, Productvideo, Shippingmethod, Cartshippingmethod
from StartupWebApp.form import validator
from StartupWebApp.utilities import random, identifier
import time
from clientevent.models import Configuration as ClientEventConfiguration, AJAXError
from django.utils import timezone
import json
import stripe
stripe.api_key = settings.STRIPE_SERVER_SECRET_KEY
stripe.log = settings.STRIPE_LOG_LEVEL

email_unsubscribe_signer = Signer(salt='email_unsubscribe')
 
#from user.models import 


order_api_version = '0.0.1'

#@cache_control(max_age=10) #set cache control to 10 seconds
@never_cache

def index(request):
    return HttpResponse("Hello, you're at the order API (version " + order_api_version + ") root. Nothing to see here...")

def order_detail(request, order_identifier):
    #raise ValueError('A very specific bad thing happened.')
    #print(order_identifier)
    try:
        order = Order.objects.get(identifier=order_identifier)
        #print(order)
        #print(order.member)
        #print(request.user.member)
        if request.user.is_anonymous:
            print('AnonymousUser found!')
            if order.member is None:
                order_data = order_utils.get_order_data(order)
                response = JsonResponse({'order_detail':'success','order_data':order_data, 'order-api-version':order_api_version}, safe=False)    
            else:
                error_dict = {"error" : 'log-in-required-to-view-order'}
                response = JsonResponse({'order_detail':'error','errors': error_dict,'order_identifier':order_identifier, 'order-api-version':order_api_version}, safe=False)
        else:
            if order.member == request.user.member:
                order_data = order_utils.get_order_data(order)
                response = JsonResponse({'order_detail':'success','order_data':order_data, 'order-api-version':order_api_version}, safe=False)    
            else:
                error_dict = {"error" : 'order-not-in-account'}
                response = JsonResponse({'order_detail':'error','errors': error_dict,'order_identifier':order_identifier, 'order-api-version':order_api_version}, safe=False)
    except (ObjectDoesNotExist, ValueError) as e:
        order = None
        #print(e)
        error_dict = {"error" : 'order-not-found'}
        response = JsonResponse({'order_detail':'error','errors': error_dict,'order_identifier':order_identifier, 'order-api-version':order_api_version}, safe=False)
    return response

def products(request):
    #raise ValueError('A very specific bad thing happened.')    
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
            if price_low is None or Skuprice.objects.filter(sku=product_sku.sku).latest('created_date_time').price < price_low:
                price_low = Skuprice.objects.filter(sku=product_sku.sku).latest('created_date_time').price
            if price_high is None or Skuprice.objects.filter(sku=product_sku.sku).latest('created_date_time').price > price_high:
                price_high = Skuprice.objects.filter(sku=product_sku.sku).latest('created_date_time').price
        product_data['price_low'] = price_low
        product_data['price_high'] = price_high


        product_image_main_exists = Productimage.objects.filter(product=product, main_image=True).exists()
        product_image_url = None
        if product_image_main_exists is True:
            product_image_url = Productimage.objects.get(product=product, main_image=True).image_url
        product_data['product_image_url'] = product_image_url
        products_dict[product.identifier] = product_data

    response = JsonResponse({'products_data':products_dict,'order-api-version':order_api_version}, safe=False)
    return response 

def product(request, product_identifier):
    #raise ValueError('A very specific bad thing happened.')
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

        response = JsonResponse({'product':'success','product_identifier':product_identifier,'product_data':product_data,'order-api-version':order_api_version}, safe=False)
    except (ObjectDoesNotExist, ValueError) as e:
        print(e)
        error_dict = {"error" : 'product-identifier-not-found'}
        response = JsonResponse({'product':'error','errors': error_dict,'product_identifier':product_identifier,'order-api-version':order_api_version}, safe=False)
    return response

def checkout_allowed(request):
    #raise ValueError('A very specific bad thing happened.')    
    checkout_allowed = order_utils.checkout_allowed(request)
    response = JsonResponse({'checkout_allowed':checkout_allowed, 'order-api-version':order_api_version}, safe=False)
    return response

def cart_items(request):
    #raise ValueError('A very specific bad thing happened.')    
    #print(request.user.session)
    cart = order_utils.look_up_cart(request)
    cart_item_dict = order_utils.get_cart_items(request, cart)
    response = JsonResponse({'cart_found':(True if cart is not None else False),'item_data':cart_item_dict,'order-api-version':order_api_version}, safe=False)
    return response 

def confirm_items(request):
    #raise ValueError('A very specific bad thing happened.')    
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        cart = order_utils.look_up_cart(request)
        confirm_item_dict = order_utils.get_cart_items(request, cart)
        response = JsonResponse({'checkout_allowed':checkout_allowed, 'cart_found':(True if cart is not None else False),'item_data':confirm_item_dict,'order-api-version':order_api_version}, safe=False)
    else:
        response = JsonResponse({'checkout_allowed':checkout_allowed,'order-api-version':order_api_version}, safe=False)
    return response 

def cart_shipping_methods(request):
    #raise ValueError('A very specific bad thing happened.')    
    shipping_methods = {}
    shipping_method_selected = None
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        if Cartshippingmethod.objects.filter(cart=cart).exists():
            shipping_method_selected = Cartshippingmethod.objects.get(cart=cart).shippingmethod.identifier            
        else:
            Cartshippingmethod.objects.create(cart=cart, shippingmethod=Shippingmethod.objects.get(identifier=Orderconfiguration.objects.get(key='default_shipping_method').string_value))
            shipping_method_selected = Orderconfiguration.objects.get(key='default_shipping_method').string_value

        shipping_method_arr = Shippingmethod.objects.filter(active=True,).order_by('-shipping_cost')

        counter = 0
        for shippingmethod in shipping_method_arr:
            shipping_method_data = {}
            shipping_method_data['identifier'] = shippingmethod.identifier
            shipping_method_data['carrier'] = shippingmethod.carrier
            shipping_method_data['shipping_cost'] = shippingmethod.shipping_cost
            shipping_method_data['tracking_code_base_url'] = shippingmethod.tracking_code_base_url
            shipping_methods[counter] = shipping_method_data
            counter += 1

    response = JsonResponse({'cart_found':(True if cart is not None else False),'cart_shipping_methods':shipping_methods, 'shipping_method_selected':shipping_method_selected, 'order-api-version':order_api_version}, safe=False)
    return response 

def confirm_shipping_method(request):
    #raise ValueError('A very specific bad thing happened.')    
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        cart = order_utils.look_up_cart(request)
        shipping_method = {}
        if cart is not None:
            if Cartshippingmethod.objects.filter(cart=cart).exists():
                shipping_method_selected = Cartshippingmethod.objects.get(cart=cart).shippingmethod
                #print(shipping_method_selected)
                shipping_method['identifier'] = shipping_method_selected.identifier
                shipping_method['carrier'] = shipping_method_selected.carrier
                shipping_method['shipping_cost'] = shipping_method_selected.shipping_cost
                shipping_method['tracking_code_base_url'] = shipping_method_selected.tracking_code_base_url
        response = JsonResponse({'checkout_allowed':checkout_allowed, 'cart_found':(True if cart is not None else False),'confirm_shipping_method':shipping_method, 'order-api-version':order_api_version}, safe=False)
    else:
        response = JsonResponse({'checkout_allowed':checkout_allowed,'order-api-version':order_api_version}, safe=False)
    return response 

def cart_discount_codes(request):
    #raise ValueError('A very specific bad thing happened.')    
    #print(request.user.session)
    cart = order_utils.look_up_cart(request)
    discount_code_dict = order_utils.get_cart_discount_codes(cart);
    response = JsonResponse({'cart_found':(True if cart is not None else False),'discount_code_data':discount_code_dict,'order-api-version':order_api_version}, safe=False)
    return response 

def confirm_discount_codes(request):
    #raise ValueError('A very specific bad thing happened.')    
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        cart = order_utils.look_up_cart(request)
        discount_code_dict = order_utils.get_cart_discount_codes(cart);
        response = JsonResponse({'checkout_allowed':checkout_allowed, 'cart_found':(True if cart is not None else False),'discount_code_data':discount_code_dict,'order-api-version':order_api_version}, safe=False)
    else:
        response = JsonResponse({'checkout_allowed':checkout_allowed,'order-api-version':order_api_version}, safe=False)
    return response 

def cart_totals(request):
    #raise ValueError('A very specific bad thing happened.')    
    #print(request.user.session)
    cart = order_utils.look_up_cart(request)
    cart_totals_dict = order_utils.get_cart_totals(cart);
    response = JsonResponse({'cart_found':(True if cart is not None else False),'cart_totals_data':cart_totals_dict,'order-api-version':order_api_version}, safe=False)
    return response 

def confirm_totals(request):
    #raise ValueError('A very specific bad thing happened.')    

    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        cart = order_utils.look_up_cart(request)
        cart_totals_dict = order_utils.get_cart_totals(cart);
        response = JsonResponse({'checkout_allowed':checkout_allowed, 'cart_found':(True if cart is not None else False),'confirm_totals_data':cart_totals_dict, 'order-api-version':order_api_version}, safe=False)
    else:
        response = JsonResponse({'checkout_allowed':checkout_allowed,'order-api-version':order_api_version}, safe=False)
    return response 

def confirm_payment_data(request):
    #raise ValueError('A very specific bad thing happened.')    

    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        stripe_publishable_key = settings.STRIPE_PUBLISHABLE_SECRET_KEY
        customer_dict = None
        cart = order_utils.look_up_cart(request)
        shipping_address_dict = {}
        if cart is not None:
            if request.user.is_authenticated:
                email = request.user.email
            else:
                email = None

            #print(cart.shipping_address)
            if cart.shipping_address is not None:
                shipping_address_dict = order_utils.load_address_dict(cart.shipping_address)
            else:
                if request.user.is_authenticated:
                    if request.user.member.use_default_shipping_and_payment_info == True:
                        if request.user.member.default_shipping_address is not None:
                            cart_shipping_address = Cartshippingaddress.objects.create(name=request.user.member.default_shipping_address.name, address_line1=request.user.member.default_shipping_address.address_line1, city=request.user.member.default_shipping_address.city, state=request.user.member.default_shipping_address.state, zip=request.user.member.default_shipping_address.zip, country=request.user.member.default_shipping_address.country, country_code=request.user.member.default_shipping_address.country_code)
                            cart.shipping_address = cart_shipping_address
                            cart.save()
                            shipping_address_dict = order_utils.load_address_dict(cart.shipping_address)
            if cart.payment is None:
                if request.user.is_authenticated:
                    if request.user.member.use_default_shipping_and_payment_info == True:
                        if request.user.member.stripe_customer_token is not None:
                            cart_payment = Cartpayment.objects.create(stripe_customer_token=request.user.member.stripe_customer_token, email=request.user.email)
                            cart.payment = cart_payment
                            cart.save()
            if cart.shipping_address is not None and cart.payment is not None:
                if cart.payment.stripe_customer_token is not None:
                    stripe_customer_token = cart.payment.stripe_customer_token
                    customer = stripe.Customer.retrieve(stripe_customer_token)
                    #print('### CUSTOMER ###')
                    #print(customer)
                    #print(customer.sources)
                    #print(customer.sources.data)
                    #print('### END CUSTOMER ###')
                    customer_dict = order_utils.get_stripe_customer_payment_data(customer, shipping_address_dict, cart.payment.stripe_card_id)    
                    #print(customer_dict)                
        else:
            email = None
        response = JsonResponse({'checkout_allowed':checkout_allowed, 'stripe_publishable_key':stripe_publishable_key, 'email':email, 'customer_data':customer_dict, 'order-api-version':order_api_version}, safe=False)
    else:
        response = JsonResponse({'checkout_allowed':checkout_allowed,'order-api-version':order_api_version}, safe=False)
    return response 

def cart_add_product_sku(request):
    #raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is None:
        cart = order_utils.create_cart(request)
    sku_id = None
    if request.method == 'POST' and 'sku_id' in request.POST:    
        sku_id = request.POST['sku_id']
    #print(sku_id)
    quantity = None
    if request.method == 'POST' and 'quantity' in request.POST:    
        quantity = request.POST['quantity']
    #print(sku_id)
    if sku_id is not None:
        try:
            quantity_valid = validator.validateSkuQuantity(quantity)
            if quantity_valid == True:
                sku = Sku.objects.get(id=sku_id)
                product_sku = Productsku.objects.get(sku=sku)
                cart_sku_exists = Cartsku.objects.filter(cart=cart, sku=product_sku.sku).exists()
                if cart_sku_exists == True:
                    cart_sku = Cartsku.objects.get(cart=cart, sku=product_sku.sku)
                    cart_sku.quantity = cart_sku.quantity + int(quantity)
                    cart_sku.save()
                else:
                    Cartsku.objects.create(cart=cart, sku=product_sku.sku, quantity=int(quantity))
                cart_item_count = order_utils.count_cart_items(cart)
                response = JsonResponse({'cart_add_product_sku':'success', 'sku_id':sku_id, 'cart_item_count': cart_item_count, 'order-api-version':order_api_version}, safe=False)
                order_utils.set_anonymous_cart_cookie(request, response, cart)
            else:
                #print('VALIDATION ERRORS - RETURN ERRORS')
                error_dict = {"quantity" : quantity_valid}
                return JsonResponse({'cart_add_product_sku': 'error', 'errors':error_dict, 'sku_id':sku_id, 'order-api-version':order_api_version}, safe=False )
        except (ObjectDoesNotExist, ValueError) as e:
            print(e)
            error_dict = {"error" : 'sku-not-found'}
            response = JsonResponse({'cart_add_product_sku':'error', 'errors': error_dict,'sku_id':sku_id, 'order-api-version':order_api_version}, safe=False)
    else:
        error_dict = {"error" : 'sku-id-required'}
        response = JsonResponse({'cart_add_product_sku':'error', 'errors': error_dict,'sku_id':sku_id, 'order-api-version':order_api_version}, safe=False)
    return response

def cart_update_sku_quantity(request):
    #raise ValueError('A very specific bad thing happened.')
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
                sku_subtotal = Skuprice.objects.filter(sku=cart_sku.sku).latest('created_date_time').price * Cartsku.objects.get(cart=cart, sku=cart_sku.sku).quantity
                discount_code_dict = order_utils.get_cart_discount_codes(cart);
                cart_totals_dict = order_utils.get_cart_totals(cart);
                response = JsonResponse({'cart_update_sku_quantity':'success', 'cart_found':(True if cart is not None else False), 'sku_id':sku_id, 'sku_subtotal': sku_subtotal, 'discount_code_data': discount_code_dict, 'cart_totals_data':cart_totals_dict, 'order-api-version':order_api_version}, safe=False)
            except (ObjectDoesNotExist, ValueError) as e:
                print(e)
                error_dict = {"error" : 'cart-sku-not-found'}
                response = JsonResponse({'cart_update_sku_quantity':'error','errors': error_dict,'sku_id':sku_id, 'order-api-version':order_api_version}, safe=False)
        else:            
            error_dict = {"error" : 'sku-id-required'}
            response = JsonResponse({'cart_update_sku_quantity':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    else:            
        error_dict = {"error" : 'cart-not-found'}
        response = JsonResponse({'cart_update_sku_quantity':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    return response

def cart_remove_sku(request):
    #raise ValueError('A very specific bad thing happened.')
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

                discount_code_dict = order_utils.get_cart_discount_codes(cart);
                cart_totals_dict = order_utils.get_cart_totals(cart);
                cart_item_count = order_utils.count_cart_items(cart)
                response = JsonResponse({'cart_remove_sku':'success', 'cart_found':(True if cart is not None else False), 'sku_id':sku_id, 'cart_item_count': cart_item_count, 'cart_shipping_methods':shipping_methods, 'shipping_method_selected':shipping_method_selected, 'discount_code_data': discount_code_dict, 'cart_totals_data':cart_totals_dict, 'order-api-version':order_api_version}, safe=False)
            except (ObjectDoesNotExist, ValueError) as e:
                print(e)
                error_dict = {"error" : 'cart-sku-not-found'}
                response = JsonResponse({'cart_remove_sku':'error','errors': error_dict,'sku_id':sku_id, 'order-api-version':order_api_version}, safe=False)
        else:            
            error_dict = {"error" : 'sku-id-required'}
            response = JsonResponse({'cart_remove_sku':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    else:            
        error_dict = {"error" : 'cart-not-found'}
        response = JsonResponse({'cart_remove_sku':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    return response

def cart_apply_discount_code(request):
    #raise ValueError('A very specific bad thing happened.')
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
                    error_dict = {"error" : 'cart-discount-code-not-active'}
                    response = JsonResponse({'cart_apply_discount_code':'error','errors': error_dict,'discount_code_id':discount_code_id, 'order-api-version':order_api_version}, safe=False)
                elif Cartdiscount.objects.filter(cart=cart, discountcode=discountcode).exists():
                    error_dict = {"error" : 'cart-discount-code-already-applied'}
                    response = JsonResponse({'cart_apply_discount_code':'error','errors': error_dict,'discount_code_id':discount_code_id, 'order-api-version':order_api_version}, safe=False)
                else:
                    cartdiscount = Cartdiscount.objects.create(cart=cart, discountcode=discountcode)
                    discount_code_dict = order_utils.get_cart_discount_codes(cart);
                    cart_totals_dict = order_utils.get_cart_totals(cart);
                    response = JsonResponse({'cart_apply_discount_code':'success', 'cart_found':(True if cart is not None else False), 'discount_code_id':discount_code_id, 'discount_code_data': discount_code_dict, 'cart_totals_data':cart_totals_dict, 'order-api-version':order_api_version}, safe=False)
            except (ObjectDoesNotExist, ValueError) as e:
                print(e)
                error_dict = {"error" : 'cart-discount-code-not-found'}
                response = JsonResponse({'cart_apply_discount_code':'error','errors': error_dict,'discount_code_id':discount_code_id, 'order-api-version':order_api_version}, safe=False)
        else:            
            error_dict = {"error" : 'discount-code-required'}
            response = JsonResponse({'cart_apply_discount_code':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    else:            
        error_dict = {"error" : 'cart-not-found'}
        response = JsonResponse({'cart_apply_discount_code':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    return response

def cart_remove_discount_code(request):
    #raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        discount_code_id = None
        if request.method == 'POST' and 'discount_code_id' in request.POST:    
            discount_code_id = request.POST['discount_code_id']
        if discount_code_id is not None:
            try:
                discounttype__applies_to = Discountcode.objects.get(id=discount_code_id).discounttype.applies_to
                Cartdiscount.objects.filter(cart=cart, discountcode=Discountcode.objects.get(id=discount_code_id)).delete()
                discount_code_dict = order_utils.get_cart_discount_codes(cart);
                cart_totals_dict = order_utils.get_cart_totals(cart);
                response = JsonResponse({'cart_remove_discount_code':'success', 'cart_found':(True if cart is not None else False), 'discount_code_id':discount_code_id, 'discount_code_data': discount_code_dict, 'cart_totals_data':cart_totals_dict, 'order-api-version':order_api_version}, safe=False)
            except (ObjectDoesNotExist, ValueError) as e:
                print(e)
                error_dict = {"error" : 'cart-discount-code-not-found'}
                response = JsonResponse({'cart_remove_discount_code':'error','errors': error_dict,'discount_code_id':discount_code_id, 'order-api-version':order_api_version}, safe=False)
        else:            
            error_dict = {"error" : 'discount-code-required'}
            response = JsonResponse({'cart_remove_discount_code':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    else:            
        error_dict = {"error" : 'cart-not-found'}
        response = JsonResponse({'cart_remove_discount_code':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    return response

def cart_update_shipping_method(request):
    #raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        shipping_method_identifier = None
        if request.method == 'POST' and 'shipping_method_identifier' in request.POST:    
            shipping_method_identifier = request.POST['shipping_method_identifier']
        if shipping_method_identifier is not None:
            try:
                #raise ValueError('A very specific bad thing happened.')
                cart_shipping_method_exists = Cartshippingmethod.objects.filter(cart=cart).exists()
                if cart_shipping_method_exists == True:
                    cart_shipping_method = Cartshippingmethod.objects.get(cart=cart)
                    cart_shipping_method.shippingmethod = Shippingmethod.objects.get(identifier=shipping_method_identifier)
                    cart_shipping_method.save()
                else:
                    Cartshippingmethod.objects.create(cart=cart, shippingmethod=Shippingmethod.objects.get(identifier=shipping_method_identifier))
                discount_code_dict = order_utils.get_cart_discount_codes(cart);
                cart_totals_dict = order_utils.get_cart_totals(cart);
                response = JsonResponse({'cart_update_shipping_method':'success', 'cart_found':(True if cart is not None else False), 'shipping_method_identifier':shipping_method_identifier, 'discount_code_data': discount_code_dict, 'cart_totals_data':cart_totals_dict, 'order-api-version':order_api_version}, safe=False)
            except (ObjectDoesNotExist, ValueError) as e:
                print(e)
                error_dict = {"error" : 'error-setting-cart-shipping-method'}
                response = JsonResponse({'cart_update_shipping_method':'error','errors': error_dict,'shipping_method_identifier':shipping_method_identifier, 'order-api-version':order_api_version}, safe=False)
        else:            
            error_dict = {"error" : 'shipping-method-identifier-required'}
            response = JsonResponse({'cart_update_shipping_method':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    else:            
        error_dict = {"error" : 'cart-not-found'}
        response = JsonResponse({'cart_update_shipping_method':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    return response

def cart_delete_cart(request):
    #raise ValueError('A very specific bad thing happened.')
    cart = order_utils.look_up_cart(request)
    if cart is not None:
        cart.delete()
        response = JsonResponse({'cart_delete_cart':'success', 'order-api-version':order_api_version}, safe=False)
    else:            
        error_dict = {"error" : 'cart-not-found'}
        response = JsonResponse({'cart_delete_cart':'error','errors': error_dict,'order-api-version':order_api_version}, safe=False)
    return response


def confirm_place_order(request):
    #raise ValueError('A very specific bad thing happened.')
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:

        agree_to_terms_of_sale = None
        if request.method == 'POST' and 'agree_to_terms_of_sale' in request.POST:    
            agree_to_terms_of_sale = request.POST['agree_to_terms_of_sale']

        agree_to_terms_of_sale = None
        if request.method == 'POST' and 'agree_to_terms_of_sale' in request.POST:    
            agree_to_terms_of_sale = request.POST['agree_to_terms_of_sale']

        newsletter = None
        if request.method == 'POST' and 'newsletter' in request.POST:    
            newsletter = request.POST['newsletter']

        save_defaults = None
        if request.method == 'POST' and 'save_defaults' in request.POST:    
            save_defaults = request.POST['save_defaults']

        #print(request.POST)

        stripe_payment_info = None
        if request.method == 'POST' and 'stripe_payment_info' in request.POST:    
            stripe_payment_info = request.POST['stripe_payment_info']
        #print(stripe_payment_info)
        stripe_payment_info = json.loads(stripe_payment_info)

        stripe_shipping_addr = None
        if request.method == 'POST' and 'stripe_shipping_addr' in request.POST:    
            stripe_shipping_addr = request.POST['stripe_shipping_addr']
        print(stripe_shipping_addr)
        stripe_shipping_addr = json.loads(stripe_shipping_addr)

        stripe_billing_addr = None
        if request.method == 'POST' and 'stripe_billing_addr' in request.POST:    
            stripe_billing_addr = request.POST['stripe_billing_addr']
        #print(stripe_billing_addr)
        stripe_billing_addr = json.loads(stripe_billing_addr)

        if agree_to_terms_of_sale is not None:
            if agree_to_terms_of_sale == 'true':
                cart = order_utils.look_up_cart(request)
                if cart is not None:
                    try:
                        order_identifier = identifier.getNewOrderIdentifier()

                        # Get the payment token ID submitted by the form:
                        payment_email_addr = stripe_payment_info['email']

                        #create Payment object
                        payment = Orderpayment.objects.create(email=payment_email_addr, payment_type=stripe_payment_info['payment_type'], card_name=stripe_payment_info['card_name'], card_brand=stripe_payment_info['card_brand'], card_last4=stripe_payment_info['card_last4'], card_exp_month=stripe_payment_info['card_exp_month'], card_exp_year=stripe_payment_info['card_exp_year'], card_zip=stripe_payment_info['card_zip'])

                        #create Shipping Address object
                        shipping_address = Ordershippingaddress.objects.create(name=stripe_shipping_addr['name'], address_line1=stripe_shipping_addr['address_line1'], city=stripe_shipping_addr['address_city'], state=stripe_shipping_addr['address_state'], zip=stripe_shipping_addr['address_zip'], country=stripe_shipping_addr['address_country'], country_code=stripe_shipping_addr['address_country_code'], )

                        #create Billing Address object
                        billing_address = Orderbillingaddress.objects.create(name=stripe_billing_addr['name'], address_line1=stripe_billing_addr['address_line1'], city=stripe_billing_addr['address_city'], state=stripe_billing_addr['address_state'], zip=stripe_billing_addr['address_zip'], country=stripe_billing_addr['address_country'], country_code=stripe_billing_addr['address_country_code'], )
    
                        # create Order object
                        now = timezone.now()                        
                        cart_totals_dict = order_utils.get_cart_totals(cart);
                        if request.user.is_authenticated:
                            order = Order.objects.create(identifier=order_identifier, member=request.user.member, payment=payment, shipping_address=shipping_address, billing_address=billing_address, sales_tax_amt=0, item_subtotal=cart_totals_dict['item_subtotal'], item_discount_amt=cart_totals_dict['item_discount'], shipping_amt=cart_totals_dict['shipping_subtotal'], shipping_discount_amt=cart_totals_dict['shipping_discount'], order_total=cart_totals_dict['cart_total'] ,agreed_with_terms_of_sale=True, order_date_time=now)
                            if save_defaults == 'true':
                                request.user.member.use_default_shipping_and_payment_info = True
                                request.user.member.stripe_customer_token = cart.payment.stripe_customer_token
                                order_utils.stripe_customer_change_default_payemnt(cart.payment.stripe_customer_token, cart.payment.stripe_card_id)                    
                                if request.user.member.default_shipping_address is None:
                                    #create Cart Shipping Address object
                                    default_shipping_address = Defaultshippingaddress.objects.create(name=shipping_address.name, address_line1=shipping_address.address_line1, city=shipping_address.city, state=shipping_address.state, zip=shipping_address.zip, country=shipping_address.country, country_code=shipping_address.country_code)
                                    request.user.member.default_shipping_address = default_shipping_address         
                                else:
                                    #update existing Cart shipping address
                                    request.user.member.default_shipping_address.name = shipping_address.name
                                    request.user.member.default_shipping_address.address_line1=shipping_address.address_line1
                                    request.user.member.default_shipping_address.city=shipping_address.city
                                    request.user.member.default_shipping_address.state=shipping_address.state
                                    request.user.member.default_shipping_address.zip=shipping_address.zip
                                    request.user.member.default_shipping_address.country=shipping_address.country
                                    request.user.member.default_shipping_address.country_code=shipping_address.country_code
                                    request.user.member.default_shipping_address.save()
                                request.user.member.save()
                        else:
                            prospect = Prospect.objects.get(email=payment_email_addr)
                            order = Order.objects.create(identifier=order_identifier, prospect=prospect, payment=payment, shipping_address=shipping_address, billing_address=billing_address, sales_tax_amt=0, item_subtotal=cart_totals_dict['item_subtotal'], item_discount_amt=cart_totals_dict['item_discount'], shipping_amt=cart_totals_dict['shipping_subtotal'], shipping_discount_amt=cart_totals_dict['shipping_discount'], order_total=cart_totals_dict['cart_total'] ,agreed_with_terms_of_sale=True, order_date_time=now)
                        #create Ordersku objects
                        cart_item_dict = order_utils.get_cart_items(request, cart)
                        confirmation_email_product_text = ''
                        for product_sku_id in cart_item_dict['product_sku_data']:
                            Ordersku.objects.create(order=order, sku=Sku.objects.get(id=cart_item_dict['product_sku_data'][product_sku_id]['sku_id']), quantity=cart_item_dict['product_sku_data'][product_sku_id]['quantity'], price_each=cart_item_dict['product_sku_data'][product_sku_id]['price'])

                        #Create Orderdiscount records
                        discount_code_dict = order_utils.get_cart_discount_codes(cart);
                        for discount_code_id in discount_code_dict:
                            Orderdiscount.objects.create(order=order, discountcode=Discountcode.objects.get(id=discount_code_dict[discount_code_id]['discount_code_id']), applied=discount_code_dict[discount_code_id]['discount_applied'])

                        #Create Orderstatus record
                        Orderstatus.objects.create(order=order, status=Status.objects.get(identifier=Orderconfiguration.objects.get(key='initial_order_status').string_value), created_date_time=now)

                        #Create Ordershippingmethod record
                        order_shipping_method = Ordershippingmethod.objects.create(order=order, shippingmethod=Cartshippingmethod.objects.get(cart=cart).shippingmethod)

                        #################################
                        # Send Order Confirmation Email #
                        #################################
                        order_info_text = order_utils.get_confirmation_email_order_info_text_format(order_identifier)
                        product_text = order_utils.get_confirmation_email_product_information_text_format(cart_item_dict)
                        shipping_text = order_utils.get_confirmation_email_shipping_information_text_format(order_shipping_method.shippingmethod)
                        discount_code_text = order_utils.get_confirmation_email_discount_code_text_format(discount_code_dict)
                        order_totals_text = order_utils.get_confirmation_email_order_totals_text_format(cart_totals_dict)
                        payment_text = order_utils.get_confirmation_email_order_payment_text_format(payment)
                        shipping_address_text = order_utils.get_confirmation_email_order_address_text_format(shipping_address)
                        billing_address_text = order_utils.get_confirmation_email_order_address_text_format(billing_address)

                        name_str = stripe_payment_info['card_name']
                        to_address = payment_email_addr
                        if request.user.is_authenticated:
                            order_confirmation_em_cd_member = Orderconfiguration.objects.get(key='order_confirmation_em_cd_member').string_value
                            email = Email.objects.get(em_cd=order_confirmation_em_cd_member)
                            order_confirmation_email_body_text = email.body_text
                            #order_confirmation_email_body_html = Email.objects.get(em_cd=order_confirmation_em_cd_member).body_html
                            order_confirmation_email_namespace = {'line_break':'\r\n\r\n', 'short_line_break':'\r\n' ,'recipient_first_name': name_str, 'order_information': order_info_text, 'product_information': product_text, 'shipping_information': shipping_text, 'discount_information': discount_code_text, 'order_total_information': order_totals_text, 'payment_information': payment_text, 'shipping_address_information': shipping_address_text, 'billing_address_information': billing_address_text, 'ENVIRONMENT_DOMAIN': settings.ENVIRONMENT_DOMAIN, 'identifier': order_identifier, 'em_cd': email.em_cd, 'mb_cd': request.user.member.mb_cd}
                            formatted_order_confirmation_email_body_text = order_confirmation_email_body_text.format(**order_confirmation_email_namespace)
                            #formatted_order_confirmation_email_body_html = order_confirmation_email_body_html.format(**order_confirmation_email_namespace)
                        else:
                            order_confirmation_em_cd_prospect = Orderconfiguration.objects.get(key='order_confirmation_em_cd_prospect').string_value
                            email = Email.objects.get(em_cd=order_confirmation_em_cd_prospect)
                            #print('newsletter is ' + str(newsletter))
                            if newsletter == 'true':
                                email_unsubscribed = False
                            else:
                                email_unsubscribed = True

                            prospect = Prospect.objects.get(email=to_address)
                            if email_unsubscribed == False:
                                prospect.email_unsubscribed = False
                                prosepct_email_unsubscribe_str = 'You are included in our email marketing list. If you would like to unsubscribe from marketing email messages please follow this link to unsubscribe: ' + settings.ENVIRONMENT_DOMAIN + '/account/email-unsubscribe?em_cd=' + email.em_cd + '&pr_cd=' + prospect.pr_cd + '&pr_token=' + prospect.email_unsubscribe_string_signed
                            else:
                                prospect.email_unsubscribed = True
                                prosepct_email_unsubscribe_str = 'You are NOT included in our email marketing list. If you would like to be added to our marketing email list please reply to this email and let us know.'
                            prospect.swa_comment='Captured from anonymous order identifier: ' + order_identifier
                            prospect.save()

                            order_confirmation_email_body_text = email.body_text
                            #order_confirmation_email_body_html = Email.objects.get(em_cd=order_confirmation_em_cd_member).body_html
                            order_confirmation_email_namespace = {'line_break':'\r\n\r\n', 'short_line_break':'\r\n' ,'recipient_first_name': name_str, 'order_information': order_info_text, 'product_information': product_text, 'shipping_information': shipping_text, 'discount_information': discount_code_text, 'order_total_information': order_totals_text, 'payment_information': payment_text, 'shipping_address_information': shipping_address_text, 'billing_address_information': billing_address_text, 'ENVIRONMENT_DOMAIN': settings.ENVIRONMENT_DOMAIN, 'identifier': order_identifier, 'em_cd': email.em_cd, 'pr_cd': prospect.pr_cd, 'prosepct_email_unsubscribe_str': prosepct_email_unsubscribe_str}
                            formatted_order_confirmation_email_body_text = order_confirmation_email_body_text.format(**order_confirmation_email_namespace)
                            #formatted_order_confirmation_email_body_html = order_confirmation_email_body_html.format(**order_confirmation_email_namespace)
    
                        msg = EmailMultiAlternatives(
                            subject = email.subject,
                            body = formatted_order_confirmation_email_body_text,
                            from_email = email.from_address,
                            to = [to_address],
                            bcc = [email.bcc_address],
                            reply_to=[email.from_address],
                        )
                        #msg.attach_alternative(formatted_order_confirmation_email_body_html, "text/html")
                        try:
                            msg.send(fail_silently=False)
                            now = timezone.now()
                            if email.email_type == Emailtype.objects.get(title='Prospect'):
                                emailsent = Emailsent.objects.create(member=None, prospect=prospect, email=email, sent_date_time=now)
                            elif email.email_type == Emailtype.objects.get(title='Member'):
                                emailsent = Emailsent.objects.create(member=request.user.member, prospect=None, email=email, sent_date_time=now)
                            #print(emailsent)
                        except SMTPDataError as e:
                            print(e)

                        #####################################
                        # END Send Order Confirmation Email #
                        #####################################


                        # delete the cart
                        cart.delete()

                        response = JsonResponse({'checkout_allowed':checkout_allowed, 'confirm_place_order':'success', 'order_identifier': order.identifier, 'order-api-version':order_api_version}, safe=False)
                        pass
                    except (ObjectDoesNotExist, ValueError) as e:
                        print(e)
                        error_dict = {"error" : 'error-saving-order', 'description': 'An error occurred while processing your order.'}
                        response = JsonResponse({'checkout_allowed':checkout_allowed, 'confirm_place_order':'error', 'errors': error_dict, 'agree_to_terms_of_sale':agree_to_terms_of_sale, 'order-api-version':order_api_version}, safe=False)
                else:
                    error_dict = {"error" : 'cart-not-found', 'description': 'No cart was found.'}
                    response = JsonResponse({'checkout_allowed':checkout_allowed, 'confirm_place_order':'error', 'errors': error_dict, 'order-api-version':order_api_version}, safe=False)
            else:
                error_dict = {"error" : 'agree-to-terms-of-sale-must-be-checked', 'description': 'You must agree to the Terms of Sale'}
                response = JsonResponse({'checkout_allowed':checkout_allowed, 'confirm_place_order':'error', 'errors': error_dict, 'agree_to_terms_of_sale':agree_to_terms_of_sale, 'order-api-version':order_api_version}, safe=False)
        else:
            error_dict = {"error" : 'agree-to-terms-of-sale-required', 'description': 'You must agree to the Terms of Sale'}
            response = JsonResponse({'checkout_allowed':checkout_allowed, 'confirm_place_order':'error', 'errors': error_dict, 'order-api-version':order_api_version}, safe=False)
    else:
        response = JsonResponse({'checkout_allowed':checkout_allowed,'order-api-version':order_api_version}, safe=False)
    return response 

def process_stripe_payment_token(request):
    #raise ValueError('A very specific bad thing happened.')
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:

        stripe_token = None
        if request.method == 'POST' and 'stripe_token' in request.POST:    
            stripe_token = request.POST['stripe_token']
        #print(stripe_token)

        email = None
        if request.method == 'POST' and 'email' in request.POST:    
            email = request.POST['email']
        #print('###########')
        #print(email)
        #print('###########')

        stripe_payment_args = None
        if request.method == 'POST' and 'stripe_payment_args' in request.POST:    
            stripe_payment_args = request.POST['stripe_payment_args']
        #print(stripe_payment_args)
        stripe_payment_args = json.loads(stripe_payment_args)
        #print(stripe_payment_args)

        if stripe_token is not None:
            try:
                cart = order_utils.look_up_cart(request)
                if cart is not None:

                    if cart.payment is None:
                        if request.user.is_authenticated:
                            customer = order_utils.create_stripe_customer(stripe_token, email, 'member_username', request.user.username)
                        else:
                            customer = order_utils.create_stripe_customer(stripe_token, email, 'prospect_email_addr', email)
                        #print('***********')
                        #print(customer)
                        #print('***********')
                        cart_payment = Cartpayment.objects.create(stripe_customer_token=customer.id, stripe_card_id=customer.default_source, email=email)
                        cart.payment = cart_payment
                        cart.save()
                    else: 
                        card = order_utils.stripe_customer_add_card(cart.payment.stripe_customer_token, stripe_token)
                        cart.payment.stripe_card_id = card.id
                        cart.payment.save()

                    if 'shipping_address_state' in stripe_payment_args:
                        shipping_address_state = stripe_payment_args['shipping_address_state']
                    else:
                        shipping_address_state = ''
                    if cart.shipping_address is None:
                        #create Cart Shipping Address object
                        cart_shipping_address = Cartshippingaddress.objects.create(name=stripe_payment_args['shipping_name'], address_line1=stripe_payment_args['shipping_address_line1'], city=stripe_payment_args['shipping_address_city'], state=shipping_address_state, zip=stripe_payment_args['shipping_address_zip'], country=stripe_payment_args['shipping_address_country'], country_code=stripe_payment_args['shipping_address_country_code'])
                        cart.shipping_address = cart_shipping_address         
                        cart.save()
                    else:
                        #update existing Cart shipping address
                        cart_shipping_address = cart.shipping_address
                        cart_shipping_address.name = stripe_payment_args['shipping_name']
                        cart_shipping_address.address_line1=stripe_payment_args['shipping_address_line1']
                        cart_shipping_address.city=stripe_payment_args['shipping_address_city']
                        cart_shipping_address.state=shipping_address_state
                        cart_shipping_address.zip=stripe_payment_args['shipping_address_zip']
                        cart_shipping_address.country=stripe_payment_args['shipping_address_country']
                        cart_shipping_address.country_code=stripe_payment_args['shipping_address_country_code']
                        cart_shipping_address.save()

                response = JsonResponse({'checkout_allowed':checkout_allowed, 'process_stripe_payment_token':'success', 'order-api-version':order_api_version}, safe=False)
            except (stripe.error.CardError, stripe.error.RateLimitError, stripe.error.InvalidRequestError, stripe.error.AuthenticationError, stripe.error.APIConnectionError, stripe.error.StripeError) as e:
                # Since it's a decline, stripe.error.CardError will be caught
                body = e.json_body
                err  = body.get('error', {})

                print("Status is: %s" % e.http_status)
                print("Type is: %s" % err.get('type'))
                print("Code is: %s" % err.get('code'))
                # param is '' in this case
                print("Param is: %s" % err.get('param'))
                print("Message is: %s" % err.get('message'))

                error_dict = {"error" : 'error-creating-stripe-customer', 'description': 'An error occurred while creating your Stripe customer record.'}
                response = JsonResponse({'checkout_allowed':checkout_allowed, 'process_stripe_payment_token':'error', 'errors': error_dict, 'order-api-version':order_api_version}, safe=False)
        else:
            error_dict = {"error" : 'stripe-token-required', 'description': 'Stripe token is required'}
            response = JsonResponse({'checkout_allowed':checkout_allowed, 'process_stripe_payment_token':'error', 'errors': error_dict, 'order-api-version':order_api_version}, safe=False)
    else:
        response = JsonResponse({'checkout_allowed':checkout_allowed,'order-api-version':order_api_version}, safe=False)
    return response     

def anonymous_email_address_payment_lookup(request):    
    #raise ValueError('A very specific bad thing happened.')
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:

        anonymous_email_address = None
        if request.method == 'POST' and 'anonymous_email_address' in request.POST:    
            anonymous_email_address = request.POST['anonymous_email_address']
        #print(anonymous_email_address)

        if anonymous_email_address is not None:
            if User.objects.filter(email=anonymous_email_address).exists():
                error_dict = {"error" : 'email-address-is-associated-with-member', 'description': 'This email address is already associated with a member account. Please <span class="login-form-error-link"><a href=\"/login?next=checkout/confirm\">login</a></span> to continue.'}
                response = JsonResponse({'checkout_allowed':checkout_allowed, 'anonymous_email_address_payment_lookup':'error', 'errors': error_dict, 'order-api-version':order_api_version}, safe=False)
            else:
                stripe_publishable_key = settings.STRIPE_PUBLISHABLE_SECRET_KEY
                if Prospect.objects.filter(email=anonymous_email_address).exists():
                    customer_dict = None
                    response = JsonResponse({'checkout_allowed':checkout_allowed, 'anonymous_email_address_payment_lookup':'success', 'stripe_publishable_key':stripe_publishable_key, 'customer_data':customer_dict, 'order-api-version':order_api_version}, safe=False)
                else:
                    now = timezone.now()
                    email_unsubscribe_string = identifier.getNewProspectEmailUnsubscribeString()
                    email_unsubscribe_string_signed = email_unsubscribe_signer.sign(email_unsubscribe_string) 
                    email_unsubscribe_string_signed = email_unsubscribe_string_signed.rsplit(':', 1)[1]
                    pr_cd = identifier.getNewProspectCode()
                    prospect = Prospect.objects.create(email=anonymous_email_address, email_unsubscribed=True, email_unsubscribe_string=email_unsubscribe_string, email_unsubscribe_string_signed=email_unsubscribe_string_signed, swa_comment='Captured from incomplete anonymous order', pr_cd=pr_cd, created_date_time=now)
                    customer_dict = None
                    response = JsonResponse({'checkout_allowed':checkout_allowed, 'anonymous_email_address_payment_lookup':'success', 'stripe_publishable_key':stripe_publishable_key, 'customer_data':customer_dict, 'order-api-version':order_api_version}, safe=False)
        else:
            error_dict = {"error" : 'anonymous-email-address-required', 'description': 'Anonymous email address is required'}
            response = JsonResponse({'checkout_allowed':checkout_allowed, 'anonymous_email_address_payment_lookup':'error', 'errors': error_dict, 'order-api-version':order_api_version}, safe=False)
    else:
        response = JsonResponse({'checkout_allowed':checkout_allowed,'order-api-version':order_api_version}, safe=False)
    return response  

def change_confirmation_email_address(request):
    checkout_allowed = order_utils.checkout_allowed(request)
    if checkout_allowed:
        cart = order_utils.look_up_cart(request)
        cart.payment = None
        cart.shipping_address = None
        cart.save()
        response = JsonResponse({'checkout_allowed':checkout_allowed, 'change_confirmation_email_address':'success', 'order-api-version':order_api_version}, safe=False)
    else:
        response = JsonResponse({'checkout_allowed':checkout_allowed,'order-api-version':order_api_version}, safe=False)
    return response  



