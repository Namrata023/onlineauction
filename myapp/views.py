from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import *
from .forms import ItemForm, BidForm, FeedbackForm, UserCreationForm
from django.contrib.auth import authenticate, login,logout
from collections import namedtuple


def simple_page_view(request):
    return render(request, 'myapp/simple_page.html')

def home(request):

    # Items for testing purposes

    ItemMock = namedtuple('ItemMock', ['id', 'name', 'description', 'price'])

    # Create temporary fake items
    items = [
        ItemMock(id=1, name='Test Item 1', description='This is item 1.', price=9.99),
        ItemMock(id=2, name='Test Item 2', description='This is item 2.', price=19.99),
        ItemMock(id=3, name='Test Item 3', description='This is item 3.', price=29.99),
    ]

     
    return render(request, 'base.html', {'items': items})
    
def about(request):
    return render(request, 'myapp/about.html')

def contact(request):
    return render(request, 'myapp/contact.html')


@login_required
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            return render(request, 'item_success.html', {'item': item})
    else:
        form = ItemForm()
    
    return render(request, 'myapp/add_item.html')

def login_view(request):
    if request.method == 'POST':
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


def register(request):
    form = UserCreationForm()
    if request.method == "POST":
        form =UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.save()

            login(request, user)

            subject = "Welcome to Auction"
            message = "Thank you for registering! We are glad to have you."
            from_email = settings.EMAIL_HOST_USER
            to_email = [user.email]

            send_mail(subject, message, from_email, to_email)
            return redirect('login_view')
    
        # form = UserCreationForm()
    return render(request, 'register.html', {'form':form})

def logout_view(request):
    logout(request)
    return redirect('home')

def product(request,id):
    item = Item.objects.get(id=id)
    bids = item.bid_set.order_by('-bid_price')
    if request.method == 'POST' and request.user.is_authenticated:
        form = BidForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            highest_bid = bids.first()
            min_bid = item.minimum_price
            if highest_bid:
                min_bid = max(min_bid, highest_bid.bid_price)
            if bid.bid_price > min_bid:
                bid.item = item
                bid.bidder = request.user
                bid.save()
                return redirect('product', id=id)
            else:
                form.add_error('bid_price', 'Your bid must be higher than current highest bid and minimum price.')
    else:
        form = BidForm()
    return render(request, 'product.html', {'item': item, 'bids': bids, 'form': form})

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            return redirect('item_detail', item_id=item.id)  
    else:
        form = ItemForm()
    return render(request, 'add_product.html', {'form': form})

def submit_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'feedback_thanks.html')
    else:
        form = FeedbackForm()
    return render(request, 'feedback.html', {'form': form})