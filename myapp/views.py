from django.shortcuts import render

def simple_page_view(request):
    return render(request, 'myapp/simple_page.html')

def home(request):
   return render(request,'home.html')

