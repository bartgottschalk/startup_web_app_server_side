from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('token', views.token, name='token'),
    path('login', views.client_login, name='client_login'),
    path('logout', views.client_logout, name='client_logout'),
    path('logged-in', views.logged_in, name='logged_in'),
    path('account-content', views.account_content, name='account_content'),
    path('create-account', views.create_account, name='create_account'),
    path('verify-email-address', views.verify_email_address, name='verify_email_address'),
    path('verify-email-address-response', views.verify_email_address_response, name='verify_email_address_response'),
    path('reset-password', views.reset_password, name='reset_password'),
    path('set-new-password', views.set_new_password, name='set_new_password'),
    path('forgot-username', views.forgot_username, name='forgot_username'),
    path('update-my-information', views.update_my_information, name='update_my_information'),
    path('update-communication-preferences', views.update_communication_preferences, name='update_communication_preferences'),
    path('change-my-password', views.change_my_password, name='change_my_password'),
    path('email-unsubscribe-lookup', views.email_unsubscribe_lookup, name='email_unsubscribe_lookup'),
    path('email-unsubscribe-confirm', views.email_unsubscribe_confirm, name='email_unsubscribe_confirm'),
    path('email-unsubscribe-why', views.email_unsubscribe_why, name='email_unsubscribe_why'),
    path('terms-of-use-agree-check', views.terms_of_use_agree_check, name='terms_of_use_agree_check'),
    path('terms-of-use-agree', views.terms_of_use_agree, name='terms_of_use_agree'),
    path('put-chat-message', views.put_chat_message, name='put_chat_message'),
    path('process-stripe-payment-token', views.process_stripe_payment_token, name='process_stripe_payment_token'),
    path('pythonabot-notify-me', views.pythonabot_notify_me, name='pythonabot_notify_me'),
    
]