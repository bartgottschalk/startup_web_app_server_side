# Run these inserts after migrations have been applied to DB

INSERT INTO `auth_group` (`id`, `name`) VALUES ('1', 'Members');
INSERT INTO `clientevent_configuration` (`id`, `log_client_events`) VALUES ('1', '1');
INSERT INTO `user_terms_of_use_version` (`id`, `version`, `version_note`, `publication_date_time`) VALUES ('1', '1', 'Specifically, we\'ve modified our <a class=\"raw-link\" href=\"/privacy-policy\">Privacy Policy</a> and <a class=\"raw-link\" href=\"/terms-of-sale\">Terms of Sale</a>. Modifications include...', '2019-04-20 00:00:00.000000');
INSERT INTO `user_email_type` (`id`, `title`) VALUES (1, 'Member'), (2, 'Prospect');
INSERT INTO `user_email_status` (`id`, `title`) VALUES ('1', 'Draft'), ('2', 'Ready'), ('3', 'Sent');
INSERT INTO `user_ad_type` (`id`, `title`) VALUES ('1', 'Google AdWords'), ('2', 'Facebook');
INSERT INTO `user_ad_status` (`id`, `title`) VALUES ('1', 'Draft'), ('2', 'Ready'), ('3', 'Running'), ('4', 'Stopped');
INSERT INTO `order_status` (`id`, `identifier`, `title`, `description`) VALUES ('1', 'accepted', 'Accepted', 'The order has been accepted by StartUpWebApp.com and is being processed.'), ('2', 'manufacturing', 'Manufacturing', 'Custom items in the order are being manufactured.'), ('3', 'packing', 'Packing', 'The order is being packed for shipment.'), ('4', 'shipped', 'Shipped', 'The order has been shipped.');
INSERT INTO `order_sku_type` (`id`, `title`) VALUES ('1', 'product');
INSERT INTO `order_sku_inventory` (`id`, `title`, `identifier`, `description`) VALUES ('1', 'In Stock', 'in-stock', 'In Stock items are available to purchase.'), ('2', 'Back Ordered', 'back-ordered', 'Back Ordered items are not available to purchase at this time.'), ('3', 'Out of Stock', 'out-of-stock', 'Out of Stock items are not available to purchase.');

INSERT INTO `order_configuration` (`key`, `float_value`, `string_value`) VALUES
('usernames_allowed_to_checkout', NULL, '*'),
('an_ct_values_allowed_to_checkout', NULL, '*'),
('default_shipping_method', NULL, 'USPSRetailGround'),
('initial_order_status', NULL, 'accepted'),
('order_confirmation_em_cd_member', NULL, 'gvREoqen93ffZsmBIc8zl'),
('order_confirmation_em_cd_prospect', NULL, 'FpGyZy6kld9R2XTjqvBQN');

