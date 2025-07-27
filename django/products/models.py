from django.db import models

# Create your models here.


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    brand = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=16)
    stock = models.IntegerField()
    ean = models.CharField(max_length=64)
    color = models.CharField(max_length=64)
    size = models.CharField(max_length=64)
    availability = models.CharField(max_length=32)
    internal_id = models.CharField(max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["name"]
        db_table = "product"
