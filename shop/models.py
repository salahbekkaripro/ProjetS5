from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Commande #{self.id}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="order_items", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity


LISTING_CONDITIONS = [
    ("new", "Neuf"),
    ("good", "Bon état"),
    ("used", "Usagé"),
]


class MarketplaceListing(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="listings", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    condition = models.CharField(max_length=20, choices=LISTING_CONDITIONS, default="good")
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ListingMessage(models.Model):
    listing = models.ForeignKey(MarketplaceListing, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="listing_messages", on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender.email}: {self.content[:20]}"


class ListingRating(models.Model):
    listing = models.ForeignKey(MarketplaceListing, related_name="ratings", on_delete=models.CASCADE)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="seller_ratings", on_delete=models.CASCADE)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="buyer_ratings", on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("listing", "buyer")

    def __str__(self):
        return f"{self.score}/5 by {self.buyer.email}"
