from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_history, name="order_history"),
    path("marketplace/", views.marketplace_list, name="marketplace_list"),
    path("marketplace/create/", views.marketplace_create, name="marketplace_create"),
    path("marketplace/<int:pk>/", views.marketplace_detail, name="marketplace_detail"),
    path("marketplace/<int:pk>/close/", views.close_listing, name="marketplace_close"),
]
