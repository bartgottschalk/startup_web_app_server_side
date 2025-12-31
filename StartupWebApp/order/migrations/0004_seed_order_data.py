# Data migration to seed Order app data
# Based on db_inserts.sql and load_sample_data.py

from django.db import migrations
from django.utils import timezone
from datetime import datetime, timedelta, UTC


def create_order_seed_data(apps, schema_editor):
    """
    Create seed data for Order app:
    - Order Statuses
    - SKU Type
    - Order Configuration
    - Discount Types
    - One example Discount Code
    - Shipping Methods
    - Sample Products with SKUs, Prices, and Images

    Based on db_inserts.sql lines 10-88
    Note: Skuinventory is created in migration 0002_add_default_inventory_statuses
    """
    # Skip during test runs - tests create their own data
    db_name = schema_editor.connection.settings_dict.get('NAME', '')
    if 'memory' in db_name.lower() or db_name.startswith('test_'):
        return

    # Get models
    Status = apps.get_model('order', 'Status')
    Skutype = apps.get_model('order', 'Skutype')
    Orderconfiguration = apps.get_model('order', 'Orderconfiguration')
    Discounttype = apps.get_model('order', 'Discounttype')
    Discountcode = apps.get_model('order', 'Discountcode')
    Shippingmethod = apps.get_model('order', 'Shippingmethod')
    Product = apps.get_model('order', 'Product')
    Productimage = apps.get_model('order', 'Productimage')
    Productvideo = apps.get_model('order', 'Productvideo')
    Sku = apps.get_model('order', 'Sku')
    Skuprice = apps.get_model('order', 'Skuprice')
    Productsku = apps.get_model('order', 'Productsku')
    Skuimage = apps.get_model('order', 'Skuimage')

    # Order Statuses (line 10)
    Status.objects.get_or_create(
        id=1,
        defaults={
            'identifier': 'accepted',
            'title': 'Accepted',
            'description': 'The order has been accepted by StartUpWebApp.com and is being processed.'
        }
    )
    Status.objects.get_or_create(
        id=2,
        defaults={
            'identifier': 'manufacturing',
            'title': 'Manufacturing',
            'description': 'Custom items in the order are being manufactured.'
        }
    )
    Status.objects.get_or_create(
        id=3,
        defaults={
            'identifier': 'packing',
            'title': 'Packing',
            'description': 'The order is being packed for shipment.'
        }
    )
    Status.objects.get_or_create(
        id=4,
        defaults={
            'identifier': 'shipped',
            'title': 'Shipped',
            'description': 'The order has been shipped.'
        }
    )

    # SKU Type (line 11)
    Skutype.objects.get_or_create(id=1, defaults={'title': 'product'})

    # Order Configuration (lines 14-20)
    config_items = [
        ('usernames_allowed_to_checkout', None, '*'),
        ('an_ct_values_allowed_to_checkout', None, '*'),
        ('default_shipping_method', None, 'USPSRetailGround'),
        ('initial_order_status', None, 'accepted'),
        ('order_confirmation_em_cd_member', None, 'gvREoqen93ffZsmBIc8zl'),
        ('order_confirmation_em_cd_prospect', None, 'FpGyZy6kld9R2XTjqvBQN'),
    ]
    for key, float_val, string_val in config_items:
        Orderconfiguration.objects.get_or_create(
            key=key,
            defaults={'float_value': float_val, 'string_value': string_val}
        )

    # Discount Types (lines 28-31)
    Discounttype.objects.get_or_create(
        id=1,
        defaults={
            'title': 'Save Percent Off Your Item Total',
            'description': 'Take {}% off your item total',
            'applies_to': 'item_total',
            'action': 'percent-off'
        }
    )
    Discounttype.objects.get_or_create(
        id=2,
        defaults={
            'title': 'Save Dollar Amount Off Your Item Total',
            'description': 'Save ${} on your item total',
            'applies_to': 'item_total',
            'action': 'dollar-amt-off'
        }
    )
    Discounttype.objects.get_or_create(
        id=3,
        defaults={
            'title': 'Free Months Digital Subscription',
            'description': 'Get {} months of free digital subscription with your order',
            'applies_to': 'subscription',
            'action': 'free-digital-months'
        }
    )
    Discounttype.objects.get_or_create(
        id=4,
        defaults={
            'title': 'Free USPS Retail Ground Shipping',
            'description': 'Free USPS Retail Ground shipping on your order',
            'applies_to': 'shipping',
            'action': 'free-usps-ground-shipping'
        }
    )

    # One example Discount Code - valid for 1 year from migration run
    # This demonstrates the discount system for the example site
    now = timezone.now()
    one_year_later = now + timedelta(days=365)
    Discountcode.objects.get_or_create(
        id=1,
        defaults={
            'code': 'WELCOME10',
            'description': 'Welcome! Get 10% off your first order',
            'start_date_time': now,
            'end_date_time': one_year_later,
            'combinable': False,
            'discount_amount': '10',
            'discounttype_id': 1,  # percent-off
            'order_minimum': '0'
        }
    )

    # Shipping Methods (lines 42-46)
    shipping_methods = [
        (1, 'USPS Priority Mail 2-Day', '13.65',
         'https://tools.usps.com/go/TrackConfirmAction.action?tRef=fullpage&tLc=1&text28777=&tLabels=',
         True, 'USPSPriorityMail2Day'),
        (2, 'USPS Retail Ground', '9.56',
         'https://tools.usps.com/go/TrackConfirmAction.action?tRef=fullpage&tLc=1&text28777=&tLabels=',
         True, 'USPSRetailGround'),
        (3, 'FedEx Ground', '10.85',
         'https://www.fedex.com/apps/fedextrack/?action=track&cntry_code=us&trackingnumber=',
         True, 'FedExGround'),
        (4, 'UPS Ground', '11.34',
         'https://wwwapps.ups.com/WebTracking/track?&track.x=Track&trackNums=',
         True, 'UPSGround'),
        (5, 'None', '0.00', 'none', False, 'None'),
    ]
    for ship_id, carrier, cost, url, active, identifier in shipping_methods:
        Shippingmethod.objects.get_or_create(
            id=ship_id,
            defaults={
                'carrier': carrier,
                'shipping_cost': cost,
                'tracking_code_base_url': url,
                'active': active,
                'identifier': identifier
            }
        )

    # =========================================================================
    # Sample Products (lines 48-88)
    # These provide example data for the demo site
    # =========================================================================

    # Product 1: Paper Clips
    product1, _ = Product.objects.get_or_create(
        id=1,
        defaults={
            'title': 'Paper Clips',
            'title_url': 'PaperClips',
            'identifier': 'bSusp6dBHm',
            'headline': 'Paper clips can hold up to 20 pieces of paper together!',
            'description_part_1': 'Made out of high quality metal and folded to exact specifications.',
            'description_part_2': 'Use paperclips for all your paper binding needs!'
        }
    )
    Productimage.objects.get_or_create(
        id=1,
        defaults={
            'image_url': '/img/product/paper_clip_main_2.jpg',
            'main_image': True,
            'product': product1,
            'caption': 'Paperclips'
        }
    )
    Productvideo.objects.get_or_create(
        id=1,
        defaults={
            'video_url': 'https://player.vimeo.com/video/334006583',
            'video_thumbnail_url': '/img/product/paper_clip_video_1_2_thumbnail.jpg',
            'product': product1,
            'caption': 'Watch the paper clip in action!'
        }
    )

    # SKU 1: Left Sided Paperclip (In Stock)
    sku1, _ = Sku.objects.get_or_create(
        id=1,
        defaults={
            'color': 'Silver',
            'size': 'Medium',
            'sku_type_id': 1,
            'description': 'Left Sided Paperclip',
            'sku_inventory_id': 1  # In Stock
        }
    )
    Skuprice.objects.get_or_create(
        id=1,
        defaults={
            'price': 3.5,
            'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=UTC),
            'sku': sku1
        }
    )
    Productsku.objects.get_or_create(id=1, defaults={'product': product1, 'sku': sku1})
    Skuimage.objects.get_or_create(
        id=1,
        defaults={
            'image_url': '/img/product/paper_clip_left_2.jpg',
            'main_image': True,
            'sku': sku1,
            'caption': 'Left sided paperclip'
        }
    )

    # SKU 2: Right Sided Paperclip (Back Ordered)
    sku2, _ = Sku.objects.get_or_create(
        id=2,
        defaults={
            'color': 'Silver',
            'size': 'Medium',
            'sku_type_id': 1,
            'description': 'Right sided paperclip',
            'sku_inventory_id': 2  # Back Ordered
        }
    )
    Skuprice.objects.get_or_create(
        id=2,
        defaults={
            'price': 3.5,
            'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=UTC),
            'sku': sku2
        }
    )
    Productsku.objects.get_or_create(id=2, defaults={'product': product1, 'sku': sku2})
    Skuimage.objects.get_or_create(
        id=2,
        defaults={
            'image_url': '/img/product/paper_clip_right_2.jpg',
            'main_image': True,
            'sku': sku2,
            'caption': 'Right sided paperclip'
        }
    )

    # Product 2: Binder Clips
    product2, _ = Product.objects.get_or_create(
        id=2,
        defaults={
            'title': 'Binder Clips',
            'title_url': 'BinderClips',
            'identifier': 'ITHJW3mytn',
            'headline': 'Binder clips can hold up to 100 pieces of paper together!',
            'description_part_1': (
                'These strong binder clips will hold your papers together '
                'and won\'t ever give up!'
            ),
            'description_part_2': 'Just be careful not to pinch your finger!<br><br>Come in packs of 10.'
        }
    )
    Productimage.objects.get_or_create(
        id=2,
        defaults={
            'image_url': '/img/product/binder_clips_main_2.jpg',
            'main_image': True,
            'product': product2,
            'caption': 'Multiple sizes available'
        }
    )
    Productvideo.objects.get_or_create(
        id=2,
        defaults={
            'video_url': 'https://player.vimeo.com/video/334006589',
            'video_thumbnail_url': '/img/product/binder_clip_video_1_2_thumbnail.jpg',
            'product': product2,
            'caption': 'Watch the paper binder in action!'
        }
    )

    # SKU 4: Large Binder Clip (Back Ordered)
    sku4, _ = Sku.objects.get_or_create(
        id=4,
        defaults={
            'color': 'Black',
            'size': 'Large',
            'sku_type_id': 1,
            'description': 'Large Binder Clip',
            'sku_inventory_id': 2  # Back Ordered
        }
    )
    Skuprice.objects.get_or_create(
        id=4,
        defaults={
            'price': 5.99,
            'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=UTC),
            'sku': sku4
        }
    )
    Productsku.objects.get_or_create(id=4, defaults={'product': product2, 'sku': sku4})
    Skuimage.objects.get_or_create(
        id=4,
        defaults={
            'image_url': '/img/product/binder_clip_large_2.jpg',
            'main_image': True,
            'sku': sku4,
            'caption': 'Large Binder Clip'
        }
    )

    # SKU 5: Medium Binder Clip (Out of Stock)
    sku5, _ = Sku.objects.get_or_create(
        id=5,
        defaults={
            'color': 'Black',
            'size': 'Medium',
            'sku_type_id': 1,
            'description': 'Medium Binder Clip',
            'sku_inventory_id': 3  # Out of Stock
        }
    )
    Skuprice.objects.get_or_create(
        id=5,
        defaults={
            'price': 4.99,
            'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=UTC),
            'sku': sku5
        }
    )
    Productsku.objects.get_or_create(id=5, defaults={'product': product2, 'sku': sku5})
    Skuimage.objects.get_or_create(
        id=5,
        defaults={
            'image_url': '/img/product/binder_clip_medium_2.jpg',
            'main_image': True,
            'sku': sku5,
            'caption': 'Medium Binder Clip'
        }
    )

    # SKU 6: Small Binder Clip (In Stock)
    sku6, _ = Sku.objects.get_or_create(
        id=6,
        defaults={
            'color': 'Black',
            'size': 'Small',
            'sku_type_id': 1,
            'description': 'Small Binder Clip',
            'sku_inventory_id': 1  # In Stock
        }
    )
    Skuprice.objects.get_or_create(
        id=6,
        defaults={
            'price': 3.99,
            'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=UTC),
            'sku': sku6
        }
    )
    Productsku.objects.get_or_create(id=6, defaults={'product': product2, 'sku': sku6})
    Skuimage.objects.get_or_create(
        id=6,
        defaults={
            'image_url': '/img/product/binder_clip_small_2.jpg',
            'main_image': True,
            'sku': sku6,
            'caption': 'Small Binder Clip'
        }
    )

    # Product 3: Rubber Bands
    product3, _ = Product.objects.get_or_create(
        id=3,
        defaults={
            'title': 'Rubber Bands',
            'title_url': 'RubberBands',
            'identifier': 'v26ujdy3N1',
            'headline': 'Rubber bands are perfect for keeping rolled paper rolled!',
            'description_part_1': 'Assorted colors and sizes.',
            'description_part_2': ''
        }
    )
    Productimage.objects.get_or_create(
        id=3,
        defaults={
            'image_url': '/img/product/rubber_bands_2.jpg',
            'main_image': True,
            'product': product3,
            'caption': 'Multicolor rubber bands'
        }
    )

    # SKU 7: Multi-color Rubber Bands (In Stock) with price history
    sku7, _ = Sku.objects.get_or_create(
        id=7,
        defaults={
            'color': 'Multi',
            'size': 'Multi',
            'sku_type_id': 1,
            'description': 'Multiple sizes and colors',
            'sku_inventory_id': 1  # In Stock
        }
    )
    # Two prices showing price history
    Skuprice.objects.get_or_create(
        id=7,
        defaults={
            'price': 10.99,
            'created_date_time': datetime(2019, 4, 20, 0, 0, 0, tzinfo=UTC),
            'sku': sku7
        }
    )
    Skuprice.objects.get_or_create(
        id=8,
        defaults={
            'price': 14.99,
            'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=UTC),
            'sku': sku7
        }
    )
    Productsku.objects.get_or_create(id=7, defaults={'product': product3, 'sku': sku7})


