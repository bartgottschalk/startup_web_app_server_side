"""
Django management command to load sample data for development.

This replaces the MySQL-formatted db_inserts.sql file with a Python-based
approach that works with any database backend (SQLite, PostgreSQL, MySQL).

Usage:
    python manage.py load_sample_data
    python manage.py load_sample_data --flush  # Clear existing data first

Based on: db_inserts.sql
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import Group
from datetime import datetime

from clientevent.models import Configuration as ClientEventConfiguration
from user.models import (
    Termsofuse, Emailtype, Emailstatus, Adtype, Adstatus, Email
)
from order.models import (
    Status, Skutype, Skuinventory, Orderconfiguration,
    Discounttype, Discountcode, Shippingmethod,
    Product, Productimage, Productvideo,
    Sku, Skuprice, Productsku, Skuimage
)


class Command(BaseCommand):
    help = 'Load sample data for development (based on db_inserts.sql)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete existing sample data before loading',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing existing data...'))
            self.flush_data()

        self.stdout.write(self.style.SUCCESS('Loading sample data...'))

        self.load_auth_groups()
        self.load_clientevent_config()
        self.load_user_data()
        self.load_order_config()
        self.load_products()

        self.stdout.write(self.style.SUCCESS('✅ Sample data loaded successfully!'))

    def flush_data(self):
        """Delete existing sample data"""
        # Order matters due to foreign keys
        Product.objects.all().delete()
        Sku.objects.all().delete()
        Discountcode.objects.all().delete()
        self.stdout.write('  Cleared existing product and order data')

    def load_auth_groups(self):
        """Line 3 of db_inserts.sql"""
        Group.objects.get_or_create(id=1, defaults={'name': 'Members'})
        self.stdout.write('  ✓ Auth groups')

    def load_clientevent_config(self):
        """Line 4 of db_inserts.sql"""
        ClientEventConfiguration.objects.get_or_create(
            id=1,
            defaults={'log_client_events': True}
        )
        self.stdout.write('  ✓ ClientEvent configuration')

    def load_user_data(self):
        """Lines 5-9 of db_inserts.sql"""
        # Terms of Use (line 5)
        Termsofuse.objects.get_or_create(
            id=1,
            defaults={
                'version': '1',
                'version_note': 'Specifically, we\'ve modified our <a class="raw-link" href="/privacy-policy">Privacy Policy</a> and <a class="raw-link" href="/terms-of-sale">Terms of Sale</a>. Modifications include...',
                'publication_date_time': datetime(2019, 4, 20, 0, 0, 0, tzinfo=timezone.utc)
            }
        )

        # Email types (line 6)
        Emailtype.objects.get_or_create(id=1, defaults={'title': 'Member'})
        Emailtype.objects.get_or_create(id=2, defaults={'title': 'Prospect'})

        # Email statuses (line 7)
        Emailstatus.objects.get_or_create(id=1, defaults={'title': 'Draft'})
        Emailstatus.objects.get_or_create(id=2, defaults={'title': 'Ready'})
        Emailstatus.objects.get_or_create(id=3, defaults={'title': 'Sent'})

        # Ad types (line 8)
        Adtype.objects.get_or_create(id=1, defaults={'title': 'Google AdWords'})
        Adtype.objects.get_or_create(id=2, defaults={'title': 'Facebook'})

        # Ad statuses (line 9)
        Adstatus.objects.get_or_create(id=1, defaults={'title': 'Draft'})
        Adstatus.objects.get_or_create(id=2, defaults={'title': 'Ready'})
        Adstatus.objects.get_or_create(id=3, defaults={'title': 'Running'})
        Adstatus.objects.get_or_create(id=4, defaults={'title': 'Stopped'})

        self.stdout.write('  ✓ User app data (Terms, Email types, Ad types)')

    def load_order_config(self):
        """Lines 10-47 of db_inserts.sql"""
        # Order statuses (line 10)
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

        # SKU type (line 11) - created by migration
        Skutype.objects.get_or_create(id=1, defaults={'title': 'product'})

        # SKU inventory statuses (line 12) - created by migration 0002
        # Verify they exist
        Skuinventory.objects.get(id=1)
        Skuinventory.objects.get(id=2)
        Skuinventory.objects.get(id=3)

        # Order configuration (lines 14-20)
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

        # Discount types (lines 28-31)
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

        # Discount codes (lines 33-40)
        discount_codes = [
            (1, 'APRIL50PERCENT', '50% off your item total in April', 1, 50, 0),
            (2, 'APRILSAVER', 'Get $10 off your order of $20 or more in April', 2, 10, 20),
            (3, 'FREE3MONTHS', 'Get 3 free months subscription to our digital services', 3, 3, 0),
            (4, 'FREESHIPPING', 'Get free USPS Retail Ground shipping on all orders', 4, 100, 0),
            (5, 'AUG50PERCENT', '50% off your item total in August!', 1, 50, 0),
            (6, 'AUGSAVER', 'Get $10 off your order of $20 or more in August!', 2, 10, 20),
            (7, 'SEPT50PERCENT', '50% off your item total in September!', 1, 50, 0),
            (8, 'SEPTSAVER', 'Get $10 off your order of $20 or more in September!', 2, 10, 20),
        ]
        for code_id, code, desc, dtype_id, amount, min_order in discount_codes:
            Discountcode.objects.get_or_create(
                id=code_id,
                defaults={
                    'code': code,
                    'description': desc,
                    'start_date_time': datetime(2019, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
                    'end_date_time': datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                    'combinable': code_id in [3, 4],  # FREE3MONTHS and FREESHIPPING
                    'discount_amount': amount,
                    'discounttype_id': dtype_id,
                    'order_minimum': min_order
                }
            )

        # Shipping methods (lines 42-46)
        shipping_methods = [
            (1, 'USPS Priority Mail 2-Day', '13.65', 'https://tools.usps.com/go/TrackConfirmAction.action?tRef=fullpage&tLc=1&text28777=&tLabels=', True, 'USPSPriorityMail2Day'),
            (2, 'USPS Retail Ground', '9.56', 'https://tools.usps.com/go/TrackConfirmAction.action?tRef=fullpage&tLc=1&text28777=&tLabels=', True, 'USPSRetailGround'),
            (3, 'FedEx Ground', '10.85', 'https://www.fedex.com/apps/fedextrack/?action=track&cntry_code=us&trackingnumber=', True, 'FedExGround'),
            (4, 'UPS Ground', '11.34', 'https://wwwapps.ups.com/WebTracking/track?&track.x=Track&trackNums=', True, 'UPSGround'),
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

        self.stdout.write('  ✓ Order configuration (Status, Discounts, Shipping)')

    def load_products(self):
        """Lines 48-88 of db_inserts.sql - Create 3 products with SKUs"""

        # Product 1: Paper Clips (lines 48-60)
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

        # SKU 1: Silver/Medium (lines 52-55)
        sku1, _ = Sku.objects.get_or_create(
            id=1,
            defaults={
                'color': 'Silver',
                'size': 'Medium',
                'sku_type_id': 1,
                'description': 'Left Sided Paperclip',
                'sku_inventory_id': 1
            }
        )
        Skuprice.objects.get_or_create(
            id=1,
            defaults={
                'price': 3.5,
                'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=timezone.utc),
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

        # SKU 2: Silver/Medium Right-sided (lines 57-60)
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
                'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=timezone.utc),
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

        # Product 2: Binder Clips (lines 62-79)
        product2, _ = Product.objects.get_or_create(
            id=2,
            defaults={
                'title': 'Binder Clips',
                'title_url': 'BinderClips',
                'identifier': 'ITHJW3mytn',
                'headline': 'Binder clips can hold up to 100 pieces of paper together!',
                'description_part_1': 'These strong binder clips will hold your papers together and won\'t ever give up!',
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

        # Binder Clip SKUs (3 sizes)
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
            defaults={'price': 5.99, 'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=timezone.utc), 'sku': sku4}
        )
        Productsku.objects.get_or_create(id=4, defaults={'product': product2, 'sku': sku4})
        Skuimage.objects.get_or_create(
            id=4,
            defaults={'image_url': '/img/product/binder_clip_large_2.jpg', 'main_image': True, 'sku': sku4, 'caption': 'Large Binder Clip'}
        )

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
            defaults={'price': 4.99, 'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=timezone.utc), 'sku': sku5}
        )
        Productsku.objects.get_or_create(id=5, defaults={'product': product2, 'sku': sku5})
        Skuimage.objects.get_or_create(
            id=5,
            defaults={'image_url': '/img/product/binder_clip_medium_2.jpg', 'main_image': True, 'sku': sku5, 'caption': 'Medium Binder Clip'}
        )

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
            defaults={'price': 3.99, 'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=timezone.utc), 'sku': sku6}
        )
        Productsku.objects.get_or_create(id=6, defaults={'product': product2, 'sku': sku6})
        Skuimage.objects.get_or_create(
            id=6,
            defaults={'image_url': '/img/product/binder_clip_small_2.jpg', 'main_image': True, 'sku': sku6, 'caption': 'Small Binder Clip'}
        )

        # Product 3: Rubber Bands (lines 81-87)
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

        sku7, _ = Sku.objects.get_or_create(
            id=7,
            defaults={
                'color': 'Multi',
                'size': 'Mulit',  # Note: typo in original SQL
                'sku_type_id': 1,
                'description': 'Multiple sizes and colors',
                'sku_inventory_id': 1  # In Stock
            }
        )
        # Two prices for this SKU (showing price history)
        Skuprice.objects.get_or_create(
            id=7,
            defaults={'price': 10.99, 'created_date_time': datetime(2019, 4, 20, 0, 0, 0, tzinfo=timezone.utc), 'sku': sku7}
        )
        Skuprice.objects.get_or_create(
            id=8,
            defaults={'price': 14.99, 'created_date_time': datetime(2019, 4, 22, 0, 0, 0, tzinfo=timezone.utc), 'sku': sku7}
        )
        Productsku.objects.get_or_create(id=7, defaults={'product': product3, 'sku': sku7})

        self.stdout.write('  ✓ Products loaded:')
        self.stdout.write(f'    - {product1.title} ({product1.identifier}) with 2 SKUs')
        self.stdout.write(f'    - {product2.title} ({product2.identifier}) with 3 SKUs')
        self.stdout.write(f'    - {product3.title} ({product3.identifier}) with 1 SKU')
