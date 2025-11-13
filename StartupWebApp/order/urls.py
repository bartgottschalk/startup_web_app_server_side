from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('products', views.products, name='products'),
    # matches for all character and digit product identifiers
    re_path(r'^product/(?P<product_identifier>[a-zA-Z\d]+$)', views.product, name='product'),

    path('cart-items', views.cart_items, name='cart_items'),
    path('cart-shipping-methods', views.cart_shipping_methods, name='cart_shipping_methods'),
    path('cart-discount-codes', views.cart_discount_codes, name='cart_discount_codes'),
    path('cart-totals', views.cart_totals, name='cart_totals'),

    path('cart-update-sku-quantity',
         views.cart_update_sku_quantity,
         name='cart_update_sku_quantity'),
    path('cart-remove-sku', views.cart_remove_sku, name='cart_remove_sku'),
    path('cart-apply-discount-code',
         views.cart_apply_discount_code,
         name='cart_apply_discount_code'),
    path('cart-remove-discount-code',
         views.cart_remove_discount_code,
         name='cart_remove_discount_code'),
    path('cart-update-shipping-method',
         views.cart_update_shipping_method,
         name='cart_update_shipping_method'),
    path('cart-delete-cart', views.cart_delete_cart, name='cart_delete_cart'),

    path('cart-add-product-sku', views.cart_add_product_sku, name='cart_add_product_sku'),

    path('checkout-allowed', views.checkout_allowed, name='checkout_allowed'),

    path('confirm-items', views.confirm_items, name='confirm_items'),
    path('confirm-shipping-method', views.confirm_shipping_method, name='confirm_shipping_method'),
    path('confirm-discount-codes', views.confirm_discount_codes, name='confirm_discount_codes'),
    path('confirm-totals', views.confirm_totals, name='confirm_totals'),
    path('confirm-payment-data', views.confirm_payment_data, name='confirm_payment_data'),
    path('confirm-place-order', views.confirm_place_order, name='confirm_place_order'),

    path('process-stripe-payment-token',
         views.process_stripe_payment_token,
         name='process_stripe_payment_token'),
    path('anonymous-email-address-payment-lookup',
         views.anonymous_email_address_payment_lookup,
         name='anonymous_email_address_payment_lookup'),
    path('change-confirmation-email-address',
         views.change_confirmation_email_address,
         name='change_confirmation_email_address'),


    re_path(r'(?P<order_identifier>^[a-zA-Z\d]+$)', views.order_detail, name='order_detail'),

]
