from django.contrib import admin
from .models import CustomUser, Item, Bid, Feedback,ItemImage, Payment, Notification, PasswordResetOTP

admin.site.register(CustomUser)
admin.site.register(Item)
admin.site.register(Bid)
admin.site.register(Feedback)
admin.site.register(ItemImage)
admin.site.register(Payment)
admin.site.register(Notification)
admin.site.register(PasswordResetOTP)
