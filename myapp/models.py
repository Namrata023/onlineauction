from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_seller = models.BooleanField(default=False)
    def __str__(self):
        return self.username

class Item(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
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