INSERT INTO `user_email` (`id`, `subject`, `body_html`, `body_text`, `from_address`, `bcc_address`, `email_status_id`, `email_type_id`, `em_cd`) VALUES
(1, 'StartUpWebApp.com (Local) Order Confirmation', 'test',          'Hi {recipient_first_name}, {line_break}Thank you for your order! {line_break}ORDER INFORMATION {short_line_break}{order_information} {short_line_break}View your order here: {ENVIRONMENT_DOMAIN}/account/order?identifier={identifier}&em_cd={em_cd}&mb_cd={mb_cd} {line_break}PRODUCTS {short_line_break}{product_information} {line_break}SHIPPING METHOD {short_line_break}{shipping_information} {line_break}DISCOUNT CODES {short_line_break}{discount_information} {line_break}ORDER TOTAL {short_line_break}{order_total_information} {line_break}SHIPPING ADDRESS {short_line_break}{shipping_address_information} {line_break}BILLING ADDRESS {short_line_break}{billing_address_information} {line_break}PAYMENT INFORMATION {short_line_break}{payment_information} {line_break}Note: If you did NOT place an order at {ENVIRONMENT_DOMAIN}, do not click on the link. Instead, please forward this notification to contact@startupwebapp.com and let us know that you did not place this order and we\'ll dig in further to figure out what is going on. {line_break}We\'ll send you further emails with updates on your order along with shipping tracking information once it\'s available. {line_break}Thank you for being part of the StartUp Web App community! {line_break}By placing this order you agreed to the StartUpWebApp.com Terms of Sale: {ENVIRONMENT_DOMAIN}/terms-of-sale {line_break}© 2018 StartUp Web App LLC, All rights reserved.', 'contact@startupwebapp.com', 'contact@startupwebapp.com', 2, 1, 'gvREoqen93ffZsmBIc8zl'),
(2, 'StartUpWebApp.com (Local) Order Confirmation', 'test prospect', 'Hi {recipient_first_name}, {line_break}Thank you for your order! {line_break}ORDER INFORMATION {short_line_break}{order_information} {short_line_break}View your order here: {ENVIRONMENT_DOMAIN}/account/order?identifier={identifier}&em_cd={em_cd}&pr_cd={pr_cd} {line_break}PRODUCTS {short_line_break}{product_information} {line_break}SHIPPING METHOD {short_line_break}{shipping_information} {line_break}DISCOUNT CODES {short_line_break}{discount_information} {line_break}ORDER TOTAL {short_line_break}{order_total_information} {line_break}SHIPPING ADDRESS {short_line_break}{shipping_address_information} {line_break}BILLING ADDRESS {short_line_break}{billing_address_information} {line_break}PAYMENT INFORMATION {short_line_break}{payment_information} {line_break}Note: If you did NOT place an order at {ENVIRONMENT_DOMAIN}, do not click on the link. Instead, please forward this notification to contact@startupwebapp.com and let us know that you did not place this order and we\'ll dig in further to figure out what is going on. {line_break}We\'ll send you further emails with updates on your order along with shipping tracking information once it\'s available. {line_break}Thank you for being part of the StartUp Web App community! {line_break}By placing this order you agreed to the StartUpWebApp.com Terms of Sale: {ENVIRONMENT_DOMAIN}/terms-of-sale {line_break}© 2018 StartUp Web App LLC, All rights reserved. {line_break}{prosepct_email_unsubscribe_str}', 'contact@startupwebapp.com', 'contact@startupwebapp.com', 2, 2, 'FpGyZy6kld9R2XTjqvBQN');

INSERT INTO `order_discount_type` (`id`, `title`, `description`, `applies_to`, `action`) VALUES ('1', 'Save Percent Off Your Item Total', 'Take {}% off your item total', 'item_total', 'percent-off');
INSERT INTO `order_discount_type` (`id`, `title`, `description`, `applies_to`, `action`) VALUES ('2', 'Save Dollar Amount Off Your Item Total', 'Save ${} on your item total', 'item_total', 'dollar-amt-off');
INSERT INTO `order_discount_type` (`id`, `title`, `description`, `applies_to`, `action`) VALUES ('3', 'Free Months Digital Subscription', 'Get {} months of free digital subscription with your order', 'subscription', 'free-digital-months');
INSERT INTO `order_discount_type` (`id`, `title`, `description`, `applies_to`, `action`) VALUES ('4', 'Free USPS Retail Ground Shipping', 'Free USPS Retail Ground shipping on your order', 'shipping', 'free-usps-ground-shipping');

