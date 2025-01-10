from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

class Item(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    minimum_price = models.FloatField()
    image_path = models.ImageField(upload_to="images")

 
class Bid(models.Model):
    item_id = models.ForeignKey(Item, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    bid_price = models.FloatField()
    
class Feedback(models.Model):
    name = models.CharField(max_length=100)
    message = models.CharField(max_length=1000)
    email = models.CharField(max_length=100)

    
  



