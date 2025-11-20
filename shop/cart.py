from decimal import Decimal

from django.conf import settings

from .models import Product


class Cart:
    """Session-based cart."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product_id, quantity=1):
        product_id = str(product_id)
        self.cart[product_id] = self.cart.get(product_id, 0) + int(quantity)
        self.save()

    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            qty = self.cart[str(product.id)]
            yield {
                "product": product,
                "quantity": qty,
                "price": product.price,
                "subtotal": Decimal(product.price) * qty,
            }

    def __len__(self):
        return sum(self.cart.values())

    @property
    def total(self):
        return sum(item["subtotal"] for item in self)