INSERT INTO `order_discount_code` (`id`, `code`, `description`, `start_date_time`, `end_date_time`, `combinable`, `discount_amount`, `discounttype_id`, `order_minimum`) VALUES ('1', 'APRIL50PERCENT', '50% off your item total in April', '2019-04-01 00:00:00.000000', '2019-05-01 00:00:00.000000', '0', '50', '1', '0');
INSERT INTO `order_discount_code` (`id`, `code`, `description`, `start_date_time`, `end_date_time`, `combinable`, `discount_amount`, `discounttype_id`, `order_minimum`) VALUES ('2', 'APRILSAVER', 'Get $10 off your order of $20 or more in April', '2019-04-01 00:00:00.000000', '2019-05-01 00:00:00.000000', '0', '10', '2', '20');
INSERT INTO `order_discount_code` (`id`, `code`, `description`, `start_date_time`, `end_date_time`, `combinable`, `discount_amount`, `discounttype_id`, `order_minimum`) VALUES ('3', 'FREE3MONTHS', 'Get 3 free months subscription to our digital services', '2019-04-01 00:00:00.000000', '2020-01-01 00:00:00.000000', '1', '3', '3', '0');
INSERT INTO `order_discount_code` (`id`, `code`, `description`, `start_date_time`, `end_date_time`, `combinable`, `discount_amount`, `discounttype_id`, `order_minimum`) VALUES ('4', 'FREESHIPPING', 'Get free USPS Retail Ground shipping on all orders', '2019-04-01 00:00:00.000000', '2020-01-01 00:00:00.000000', '1', '100', '4', '0');
INSERT INTO `order_discount_code` (`id`, `code`, `description`, `start_date_time`, `end_date_time`, `combinable`, `discount_amount`, `discounttype_id`, `order_minimum`) VALUES ('5', 'AUG50PERCENT', '50% off your item total in August!', '2019-08-01 00:00:00.000000', '2019-09-01 00:00:00.000000', '0', '50', '1', '0');
INSERT INTO `order_discount_code` (`id`, `code`, `description`, `start_date_time`, `end_date_time`, `combinable`, `discount_amount`, `discounttype_id`, `order_minimum`) VALUES ('6', 'AUGSAVER', 'Get $10 off your order of $20 or more in August!', '2019-08-01 00:00:00.000000', '2019-09-01 00:00:00.000000', '0', '10', '2', '20');
INSERT INTO `order_discount_code` (`id`, `code`, `description`, `start_date_time`, `end_date_time`, `combinable`, `discount_amount`, `discounttype_id`, `order_minimum`) VALUES ('7', 'SEPT50PERCENT', '50% off your item total in September!', '2019-09-01 00:00:00.000000', '2019-10-01 00:00:00.000000', '0', '50', '1', '0');
INSERT INTO `order_discount_code` (`id`, `code`, `description`, `start_date_time`, `end_date_time`, `combinable`, `discount_amount`, `discounttype_id`, `order_minimum`) VALUES ('8', 'SEPTSAVER', 'Get $10 off your order of $20 or more in September!', '2019-09-01 00:00:00.000000', '2019-10-01 00:00:00.000000', '0', '10', '2', '20');

INSERT INTO `order_shipping_method` (`id`, `carrier`, `shipping_cost`, `tracking_code_base_url`, `active`, `identifier`) VALUES ('1', 'USPS Priority Mail 2-Day', '13.65', 'https://tools.usps.com/go/TrackConfirmAction.action?tRef=fullpage&tLc=1&text28777=&tLabels=', '1', 'USPSPriorityMail2Day');
INSERT INTO `order_shipping_method` (`id`, `carrier`, `shipping_cost`, `tracking_code_base_url`, `active`, `identifier`) VALUES ('2', 'USPS Retail Ground', '9.56', 'https://tools.usps.com/go/TrackConfirmAction.action?tRef=fullpage&tLc=1&text28777=&tLabels=', '1', 'USPSRetailGround');
INSERT INTO `order_shipping_method` (`id`, `carrier`, `shipping_cost`, `tracking_code_base_url`, `active`, `identifier`) VALUES ('3', 'FedEx Ground', '10.85', 'https://www.fedex.com/apps/fedextrack/?action=track&cntry_code=us&trackingnumber=', '1', 'FedExGround');
INSERT INTO `order_shipping_method` (`id`, `carrier`, `shipping_cost`, `tracking_code_base_url`, `active`, `identifier`) VALUES ('4', 'UPS Ground', '11.34', 'https://wwwapps.ups.com/WebTracking/track?&track.x=Track&trackNums=', '1', 'UPSGround');
INSERT INTO `order_shipping_method` (`id`, `carrier`, `shipping_cost`, `tracking_code_base_url`, `active`, `identifier`) VALUES ('5', 'None', '0.00', 'none', '0', 'None');

