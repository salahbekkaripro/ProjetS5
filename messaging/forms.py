from django import forms
from django.contrib.auth import get_user_model

from .models import Message

User = get_user_model()


class FriendRequestForm(forms.Form):
    identifier = forms.CharField(
        label="Email",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "email@domaine.com"}),
    )

    def clean_identifier(self):
        value = self.cleaned_data["identifier"].strip()
        if not value:
            raise forms.ValidationError("Merci d'indiquer un utilisateur.")
        user = User.objects.filter(email__iexact=value).first()
        if not user:
            raise forms.ValidationError("Utilisateur introuvable.")
        self.cleaned_data["user_obj"] = user
        return value


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control",
                    "placeholder": "Écrivez votre message...",
                }
            )
        }
        labels = {"body": ""}
