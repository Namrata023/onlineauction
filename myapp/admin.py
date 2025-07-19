from django.contrib import admin
from .models import CustomUser, Item, Bid, Feedback,ItemImage, Payment, Notification, PasswordResetOTP, Comment

admin.site.register(CustomUser)
admin.site.register(Item)
admin.site.register(Bid)
admin.site.register(Feedback)
admin.site.register(ItemImage)
admin.site.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'item', 'amount', 'payment_status', 'created_at']
admin.site.register(Notification)
admin.site.register(PasswordResetOTP)
admin.site.register(Comment)
