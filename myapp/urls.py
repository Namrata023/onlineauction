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
    path('logout_view/', logout_view, name='logout_view'),
    path('product/<int:id>/', product, name='product'),
    path('delete_item/<int:id>/', delete_item, name='delete_item'),
    path('edit_item/<int:id>/', edit_item, name='edit_item'),
    path('notify_outbid_user/<int:item_id>/', notify_outbid_user, name='notify_outbid_user'),
    path('notify_auction_winner/<int:item_id>/', notify_auction_winner, name='notify_auction_winner'),

]
