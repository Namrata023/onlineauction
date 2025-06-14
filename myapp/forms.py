from django import forms
from .models import Item, Bid, Feedback, CustomUser, ItemImage
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms import modelformset_factory


class ItemForm(forms.ModelForm):
    
    class Meta:
        model = Item
        fields = ['name', 'description', 'minimum_price','end_time']
        widgets = {
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
ItemImageFormSet = modelformset_factory(
    ItemImage,
    fields=('image',),
    extra=3, 
    widgets={'image': forms.ClearableFileInput(attrs={'class': 'form-control'})}
)

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid_price']

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'email', 'message']
        

class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'is_seller', 'phone_number', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].required = True
        self.fields['phone_number'].widget.attrs.update({
            'placeholder': 'e.g., +1234567890',
            'type': 'tel',
        })