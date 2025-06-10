from django import forms
from .models import Item, Bid, Feedback, CustomUser
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'description', 'minimum_price','end_time', 'image']
        widgets = {
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid_price']

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'email', 'message']

class UserCreationForm(BaseUserCreationForm):
    is_author = forms.BooleanField(required=False, initial=False, label="Register as a Seller?")
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'is_seller',  "password1", "password2"]
