from django.contrib import admin
from order.models import Orderpayment, Ordershippingaddress, Orderbillingaddress, Order, Ordersku, Orderdiscount, Status, Orderstatus, Ordershippingmethod
from order.models import Orderconfiguration, Cartshippingaddress, Cart, Cartsku, Sku, Skuprice, Skuimage, Skutype, Skuinventory, Product, Productimage, Productvideo, Productsku, Discounttype, Discountcode, Cartdiscount, Shippingmethod, Cartshippingmethod

class OrderAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'member', 'agreed_with_terms_of_sale', 'order_total', 'item_subtotal', 'item_discount_amt', 'shipping_amt', 'shipping_discount_amt', 'sales_tax_amt', 'order_date_time')
    actions = ['generate_order_pdfs_for_home', 'generate_order_pdfs_for_terraslate', 'generate_order_pdfs_for_terraslate2', 'generate_order_pdfs_for_shapco']

# Define a new Orderpayment admin
class OrderpaymentAdmin(admin.ModelAdmin):
    list_display = ('order_identifier', 'card_brand', 'card_last4', 'card_exp_month', 'card_exp_year', 'email', 'card_zip')

# Define a new Ordershippingaddress admin
class OrdershippingaddressAdmin(admin.ModelAdmin):
    list_display = ('order_identifier', 'name', 'address_line1', 'city', 'state', 'zip', 'country_code')

# Define a new Orderbillingaddress admin
class OrderbillingaddressAdmin(admin.ModelAdmin):
    list_display = ('order_identifier', 'name', 'address_line1', 'city', 'state', 'zip', 'country_code')

# Define a new Cart admin
class CartAdmin(admin.ModelAdmin):
    list_display = ('member', 'anonymous_cart_id')

# Define a new Cartshippingaddress admin
class CartshippingaddressAdmin(admin.ModelAdmin):
    list_display = ('name', 'address_line1', 'city', 'state', 'zip', 'country_code')

# Define a new Skutype admin
class SkutypeAdmin(admin.ModelAdmin):
    list_display = ['title']

# Define a new Skuinventory admin
class SkuinventoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'identifier', 'description')
    
# Define a new Product admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_url', 'identifier', 'headline')

# Define a new Productimage admin
class ProductimageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_url', 'main_image', 'caption') 

# Define a new Productvideo admin
class ProductvideoAdmin(admin.ModelAdmin):
    list_display = ('product', 'video_url', 'video_thumbnail_url', 'caption') 

# Define a new Sku admin
class SkuAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'sku_type', 'sku_inventory', 'color', 'size')

# Define a new Skuprice admin
class SkupriceAdmin(admin.ModelAdmin):
    list_display = ('sku', 'price', 'created_date_time')

# Define a new Productsku admin
class ProductskuAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku')

# Define a new Skuimage admin
class SkuimageAdmin(admin.ModelAdmin):
    list_display = ('sku', 'image_url', 'main_image', 'caption')

# Define a new Cartsku admin
class CartskuAdmin(admin.ModelAdmin):
    list_display = ('cart', 'sku', 'quantity')

# Define a new Discounttype admin
class DiscounttypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'applies_to', 'action')

# Define a new Discountcode admin
class DiscountcodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'start_date_time', 'end_date_time', 'combinable', 'discounttype', 'discount_amount', 'order_minimum')

# Define a new Cartdiscount admin
class CartdiscountAdmin(admin.ModelAdmin):
    list_display = ('cart', 'discountcode')

# Define a new Shippingmethod admin
class ShippingmethodAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'carrier', 'shipping_cost', 'tracking_code_base_url', 'active')

# Define a new Cartshippingmethod admin
class CartshippingmethodAdmin(admin.ModelAdmin):
    list_display = ('cart', 'shippingmethod')

# Define a new Orderconfiguration admin
class OrderconfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'float_value', 'string_value')

# Define a new Cartsku admin
class OrderskuAdmin(admin.ModelAdmin):
    list_display = ('order_identifier', 'order', 'sku', 'quantity', 'price_each')

# Define a new Orderdiscount admin
class OrderdiscountAdmin(admin.ModelAdmin):
    list_display = ('order_identifier', 'order', 'discountcode', 'applied')

# Define a new Status admin
class StatusAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'title', 'description')

# Define a new Orderstatus admin
class OrderstatusAdmin(admin.ModelAdmin):
    list_display = ('order_identifier', 'order', 'status', 'created_date_time')

# Define a new Ordershippingmethod admin
class OrdershippingmethodAdmin(admin.ModelAdmin):
    list_display = ('order_identifier', 'order', 'shippingmethod', 'tracking_number')



# Register your models here.
admin.site.register(Orderpayment, OrderpaymentAdmin)
admin.site.register(Ordershippingaddress, OrdershippingaddressAdmin)
admin.site.register(Orderbillingaddress, OrderbillingaddressAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Ordersku, OrderskuAdmin)
admin.site.register(Orderdiscount, OrderdiscountAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(Orderstatus, OrderstatusAdmin)
admin.site.register(Ordershippingmethod, OrdershippingmethodAdmin)

admin.site.register(Orderconfiguration, OrderconfigurationAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Cartshippingaddress, CartshippingaddressAdmin)
admin.site.register(Cartsku, CartskuAdmin)
admin.site.register(Sku, SkuAdmin)
admin.site.register(Skuprice, SkupriceAdmin)
admin.site.register(Skuimage, SkuimageAdmin)
admin.site.register(Skutype, SkutypeAdmin)
admin.site.register(Skuinventory, SkuinventoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Productimage, ProductimageAdmin)
admin.site.register(Productvideo, ProductvideoAdmin)
admin.site.register(Productsku, ProductskuAdmin)
admin.site.register(Discounttype, DiscounttypeAdmin)
admin.site.register(Discountcode, DiscountcodeAdmin)
admin.site.register(Cartdiscount, CartdiscountAdmin)
admin.site.register(Shippingmethod, ShippingmethodAdmin)
admin.site.register(Cartshippingmethod, CartshippingmethodAdmin)






