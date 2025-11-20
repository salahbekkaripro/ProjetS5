from decimal import Decimal
from django.db import models

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from subscriptions.decorators import requires_plan
from .cart import Cart
from .forms import CheckoutForm, ListingMessageForm, ListingRatingForm, MarketplaceListingForm
from .models import Category, ListingRating, MarketplaceListing, Order, OrderItem, Product


def _discount_rate(request):
    sub = getattr(request, "current_subscription", None)
    if not sub:
        return Decimal("0")
    code = sub.plan.code
    if code == "pro":
        return Decimal("0.10")
    if code == "ultra":
        return Decimal("0.25")
    return Decimal("0")


def product_list(request):
    category_slug = request.GET.get("category")
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)
    if category_slug:
        products = products.filter(category__slug=category_slug)
    return render(request, "shop/product_list.html", {"products": products, "categories": categories, "selected": category_slug})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return render(request, "shop/product_detail.html", {"product": product})


def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    cart = Cart(request)
    cart.add(product.id)
    messages.success(request, f"{product.name} ajouté au panier.")
    return redirect("shop:cart_detail")


def remove_from_cart(request, pk):
    cart = Cart(request)
    cart.remove(pk)
    messages.info(request, "Produit retiré.")
    return redirect("shop:cart_detail")


def cart_detail(request):
    cart = Cart(request)
    rate = _discount_rate(request)
    discounted_total = cart.total * (Decimal("1") - rate)
    discount_percent = int(rate * 100)
    return render(request, "shop/cart_detail.html", {"cart": cart, "discount_rate": rate, "discount_percent": discount_percent, "discounted_total": discounted_total})


@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, "Votre panier est vide.")
        return redirect("shop:product_list")
    rate = _discount_rate(request)
    discount_percent = int(rate * 100)
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data["full_name"],
                email=form.cleaned_data["email"],
                address=form.cleaned_data["address"],
                city=form.cleaned_data["city"],
                paid=True,
            )
            for item in cart:
                price_after = item["price"] * (Decimal("1") - rate)
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    quantity=item["quantity"],
                    price=price_after,
                )
            cart.clear()
            messages.success(request, "Commande créée. (Pas de paiement réel)")
            return redirect("shop:order_history")
    else:
        initial = {
            "full_name": request.user.full_name if hasattr(request.user, "full_name") else request.user.email,
            "email": request.user.email,
        }
        form = CheckoutForm(initial=initial)
    discounted_total = cart.total * (Decimal("1") - rate)
    return render(request, "shop/checkout.html", {"cart": cart, "form": form, "discount_rate": rate, "discount_percent": discount_percent, "discounted_total": discounted_total})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items__product")
    return render(request, "shop/order_history.html", {"orders": orders})


@requires_plan("ultra")
def marketplace_list(request):
    listings = (
        MarketplaceListing.objects.filter(available=True)
        .select_related("seller")
        .annotate(avg_score=models.Avg("ratings__score"))
    )
    return render(request, "shop/marketplace_list.html", {"listings": listings})


@requires_plan("ultra")
def marketplace_create(request):
    if request.method == "POST":
        form = MarketplaceListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.save()
            messages.success(request, "Annonce publiée.")
            return redirect("shop:marketplace_list")
    else:
        form = MarketplaceListingForm()
    return render(request, "shop/marketplace_form.html", {"form": form})


@requires_plan("ultra")
def marketplace_detail(request, pk):
    listing = get_object_or_404(MarketplaceListing.objects.select_related("seller"), pk=pk)
    msg_form = ListingMessageForm(request.POST if request.POST.get("form_type") == "message" else None)
    rating_form = ListingRatingForm(request.POST if request.POST.get("form_type") == "rating" else None)
    ratings = listing.ratings.select_related("buyer")
    existing_rating = ratings.filter(buyer=request.user).first()
    if request.method == "POST":
        if request.POST.get("form_type") == "message" and msg_form.is_valid():
            msg = msg_form.save(commit=False)
            msg.listing = listing
            msg.sender = request.user
            msg.save()
            messages.success(request, "Message envoyé au vendeur.")
            return redirect("shop:marketplace_detail", pk=pk)
        if request.POST.get("form_type") == "rating" and rating_form.is_valid():
            if listing.seller == request.user:
                messages.error(request, "Vous ne pouvez pas vous noter vous-même.")
            elif existing_rating:
                messages.error(request, "Vous avez déjà noté cette annonce.")
            else:
                rating = rating_form.save(commit=False)
                rating.listing = listing
                rating.seller = listing.seller
                rating.buyer = request.user
                rating.save()
                messages.success(request, "Avis enregistré.")
                return redirect("shop:marketplace_detail", pk=pk)
    messages_qs = listing.messages.select_related("sender")
    avg_score = ratings.aggregate(avg=models.Avg("score"))["avg"]
    return render(
        request,
        "shop/marketplace_detail.html",
        {"listing": listing, "messages": messages_qs, "form": msg_form, "rating_form": rating_form, "ratings": ratings, "avg_score": avg_score, "existing_rating": existing_rating},
    )


@requires_plan("ultra")
def close_listing(request, pk):
    listing = get_object_or_404(MarketplaceListing, pk=pk, seller=request.user)
    listing.available = False
    listing.save(update_fields=["available"])
    messages.info(request, "Annonce clôturée.")
    return redirect("shop:marketplace_detail", pk=pk)
