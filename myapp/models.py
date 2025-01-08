from django.db import models

class User(models.Model):
    id = models.IntegerField()
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

class Items(models.Model):
    user_id = models.ForeignKey(id, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    minimum_price = models.FloatField()
    image_path = models.ImageField(upload_to="/images")

