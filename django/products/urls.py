from django.urls import path
from . import views

urlpatterns = [
    path("plain-text/", views.plain_text, name="plain_text"),
    path("json/", views.json_echo, name="json_echo"),
    path(
        "products/", views.ProductListCreateView.as_view(), name="product_list_create"
    ),
    path(
        "products/<int:pk>/",
        views.ProductRetrieveUpdateDestroyView.as_view(),
        name="product_detail",
    ),
    path("fortune/", views.fortune_100, name="fortune_100"),
]
