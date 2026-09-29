from django.db import models

# Create your models here.
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

POSITIVE = [MinValueValidator(Decimal("0.01"))]


class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=POSITIVE)
    width_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=POSITIVE)
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=POSITIVE)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3, validators=POSITIVE)

    def __str__(self):
        return self.name

    @property
    def dimensions(self):
        return (self.length_cm, self.width_cm, self.height_cm)

    @property
    def volume(self):
        return self.length_cm * self.width_cm * self.height_cm


class Box(models.Model):
    name = models.CharField(max_length=200, unique=True)
    inner_length_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=POSITIVE)
    inner_width_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=POSITIVE)
    inner_height_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=POSITIVE)
    max_weight_kg = models.DecimalField(max_digits=8, decimal_places=3, validators=POSITIVE)
    cost = models.DecimalField(max_digits=8, decimal_places=2, validators=POSITIVE)

    def __str__(self):
        return self.name

    @property
    def dimensions(self):
        return (self.inner_length_cm, self.inner_width_cm, self.inner_height_cm)

    @property
    def volume(self):
        return self.inner_length_cm * self.inner_width_cm * self.inner_height_cm


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.quantity} x {self.product}"