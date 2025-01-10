from django.contrib import admin
from .models import User, Item, Bid, Feedback

admin.site.register(User)
admin.site.register(Item)
admin.site.register(Bid)
admin.site.register(Feedback)
