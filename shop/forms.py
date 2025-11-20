from django import forms

from .models import ListingMessage, ListingRating, MarketplaceListing


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    address = forms.CharField(max_length=255)
    city = forms.CharField(max_length=120)


class MarketplaceListingForm(forms.ModelForm):
    class Meta:
        model = MarketplaceListing
        fields = ("title", "description", "price", "condition")


class ListingMessageForm(forms.ModelForm):
    class Meta:
        model = ListingMessage
        fields = ("content",)


class ListingRatingForm(forms.ModelForm):
    score = forms.IntegerField(min_value=1, max_value=5, initial=5, label="Note (1-5)")

    class Meta:
        model = ListingRating
        fields = ("score", "comment")
