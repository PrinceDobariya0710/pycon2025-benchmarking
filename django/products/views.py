from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404, render
from .models import Product
from .serializers import ProductSerializer

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# PlainText endpoint
@api_view(["GET"])
def plain_text(request):
    return Response("Hello, world!", content_type="text/plain")


# JSON Echo endpoint
@api_view(["GET"])
def json_echo(request):
    return Response({"message": "Hello, world from JSON serialization endpoint!"})


# Product CRUD endpoints
class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True  # Allow partial updates for PUT
        return super().update(request, *args, **kwargs)


# Fortune 100 HTML endpoint
@api_view(["GET"])
def fortune_100(request):
    products = Product.objects.all()[:100]
    return render(request, "fortune.html", {"products": products})
