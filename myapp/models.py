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
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    identification_number = models.IntegerField(validators=[MinValueValidator(1)], blank=True, null=True)
    identification_image = models.ImageField(upload_to='identification_images/', blank=True, null=True)
    is_seller = models.BooleanField(default=False)
   
    def __str__(self):
        return self.username
    
# class UserProfile(models.Model):
#     user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
#     bio = models.TextField(blank=True)

class Item(models.Model): 
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing & Fashion'),
        ('home_garden', 'Home & Garden'),
        ('collectibles', 'Collectibles & Art'),
        ('vehicles', 'Vehicles & Parts'),
        ('books', 'Books & Stationery'),
        ('sports', 'Sports & Outdoors'),
        ('toys', 'Toys & Games'),
        ('health_beauty', 'Health & Beauty'),
        ('jewelry', 'Jewelry & Accessories'),
        ('music_movies', 'Music & Movies'),
        ('pet_supplies', 'Pet Supplies'),
        ('tools_home_improvement', 'Tools & Home Improvement'),
        ('baby_products', 'Baby Products'),
        ('other', 'Other'),
    ]
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='electronics')
    description = models.CharField(max_length=10000)
    tags = models.CharField(max_length=255, blank=True, null=True)
    minimum_price = models.FloatField()
    # image = models.ImageField(upload_to="images/", blank=True, null=True)
    is_sold = models.BooleanField(default=False)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now() + timedelta(days=15))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def get_time_remaining(self):
        """Calculate time remaining until auction ends"""
        if not self.end_time:
            return None
        
        now = timezone.now()
        if now >= self.end_time:
            return "Auction ended"
        
        time_diff = self.end_time - now
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} d")
        if hours > 0:
            parts.append(f"{hours} h")
        if minutes > 0:
            parts.append(f"{minutes} m")
        if seconds > 0:
            parts.append(f"{seconds} s")
        
        if not parts:
            return "0 s"
        
        return " ".join(parts)
    
    def is_auction_expired(self):
        """Check if auction has expired"""
        if not self.end_time:
            return False
        return timezone.now() >= self.end_time

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
    NOTIFICATION_TYPES = [
        ('bid', 'Bid Related'),
        ('auction_won', 'Auction Won'),
        ('auction_lost', 'Auction Lost'),
        ('item_sold', 'Item Sold'),
        ('payment', 'Payment'),
        ('payment_received', 'Payment Received'),
        ('general', 'General'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    related_item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:30]}"

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)