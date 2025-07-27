from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "brand",
            "category",
            "price",
            "currency",
            "stock",
            "ean",
            "color",
            "size",
            "availability",
            "internal_id",
        ]
