from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.template import loader
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.core.mail import EmailMessage
from django.db.models import Max
from smtplib import SMTPDataError
from django.core.signing import TimestampSigner, Signer, SignatureExpired, BadSignature
from user.models import Defaultshippingaddress, Member, Emailunsubscribereasons, Termsofuse, Membertermsofuseversionagreed, Prospect, Chatmessage
from order.models import Order, Cartsku, Cartdiscount, Cartshippingmethod
from StartupWebApp.form import validator
from StartupWebApp.utilities import random, identifier, email_helpers
from clientevent.models import Configuration as ClientEventConfiguration
from django.utils import timezone
import json
from order.utilities import order_utils
import stripe
stripe.api_key = settings.STRIPE_SERVER_SECRET_KEY
stripe.log = settings.STRIPE_LOG_LEVEL


#from user.models import


user_api_version = '0.0.1'
email_verification_signer = TimestampSigner(salt='email_verification')
reset_password_signer = TimestampSigner(salt='reset_email')
email_unsubscribe_signer = Signer(salt='email_unsubscribe')
title_character_limit = 44

#@cache_control(max_age=10) #set cache control to 10 seconds


@never_cache

def index(request):
    return HttpResponse("Hello, you're at the user API (version " + user_api_version + ") root. Nothing to see here...")


def token(request):
    #raise ValueError('A very specific bad thing happened.')
    template = loader.get_template('user/token.html')
    context = {}
    #return HttpResponse(template.render(context, request))
    return JsonResponse({'token': template.render(context, request), 'user-api-version': user_api_version}, safe=False)
    #return HttpResponse("login_form")


@ensure_csrf_cookie
def logged_in(request):
    #raise ValueError('A very specific bad thing happened.')
    #print(request.user.session)
    cart = order_utils.look_up_cart(request)
    cart_item_count = 0
    if cart is not None:
        for cartsku in Cartsku.objects.filter(cart=cart):
            cart_item_count += 1

    if request.user.is_authenticated:
        #print ('is_authenticated')
        member_initials = request.user.first_name[:1] + request.user.last_name[:1]
        response = JsonResponse({'logged_in': True, 'log_client_events': ClientEventConfiguration.objects.get(id=1).log_client_events, 'client_event_id': request.user.id, 'member_initials': member_initials, 'first_name': request.user.first_name, 'last_name': request.user.last_name, 'email_address': request.user.email, 'cart_item_count': cart_item_count, 'user-api-version': user_api_version}, safe=False)
    else:
        #print ('not_authenticated')
        response = JsonResponse({'logged_in': False, 'log_client_events': ClientEventConfiguration.objects.get(id=1).log_client_events, 'client_event_id': 'null', 'cart_item_count': cart_item_count, 'user-api-version': user_api_version}, safe=False)
        if request.get_signed_cookie(key='anonymousclientevent', default=False, salt='clienteventanonymousclienteventoccurrence') == False:
            response.set_signed_cookie(key='anonymousclientevent', value=random.getRandomString(20, 20), salt='clienteventanonymousclienteventoccurrence', max_age=31536000, expires=None, path='/', domain='.startupwebapp.com', secure=None, httponly=False)
    return response


def client_login(request):
    #raise ValueError('A very specific bad thing happened.')
    username = request.POST['username']
    #print(username)
    password = request.POST['password']
    remember_me = request.POST['remember_me']
    #print('remember_me is ' + remember_me)
    if remember_me != 'true':
        request.session.set_expiry(0)

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        #print(user.is_authenticated)
        #print ('successful login')

        member_cart = order_utils.look_up_member_cart(request)
        if member_cart is None:
            #print ('member_cart is None')
            anonymous_cart = order_utils.look_up_anonymous_cart(request)
            if anonymous_cart is not None:
                #print ('anonymous_cart is NOT None')
                anonymous_cart.member = request.user.member
                anonymous_cart.anonymous_cart_id = None
                anonymous_cart.save()
        else:
            #print ('member_cart is NOT None')
            anonymous_cart = order_utils.look_up_anonymous_cart(request)
            if anonymous_cart is not None:
                #print ('anonymous_cart is NOT None')
                # merge anonymous cart into member cart
                # skus. put any skus from the anonymous cart into the member cart if they're not already there
                for anonymous_cart_sku in Cartsku.objects.filter(cart=anonymous_cart):
                    sku_exists_in_member_cart = Cartsku.objects.filter(cart=member_cart, sku=anonymous_cart_sku.sku).exists()
                    if sku_exists_in_member_cart == False:
                        Cartsku.objects.create(cart=member_cart, sku=anonymous_cart_sku.sku, quantity=anonymous_cart_sku.quantity)
                # discount codes. put any discount codes from the anonymous cart into the member cart if they're not already there
                for anonymous_cart_discount_code in Cartdiscount.objects.filter(cart=anonymous_cart):
                    discount_code_exists_in_member_cart = Cartdiscount.objects.filter(cart=member_cart, discountcode=anonymous_cart_discount_code.discountcode).exists()
                    if discount_code_exists_in_member_cart == False:
                        Cartdiscount.objects.create(cart=member_cart, discountcode=anonymous_cart_discount_code.discountcode)
                # shipping method. If member cart doesn't have shipping method see if we can apply the anonymous cart shipping method
                member_cart_shipping_method_exists = Cartshippingmethod.objects.filter(cart=member_cart).exists()
                if member_cart_shipping_method_exists == False:
                    anonymous_cart_shipping_method_exists = Cartshippingmethod.objects.filter(cart=anonymous_cart).exists()
                    if anonymous_cart_shipping_method_exists == True:
                        Cartshippingmethod.objects.create(cart=member_cart, shippingmethod=Cartshippingmethod.objects.get(cart=anonymous_cart).shippingmethod)
                # delete anonymous cart
                anonymous_cart.delete()

        response = JsonResponse({'login': 'true', 'user-api-version': user_api_version}, safe=False )
        response.delete_cookie(key='an_ct', path='/', domain='.startupwebapp.com')
        return response
    else:
        # Return an 'invalid login' error message.
        print ('failed login')
        return JsonResponse({'login': 'false', 'user-api-version': user_api_version}, safe=False )


def client_logout(request):
    #raise ValueError('A very specific bad thing happened.')
    if request.user.is_anonymous:
        print('AnonymousUser found!')
        return JsonResponse({'logout': 'user_not_authenticated', 'user-api-version': user_api_version}, safe=False )

    logout(request)
    response = JsonResponse({'logout': 'true', 'user-api-version': user_api_version}, safe=False)
    response.delete_cookie(key='an_ct', path='/', domain='.startupwebapp.com')
    response.set_signed_cookie(key='anonymousclientevent', value=random.getRandomString(20, 20), salt='clienteventanonymousclienteventoccurrence', max_age=31536000, expires=None, path='/', domain='.startupwebapp.com', secure=None, httponly=False)
    return response
    #return HttpResponse("logout")