def reverse_create_order_seed_data(apps, schema_editor):
    """Reverse migration - delete seed data in reverse dependency order."""
    Status = apps.get_model('order', 'Status')
    Skutype = apps.get_model('order', 'Skutype')
    Orderconfiguration = apps.get_model('order', 'Orderconfiguration')
    Discounttype = apps.get_model('order', 'Discounttype')
    Discountcode = apps.get_model('order', 'Discountcode')
    Shippingmethod = apps.get_model('order', 'Shippingmethod')
    Product = apps.get_model('order', 'Product')
    Productimage = apps.get_model('order', 'Productimage')
    Productvideo = apps.get_model('order', 'Productvideo')
    Sku = apps.get_model('order', 'Sku')
    Skuprice = apps.get_model('order', 'Skuprice')
    Productsku = apps.get_model('order', 'Productsku')
    Skuimage = apps.get_model('order', 'Skuimage')

    # Delete in reverse order of dependencies
    Skuimage.objects.filter(id__in=[1, 2, 4, 5, 6]).delete()
    Productsku.objects.filter(id__in=[1, 2, 4, 5, 6, 7]).delete()
    Skuprice.objects.filter(id__in=[1, 2, 4, 5, 6, 7, 8]).delete()
    Sku.objects.filter(id__in=[1, 2, 4, 5, 6, 7]).delete()
    Productvideo.objects.filter(id__in=[1, 2]).delete()
    Productimage.objects.filter(id__in=[1, 2, 3]).delete()
    Product.objects.filter(id__in=[1, 2, 3]).delete()
    Shippingmethod.objects.filter(id__in=[1, 2, 3, 4, 5]).delete()
    Discountcode.objects.filter(id=1).delete()
    Discounttype.objects.filter(id__in=[1, 2, 3, 4]).delete()
    Orderconfiguration.objects.filter(key__in=[
        'usernames_allowed_to_checkout',
        'an_ct_values_allowed_to_checkout',
        'default_shipping_method',
        'initial_order_status',
        'order_confirmation_em_cd_member',
        'order_confirmation_em_cd_prospect',
    ]).delete()
    Skutype.objects.filter(id=1).delete()
    Status.objects.filter(id__in=[1, 2, 3, 4]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_alter_discountcode_discount_amount_and_more'),
    ]

    operations = [
        migrations.RunPython(
            create_order_seed_data,
            reverse_create_order_seed_data
        ),
    ]
