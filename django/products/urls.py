from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path(f"plain-text/?$", views.plain_text, name="plain_text"),
    re_path("json/?$", views.json_echo, name="json_echo"),
    re_path(
        "^products/?$",
        views.ProductListCreateView.as_view(),
        name="product_list_create",
    ),
    re_path(
        "^products/(?P<pk>\d+)/?$",
        views.ProductRetrieveUpdateDestroyView.as_view(),
        name="product_detail",
    ),
    re_path("fortune/?$", views.fortune_100, name="fortune_100"),
]