def account_content(request):
    #raise ValueError('A very specific bad thing happened.')
    #print(request.user.session)
    #response_html = {}
    if request.user.is_authenticated:
        #print ('is_authenticated')
        #response_data = "user IS logged in"

        #print(request.user.member.email_verification_string_signed)

        verification_request_sent_within_24_hours = False
        if request.user.member.email_verification_string_signed is not None and request.user.member.email_verified == False:
            try:
                unsigned_string = email_verification_signer.unsign(request.user.member.email_verification_string_signed, max_age=86400) #86400 seconds is one day
                verification_request_sent_within_24_hours = True
            except (BadSignature, SignatureExpired):
                verification_request_sent_within_24_hours = False

        email_data = {"email_address": request.user.email, "email_verified": request.user.member.email_verified, "verification_request_sent_within_24_hours": verification_request_sent_within_24_hours}
        if Membertermsofuseversionagreed.objects.filter(member=request.user.member).exists() == True:
            agreed_date_time = Membertermsofuseversionagreed.objects.filter(member=request.user.member).latest('agreed_date_time').agreed_date_time
        else:
            agreed_date_time = None
        personal_data = {"username": request.user.username, "first_name": request.user.first_name, "last_name": request.user.last_name, "newsletter_subscriber": request.user.member.newsletter_subscriber, "email_unsubscribed": request.user.member.email_unsubscribed, "joined_date_time": request.user.date_joined, "last_login_date_time": request.user.last_login, "terms_of_use_agreed_date_time": agreed_date_time}
        orders_data = {}
        members_orders = Order.objects.filter(member=request.user.member).order_by('-order_date_time')
        order_order_counter = 1
        for order in members_orders:
            #print(order.id)
            orders_data[order_order_counter] = {}
            orders_data[order_order_counter]['order_id'] = order.id
            orders_data[order_order_counter]['identifier'] = order.identifier
            orders_data[order_order_counter]['order_date_time'] = order.order_date_time
            orders_data[order_order_counter]['sales_tax_amt'] = order.sales_tax_amt
            orders_data[order_order_counter]['order_total'] = order.order_total
            order_order_counter += 1
        #print(orders_data)
        stripe_publishable_key = settings.STRIPE_PUBLISHABLE_SECRET_KEY

        shipping_billing_addresses_and_payment_dict = {}
        if request.user.member.use_default_shipping_and_payment_info == True:
            if request.user.member.default_shipping_address is not None and request.user.member.stripe_customer_token is not None:
                shipping_address_dict = order_utils.load_address_dict(request.user.member.default_shipping_address)
                stripe_customer_token = request.user.member.stripe_customer_token
                customer = order_utils.retrieve_stripe_customer(stripe_customer_token)
                #print('### CUSTOMER ###')
                #print(customer)
                #print(customer.sources)
                #print(customer.sources.data)
                #print('### END CUSTOMER ###')
                if customer is not None:
                    shipping_billing_addresses_and_payment_dict = order_utils.get_stripe_customer_payment_data(customer, shipping_address_dict, None)
                #print(customer_dict)

        response_data = {"authenticated": "true", "personal_data": personal_data, "email_data": email_data, "orders_data": orders_data, "shipping_billing_addresses_and_payment_data": shipping_billing_addresses_and_payment_dict, 'stripe_publishable_key': stripe_publishable_key}
    else:
        #print ('not_authenticated')
        response_data = {"authenticated": "false"}
    return JsonResponse({'account_content': response_data, 'user-api-version': user_api_version}, safe=False)


