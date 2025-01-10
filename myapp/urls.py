from django.urls import path
from . import views

urlpatterns = [
    path('simple-page/', views.simple_page_view, name='simple_page'),
    path('home/', views.home, name='home')
]
