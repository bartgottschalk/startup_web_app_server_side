from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
import time
from clientevent.models import Pageview, AJAXError, Buttonclick, Linkevent
from datetime import datetime
from django.utils import timezone
from user.models import Member, Prospect, Email, Ad

#from user.models import 


clientevent_api_version = '0.0.1'

#@cache_control(max_age=10) #set cache control to 10 seconds
@never_cache

def index(request):
    return HttpResponse("Hello, you're at the clientevent API (version " + clientevent_api_version + ") root. Nothing to see here...")

def pageview(request):
    #raise ValueError('A very specific bad thing happened.')    
    #return HttpResponse(status=500)
    user_id = None
    url = None
    anonymous_id = None
    pageWidth = None
    if request.method == 'GET' and 'client_event_id' in request.GET:    
        user_id = request.GET['client_event_id'] #translate client_event_id to user_id
    if request.method == 'GET' and 'anonymous_id' in request.GET:    
        anonymous_id = request.GET['anonymous_id']
    if request.method == 'GET' and 'pageWidth' in request.GET:    
        pageWidth = request.GET['pageWidth']
    if request.method == 'GET' and 'url' in request.GET:    
        url = request.GET['url']
    if url is not None:
        try:
            if user_id is None or user_id == 'null':
                user = None
            else:
                user = User.objects.get(id=user_id)
        except (ObjectDoesNotExist, ValueError) as e:
            user = None
            print('clientevent pageview user_id is None - Error: ' + str(e))
        now = timezone.now()
        remote_addr = request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR') is not None else request.META.get('REMOTE_ADDR')
        pageview = Pageview(user=user, anonymous_id=anonymous_id, url=url, page_width=pageWidth, remote_addr=remote_addr, http_user_agent=request.META.get('HTTP_USER_AGENT'), created_date_time=now)
        pageview.save()        
    return JsonResponse('thank you', safe=False)

def ajaxerror(request):
    user_id = None
    url = None
    anonymous_id = None
    error_id = None
    if request.method == 'GET' and 'client_event_id' in request.GET:    
        user_id = request.GET['client_event_id'] #translate client_event_id to user_id
    if request.method == 'GET' and 'anonymous_id' in request.GET:    
        anonymous_id = request.GET['anonymous_id']
    if request.method == 'GET' and 'url' in request.GET:    
        url = request.GET['url']
    if request.method == 'GET' and 'error_id' in request.GET:    
        error_id = request.GET['error_id']
    if url is not None:
        try:
            user = User.objects.get(id=user_id)
        except (ObjectDoesNotExist, ValueError) as e:
            user = None
            print(e)
        now = timezone.now()
        ajaxerror = AJAXError(user=user, anonymous_id=anonymous_id, url=url, error_id=error_id, created_date_time=now)
        ajaxerror.save()        
    return JsonResponse('thank you', safe=False)

def buttonclick(request):
    user_id = None
    url = None
    anonymous_id = None
    button_id = None
    if request.method == 'GET' and 'client_event_id' in request.GET:    
        user_id = request.GET['client_event_id'] #translate client_event_id to user_id
    if request.method == 'GET' and 'anonymous_id' in request.GET:    
        anonymous_id = request.GET['anonymous_id']
    if request.method == 'GET' and 'url' in request.GET:    
        url = request.GET['url']
    if request.method == 'GET' and 'button_id' in request.GET:    
        button_id = request.GET['button_id']
    if url is not None:
        try:
            user = User.objects.get(id=user_id)
        except (ObjectDoesNotExist, ValueError) as e:
            user = None
            print(e)
        now = timezone.now()
        buttonclick = Buttonclick(user=user, anonymous_id=anonymous_id, url=url, button_id=button_id, created_date_time=now)
        buttonclick.save()        
    return JsonResponse('thank you', safe=False)

def linkevent(request):
    #raise ValueError('A very specific bad thing happened.')    
    #return HttpResponse(status=500)
    user_id = None
    mb_cd = None
    pr_cd = None
    anonymous_id = None
    em_cd = None
    ad_cd = None
    url = None
    if request.method == 'GET' and 'mb_cd' in request.GET:    
        mb_cd = request.GET['mb_cd']
    if request.method == 'GET' and 'pr_cd' in request.GET:    
        pr_cd = request.GET['pr_cd']
    if request.method == 'GET' and 'anonymous_id' in request.GET:    
        anonymous_id = request.GET['anonymous_id']
    if request.method == 'GET' and 'em_cd' in request.GET:    
        em_cd = request.GET['em_cd']
    if request.method == 'GET' and 'ad_cd' in request.GET:    
        ad_cd = request.GET['ad_cd']
    if request.method == 'GET' and 'url' in request.GET:    
        url = request.GET['url']
    if url is not None:
        # Initialize all variables to None
        user = None
        prospect = None
        email = None
        ad = None

        try:
            if mb_cd is not None:
                member = Member.objects.get(mb_cd=mb_cd)
                user = member.user
        except (ObjectDoesNotExist, ValueError) as e:
            user = None
            print(e)
        try:
            if pr_cd is not None:
                prospect = Prospect.objects.get(pr_cd=pr_cd)
        except (ObjectDoesNotExist, ValueError) as e:
            prospect = None
            print(e)
        try:
            if em_cd is not None:
                email = Email.objects.get(em_cd=em_cd)
        except (ObjectDoesNotExist, ValueError) as e:
            email = None
            print(e)
        try:
            if ad_cd is not None:
                ad = Ad.objects.get(ad_cd=ad_cd)
        except (ObjectDoesNotExist, ValueError) as e:
            ad = None
            print(e)
        now = timezone.now()
        linkevent = Linkevent(user=user, prospect=prospect, anonymous_id=anonymous_id, email=email, ad=ad, url=url, created_date_time=now)
        linkevent.save()        
    return JsonResponse('thank you', safe=False)