INSERT INTO `order_product` (`id`, `title`, `title_url`, `identifier`, `headline`, `description_part_1`, `description_part_2`) VALUES ('1', 'Paper Clips', 'PaperClips', 'bSusp6dBHm', 'Paper clips can hold up to 20 pieces of paper together!', 'Made out of high quality metal and folded to exact specifications.', 'Use paperclips for all your paper binding needs!');
INSERT INTO `order_product_image` (`id`, `image_url`, `main_image`, `product_id`, `caption`) VALUES ('1', '/img/product/paper_clip_main.png', '1', '1', 'Paperclips');
INSERT INTO `order_product_video` (`id`, `video_url`, `video_thumbnail_url`, `product_id`, `caption`) VALUES ('1', 'https://player.vimeo.com/video/218142267', '/img/product/paper_clip_video1_thumbnail.png', '1', 'Watch the paper clip in action!');

INSERT INTO `order_sku` (`id`, `color`, `size`, `sku_type_id`, `description`, `sku_inventory_id`) VALUES ('1', 'Silver', 'Medium', '1', 'Left Sided Paperclip', '1');
INSERT INTO `order_sku_price` (`id`, `price`, `created_date_time`, `sku_id`) VALUES ('1', '3.5', '2019-04-22 00:00:00.000000', '1');
INSERT INTO `order_product_sku` (`id`, `product_id`, `sku_id`) VALUES ('1', '1', '1');
INSERT INTO `order_sku_image` (`id`, `image_url`, `main_image`, `sku_id`, `caption`) VALUES ('1', '/img/product/paper_clip1.png', '1', '1', 'Left sided paperclip');

INSERT INTO `order_sku` (`id`, `color`, `size`, `sku_type_id`, `description`, `sku_inventory_id`) VALUES ('2', 'Silver', 'Medium', '1', 'Right sided paperclip', '2');
INSERT INTO `order_sku_price` (`id`, `price`, `created_date_time`, `sku_id`) VALUES ('2', '3.5', '2019-04-22 00:00:00.000000', '2');
INSERT INTO `order_product_sku` (`id`, `product_id`, `sku_id`) VALUES ('2', '1', '2');
INSERT INTO `order_sku_image` (`id`, `image_url`, `main_image`, `sku_id`, `caption`) VALUES ('2', '/img/product/paper_clip2.png', '1', '2', 'Right sided paperclip');

INSERT INTO `order_product` (`id`, `title`, `title_url`, `identifier`, `headline`, `description_part_1`, `description_part_2`) VALUES ('2', 'Binder Clips', 'BinderClips', 'ITHJW3mytn', 'Binder clips can hold up to 100 pieces of paper together!', 'These strong binder clips will hold your papers together and won\'t ever give up!', 'Just be careful not to pinch your finger!<br><br>Come in packs of 10.');
INSERT INTO `order_product_image` (`id`, `image_url`, `main_image`, `product_id`, `caption`) VALUES ('2', '/img/product/binder_clips_main.png', '1', '2', 'Multiple sizes available');