def create_account(request):
    #raise ValueError('A very specific bad thing happened.')
    firstname = request.POST['firstname']
    #print(firstname)
    firstname_valid = validator.isNameValid(firstname, 30)
    #print(firstname_valid)

    lastname = request.POST['lastname']
    #print(lastname)
    lastname_valid = validator.isNameValid(lastname, 150)
    #print(lastname_valid)

    username = request.POST['username']
    #print(username)
    username_valid = validator.isUserNameValid(username, 150)
    #print(username_valid)

    email_address = request.POST['email_address']
    #print(email_address)
    email_address_valid = validator.isEmailValid(email_address, 254)
    #print(email_address_valid)

    password = request.POST['password']
    confirm_password = request.POST['confirm_password']
    password_valid = validator.isPasswordValid(password, confirm_password, 150)

    newsletter = request.POST['newsletter']
    #print(newsletter)
    remember_me = request.POST['remember_me']
    #print('remember_me is ' + remember_me)

    # Validators return True or error array - must use == True
    if firstname_valid == True and lastname_valid == True and username_valid == True and email_address_valid == True and password_valid == True:  # noqa: E712
        print('VALIDATION PASSED - CREATE USER')
        user_new = User.objects.create_user(username, email_address, password)
        user_new.first_name = firstname
        user_new.last_name = lastname
        member_group = Group.objects.get(name='Members')
        user_new.groups.add(member_group)
        user_new.save()
        random_str = identifier.getNewMemberEmailUnsubscribeString()
        signed_string = email_unsubscribe_signer.sign(random_str)
        mb_cd = identifier.getNewMemberCode()
        if newsletter == 'true':
            member = Member(user=user_new, newsletter_subscriber=True, email_verified=False, email_unsubscribe_string=random_str, email_unsubscribe_string_signed=signed_string.rsplit(':', 1)[1], mb_cd=mb_cd)
        else:
            member = Member(user=user_new, newsletter_subscriber=False, email_verified=False, email_unsubscribe_string=random_str, email_unsubscribe_string_signed=signed_string.rsplit(':', 1)[1], mb_cd=mb_cd)
        member.save()
        most_recent_terms_of_use_version = Termsofuse.objects.all().aggregate(Max('version'))
        most_recent_terms_of_use_version_obj = Termsofuse.objects.get(version=most_recent_terms_of_use_version['version__max'])
        now = timezone.now()
        membertermsofuseversionagreed = Membertermsofuseversionagreed.objects.create(member=member, termsofuseversion=most_recent_terms_of_use_version_obj, agreed_date_time=now)

        if remember_me != 'true':
            request.session.set_expiry(0)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            #print(user.is_authenticated)

            anonymous_cart = order_utils.look_up_anonymous_cart(request)
            if anonymous_cart is not None:
                print ('anonymous_cart is NOT None')
                anonymous_cart.member = user.member
                anonymous_cart.anonymous_cart_id = None
                anonymous_cart.save()

            if Prospect.objects.filter(email=email_address).exists():
                prospect = Prospect.objects.get(email=email_address)
                if prospect.converted_date_time is None:
                    now = timezone.now()
                    prospect.converted_date_time = now
                if prospect.swa_comment is None:
                    swa_comment_str = 'Prospect converted by creating user id ' + str(user.id) + '.'
                else:
                    swa_comment_str = prospect.swa_comment + '. Prospect converted by creating user id ' + str(user.id) + '.'
                prospect.swa_comment = swa_comment_str
                prospect.email_unsubscribed = True
                prospect.save()
                prospect_orders_count = Order.objects.filter(prospect=prospect).count()
                if prospect_orders_count > 0:
                    prospect_orders = Order.objects.filter(prospect=prospect)
                    for order in prospect_orders:
                        order.member = user.member
                        #order.prospect = None leave this for now
                        order.save()

                chat_messages_exist = Chatmessage.objects.filter(email_address=email_address).exists()
                if chat_messages_exist is True:
                    for chat_message in Chatmessage.objects.filter(email_address=email_address):
                        chat_message.member = user.member
                        chat_message.save()

            print ('successful registration')

            random_str = random.getRandomString(20, 20)
            request.user.member.email_verification_string = random_str
            signed_string = email_verification_signer.sign(random_str)
            request.user.member.email_verification_string_signed = signed_string
            request.user.member.save()

            welcome_email_content = 'Hi ' + request.user.first_name + ' ' + request.user.last_name + '!'
            welcome_email_content += '\r\n\r\n'
            welcome_email_content += 'Welcome to ' + settings.ENVIRONMENT_DOMAIN + '. We\'re excited that you\'ve signed up and we hope you enjoy using our product as a member!'
            welcome_email_content += '\r\n\r\n'
            welcome_email_content += 'A quick reminder that you registered with the username "' + request.user.username + '".'
            welcome_email_content += '\r\n\r\n'
            welcome_email_content += 'While we have your attention, we\'d love it if you took a few seconds to verify your email address. If it really was you who registered for an account at ' + settings.ENVIRONMENT_DOMAIN + ', please go to the following URL to confirm that you are authorized to use this email address:'
            welcome_email_content += '\r\n\r\n'
            welcome_email_content += settings.ENVIRONMENT_DOMAIN + '/account/?email_verification_code=' + signed_string
            welcome_email_content += '\r\n\r\n'
            welcome_email_content += 'Your request to verify this email address will not be processed unless you confirm the address using this URL. This link expires 24 hours after you registered. However, you can always verify your email address at a future date using the options on your account page.'
            welcome_email_content += '\r\n\r\n'
            welcome_email_content += 'If you did NOT register for an account at ' + settings.ENVIRONMENT_DOMAIN + ' using this email address, do not click on the link. Instead, please forward this notification to contact@startupwebapp.com and let us know that you did not request this account and we\'ll dig in further to figure out what is going on.'
            welcome_email_content += '\r\n\r\n'
            welcome_email_content += 'If you have questions or would like to reach us for any reason you can reply to this email or call us toll-free at 1-844-473-3744.'
            welcome_email_content += '\r\n\r\n'
            welcome_email_content += 'We\'re excited to have you as a member!'
            welcome_email_content += '\r\n'
            welcome_email_content += 'StartUpWebApp.com'

            email = EmailMessage(
                subject = 'Welcome to ' + settings.ENVIRONMENT_DOMAIN,
                body = welcome_email_content,
                from_email = 'contact@startupwebapp.com',
                to = [request.user.email],
                bcc = ['contact@startupwebapp.com'],
                reply_to=['contact@startupwebapp.com'],
            )
            try:
                email.send(fail_silently=False)
            except SMTPDataError as e:
                print('failed to send welcome email')
                print(e)

            return JsonResponse({'create_account': 'true', 'user-api-version': user_api_version}, safe=False )
        else:
            #Return an 'invalid login' error message.
            print ('failed registration')
            return JsonResponse({'create_account': 'created_but_login_failed', 'user-api-version': user_api_version}, safe=False )
    else:
        #print('VALIDATION ERRORS - RETURN ERRORS')
        error_dict = {"firstname": firstname_valid, "lastname": lastname_valid, "username": username_valid, "email-address": email_address_valid, "password": password_valid}
        return JsonResponse({'create_account': 'false', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )


def verify_email_address(request):
    #raise ValueError('A very specific bad thing happened.')
    if request.user.is_anonymous:
        print('AnonymousUser found!')
        return JsonResponse({'verify_email_address': 'user_not_authenticated', 'user-api-version': user_api_version}, safe=False )

    if request.user.is_authenticated:

        random_str = random.getRandomString(20, 20)
        request.user.member.email_verification_string = random_str
        signed_string = email_verification_signer.sign(random_str)
        request.user.member.email_verification_string_signed = signed_string
        request.user.member.save()

        verification_email_content = request.user.first_name + ' ' + request.user.last_name + ','
        verification_email_content += '\r\n\r\n'
        verification_email_content += 'We have received a request to verify this email address for the username "' + request.user.username + '"" at ' + settings.ENVIRONMENT_DOMAIN + '. If you requested this verification, please go to the following URL to confirm that you are authorized to use this email address:'
        verification_email_content += '\r\n\r\n'
        verification_email_content += settings.ENVIRONMENT_DOMAIN + '/account/?email_verification_code=' + signed_string
        verification_email_content += '\r\n\r\n'
        verification_email_content += 'Your request to verify this email address will not be processed unless you confirm the address using this URL. This link expires 24 hours after your original verification request.'
        verification_email_content += '\r\n\r\n'
        verification_email_content += 'If you did NOT request to verify this email address, do not click on the link. If you are concerned, please forward this notification to contact@startupwebapp.com and let us know that you did not request the verification.'
        verification_email_content += '\r\n\r\n'
        verification_email_content += 'If you have questions or would like to reach us for any reason you can reply to this email or call us toll-free at 1-844-473-3744.'
        verification_email_content += '\r\n\r\n'
        verification_email_content += 'Sincerely,'
        verification_email_content += '\r\n'
        verification_email_content += 'StartUpWebApp.com'

        email = EmailMessage(
            subject = 'Email Verification Request for ' + settings.ENVIRONMENT_DOMAIN,
            body = verification_email_content,
            from_email = 'contact@startupwebapp.com',
            to = [request.user.email],
            bcc = ['contact@startupwebapp.com'],
            reply_to=['contact@startupwebapp.com'],
        )
        try:
            email.send(fail_silently=False)
            return JsonResponse({'verify_email_address': 'verification_email_sent', 'user-api-version': user_api_version}, safe=False )
        except SMTPDataError:
            return JsonResponse({'verify_email_address': 'email_failed', 'user-api-version': user_api_version}, safe=False )

    else:
        return JsonResponse({'verify_email_address': 'user_not_authenticated', 'user-api-version': user_api_version}, safe=False )


def verify_email_address_response(request):
    #raise ValueError('A very specific bad thing happened.')
    if request.user.is_anonymous:
        print('AnonymousUser found!')
        return JsonResponse({'verify_email_address_response': 'user_not_authenticated', 'user-api-version': user_api_version}, safe=False )

    email_verification_code = request.POST['email_verification_code']
    #print(email_verification_code)
    try:
        unsigned_string = email_verification_signer.unsign(email_verification_code, max_age=86400) #86400 seconds is one day
        if request.user.member.email_verification_string == unsigned_string:
            request.user.member.email_verified = True
            request.user.member.email_verification_string = None
            request.user.member.email_verification_string_signed = None
            request.user.member.save()
            return JsonResponse({'verify_email_address_response': 'success', 'user-api-version': user_api_version}, safe=False )
        else:
            return JsonResponse({'verify_email_address_response': 'code-doesnt-match', 'user-api-version': user_api_version}, safe=False )
    except BadSignature:
        return JsonResponse({'verify_email_address_response': 'signature-invalid', 'user-api-version': user_api_version}, safe=False )
    except SignatureExpired:
        return JsonResponse({'verify_email_address_response': 'signature-expired', 'user-api-version': user_api_version}, safe=False )


def reset_password(request):
    #raise ValueError('A very specific bad thing happened.')
    # see if we can find a user who matches the requested values
    username = request.POST['username']
    email_address = request.POST['email_address']
    #print(username)
    #print(email_address)
    try:
        user = User.objects.get(username=username)
        #print(user)
        if user.email.lower() == email_address.lower():
            #print('found a match!!!!')
            random_str = random.getRandomString(20, 20)
            user.member.reset_password_string = random_str
            signed_string = reset_password_signer.sign(random_str)
            user.member.reset_password_string_signed = signed_string
            user.member.save()

            reset_password_content = user.first_name + ' ' + user.last_name + ','
            reset_password_content += '\r\n\r\n'
            reset_password_content += 'We have received a request to send you a password reset link the username "' + username + '"" at ' + settings.ENVIRONMENT_DOMAIN + '. If you requested this password reset, please go to the following URL to complete the password reset process:'
            reset_password_content += '\r\n\r\n'
            reset_password_content += settings.ENVIRONMENT_DOMAIN + '/set-new-password?password_reset_code=' + signed_string
            reset_password_content += '\r\n\r\n'
            reset_password_content += 'Your request to reset your password will not be processed unless you complete the process using this URL. This link expires 1 hours after your original password reset request.'
            reset_password_content += '\r\n\r\n'
            reset_password_content += 'If you did NOT request to reset your password, do not click on the link. If you are concerned, please forward this notification to contact@startupwebapp.com and let us know that you did not request the password reset.'
            reset_password_content += '\r\n\r\n'
            reset_password_content += 'If you have questions or would like to reach us for any reason you can reply to this email or call us toll-free at 1-844-473-3744.'
            reset_password_content += '\r\n\r\n'
            reset_password_content += 'Sincerely,'
            reset_password_content += '\r\n'
            reset_password_content += 'StartupWebApp.com'

            email = EmailMessage(
                subject = 'Password Reset Request for ' + settings.ENVIRONMENT_DOMAIN,
                body = reset_password_content,
                from_email = 'contact@startupwebapp.com',
                to = [user.email],
                bcc = ['contact@startupwebapp.com'],
                reply_to=['contact@startupwebapp.com'],
            )
            try:
                email.send(fail_silently=False)
            except SMTPDataError as e:
                print(e)
        else:
            print(user.email + " != " + email_address)
    except ObjectDoesNotExist as e:
        print(e)
    return JsonResponse({'reset_password': 'success', 'user-api-version': user_api_version}, safe=False )


def set_new_password(request):
    #raise ValueError('A very specific bad thing happened.')
    username = request.POST['username']
    #print(username)
    try:
        user = User.objects.get(username=username)

        try:
            unsigned_string = reset_password_signer.unsign(request.POST['password_reset_code'], max_age=86400) #86400 seconds is one day
            #print(user.member.reset_password_string)
            #print(unsigned_string)
            if user.member.reset_password_string == unsigned_string:
                password = request.POST['new_password']
                confirm_password = request.POST['confirm_new_password']
                password_valid = validator.isPasswordValid(password, confirm_password, 150)
                # Validators return True or error array - must use == True
                if password_valid == True:  # noqa: E712
                    user.set_password(password)
                    user.save()
                    user.member.reset_password_string = None
                    user.member.reset_password_string_signed = None
                    user.member.save()

                    set_new_password_confirmation_content = user.first_name + ' ' + user.last_name + ','
                    set_new_password_confirmation_content += '\r\n\r\n'
                    set_new_password_confirmation_content += 'Your account password has been changed for the username "' + username + '" at ' + settings.ENVIRONMENT_DOMAIN + '. You will now be able to login with your new password.'
                    set_new_password_confirmation_content += '\r\n\r\n'
                    set_new_password_confirmation_content += 'If you did NOT make this change, please forward this notification to contact@startupwebapp.com and let us know that you did not request the password change.'
                    set_new_password_confirmation_content += '\r\n\r\n'
                    set_new_password_confirmation_content += 'If you have questions or would like to reach us for any reason you can reply to this email or call us toll-free at 1-844-473-3744.'
                    set_new_password_confirmation_content += '\r\n\r\n'
                    set_new_password_confirmation_content += 'Sincerely,'
                    set_new_password_confirmation_content += '\r\n'
                    set_new_password_confirmation_content += 'StartupWebApp.com'

                    email = EmailMessage(
                        subject = 'Password Changed on ' + settings.ENVIRONMENT_DOMAIN,
                        body = set_new_password_confirmation_content,
                        from_email = 'contact@startupwebapp.com',
                        to = [user.email],
                        bcc = ['contact@startupwebapp.com'],
                        reply_to=['contact@startupwebapp.com'],
                    )
                    try:
                        email.send(fail_silently=False)
                    except SMTPDataError as e:
                        print(e)

                    return JsonResponse({'set_new_password': 'success', 'user-api-version': user_api_version}, safe=False )
                else:
                    print('VALIDATION ERRORS - RETURN ERRORS')
                    error_dict = {"new-password": password_valid}
                    return JsonResponse({'set_new_password': 'password-error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )
            else:
                return JsonResponse({'set_new_password': 'code-doesnt-match', 'user-api-version': user_api_version}, safe=False )
        except BadSignature:
            return JsonResponse({'set_new_password': 'signature-invalid', 'user-api-version': user_api_version}, safe=False )
        except SignatureExpired:
            return JsonResponse({'set_new_password': 'signature-expired', 'user-api-version': user_api_version}, safe=False )
    except ObjectDoesNotExist as e:
        print(e)
        return JsonResponse({'set_new_password': 'username-not-found', 'error': 'No account with that username could be found.', 'user-api-version': user_api_version}, safe=False )


def forgot_username(request):
    #raise ValueError('A very specific bad thing happened.')
    # see if we can find a user who matches the requested emailaddress
    email_address = request.POST['email_address']
    #print(email_address)
    try:
        users = User.objects.filter(email=email_address)
        #print(users)
        for user in users:
            #print(user.email)

            forgot_username_content = user.first_name + ' ' + user.last_name + ','
            forgot_username_content += '\r\n\r\n'
            forgot_username_content += 'We received a request to resend your username at ' + settings.ENVIRONMENT_DOMAIN + '.'
            forgot_username_content += '\r\n\r\n'
            forgot_username_content += 'The username for the account associated with ' + email_address + ' is "' + user.username + '". Please go to the following URL to login:'
            forgot_username_content += '\r\n\r\n'
            forgot_username_content += settings.ENVIRONMENT_DOMAIN + '/login'
            forgot_username_content += '\r\n\r\n'
            forgot_username_content += 'If you did NOT submit a request for this username reminder do not click on the link. If you are concerned, please forward this notification to contact@startupwebapp.com and let us know that you did not request this username reminder.'
            forgot_username_content += '\r\n\r\n'
            forgot_username_content += 'If you have questions or would like to reach us for any reason you can reply to this email or call us toll-free at 1-844-473-3744.'
            forgot_username_content += '\r\n\r\n'
            forgot_username_content += 'Sincerely,'
            forgot_username_content += '\r\n'
            forgot_username_content += 'StartupWebApp.com'

            email = EmailMessage(
                subject = 'Forgot Username Request for ' + settings.ENVIRONMENT_DOMAIN,
                body = forgot_username_content,
                from_email = 'contact@startupwebapp.com',
                to = [user.email],
                bcc = ['contact@startupwebapp.com'],
                reply_to=['contact@startupwebapp.com'],
            )
            try:
                email.send(fail_silently=False)
            except SMTPDataError as e:
                print(e)
    except ObjectDoesNotExist as e:
        print(e)
    return JsonResponse({'forgot_username': 'success', 'user-api-version': user_api_version}, safe=False )


def update_my_information(request):
    #raise ValueError('A very specific bad thing happened.')
    if request.user.is_anonymous:
        print('AnonymousUser found!')
        return JsonResponse({'update_my_information': 'user_not_authenticated', 'user-api-version': user_api_version}, safe=False )
    #raise ValueError('A very specific bad thing happened.')
    firstname = request.POST['firstname']
    #print(firstname)
    firstname_valid = validator.isNameValid(firstname, 30)
    #print(firstname_valid)

    lastname = request.POST['lastname']
    #print(lastname)
    lastname_valid = validator.isNameValid(lastname, 150)
    #print(lastname_valid)

    email_address = request.POST['email_address']
    #print(email_address)
    email_address_valid = validator.isEmailValid(email_address, 254)
    #print(email_address_valid)

    # Validators return True or error array - must use == True
    if firstname_valid == True and lastname_valid == True and email_address_valid == True:  # noqa: E712
        print('VALIDATION PASSED - UPDATE USER INFO')
        request.user.first_name = firstname
        request.user.last_name = lastname
        old_email_address = request.user.email
        request.user.email = email_address
        request.user.save()

        if old_email_address != request.user.email:

            random_str = random.getRandomString(20, 20)
            request.user.member.email_verification_string = random_str
            signed_string = email_verification_signer.sign(random_str)
            request.user.member.email_verification_string_signed = signed_string
            request.user.member.email_verified = False
            request.user.member.save()

            edit_my_information_email_content = 'Hi ' + request.user.first_name + ' ' + request.user.last_name + '!'
            edit_my_information_email_content += '\r\n\r\n'
            edit_my_information_email_content += 'The email address associated with your ' + settings.ENVIRONMENT_DOMAIN + ' account has been modified. This email has been sent to both the previous and new email addresses associated with this account.'
            edit_my_information_email_content += '\r\n\r\n'
            edit_my_information_email_content += 'Previous email address: ' +  old_email_address
            edit_my_information_email_content += '\r\n'
            edit_my_information_email_content += 'New email address: ' +  request.user.email
            edit_my_information_email_content += '\r\n\r\n'
            edit_my_information_email_content += 'While we have your attention, we\'d love it if you took a few seconds to verify your new email address. Please go to the following URL to confirm that you are authorized to use this new email address:'
            edit_my_information_email_content += '\r\n\r\n'
            edit_my_information_email_content += settings.ENVIRONMENT_DOMAIN + '/account/?email_verification_code=' + signed_string
            edit_my_information_email_content += '\r\n\r\n'
            edit_my_information_email_content += 'Your request to verify this new email address will not be processed unless you confirm the address using this URL. This link expires 24 hours after you changed email addresses. However, you can always verify your new email address at a future date using the options on your account page.'
            edit_my_information_email_content += '\r\n\r\n'
            edit_my_information_email_content += 'If you did NOT make this request to change your email address for your account at ' + settings.ENVIRONMENT_DOMAIN + ' , do not click on the link. Instead, please forward this notification to contact@startupwebapp.com and let us know that you did not request this email address change and we\'ll dig in further to figure out what is going on.'
            edit_my_information_email_content += '\r\n\r\n'
            edit_my_information_email_content += 'If you have questions or would like to reach us for any reason you can reply to this email or call us toll-free at 1-844-473-3744.'
            edit_my_information_email_content += '\r\n\r\n'
            edit_my_information_email_content += 'Sincerely,'
            edit_my_information_email_content += '\r\n'
            edit_my_information_email_content += 'StartupWebApp.com'

            email = EmailMessage(
                subject = 'Email Address Changed on ' + settings.ENVIRONMENT_DOMAIN,
                body = edit_my_information_email_content,
                from_email = 'contact@startupwebapp.com',
                to = [request.user.email, old_email_address],
                bcc = ['contact@startupwebapp.com'],
                reply_to=['contact@startupwebapp.com'],
            )
            try:
                email.send(fail_silently=False)
            except SMTPDataError as e:
                print(e)

            return JsonResponse({'update_my_information': 'success', 'user-api-version': user_api_version}, safe=False )
        else:
            print ('email didn\'t change')
            return JsonResponse({'update_my_information': 'success', 'user-api-version': user_api_version}, safe=False )
    else:
        print('VALIDATION ERRORS - RETURN ERRORS')
        error_dict = {"firstname": firstname_valid, "lastname": lastname_valid, "email-address": email_address_valid}
        return JsonResponse({'update_my_information': 'errors', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )


def update_communication_preferences(request):
    #raise ValueError('A very specific bad thing happened.')
    #print(request.user)
    if request.user.is_anonymous:
        print('AnonymousUser found!')
        return JsonResponse({'update_communication_preferences': 'user_not_authenticated', 'user-api-version': user_api_version}, safe=False )
    if request.method == 'POST' and 'newsletter' in request.POST and 'email_unsubscribe' in request.POST:
        newsletter = request.POST['newsletter']
        email_unsubscribe = request.POST['email_unsubscribe']
        #print(newsletter)
        #print(email_unsubscribe)
        if newsletter == 'true' and email_unsubscribe == 'true':
            error_dict = {"invalid_data": "The request included an invalid data combination."}
            return JsonResponse({'update_communication_preferences': 'errors', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )
        else:
            if newsletter == 'true':
                newsletter_val = True
            else:
                newsletter_val = False

            if email_unsubscribe == 'true':
                email_unsubscribe_val = True
            else:
                email_unsubscribe_val = False

            # reset email unsubscribe string if the value of email_unsubscribe is changing from what it was
            #print(email_unsubscribe_val)
            print(request.user.member.email_unsubscribed)
            if email_unsubscribe_val != request.user.member.email_unsubscribed:
                random_str = identifier.getNewMemberEmailUnsubscribeString()
                request.user.member.email_unsubscribe_string = random_str
                signed_string = email_unsubscribe_signer.sign(random_str)
                request.user.member.email_unsubscribe_string_signed = signed_string.rsplit(':', 1)[1]

            request.user.member.newsletter_subscriber = newsletter_val
            request.user.member.email_unsubscribed = email_unsubscribe_val
            request.user.member.save()

            no_longer_want_to_receive_val = True if request.POST['no_longer_want_to_receive'] == 'true' else False
            never_signed_up_val = True if request.POST['never_signed_up'] == 'true' else False
            inappropriate_val = True if request.POST['inappropriate'] == 'true' else False
            spam_val = True if request.POST['spam'] == 'true' else False
            other_val = request.POST['other']
            if no_longer_want_to_receive_val == True or never_signed_up_val == True or inappropriate_val == True or spam_val == True or other_val == True:
                now = timezone.now()
                Emailunsubscribereasons.objects.create(member=request.user.member, no_longer_want_to_receive=no_longer_want_to_receive_val, never_signed_up=never_signed_up_val, inappropriate=inappropriate_val, spam=spam_val, other=other_val, created_date_time=now)

    else:
        error_dict = {"data_missing": "Required data was missing from the request."}
        return JsonResponse({'update_communication_preferences': 'errors', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )

    return JsonResponse({'update_communication_preferences': 'success', 'user-api-version': user_api_version}, safe=False )


def change_my_password(request):
    #raise ValueError('A very specific bad thing happened.')
    if request.user.is_anonymous:
        print('AnonymousUser found!')
        return JsonResponse({'change_my_password': 'user_not_authenticated', 'user-api-version': user_api_version}, safe=False )

    current_password = request.POST['current_password']
    password = request.POST['new_password']
    confirm_password = request.POST['confirm_new_password']

    if request.user.check_password(current_password) != True:
        error_dict = {"current-password": [{'type': 'current_password_invalid', 'description': 'The current password you provided is incorrect.'}]}
        return JsonResponse({'change_my_password': 'errors', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )
    elif request.user.check_password(password) == True:
        error_dict = {"password": [{'type': 'new_password_same_as_current_password', 'description': 'The new password cannot be the same as the old password.'}]}
        return JsonResponse({'change_my_password': 'errors', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )
    else:
        password_valid = validator.isPasswordValid(password, confirm_password, 150)
        # Validators return True or error array - must use == True
        if password_valid == True and request.user.check_password(current_password) == True:  # noqa: E712
            username = request.user.username
            request.user.set_password(password)
            request.user.save()

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                change_password_confirmation_content = user.first_name + ' ' + user.last_name + ','
                change_password_confirmation_content += '\r\n\r\n'
                change_password_confirmation_content += 'Your account password has been changed for the username "' + username + '"" at ' + settings.ENVIRONMENT_DOMAIN + '. You will now be able to login with your new password.'
                change_password_confirmation_content += '\r\n\r\n'
                change_password_confirmation_content += 'If you did NOT make this change, please forward this notification to contact@startupwebapp.com and let us know that you did not request the password change.'
                change_password_confirmation_content += '\r\n\r\n'
                change_password_confirmation_content += 'If you have questions or would like to reach us for any reason you can reply to this email or call us toll-free at 1-844-473-3744.'
                change_password_confirmation_content += '\r\n\r\n'
                change_password_confirmation_content += 'Sincerely,'
                change_password_confirmation_content += '\r\n'
                change_password_confirmation_content += 'StartupWebApp.com'

                email = EmailMessage(
                    subject = 'Password Changed on ' + settings.ENVIRONMENT_DOMAIN,
                    body = change_password_confirmation_content,
                    from_email = 'contact@startupwebapp.com',
                    to = [user.email],
                    bcc = ['contact@startupwebapp.com'],
                    reply_to=['contact@startupwebapp.com'],
                )
                try:
                    email.send(fail_silently=False)
                    return JsonResponse({'change_my_password': 'success', 'user-api-version': user_api_version}, safe=False )
                except SMTPDataError as e:
                    print(e)
                return JsonResponse({'change_my_password': 'success', 'user-api-version': user_api_version}, safe=False )

            else:
                #Return an 'invalid login' error message.
                print ('failed registration')
                return JsonResponse({'change_my_password': 'changed_password_but_login_failed', 'user-api-version': user_api_version}, safe=False )
        else:
            print('VALIDATION ERRORS - RETURN ERRORS')
            error_dict = {"password": password_valid}
            return JsonResponse({'change_my_password': 'errors', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )


def email_unsubscribe_lookup(request):
    #raise ValueError('A very specific bad thing happened.')
    token = None
    pr_token = None
    if request.method == 'GET' and ('token' in request.GET or 'pr_token' in request.GET):
        if 'token' in request.GET:
            token = request.GET['token']
        elif 'pr_token' in request.GET:
            pr_token = request.GET['pr_token']
        try:
            if token is not None:
                print('looking up member')
                member_or_prospect = Member.objects.get(email_unsubscribe_string_signed=token)
                full_email_address = member_or_prospect.user.email
                token_val = token
            elif pr_token is not None:
                print('looking up prospect')
                member_or_prospect = Prospect.objects.get(email_unsubscribe_string_signed=pr_token)
                full_email_address = member_or_prospect.email
                token_val = pr_token
            if member_or_prospect.email_unsubscribed != True:
                unsigned_value = email_unsubscribe_signer.unsign(member_or_prospect.email_unsubscribe_string + ':' + token_val)
                if unsigned_value == member_or_prospect.email_unsubscribe_string:
                    masked_email_address = email_helpers.maskEmailAddress(full_email_address)
                    response = JsonResponse({'email_unsubscribe_lookup': 'success', 'email_address': masked_email_address, 'user-api-version': user_api_version}, safe=False)
                else:
                    print("email_unsubscribe_lookup:token-invalid")
                    error_dict = {"error": 'token-invalid'}
                    response = JsonResponse({'email_unsubscribe_lookup': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
            else:
                print("email_unsubscribe_lookup:email-address-already-unsubscribed")
                error_dict = {"error": 'email-address-already-unsubscribed'}
                response = JsonResponse({'email_unsubscribe_lookup': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
        except (BadSignature) as e:
            print(e)
            print("email_unsubscribe_lookup:token-altered")
            error_dict = {"error": 'token-altered'}
            response = JsonResponse({'email_unsubscribe_lookup': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
        except (ObjectDoesNotExist, ValueError) as e:
            print(e)
            error_dict = {"error": 'member-not-found'}
            response = JsonResponse({'email_unsubscribe_lookup': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
    else:
        error_dict = {"error": 'token-required'}
        response = JsonResponse({'email_unsubscribe_lookup': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
    return response


def email_unsubscribe_confirm(request):
    token = None
    pr_token = None
    print(request.POST)
    if request.method == 'POST' and ('token' in request.POST or 'pr_token' in request.POST):
        if 'token' in request.POST:
            token = request.POST['token']
        elif 'pr_token' in request.POST:
            pr_token = request.POST['pr_token']
        try:
            if token is not None:
                member_or_prospect = Member.objects.get(email_unsubscribe_string_signed=token)
                full_email_address = member_or_prospect.user.email
                token_val = token
            elif pr_token is not None:
                member_or_prospect = Prospect.objects.get(email_unsubscribe_string_signed=pr_token)
                full_email_address = member_or_prospect.email
                token_val = pr_token
            if member_or_prospect.email_unsubscribed != True:
                unsigned_value = email_unsubscribe_signer.unsign(member_or_prospect.email_unsubscribe_string + ':' + token_val)
                if unsigned_value == member_or_prospect.email_unsubscribe_string:
                    member_or_prospect.email_unsubscribed = True
                    if token is not None:
                        member_or_prospect.newsletter_subscriber = False
                        random_str = identifier.getNewMemberEmailUnsubscribeString()
                    elif pr_token is not None:
                        random_str = identifier.getNewProspectEmailUnsubscribeString()
                    member_or_prospect.email_unsubscribe_string = random_str
                    signed_string = email_unsubscribe_signer.sign(random_str)
                    member_or_prospect.email_unsubscribe_string_signed = signed_string.rsplit(':', 1)[1]
                    member_or_prospect.save()
                    masked_email_address = email_helpers.maskEmailAddress(full_email_address)
                    response = JsonResponse({'email_unsubscribe_confirm': 'success', 'email_address': masked_email_address, 'token': signed_string.rsplit(':', 1)[1], 'user-api-version': user_api_version}, safe=False)
                else:
                    print("email_unsubscribe_lookup:token-invalid")
                    error_dict = {"error": 'token-invalid'}
                    response = JsonResponse({'email_unsubscribe_confirm': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
            else:
                print("email_unsubscribe_lookup:email-address-already-unsubscribed")
                error_dict = {"error": 'email-address-already-unsubscribed'}
                response = JsonResponse({'email_unsubscribe_confirm': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
        except (BadSignature) as e:
            print(e)
            print("email_unsubscribe_lookup:token-altered")
            error_dict = {"error": 'token-altered'}
            response = JsonResponse({'email_unsubscribe_confirm': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
        except (ObjectDoesNotExist, ValueError) as e:
            print(e)
            error_dict = {"error": 'member-not-found'}
            response = JsonResponse({'email_unsubscribe_confirm': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
    else:
        error_dict = {"error": 'token-required'}
        response = JsonResponse({'email_unsubscribe_confirm': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
    return response


def email_unsubscribe_why(request):

    token = None
    pr_token = None
    member_obj = None
    prospect_obj = None
    print(request.POST)
    if request.method == 'POST' and ('token' in request.POST or 'pr_token' in request.POST):
        if 'token' in request.POST:
            token = request.POST['token']
        elif 'pr_token' in request.POST:
            pr_token = request.POST['pr_token']
        try:
            if token is not None:
                member_or_prospect = Member.objects.get(email_unsubscribe_string_signed=token)
                member_obj = member_or_prospect
                member_or_prospect.user.email
                token_val = token
            elif pr_token is not None:
                member_or_prospect = Prospect.objects.get(email_unsubscribe_string_signed=pr_token)
                prospect_obj = member_or_prospect
                member_or_prospect.email
                token_val = pr_token


            unsigned_value = email_unsubscribe_signer.unsign(member_or_prospect.email_unsubscribe_string + ':' + token_val)
            if unsigned_value == member_or_prospect.email_unsubscribe_string:
                print('made it')

                no_longer_want_to_receive_val = True if request.POST['no_longer_want_to_receive'] == 'true' else False
                never_signed_up_val = True if request.POST['never_signed_up'] == 'true' else False
                inappropriate_val = True if request.POST['inappropriate'] == 'true' else False
                spam_val = True if request.POST['spam'] == 'true' else False
                other_val = request.POST['other']
                now = timezone.now()
                Emailunsubscribereasons.objects.create(member=member_obj, prospect=prospect_obj, no_longer_want_to_receive=no_longer_want_to_receive_val, never_signed_up=never_signed_up_val, inappropriate=inappropriate_val, spam=spam_val, other=other_val, created_date_time=now)
                response = JsonResponse({'email_unsubscribe_why': 'success', 'user-api-version': user_api_version}, safe=False)
            else:
                print("email_unsubscribe_lookup:token-invalid")
                error_dict = {"error": 'token-invalid'}
                response = JsonResponse({'email_unsubscribe_why': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
        except (BadSignature) as e:
            print(e)
            print("email_unsubscribe_lookup:token-altered")
            error_dict = {"error": 'token-altered'}
            response = JsonResponse({'email_unsubscribe_why': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
        except (ObjectDoesNotExist, ValueError) as e:
            print(e)
            error_dict = {"error": 'member-not-found'}
            response = JsonResponse({'email_unsubscribe_why': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
    else:
        error_dict = {"error": 'token-required'}
        response = JsonResponse({'email_unsubscribe_why': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
    return response


def terms_of_use_agree_check(request):
    #raise ValueError('A very specific bad thing happened.')
    most_recent_terms_of_use_version = Termsofuse.objects.all().aggregate(Max('version'))
    membertermsofuseversionagreed_exists = Membertermsofuseversionagreed.objects.filter(member=request.user.member, termsofuseversion=most_recent_terms_of_use_version['version__max']).exists()
    if membertermsofuseversionagreed_exists == True:
        #print ('membertermsofuseversionagreed_exists')
        response = JsonResponse({'terms_of_use_agree_check': True, 'user-api-version': user_api_version}, safe=False)
    else:
        #print ('membertermsofuseversionagreed_exists')
        most_recent_terms_of_use_version_obj = Termsofuse.objects.get(version=most_recent_terms_of_use_version['version__max'])
        response = JsonResponse({'terms_of_use_agree_check': False, 'version': most_recent_terms_of_use_version_obj.version, 'version_note': most_recent_terms_of_use_version_obj.version_note, 'user-api-version': user_api_version}, safe=False)
    return response


def terms_of_use_agree(request):
    #raise ValueError('A very specific bad thing happened.')
    if request.user.is_anonymous:
        print('AnonymousUser found!')
        return JsonResponse({'terms_of_use_agree': 'user_not_authenticated', 'user-api-version': user_api_version}, safe=False )
    version = None
    if request.method == 'POST' and 'version' in request.POST:
        version = request.POST['version']
    #print(version)
    if version is not None:
        try:
            request_version_obj = Termsofuse.objects.get(version=version)
            most_recent_terms_of_use_version = Termsofuse.objects.all().aggregate(Max('version'))
            most_recent_terms_of_use_version_obj = Termsofuse.objects.get(version=most_recent_terms_of_use_version['version__max'])
            #print(request_version_obj)
            #print(most_recent_terms_of_use_version)
            if request_version_obj.id == most_recent_terms_of_use_version_obj.id:
                now = timezone.now()
                try:
                    membertermsofuseversionagreed = Membertermsofuseversionagreed.objects.create(member=request.user.member, termsofuseversion=request_version_obj, agreed_date_time=now)
                    response = JsonResponse({'terms_of_use_agree': 'success', 'version': version, 'user-api-version': user_api_version}, safe=False)
                except (IntegrityError) as e:
                    print(e)
                    error_dict = {"error": 'version-already-agreed'}
                    response = JsonResponse({'terms_of_use_agree': 'error', 'errors': error_dict, 'version': version, 'user-api-version': user_api_version}, safe=False)
            else:
                error_dict = {"error": "version-provided-not-most-recent"}
                response = JsonResponse({'terms_of_use_agree': 'error', 'errors': error_dict, 'version': version, 'user-api-version': user_api_version}, safe=False)
        except (ObjectDoesNotExist, ValueError) as e:
            print(e)
            error_dict = {"error": 'version-not-found'}
            response = JsonResponse({'terms_of_use_agree': 'error', 'errors': error_dict, 'version': version, 'user-api-version': user_api_version}, safe=False)
    else:
        error_dict = {"error": 'version-required'}
        response = JsonResponse({'terms_of_use_agree': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
    return response


def process_stripe_payment_token(request):
    #raise ValueError('A very specific bad thing happened.')
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
            if request.user.member.stripe_customer_token is None:
                customer = order_utils.create_stripe_customer(stripe_token, email, 'member_username', request.user.username)
                #print('***********')
                #print(customer)
                #print('***********')
                request.user.member.stripe_customer_token = customer.id
                request.user.member.use_default_shipping_and_payment_info = True
                request.user.member.save()
            else:
                card = order_utils.stripe_customer_add_card(request.user.member.stripe_customer_token, stripe_token)
                order_utils.stripe_customer_change_default_payemnt(request.user.member.stripe_customer_token, card.id)
                request.user.member.use_default_shipping_and_payment_info = True
                request.user.member.save()

            if 'shipping_address_state' in stripe_payment_args:
                shipping_address_state = stripe_payment_args['shipping_address_state']
            else:
                shipping_address_state = ''
            if request.user.member.default_shipping_address is None:
                #create Default Shipping Address object
                default_shipping_address = Defaultshippingaddress.objects.create(name=stripe_payment_args['shipping_name'], address_line1=stripe_payment_args['shipping_address_line1'], city=stripe_payment_args['shipping_address_city'], state=shipping_address_state, zip=stripe_payment_args['shipping_address_zip'], country=stripe_payment_args['shipping_address_country'], country_code=stripe_payment_args['shipping_address_country_code'])
                request.user.member.default_shipping_address = default_shipping_address
                request.user.member.save()
            else:
                #update existing member default shipping address
                default_shipping_address = request.user.member.default_shipping_address
                default_shipping_address.name = stripe_payment_args['shipping_name']
                default_shipping_address.address_line1=stripe_payment_args['shipping_address_line1']
                default_shipping_address.city=stripe_payment_args['shipping_address_city']
                default_shipping_address.state=shipping_address_state
                default_shipping_address.zip=stripe_payment_args['shipping_address_zip']
                default_shipping_address.country=stripe_payment_args['shipping_address_country']
                default_shipping_address.country_code=stripe_payment_args['shipping_address_country_code']
                default_shipping_address.save()

            response = JsonResponse({'process_stripe_payment_token': 'success', 'user-api-version': user_api_version}, safe=False)
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

            error_dict = {"error": 'error-creating-stripe-customer', 'description': 'An error occurred while processing your request.'}
            response = JsonResponse({'process_stripe_payment_token': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
    else:
        error_dict = {"error": 'stripe-token-required', 'description': 'Stripe token is required'}
        response = JsonResponse({'process_stripe_payment_token': 'error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False)
    return response


def put_chat_message(request):
    #raise ValueError('A very specific bad thing happened.')
    name = request.POST['name']
    #print(firstname)
    name_valid = validator.isNameValid(name, 30)
    #print(firstname_valid)

    email_address = request.POST['email_address']
    #print(email_address)
    email_address_valid = validator.isEmailValid(email_address, 254)
    #print(email_address_valid)

    message = request.POST['message']
    message_valid = validator.isChatMessageValid(message, 5000)

    # Validators return True or error array - must use == True
    if name_valid == True and email_address_valid == True and message_valid == True:  # noqa: E712
        now = timezone.now()
        if request.user.is_authenticated:
            chat_message = Chatmessage.objects.create(member=request.user.member, prospect=None, name=name, email_address=email_address, message=message, created_date_time=now)
        elif User.objects.filter(email=email_address).exists():
            chat_message = Chatmessage.objects.create(member=User.objects.get(email=email_address).member, prospect=None, name=name, email_address=email_address, message=message, created_date_time=now)
        else:
            if Prospect.objects.filter(email=email_address).exists():
                chat_message = Chatmessage.objects.create(member=None, prospect=Prospect.objects.get(email=email_address), name=name, email_address=email_address, message=message, created_date_time=now)
            else:
                email_unsubscribe_string = identifier.getNewProspectEmailUnsubscribeString()
                email_unsubscribe_string_signed = email_unsubscribe_signer.sign(email_unsubscribe_string)
                email_unsubscribe_string_signed = email_unsubscribe_string_signed.rsplit(':', 1)[1]
                pr_cd = identifier.getNewProspectCode()
                prospect = Prospect.objects.create(email=email_address, email_unsubscribed=True, email_unsubscribe_string=email_unsubscribe_string, email_unsubscribe_string_signed=email_unsubscribe_string_signed, swa_comment='Captured from chat message submission', pr_cd=pr_cd, created_date_time=now)
                chat_message = Chatmessage.objects.create(member=None, prospect=prospect, name=name, email_address=email_address, message=message, created_date_time=now)

        chat_message_content = 'Hi!,'
        chat_message_content += '\r\n\r\n'
        chat_message_content += 'A new chat message has been submitted at ' + settings.ENVIRONMENT_DOMAIN + '.'
        chat_message_content += '\r\n\r\n'
        chat_message_content += 'Date/Time: ' + str(now)
        chat_message_content += '\r\n\r\n'
        chat_message_content += 'Check it out!'
        chat_message_content += '\r\n'
        chat_message_content += 'StartupWebApp.com'

        email = EmailMessage(
            subject = 'New Chat Message @ ' + settings.ENVIRONMENT_DOMAIN,
            body = chat_message_content,
            from_email = 'contact@startupwebapp.com',
            to = ['contact@startupwebapp.com'],
            reply_to=['contact@startupwebapp.com'],
        )
        try:
            #raise ValueError('A very specific bad thing happened.')
            email.send(fail_silently=False)
            return JsonResponse({'put_chat_message': 'true', 'user-api-version': user_api_version}, safe=False )
        except (SMTPDataError, ConnectionRefusedError, OSError, ValueError) as e:
            print('failed to send chat message email')
            print(e)
            # In development (DEBUG=True), SMTP server may not be running - this is OK
            # Chat message was saved successfully, so return success
            # In production (DEBUG=False), email failure is a real error that should be reported
            if settings.DEBUG:
                return JsonResponse({'put_chat_message': 'true', 'user-api-version': user_api_version}, safe=False )
            else:
                error_dict = {"email_failed": True}
                return JsonResponse({'put_chat_message': 'email_failed', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )


    else:
        error_dict = {"name": name_valid, "email_address": email_address_valid, "message": message_valid}
        return JsonResponse({'put_chat_message': 'validation_error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )


def pythonabot_notify_me(request):
    #raise ValueError('A very specific bad thing happened.')
    email_address = request.POST['email_address']
    #print(email_address)
    email_address_valid = validator.isEmailValid(email_address, 254)
    #print(email_address_valid)

    how_excited = request.POST['how_excited']
    #print(how_excited)
    how_excited_valid = validator.isHowExcitedValid(how_excited)
    #print(how_excited_valid)

    # Validators return True or error array - must use == True
    if email_address_valid == True and how_excited_valid == True:  # noqa: E712
        if Prospect.objects.filter(email=email_address).exists():
            prospect_errors = []
            duplicate_prospect_error = {'type': 'duplicate', 'description': 'I already know about this email address. Please enter a different email address.'};
            prospect_errors.append(duplicate_prospect_error)
            error_dict = {"email_address": prospect_errors, "how_excited": how_excited_valid}
            return JsonResponse({'pythonabot_notify_me': 'duplicate_prospect', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )
        else:
            now = timezone.now()
            email_unsubscribe_string = identifier.getNewProspectEmailUnsubscribeString()
            email_unsubscribe_string_signed = email_unsubscribe_signer.sign(email_unsubscribe_string)
            email_unsubscribe_string_signed = email_unsubscribe_string_signed.rsplit(':', 1)[1]
            pr_cd = identifier.getNewProspectCode()
            prospect = Prospect.objects.create(email=email_address, email_unsubscribed=True, email_unsubscribe_string=email_unsubscribe_string, email_unsubscribe_string_signed=email_unsubscribe_string_signed, prospect_comment=str(how_excited) + ' on a scale of 1-5 for how excited they are', swa_comment='This prospect would like to be notified when PythonABot is ready to be purchased.', pr_cd=pr_cd, created_date_time=now)
            return JsonResponse({'pythonabot_notify_me': 'success', 'user-api-version': user_api_version}, safe=False )
    else:
        error_dict = {"email_address": email_address_valid, "how_excited": how_excited_valid}
        return JsonResponse({'pythonabot_notify_me': 'validation_error', 'errors': error_dict, 'user-api-version': user_api_version}, safe=False )
