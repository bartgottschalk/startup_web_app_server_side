import time

from foods.models import Food
from order.models import Sku, Skuprice, Foodsku, Skutype, Skuinventory
from django.utils import timezone

foods = Food.objects.all()
for food in foods:
    sku = Sku.objects.create(sku_type=Skutype.objects.get(title='food'), sku_inventory=Skuinventory.objects.get(identifier='in-stock'))
    now = timezone.now()
    skuprice = Skuprice.objects.create(sku=sku, price=0.50, created_date_time=now)
    foodsku = Foodsku.objects.create(food=food, sku=sku)
    print('created sku, skuprice and foodsku for food: ' + str(food))
