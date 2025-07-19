from django import forms
from .models import Item, Bid, Feedback, CustomUser, ItemImage, Comment
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms import modelformset_factory


class ItemForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing & Fashion'),
        ('home_garden', 'Home & Garden'),
        ('collectibles', 'Collectibles & Art'),
        ('vehicles', 'Vehicles & Parts'),
    ]
    
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the category that best describes your item"
    )
    
    class Meta:
        model = Item
        fields = ['name', 'category', 'tags', 'description', 'minimum_price','end_time']
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
        

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment here...',
                'maxlength': 500
            })
        }
        labels = {
            'content': 'Your Comment'
        }

class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'address',  'is_seller', 'phone_number', 'profile_picture', 'identification_number', 'identification_image', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].required = True
        self.fields['phone_number'].widget.attrs.update({
            'placeholder': 'e.g., 98..',
            'type': 'tel',
        })


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name','email', 'address', 'is_seller', 'phone_number', 'profile_picture', 'identification_number', 'identification_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].required = True
        self.fields['phone_number'].widget.attrs.update({
            'placeholder': 'e.g., 98..',
            'type': 'tel',
        })