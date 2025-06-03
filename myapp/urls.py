from django.urls import path
from  .views import *
from django.views.generic.base import RedirectView

urlpatterns = [
    path('simple_page_view/',simple_page_view, name='simple_page_view'),
    path('', home, name='home'),
   

]
