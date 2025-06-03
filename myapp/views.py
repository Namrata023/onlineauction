from django.shortcuts import render


def simple_page_view(request):
    return render(request, 'myapp/simple_page.html')

def home(request):
   
    items = [1, 2, 3, 4, 5]

    return render(request,'home.html', {'items': items})
    
    