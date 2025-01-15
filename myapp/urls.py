from django.urls import path
from . import views
from django.views.generic.base import RedirectView

urlpatterns = [
    path('simple-page/', views.simple_page_view, name='simple_page'),
    path('home/', views.home, name='home'),
    path('', RedirectView.as_view(url='home/', permanent=True)),
]
