"""
Centralized discount calculator for order processing.

Business Rules:
1. Only ONE item discount can be applied (first valid one that meets order minimum)
2. Only ONE shipping discount can be applied (first valid one that meets order minimum)
3. Item discount + Shipping discount CAN be combined (separate calculations)
4. Subscription discounts don't affect payment amount (future feature)
5. The "combinable" flag is stored in the database but not currently used

This module centralizes all discount calculation logic to avoid duplication across:
- order/utilities/order_utils.py
- order/views.py (Stripe integration)
- Frontend display logic
"""

from decimal import Decimal
from order.models import Cartsku, Cartdiscount, Cartshippingmethod, Skuprice


def calculate_discounts(cart):
    """
    Calculate all applicable discounts for a cart.

    Args:
        cart: Cart object

    Returns:
        dict: {
            'item_subtotal': Decimal,
            'item_discount': Decimal,
            'shipping_subtotal': Decimal,
            'shipping_discount': Decimal,
            'cart_total': Decimal
        }
    """
    # Calculate item subtotal
    item_subtotal = _calculate_item_subtotal(cart)

    # Calculate shipping subtotal
    shipping_subtotal = _calculate_shipping_subtotal(cart)

    # Calculate item discount (only first valid one applies)
    item_discount = _calculate_item_discount(cart, item_subtotal)

    # Calculate shipping discount (only first valid one applies)
    shipping_discount = _calculate_shipping_discount(cart, item_subtotal)

    # Calculate cart total
    cart_total = item_subtotal - item_discount + shipping_subtotal - shipping_discount

    return {
        'item_subtotal': item_subtotal,
        'item_discount': item_discount,
        'shipping_subtotal': shipping_subtotal,
        'shipping_discount': shipping_discount,
        'cart_total': cart_total
    }


def _calculate_item_subtotal(cart):
    """
    Calculate the item subtotal (sum of all items * quantity * price).

    Args:
        cart: Cart object

    Returns:
        Decimal: Total item cost before discounts
    """
    item_subtotal = Decimal('0.00')

    if cart is None:
        return item_subtotal

    for cartsku in Cartsku.objects.filter(cart=cart):
        # Get the latest price for this SKU
        latest_price = Skuprice.objects.filter(sku=cartsku.sku).latest('created_date_time')
        item_price = latest_price.price * cartsku.quantity
        item_subtotal += item_price

    return item_subtotal


def _calculate_shipping_subtotal(cart):
    """
    Calculate the shipping subtotal.

    Args:
        cart: Cart object

    Returns:
        Decimal: Shipping cost before discounts
    """
    if cart is None:
        return Decimal('0.00')

    if Cartshippingmethod.objects.filter(cart=cart).exists():
        cart_shipping_method = Cartshippingmethod.objects.get(cart=cart)
        return cart_shipping_method.shippingmethod.shipping_cost

    return Decimal('0.00')


def _calculate_item_discount(cart, item_subtotal):
    """
    Calculate item discount. Only ONE item discount applies (first valid one).

    Args:
        cart: Cart object
        item_subtotal: Decimal - item subtotal to check against order minimum

    Returns:
        Decimal: Item discount amount
    """
    if cart is None:
        return Decimal('0.00')

    # Convert item_subtotal to Decimal for precise calculations
    if not isinstance(item_subtotal, Decimal):
        item_subtotal = Decimal(str(item_subtotal))

    item_discount = Decimal('0.00')

    # Find the first valid item discount
    for cartdiscount in Cartdiscount.objects.filter(cart=cart):
        if cartdiscount.discountcode.discounttype.applies_to == 'item_total':
            # Check if order minimum is met
            if item_subtotal >= cartdiscount.discountcode.order_minimum:
                # Apply the discount
                if cartdiscount.discountcode.discounttype.action == 'percent-off':
                    item_discount = item_subtotal * \
                        (cartdiscount.discountcode.discount_amount / Decimal('100'))
                elif cartdiscount.discountcode.discounttype.action == 'dollar-amt-off':
                    item_discount = cartdiscount.discountcode.discount_amount

                # Only apply the first valid discount, then break
                break

    return item_discount


def _calculate_shipping_discount(cart, item_subtotal):
    """
    Calculate shipping discount. Only ONE shipping discount applies (first valid one).

    Args:
        cart: Cart object
        item_subtotal: Decimal - item subtotal to check against order minimum

    Returns:
        Decimal: Shipping discount amount
    """
    if cart is None:
        return Decimal('0.00')

    shipping_discount = Decimal('0.00')

    # Find the first valid shipping discount
    for cartdiscount in Cartdiscount.objects.filter(cart=cart):
        if cartdiscount.discountcode.discounttype.applies_to == 'shipping':
            # Check if order minimum is met
            if item_subtotal >= cartdiscount.discountcode.order_minimum:
                # Check if cart has a shipping method
                if Cartshippingmethod.objects.filter(cart=cart).exists():
                    cart_shipping_method = Cartshippingmethod.objects.get(cart=cart)
                    # Check if shipping method is USPS Retail Ground (only type currently supported)
                    if cart_shipping_method.shippingmethod.identifier == 'USPSRetailGround':
                        shipping_discount = cart_shipping_method.shippingmethod.shipping_cost

                # Only apply the first valid discount, then break
                break

    return shipping_discount
