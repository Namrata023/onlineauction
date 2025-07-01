from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator,RegexValidator


nepal_phone_regex = RegexValidator(
    regex=r'^(\+977)?9\d{9}$',
    message="Phone number must be a valid Nepal mobile number like '+97798XXXXXXXX' or '98XXXXXXXX'."
)

class CustomUser(AbstractUser):
    phone_number = models.CharField(
        validators=[nepal_phone_regex],
        max_length=13,
        blank=True,
        null=True,
        help_text="Enter a valid Nepal mobile number with or without +977."
    )
    profile_picture = models.ImageField(upload_to='media/profile_pictures/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    identification_number = models.IntegerField(validators=[MinValueValidator(1)], blank=True, null=True)
    identification_image = models.ImageField(upload_to='media/identification_images/', blank=True, null=True)
    is_seller = models.BooleanField(default=False)
   
    def __str__(self):
        return self.username
    
# class UserProfile(models.Model):
#     user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
#     bio = models.TextField(blank=True)

class Item(models.Model): 
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    tags = models.CharField(max_length=255, blank=True, null=True)
    minimum_price = models.FloatField()
    # image = models.ImageField(upload_to="images/", blank=True, null=True)
    is_sold = models.BooleanField(default=False)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now() + timedelta(days=15))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images/')
    
    def __str__(self):
        return f"Image for {self.item.name}"

 
class Bid(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bid_price = models.FloatField()
    bid_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bid by {self.bidder.username} on {self.item.name} for {self.bid_price}"
    
class Feedback(models.Model):
    name = models.CharField(max_length=100)
    message = models.CharField(max_length=1000)
    email = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Feedback from {self.name}"

    
class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.FloatField()
    payment_time = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=50)  

    def __str__(self):
        return f"Payment by {self.user.username} for {self.item.name} - {self.payment_status}"



class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:30]}"

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)