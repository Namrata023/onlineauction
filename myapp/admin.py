from django.contrib import admin
from .models import CustomUser, Item, Bid, Feedback,ItemImage

admin.site.register(CustomUser)
admin.site.register(Item)
admin.site.register(Bid)
admin.site.register(Feedback)
admin.site.register(ItemImage)
