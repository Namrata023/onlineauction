from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import *
from .forms import ItemForm, BidForm, FeedbackForm, UserCreationForm, ItemImageFormSet
from django.contrib.auth import authenticate, login,logout
from collections import namedtuple
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .utils import get_similar_items, get_user_based_recommendations

def simple_page_view(request):
    return render(request, 'myapp/simple_page.html')

def home(request):
    query = request.GET.get('q') 
    if query:
        items = Item.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        ).distinct()
    else:
        items = Item.objects.all()
        query = ''

    no_results = query and not items.exists()

     
    return render(request, 'base.html', {'items': items,'query': query,'no_results': no_results,})
    
def about(request):
    faqs = [
        {
            'question': 'What is Online Auction?',
            'answer': 'Online Auction is a platform where users can list and bid on items in real-time.'
        },
        {
            'question': 'How do I place a bid?',
            'answer': 'You must be logged in. Then, go to the product page and enter your bid.'
        },
        {
            'question': 'Can I delete my own listings?',
            'answer': 'Yes, but only if you are the seller who listed the item.'
        },
        {
            'question': 'Is bidding free?',
            'answer': 'Yes, placing a bid is free. Only successful bids may involve payments.'
        },
    ]
    return render(request, 'myapp/about.html', {'faqs': faqs})

def contact(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save()

            # Send confirmation email to user
            subject = "Thank you for your feedback"
            message = (
                f"Hi {feedback.name},\n\n"
                "Thank you for your valuable feedback. We appreciate you taking the time to help us improve.\n\n"
                "Best regards,\nOnline Auction Team"
            )
            recipient_list = [feedback.email]
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

            messages.success(request, "feedback:Thank you for your feedback! A confirmation email has been sent.")
            return redirect('contact')
    else:
        form = FeedbackForm()
    return render(request, 'myapp/contact.html', {'form': form})


def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_of_service(request):
    return render(request, 'terms.html')



def add_item(request):
   
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()

            
        for img in request.FILES.getlist('images'):
            ItemImage.objects.create(item=item, image=img)

           
            subject = 'Item Added Successfully'
            message = f"Hi {request.user.username},\n\nYour item '{item.name}' has been added successfully to the auction platform."
            recipient_list = [request.user.email]
            
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            return redirect('home') 
    else:
        form = ItemForm()
       
    
    return render(request, 'add_item.html', {'form': form})

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
    
    # Check if auction has expired
    auction_expired = item.end_time and item.end_time < timezone.now()
    winner = None
    is_winner = False
    
    if auction_expired and bids.exists():
        winner = bids.first().bidder
        is_winner = request.user.is_authenticated and request.user == winner
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = BidForm(request.POST)
        if item.owner == request.user:
            
            form.add_error(None, "You cannot bid on your own item.")
        elif auction_expired:
            form.add_error(None, "Auction has ended. Bidding is closed.")
        elif form.is_valid():
            bid = form.save(commit=False)
            highest_bid = bids.first()
            min_bid = item.minimum_price

            if highest_bid:
                min_bid = max(min_bid, highest_bid.bid_price)

            if bid.bid_price > min_bid:
                bid.item = item
                bid.bidder = request.user
                bid.bid_time = timezone.now()
                bid.save()
                messages.success(request, 'Your bid has been placed!')
                return redirect('product', id=id)
            else:
                form.add_error('bid_price', f'Your bid must be higher than ${min_bid:.2f}.')
    else:
        form = BidForm()
    return render(request, 'product.html', {
        'item': item, 
        'bids': bids, 
        'form': form,
        'auction_expired': auction_expired,
        'winner': winner,
        'is_winner': is_winner,
        'now': timezone.now()
    })
@login_required
def edit_item(request, id):
    item = Item.objects.get(id=id, owner=request.user)

    if item.owner != request.user:
        return redirect('home')

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()

            images = request.FILES.getlist('images')
            if images:
                
                item.images.all().delete()

                # Create new image objects for uploaded files
                for image in images:
                    ItemImage.objects.create(item=item, image=image)
            subject = f"Your product '{item.name}' has been updated"
            message = f"Hello {request.user.username},\n\nYour product '{item.name}' has been successfully updated on Online auction.\n\nThank you for keeping your listings up to date!"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [request.user.email]

            send_mail(subject, message, from_email, recipient_list)
            return redirect('product', id=id)  # redirect to product detail page
    else:
        form = ItemForm(instance=item)

    return render(request, 'edit_item.html', {'form': form, 'item': item})


from django.shortcuts import get_object_or_404
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    all_items = Item.objects.exclude(id=item_id)

    content_based = get_similar_items(item, all_items)

    user_based = []
    if request.user.is_authenticated:
        user_based = get_user_based_recommendations(request.user)

    return render(request, 'item_detail.html', {
        'item': item,
        'content_based': content_based,
        'user_based': user_based
    })

login_required
def delete_item(request, id):
    item = Item.objects.get(id=id)
    if request.user != item.owner:
        return HttpResponseForbidden("You are not allowed to delete this item.")
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Item deleted successfully.")
        return redirect('home')

    return render(request, 'delete_item.html', {'item': item})

def notify_outbid_user(previous_highest_bid):
    user = previous_highest_bid.user
    subject = "You've been outbid!"
    message = f"Hello {user.username},\n\nYou have been outbid on '{previous_highest_bid.item.name}'. Visit the auction to place a higher bid!"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
def notify_auction_winner(item):
    winning_bid = item.bids.order_by('-amount').first()
    if winning_bid:
        subject = "You won the auction!"
        message = f"Congratulations {winning_bid.user.username}!\n\nYou won the auction for '{item.name}' with a bid of ${winning_bid.amount}."
        send_mail(subject, message, settings.EMAIL_HOST_USER, [winning_bid.user.email])


from django.http import JsonResponse
def get_latest_bid(request, id):
    latest_bid = Bid.objects.filter(item_id=id).order_by('-bid_price').first()
    if latest_bid:
        return JsonResponse({
            'amount': float(latest_bid.bid_price),
            'bidder': latest_bid.bidder.username
        })
    else:
        return JsonResponse({'amount': 'No bids yet', 'bidder': '-'})