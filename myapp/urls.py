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
   

]
