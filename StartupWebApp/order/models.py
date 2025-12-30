from django.db import models
from user.models import Member, Prospect

# Create your models here.


class Orderconfiguration(models.Model):
    key = models.CharField(max_length=100)
    float_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    string_value = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'order_configuration'

    def __str__(self):
        return 'key: ' + str(self.key) + 'float_value: ' + \
            str(self.float_value) + 'string_value: ' + str(self.string_value)


class Cartshippingaddress(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    address_line1 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=200, blank=True, null=True)
    state = models.CharField(max_length=40, blank=True, null=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = 'order_cart_shipping_address'

    def __str__(self):
        return str(self.name) + ', ' + str(self.address_line1) + ', ' + str(self.city) + \
            ', ' + str(self.state) + ' ' + str(self.zip) + ', ' + str(self.country_code)


class Cartpayment(models.Model):
    stripe_customer_token = models.CharField(max_length=100, blank=True, null=True)
    stripe_card_id = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)

    class Meta:
        db_table = 'order_cart_payment'

    def __str__(self):
        return str(self.email) + ': ' + str(self.stripe_customer_token) + \
            ': ' + str(self.stripe_card_id)


class Cart(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, blank=True, null=True)
    anonymous_cart_id = models.CharField(max_length=100, blank=True, null=True)
    shipping_address = models.ForeignKey(
        Cartshippingaddress,
        on_delete=models.CASCADE,
        blank=True,
        null=True)
    payment = models.ForeignKey(Cartpayment, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'order_cart'

    def __str__(self):
        return str(self.member.user.username if self.member is not None else None) + \
            ": " + str(self.anonymous_cart_id)


class Skutype(models.Model):
    title = models.CharField(max_length=100)

    class Meta:
        db_table = 'order_sku_type'

    def __str__(self):
        return self.title


class Skuinventory(models.Model):
    title = models.CharField(max_length=100)
    identifier = models.CharField(unique=True, max_length=100)
    description = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'order_sku_inventory'

    def __str__(self):
        return self.title


class Sku(models.Model):
    sku_type = models.ForeignKey(Skutype, on_delete=models.CASCADE)
    sku_inventory = models.ForeignKey(Skuinventory, on_delete=models.CASCADE)
    color = models.CharField(max_length=500, blank=True, null=True)
    size = models.CharField(max_length=500, blank=True, null=True)
    description = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        db_table = 'order_sku'

    def __str__(self):
        return str(self.id) + ', type: ' + str(self.sku_type) + \
            ', color: ' + str(self.color) + ', size: ' + str(self.size)


class Skuprice(models.Model):
    sku = models.ForeignKey(Sku, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_date_time = models.DateTimeField()

    class Meta:
        db_table = 'order_sku_price'

    def __str__(self):
        return str(self.sku.id) + ": $" + str(self.price) + ": " + str(self.created_date_time)


class Skuimage(models.Model):
    sku = models.ForeignKey(Sku, on_delete=models.CASCADE)
    image_url = models.CharField(max_length=500)
    main_image = models.BooleanField(default=False)
    caption = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'order_sku_image'

    def __str__(self):
        return str(self.sku) + ": $" + str(self.image_url) + ": " + str(self.main_image)


class Cartsku(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    sku = models.ForeignKey(Sku, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    class Meta:
        db_table = 'order_cart_sku'
        unique_together = (('cart', 'sku'),)

    def __str__(self):
        return str(self.cart) + ": " + str(self.sku) + ": " + str(self.quantity)


class Product(models.Model):
    title = models.CharField(max_length=200)
    title_url = models.CharField(max_length=100)
    identifier = models.CharField(unique=True, max_length=100)
    headline = models.CharField(max_length=5000, blank=True, null=True)
    description_part_1 = models.CharField(max_length=5000, blank=True, null=True)
    description_part_2 = models.CharField(max_length=5000, blank=True, null=True)

    class Meta:
        db_table = 'order_product'

    def __str__(self):
        return self.title_url


class Productimage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image_url = models.CharField(max_length=500)
    main_image = models.BooleanField(default=False)
    caption = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'order_product_image'

    def __str__(self):
        return str(self.product) + ": $" + str(self.image_url) + ": " + str(self.main_image)


class Productvideo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    video_url = models.CharField(max_length=500)
    video_thumbnail_url = models.CharField(max_length=500)
    caption = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'order_product_video'

    def __str__(self):
        return str(self.product) + ": $" + str(self.video_url)


class Productsku(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sku = models.ForeignKey(Sku, on_delete=models.CASCADE)

    class Meta:
        db_table = 'order_product_sku'
        unique_together = (('product', 'sku'),)

    def __str__(self):
        return str(self.product) + ": " + str(self.sku)


class Discounttype(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    applies_to = models.CharField(max_length=100)
    action = models.CharField(max_length=100)

    class Meta:
        db_table = 'order_discount_type'

    def __str__(self):
        return str(self.title) + ': ' + str(self.description) + ': ' + str(self.applies_to)


class Discountcode(models.Model):
    code = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    start_date_time = models.DateTimeField()
    end_date_time = models.DateTimeField()
    combinable = models.BooleanField(default=False)
    discounttype = models.ForeignKey(Discounttype, on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_minimum = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'order_discount_code'

    def __str__(self):
        return str(self.code) + ", start: " + str(self.start_date_time) + \
            ", end: " + str(self.end_date_time)


class Cartdiscount(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    discountcode = models.ForeignKey(Discountcode, on_delete=models.CASCADE)

    class Meta:
        db_table = 'order_cart_discount'
        unique_together = (('cart', 'discountcode'),)

    def __str__(self):
        return str(self.cart) + ": " + str(self.discountcode)


class Shippingmethod(models.Model):
    identifier = models.CharField(max_length=100)
    carrier = models.CharField(max_length=100)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    tracking_code_base_url = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'order_shipping_method'

    def __str__(self):
        return str(self.carrier) + ': ' + str(self.shipping_cost) + \
            ': ' + str(self.tracking_code_base_url)


class Cartshippingmethod(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    shippingmethod = models.ForeignKey(Shippingmethod, on_delete=models.CASCADE)

    class Meta:
        db_table = 'order_cart_shipping_method'
        unique_together = (('cart', 'shippingmethod'),)

    def __str__(self):
        return str(self.cart) + ": " + str(self.shippingmethod)


class Orderpayment(models.Model):
    email = models.CharField(max_length=254, blank=True, null=True)
    payment_type = models.CharField(max_length=20, blank=True, null=True)
    card_name = models.CharField(max_length=200, blank=True, null=True)
    card_brand = models.CharField(max_length=20, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_exp_month = models.CharField(max_length=2, blank=True, null=True)
    card_exp_year = models.CharField(max_length=4, blank=True, null=True)
    card_zip = models.CharField(max_length=10, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True, unique=True)

    class Meta:
        db_table = 'order_order_payment'

    def __str__(self):
        return str(self.card_brand) + ': **** **** **** ' + str(self.card_last4) + \
            ', Exp ' + str(self.card_exp_month) + '/' + str(self.card_exp_year)

    def order_identifier(self):
        if self.order_set.first() is not None:
            return self.order_set.first().identifier
        else:
            return 'Undefined'
    order_identifier.short_description = 'Order Identifier'


class Ordershippingaddress(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    address_line1 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=200, blank=True, null=True)
    state = models.CharField(max_length=40, blank=True, null=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = 'order_order_shipping_address'

    def __str__(self):
        return str(self.name) + ', ' + str(self.address_line1) + ', ' + str(self.city) + \
            ', ' + str(self.state) + ' ' + str(self.zip) + ', ' + str(self.country_code)

    def order_identifier(self):
        if self.order_set.first() is not None:
            return self.order_set.first().identifier
        else:
            return 'Undefined'
    order_identifier.short_description = 'Order Identifier'


class Orderbillingaddress(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    address_line1 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=200, blank=True, null=True)
    state = models.CharField(max_length=40, blank=True, null=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = 'order_order_billing_address'

    def __str__(self):
        return str(self.name) + ', ' + str(self.address_line1) + ', ' + str(self.city) + \
            ', ' + str(self.state) + ' ' + str(self.zip) + ', ' + str(self.country_code)

    def order_identifier(self):
        if self.order_set.first() is not None:
            return self.order_set.first().identifier
        else:
            return 'Undefined'
    order_identifier.short_description = 'Order Identifier'


class Order(models.Model):
    identifier = models.CharField(unique=True, max_length=100, blank=True, null=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, blank=True, null=True)
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, blank=True, null=True)
    payment = models.ForeignKey(Orderpayment, on_delete=models.CASCADE, blank=True, null=True)
    shipping_address = models.ForeignKey(
        Ordershippingaddress,
        on_delete=models.CASCADE,
        blank=True,
        null=True)
    billing_address = models.ForeignKey(
        Orderbillingaddress,
        on_delete=models.CASCADE,
        blank=True,
        null=True)
    sales_tax_amt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    item_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    item_discount_amt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_discount_amt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    agreed_with_terms_of_sale = models.BooleanField(default=False)
    order_date_time = models.DateTimeField()

    class Meta:
        db_table = 'order_order'

    def __str__(self):
        return str(self.order_date_time) + ":" + str(self.sales_tax_amt) + ":" + str(self.member)


class Ordersku(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    sku = models.ForeignKey(Sku, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_each = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'order_order_sku'
        unique_together = (('order', 'sku'),)

    def __str__(self):
        return str(self.order) + ":" + str(self.sku) + ":" + \
            str(self.quantity) + ":" + str(self.price_each)

    def order_identifier(self):
        if self.order is not None:
            return self.order.identifier
        else:
            return 'Undefined'
    order_identifier.short_description = 'Order Identifier'


class Orderdiscount(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    discountcode = models.ForeignKey(Discountcode, on_delete=models.CASCADE)
    applied = models.BooleanField(default=False)

    class Meta:
        db_table = 'order_order_discount'
        unique_together = (('order', 'discountcode'),)

    def __str__(self):
        return str(self.order) + ":" + str(self.discountcode) + ":" + str(self.applied)

    def order_identifier(self):
        if self.order is not None:
            return self.order.identifier
        else:
            return 'Undefined'
    order_identifier.short_description = 'Order Identifier'


class Status(models.Model):
    identifier = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)

    class Meta:
        db_table = 'order_status'

    def __str__(self):
        return str(self.identifier) + ': ' + str(self.title) + ': ' + str(self.description)


class Orderstatus(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    created_date_time = models.DateTimeField()

    class Meta:
        db_table = 'order_order_status'
        unique_together = (('order', 'status'),)

    def __str__(self):
        return str(self.order) + ":" + str(self.status) + ":" + str(self.created_date_time)

    def order_identifier(self):
        if self.order is not None:
            return self.order.identifier
        else:
            return 'Undefined'
    order_identifier.short_description = 'Order Identifier'


class Ordershippingmethod(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    shippingmethod = models.ForeignKey(Shippingmethod, on_delete=models.CASCADE)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'order_order_shipping_method'
        unique_together = (('order', 'shippingmethod'),)

    def __str__(self):
        return str(self.order) + ": " + str(self.shippingmethod) + ": " + str(self.tracking_number)

    def order_identifier(self):
        if self.order is not None:
            return self.order.identifier
        else:
            return 'Undefined'
    order_identifier.short_description = 'Order Identifier'


class Orderemailfailure(models.Model):
    FAILURE_TYPE_CHOICES = [
        ('template_lookup', 'Email template not found'),
        ('formatting', 'Email body formatting failed'),
        ('smtp_send', 'SMTP email sending failed'),
        ('emailsent_log', 'Emailsent record creation failed'),
        ('cart_delete', 'Cart deletion failed'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    failure_type = models.CharField(max_length=50, choices=FAILURE_TYPE_CHOICES)
    error_message = models.TextField()
    customer_email = models.EmailField()
    is_member_order = models.BooleanField(default=False)
    phase = models.CharField(max_length=20, blank=True, null=True)
    created_date_time = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_date_time = models.DateTimeField(blank=True, null=True)
    resolved_by = models.CharField(max_length=200, blank=True, null=True)
    resolution_notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'order_order_email_failure'
        indexes = [
            models.Index(fields=['resolved', 'created_date_time'], name='idx_resolved_created'),
            models.Index(fields=['order'], name='idx_order'),
            models.Index(fields=['customer_email'], name='idx_customer_email'),
        ]

    def __str__(self):
        return f"{self.order.identifier}: {self.failure_type} - {self.customer_email}"

    def order_identifier(self):
        if self.order is not None:
            return self.order.identifier
        else:
            return 'Undefined'
    order_identifier.short_description = 'Order Identifier'