INSERT INTO `order_sku` (`id`, `color`, `size`, `sku_type_id`, `description`, `sku_inventory_id`) VALUES ('3', 'Black', 'Extra Large', '1', 'Extra Large Binder Clip', '1');
INSERT INTO `order_sku_price` (`id`, `price`, `created_date_time`, `sku_id`) VALUES ('3', '6.99', '2019-04-22 00:00:00.000000', '3');
INSERT INTO `order_product_sku` (`id`, `product_id`, `sku_id`) VALUES ('3', '2', '3');
INSERT INTO `order_sku_image` (`id`, `image_url`, `main_image`, `sku_id`, `caption`) VALUES ('3', '/img/product/binder_clip_extra_large.png', '1', '3', 'Extra Large Binder Clip');

INSERT INTO `order_sku` (`id`, `color`, `size`, `sku_type_id`, `description`, `sku_inventory_id`) VALUES ('4', 'Black', 'Large', '1', 'Large Binder Clip', '2');
INSERT INTO `order_sku_price` (`id`, `price`, `created_date_time`, `sku_id`) VALUES ('4', '5.99', '2019-04-22 00:00:00.000000', '4');
INSERT INTO `order_product_sku` (`id`, `product_id`, `sku_id`) VALUES ('4', '2', '4');
INSERT INTO `order_sku_image` (`id`, `image_url`, `main_image`, `sku_id`, `caption`) VALUES ('4', '/img/product/binder_clip_large.png', '1', '4', 'Large Binder Clip');

INSERT INTO `order_sku` (`id`, `color`, `size`, `sku_type_id`, `description`, `sku_inventory_id`) VALUES ('5', 'Black', 'Medium', '1', 'Medium Binder Clip', '3');
INSERT INTO `order_sku_price` (`id`, `price`, `created_date_time`, `sku_id`) VALUES ('5', '4.99', '2019-04-22 00:00:00.000000', '5');
INSERT INTO `order_product_sku` (`id`, `product_id`, `sku_id`) VALUES ('5', '2', '5');
INSERT INTO `order_sku_image` (`id`, `image_url`, `main_image`, `sku_id`, `caption`) VALUES ('5', '/img/product/binder_clip_medium.png', '1', '5', 'Medium Binder Clip');

INSERT INTO `order_sku` (`id`, `color`, `size`, `sku_type_id`, `description`, `sku_inventory_id`) VALUES ('6', 'Black', 'Small', '1', 'Small Binder Clip', '1');
INSERT INTO `order_sku_price` (`id`, `price`, `created_date_time`, `sku_id`) VALUES ('6', '3.99', '2019-04-22 00:00:00.000000', '6');
INSERT INTO `order_product_sku` (`id`, `product_id`, `sku_id`) VALUES ('6', '2', '6');
INSERT INTO `order_sku_image` (`id`, `image_url`, `main_image`, `sku_id`, `caption`) VALUES ('6', '/img/product/binder_clip_small.png', '1', '6', 'Small Binder Clip');

INSERT INTO `order_product` (`id`, `title`, `title_url`, `identifier`, `headline`, `description_part_1`, `description_part_2`) VALUES ('3', 'Rubber Bands', 'RubberBands', 'v26ujdy3N1', 'Rubber bands are perfect for keeping rolled paper rolled!', 'Assorted colors and sizes.', '');
INSERT INTO `order_product_image` (`id`, `image_url`, `main_image`, `product_id`, `caption`) VALUES ('3', '/img/product/rubber_bands1.png', '1', '3', 'Multicolor rubber bands');

INSERT INTO `order_sku` (`id`, `color`, `size`, `sku_type_id`, `description`, `sku_inventory_id`) VALUES ('7', 'Multi', 'Mulit', '1', 'Multiple sizes and colors', '1');
INSERT INTO `order_sku_price` (`id`, `price`, `created_date_time`, `sku_id`) VALUES ('7', '10.99', '2019-04-20 00:00:00.000000', '7');
INSERT INTO `order_sku_price` (`id`, `price`, `created_date_time`, `sku_id`) VALUES ('8', '14.99', '2019-04-22 00:00:00.000000', '7');
INSERT INTO `order_product_sku` (`id`, `product_id`, `sku_id`) VALUES ('7', '3', '7');

