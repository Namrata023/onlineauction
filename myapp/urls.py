from django.urls import path
from  .views import *
from django.views.generic.base import RedirectView

urlpatterns = [
    path('simple_page_view/',simple_page_view, name='simple_page_view'),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('add_item/', add_item, name='add_item'),
    path('login_view/', login_view, name='login_view'),
    path('register/', register, name='register'),
    path('verify-registration-otp/', verify_registration_otp, name='verify_registration_otp'),
    path('logout_view/', logout_view, name='logout_view'),
    path('product/<int:id>/', product, name='product'),
    path('delete_item/<int:id>/', delete_item, name='delete_item'),
    path('edit_item/<int:id>/', edit_item, name='edit_item'),
    path('notify_outbid_user/<int:item_id>/', notify_outbid_user, name='notify_outbid_user'),
    path('notify_auction_winner/<int:item_id>/', notify_auction_winner, name='notify_auction_winner'),
    path('privacy_policy/', privacy_policy, name='privacy_policy'),
    path('terms_of_service/', terms_of_service, name='terms_of_service'),
    path('get-latest-bid/<int:id>/', get_latest_bid, name='get_latest_bid'),
    path('profile/', profile_view, name='profile'),
    path('edit_profile/', edit_profile, name='edit_profile'),
    path('initiate-payment/<int:item_id>/', initiate_payment, name='initiate_payment'),
    path('payment-callback/<int:item_id>/', payment_callback, name='payment_callback'),
    path('notifications/', notifications_view, name='notifications'),
    path('reset-password/', request_reset_otp_view, name='request_reset_otp'),
    path('verify-reset-otp/', verify_reset_otp_view, name='verify_reset_otp'),
    path('set-new-password/', set_new_password_view, name='set_new_password'),
    path('get-time-remaining/<int:item_id>/', get_time_remaining, name='get_time_remaining'),
    path('check-expired-auctions/', check_expired_auctions, name='check_expired_auctions'),
    path("chatbot/", chatbot_view, name="chatbot"),
    path('messages/', messages_list, name='messages_list'),
    path('messages/item/<int:item_id>/', item_messages, name='item_messages'),

]
