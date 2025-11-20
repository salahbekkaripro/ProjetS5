from django.contrib import admin

from .models import Category, ListingMessage, ListingRating, MarketplaceListing, Product, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("name",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "email", "created_at", "paid")
    list_filter = ("paid", "created_at")
    inlines = [OrderItemInline]


@admin.register(MarketplaceListing)
class MarketplaceListingAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "price", "condition", "available", "created_at")
    list_filter = ("available", "condition")
    search_fields = ("title", "seller__email")


@admin.register(ListingMessage)
class ListingMessageAdmin(admin.ModelAdmin):
    list_display = ("listing", "sender", "created_at")
    search_fields = ("listing__title", "sender__email")


@admin.register(ListingRating)
class ListingRatingAdmin(admin.ModelAdmin):
    list_display = ("listing", "seller", "buyer", "score", "created_at")
    list_filter = ("score",)
