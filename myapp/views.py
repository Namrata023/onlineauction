from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import *
from .forms import ItemForm, BidForm, FeedbackForm, UserCreationForm, UserProfileForm, ItemImageFormSet, CommentForm
from django.contrib.auth import authenticate, login,logout, get_user_model
from collections import namedtuple
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .utils import get_similar_items, get_user_based_recommendations, get_popular_items, get_homepage_recommendations_for_user, get_recently_added_items
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import random
import requests
import json
import logging
from .simple_bot import get_bot_response

User = get_user_model()
logger = logging.getLogger(__name__)


def simple_page_view(request):
    return render(request, 'myapp/simple_page.html')

def home(request):
    query = request.GET.get('q') 
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    category = request.GET.get('category')
    
    # Start with all items
    items = Item.objects.all()
    
    # Apply search query filter
    if query:
        items = items.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Apply price range filters
    if min_price:
        try:
            min_price_val = float(min_price)
            items = items.filter(minimum_price__gte=min_price_val)
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price_val = float(max_price)
            items = items.filter(minimum_price__lte=max_price_val)
        except ValueError:
            pass
    
    # Apply category filter
    if category and category != 'all':
        items = items.filter(category=category)
    
    items = items.distinct().order_by('-created_at')  # Order by creation date, newest first
    query = query or ''
    paginator = Paginator(items, 12)  # Show 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get recommendations for homepage
    popular_items = get_popular_items(6)
    recommended_items = get_homepage_recommendations_for_user(request.user, 6)
    recent_items = get_recently_added_items(6)

    no_results = query and not items.exists()
    
    # Get category choices for the filter dropdown
    from .models import Item as ItemModel
    category_choices = ItemModel.CATEGORY_CHOICES
    
    return render(request, 'base.html', {
        'items': page_obj,
        'query': query,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'category': category or '',
        'category_choices': category_choices,
        'no_results': no_results,
        'popular_items': popular_items,
        'recommended_items': recommended_items,
        'recent_items': recent_items,
    })
    
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
            send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)

            messages.success(request, "feedback:Thank you for your feedback! A confirmation email has been sent.")
            return redirect('contact')
    else:
        form = FeedbackForm()
    return render(request, 'myapp/contact.html', {'form': form})


def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_of_service(request):
    return render(request, 'terms.html')


@login_required(login_url='login_view')
def add_item(request):
    if not request.user.is_seller:
        messages.error(request, "You must be a seller to add items.")
        return redirect('edit_profile')
    
      
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()

            # Process uploaded images
            for img in request.FILES.getlist('images'):
                ItemImage.objects.create(item=item, image=img)
            
            # Notify all other users about new item (limit to prevent spam)
            users_to_notify = CustomUser.objects.exclude(id=request.user.id)[:50]  # Limit to 50 users
            notification_count = 0
            email_count = 0
            
            for user in users_to_notify:
                try:
                    # In-app notification
                    create_notification(
                        user=user,
                        message=f"New item '{item.name}' listed by {request.user.username}. Check it out!",
                        notification_type='general',
                        priority='low'
                    )
                    notification_count += 1
                    
                    # Email notification (only if user has valid email)
                    if user.email and '@' in user.email:
                        subject = "New Item Listed for Auction Check it Out!"
                        message = (
                            f"Hello {user.username},\n\n"
                            f"A new item '{item.name}' has just been listed for auction.\n"
                            "Visit the site to place your bid now!"
                        )
                        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
                        email_count += 1
                except Exception as e:
                    logger.warning(f"Failed to notify user {user.username}: {e}")
                    continue
            
            logger.info(f"Item '{item.name}' created: {notification_count} notifications, {email_count} emails sent")
           
            # Send confirmation email to the seller
            try:
                if request.user.email:
                    subject = 'Item Added Successfully'
                    message = f"Hi {request.user.username},\n\nYour item '{item.name}' has been added successfully to the auction platform."
                    send_mail(subject, message, settings.EMAIL_HOST_USER, [request.user.email])
            except Exception as e:
                logger.warning(f"Failed to send confirmation email to seller {request.user.username}: {e}")
                # Don't show error to user as item was created successfully
            
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
        form = UserCreationForm(request.POST, request.FILES)
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
    try:
        item = Item.objects.get(id=id)
    except Item.DoesNotExist:
        raise Http404("Item does not exist")
    
    bids = item.bid_set.order_by('-bid_price')
    comments = item.comments.all()
    
    auction_expired = item.end_time and item.end_time < timezone.now()
    winner = None
    is_winner = False
    payment = None
    
    if auction_expired and bids.exists():
        winner = bids.first().bidder
        is_winner = request.user.is_authenticated and request.user == winner
        
        # Check for existing payment
        if is_winner:
            payment = Payment.objects.filter(item=item, user=request.user, payment_status="Completed").first()
    
    if request.method == 'POST':
        # Handle bid form
        if 'bid_price' in request.POST and request.user.is_authenticated:
            form = BidForm(request.POST)
            comment_form = CommentForm()
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
                    try:
                        bid.item = item
                        bid.bidder = request.user
                        bid.bid_time = timezone.now()
                        bid.save()
                        
                        # Notify item owner about new bid
                        try:
                            create_notification(
                                user=item.owner,
                                message=f"New bid of Rs.{bid.bid_price} placed on your item '{item.name}' by {request.user.username}.",
                                notification_type='bid',
                                priority='medium',
                                related_item=item
                            )
                        except Exception as e:
                            logger.warning(f"Failed to notify item owner about bid: {e}")
                        
                        # Notify previous highest bidder about being outbid
                        if highest_bid and highest_bid.bidder != request.user:
                            try:
                                create_notification(
                                    user=highest_bid.bidder,
                                    message=f"You have been outbid on '{item.name}'. The new highest bid is Rs.{bid.bid_price}. Place a higher bid now!",
                                    notification_type='bid',
                                    priority='high',
                                    related_item=item
                                )
                            except Exception as e:
                                logger.warning(f"Failed to notify previous bidder: {e}")
                        
                        messages.success(request, f"Your bid of Rs.{bid.bid_price} has been placed successfully!")
                        return redirect('product', id=id)
                        
                    except Exception as e:
                        logger.error(f"Failed to save bid for item {item.id}: {e}")
                        form.add_error(None, "Failed to place bid. Please try again.")
                else:
                    form.add_error('bid_price', f'Your bid must be higher than Rs.{min_bid:.2f}.')
        
        # Handle comment form
        elif 'content' in request.POST and request.user.is_authenticated:
            comment_form = CommentForm(request.POST)
            form = BidForm()
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.item = item
                comment.user = request.user
                comment.save()
                messages.success(request, "Your comment has been added!")
                return redirect('product', id=id)
        else:
            form = BidForm()
            comment_form = CommentForm()
    else:
        form = BidForm()
        comment_form = CommentForm()
        
    return render(request, 'product.html', {
        'item': item, 
        'bids': bids, 
        'form': form,
        'comment_form': comment_form,
        'comments': comments,
        'auction_expired': auction_expired,
        'winner': winner,
        'is_winner': is_winner,
        'payment': payment,
        'now': timezone.now(),
        'time_remaining': item.get_time_remaining(),
    })
@login_required
def edit_item(request, id):
    try:
        item = Item.objects.get(id=id)
    except Item.DoesNotExist:
        raise Http404("Item does not exist")

    if item.owner != request.user:
        return HttpResponseForbidden("You don't have permission to edit this item.")
    
    if item.bid_set.exists():
        messages.error(request, "You cannot edit this item because bidding has already started.")
        return redirect('product', id=id)

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
            return redirect('product', id=id)  
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

@login_required
def delete_item(request, id):
    item = Item.objects.get(id=id)
    if request.user != item.owner:
        return HttpResponseForbidden("You are not allowed to delete this item.")
    if item.bid_set.exists():
        messages.error(request, "You cannot edit this item because bidding has already started.")
        return redirect('product', id=id)
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Item deleted successfully.")
        return redirect('home')

    return render(request, 'delete_item.html', {'item': item})

def notify_outbid_user(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    bids = Bid.objects.filter(item=item).order_by('-bid_price')
    if bids.count() < 2:
        return HttpResponse("No previous bidder to notify.")

    previous_highest_bid=bids[1]
    user = previous_highest_bid.bidder

    create_notification(
        user=user,
        message=f"You have been outbid on '{item.name}'. Place a higher bid now!",
        notification_type='bid',
        priority='high',
        related_item=item
    )
    subject = "You've been outbid!"
    message = f"Hello {user.username},\n\nYou have been outbid on '{previous_highest_bid.item.name}'. Visit the auction to place a higher bid!"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
    
    return HttpResponse(f"Notification sent to {user.username}.")

def notify_auction_winner(item):
    item= get_object_or_404(Item, id=item.id)
    winning_bid = Bid.objects.filter(item=item).order_by('-bid_price').first()
    if not winning_bid:
        return HttpResponse("No winning bid found.")
    
    user = winning_bid.bidder
    
    create_notification(
        user=user,
        message=f"Congratulations! You won the auction for '{item.name}' with a bid of Rs.{winning_bid.bid_price}.",
        notification_type='auction_won',
        priority='high',
        related_item=item
    )
    subject = "You won the auction!"
    message = f"Congratulations {winning_bid.user.username}!\n\nYou won the auction for '{item.name}' with a bid of ${winning_bid.amount}."
    send_mail(subject, message, settings.EMAIL_HOST_USER, [winning_bid.user.email])
    return HttpResponse(f"Winner notification sent to {user.username}.")

def get_latest_bid(request, id):
    latest_bid = Bid.objects.filter(item_id=id).order_by('-bid_price').first()
    if latest_bid:
        return JsonResponse({
            'amount': float(latest_bid.bid_price),
            'bidder': latest_bid.bidder.username
        })
    else:        return JsonResponse({'amount': 'No bids yet', 'bidder': '-'})

# Khalti Payment Views

@login_required
def initiate_payment(request, item_id):
    """Initiate payment with Khalti"""
    item = get_object_or_404(Item, id=item_id)
    bids = item.bid_set.order_by('-bid_price')
    
    # Check if user is the winner
    if not (bids.exists() and bids.first().bidder == request.user):
        messages.error(request, "You are not authorized to make payment for this item.")
        return redirect('product', id=item_id)
    
    # Check if auction has expired
    if not (item.end_time and item.end_time < timezone.now()):
        messages.error(request, "Auction is still active. Payment not available yet.")
        return redirect('product', id=item_id)
    
    # Check if payment already completed
    existing_payment = Payment.objects.filter(item=item, user=request.user, payment_status="Completed").first()
    if existing_payment:
        messages.info(request, "Payment already completed for this item.")
        return redirect('product', id=item_id)
    
    winning_bid = bids.first()
    amount_in_paisa = int(winning_bid.bid_price * 100)  # Convert to paisa
    
    payload = {
        "return_url": request.build_absolute_uri(f"/payment-callback/{item_id}/"),
        "website_url": request.build_absolute_uri("/"),
        "amount": amount_in_paisa,
        "purchase_order_id": f"auction_{item_id}_{request.user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}",
        "purchase_order_name": item.name,
        "customer_info": {
            "name": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
            "phone": getattr(request.user, 'phone_number', '9800000000')
        },
        "product_details": [
            {
                "identity": str(item_id),
                "name": item.name,
                "total_price": amount_in_paisa,
                "quantity": 1,
                "unit_price": amount_in_paisa
            }
        ]
    }
    
    headers = {
        'Authorization': settings.KHALTI_SECRET_KEY,
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.post(
            f"{settings.KHALTI_BASE_URL}epayment/initiate/",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Store payment info
            Payment.objects.create(
                user=request.user,
                item=item,
                amount=winning_bid.bid_price,
                payment_status="Initiated"
            )
            return redirect(data['payment_url'])
        else:
            logger.error(f"Payment API returned status {response.status_code}: {response.text}")
            messages.error(request, "Payment initiation failed. Please try again.")
            return redirect('product', id=item_id)
            
    except requests.exceptions.Timeout:
        logger.error(f"Payment API timeout for item {item_id}")
        messages.error(request, "Payment service is taking too long. Please try again.")
        return redirect('product', id=item_id)
    except requests.exceptions.ConnectionError:
        logger.error(f"Payment API connection error for item {item_id}")
        messages.error(request, "Cannot connect to payment service. Please try again later.")
        return redirect('product', id=item_id)
    except requests.exceptions.RequestException as e:
        logger.error(f"Payment API request failed for item {item_id}: {e}")
        messages.error(request, "Payment service temporarily unavailable.")
        return redirect('product', id=item_id)
    except ValueError as e:
        logger.error(f"Invalid payment response data for item {item_id}: {e}")
        messages.error(request, "Payment configuration error. Please contact support.")
        return redirect('product', id=item_id)
    except Exception as e:
        logger.error(f"Unexpected payment error for item {item_id}: {e}")
        messages.error(request, "Payment processing failed. Please try again.")
        return redirect('product', id=item_id)

def payment_callback(request, item_id):
    """Handle payment callback from Khalti"""
    item = get_object_or_404(Item, id=item_id)
    pidx = request.GET.get('pidx')
    status = request.GET.get('status')
    transaction_id = request.GET.get('transaction_id')
    
    if status == 'Completed' and pidx:
        # Verify payment with Khalti
        headers = {
            'Authorization': settings.KHALTI_SECRET_KEY,
            'Content-Type': 'application/json',
        }
        
        try:
            response = requests.post(
                f"{settings.KHALTI_BASE_URL}epayment/lookup/",
                json={"pidx": pidx},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'Completed':
                    # Update payment status
                    payment = Payment.objects.filter(item=item, user=request.user).last()
                    if payment:
                        payment.payment_status = "Completed"
                        payment.save()
                    else:
                        # Create payment record if not exists
                        Payment.objects.create(
                            user=request.user,
                            item=item,
                            amount=float(request.GET.get('amount', 0)) / 100,  # Convert from paisa
                            payment_status="Completed"
                        )
                    
                    # Mark item as sold
                    item.is_sold = True
                    item.save()
                    
                    # Notify owner that buyer has paid ✅
                    buyer_full_name = request.user.get_full_name() or request.user.username
                    buyer_address = getattr(request.user, 'address', 'Not provided')
                    buyer_phone = getattr(request.user, 'phone_number', 'Not provided')
                    buyer_email = request.user.email or 'Not provided'
                    
                    create_notification(
                        user=item.owner,
                        message=f"Payment for your item '{item.name}' has been successfully completed by {buyer_full_name}. "
                                f"Please contact the buyer to arrange delivery using the following details: Name: {buyer_full_name}, "
                                f"Email: {buyer_email}, Phone: {buyer_phone}, Address: {buyer_address}.",
                        notification_type='payment_received',
                        priority='high',
                        related_item=item
                    )
                    
                    # Email the seller
                    send_mail(
                        subject="Payment Received for Your Auction Item",
                        message=f"Dear {item.owner.username},\n\n"
                                f"Payment for your auction item '{item.name}' has been successfully completed by {buyer_full_name}. "
                                f"Please contact the buyer to arrange delivery using the following contact details: Name: {buyer_full_name}, "
                                f"Email: {buyer_email}, Phone: {buyer_phone}, Address: {buyer_address}.\n\n"
                                f"Best regards,\nOnlineAuction Team",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[item.owner.email],
                        fail_silently=True
                    )
                    
                    messages.success(request, "Payment successful! You have successfully purchased this item.")
                    return redirect('product', id=item_id)
        except:
            pass
    
    messages.error(request, "Payment failed or was cancelled.")
    return redirect('product', id=item_id)

@login_required(login_url='login_view')
def profile_view(request):
    profile=request.user
    
    # Get all bids by the user
    all_bids = Bid.objects.filter(bidder=profile).select_related('item').order_by('-bid_time')
    
    # Get user's listings
    user_listings = Item.objects.filter(owner=profile).order_by('-created_at')
    active_listings = user_listings.filter(is_sold=False)
    sold_listings = user_listings.filter(is_sold=True)
    
    # Categorize bids
    won_items = []
    active_bids = []
    lost_bids = []
    
    for bid in all_bids:
        item = bid.item
        highest_bid = Bid.objects.filter(item=item).order_by('-bid_price').first()
        
        if item.is_auction_expired() or item.is_sold:
            # Auction ended
            if highest_bid and highest_bid.bidder == profile:
                won_items.append(bid)
            else:
                lost_bids.append(bid)
        else:
            # Auction still active
            active_bids.append(bid)
    
    context = {
        'user': request.user, 
        'profile': profile, 
        'bids': all_bids,
        'won_items': won_items,
        'active_bids': active_bids,
        'lost_bids': lost_bids,
        'active_listings': active_listings,
        'sold_listings': sold_listings,
    }
    
    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'edit_profile.html', {'form': form, 'user': request.user})


@login_required(login_url='login_view')
@login_required(login_url='login_view')
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all notifications as read when viewing the page
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    return render(request, 'notifications.html', {'notifications': notifications})

def request_reset_otp_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            
            # Delete any existing OTP for this user
            PasswordResetOTP.objects.filter(user=user).delete()
            
            # Create new OTP record in database
            PasswordResetOTP.objects.create(user=user, otp=otp)
            request.session['reset_user'] = user.username

            send_mail(
                "Your Password Reset OTP",
                f"Hi {user.username}, your OTP to reset your password is: {otp}",
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            return redirect('verify_reset_otp')
        except User.DoesNotExist:
            messages.error(request, "No user with that email.")
    return render(request, 'reset_password.html', {'mode': 'request'})
def verify_reset_otp_view(request):
    username = request.session.get('reset_user')
    if not username:
        messages.warning(request, "Session expired. Please try again.")
        return redirect('request_reset_otp')

    try:
        otp_obj = PasswordResetOTP.objects.get(user__username=username)
    except PasswordResetOTP.DoesNotExist:
        messages.error(request, "No OTP request found. Please request again.")
        return redirect('request_reset_otp')

    # Check if OTP expired
    if otp_obj.is_expired():
        otp_obj.delete()
        messages.error(request, "OTP has expired. Please request a new one.")
        return redirect('request_reset_otp')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if entered_otp == otp_obj.otp:
            request.session['otp_verified_user'] = username
            otp_obj.delete()  
            return redirect('set_new_password')
        else:
            messages.error(request, "Invalid OTP.")

    return render(request, 'reset_password.html', {'mode': 'otp_verify'})

from django.contrib.auth.hashers import make_password

def set_new_password_view(request):
    username = request.session.get('otp_verified_user')
    if not username:
        return redirect('request_reset_otp')

    user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        new_pass = request.POST.get('new_password')
        confirm_pass = request.POST.get('confirm_password')
        if new_pass == confirm_pass:
            user.password = make_password(new_pass)
            user.save()
            request.session.flush()
            messages.success(request, "Password reset successful.")
            return redirect('login_view')
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, 'reset_password.html', {'mode': 'set_password'})

def get_time_remaining(request, item_id):
    """AJAX endpoint to get time remaining for an item"""
    try:
        item = Item.objects.get(id=item_id)
        time_remaining = item.get_time_remaining()
        is_expired = item.is_auction_expired()
        
        return JsonResponse({
            'time_remaining': time_remaining,
            'is_expired': is_expired,
            'end_time_timestamp': item.end_time.timestamp() if item.end_time else None
        })
    except Item.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)

@csrf_exempt
def chatbot_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_input = data.get("message", "").strip()
            
            if not user_input:
                return JsonResponse({"error": "Message cannot be empty"}, status=400)
            
            reply = get_bot_response(user_input)
            return JsonResponse({"reply": reply})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            return JsonResponse({"error": "Sorry, something went wrong. Please try again."}, status=500)
    
    # Return error for non-POST requests
    return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

# Notification utility functions
def create_notification(user, message, notification_type='general', priority='medium', related_item=None):
    """Utility function to create notifications with proper typing"""
    return Notification.objects.create(
        user=user,
        message=message,
        notification_type=notification_type,
        priority=priority,
        related_item=related_item
    )

def notify_auction_completion(item):
    """Handle all notifications when an auction completes"""
    winning_bid = Bid.objects.filter(item=item).order_by('-bid_price').first()
    
    if winning_bid:
        # Mark item as sold
        item.is_sold = True
        item.save()
        
        # Notify winner
        create_notification(
            user=winning_bid.bidder,
            message=f"🎉 Congratulations! You won the auction for '{item.name}' with a bid of Rs.{winning_bid.bid_price}. Please proceed with payment.",
            notification_type='auction_won',
            priority='high',
            related_item=item
        )
        
        # Send winner email
        try:
            subject = "🎉 Congratulations! You Won the Auction!"
            message = f"""
Dear {winning_bid.bidder.username},

Congratulations! You have successfully won the auction for "{item.name}".

Auction Details:
- Item: {item.name}
- Your Winning Bid: Rs.{winning_bid.bid_price}
- Seller: {item.owner.username}

Please log in to complete your purchase.

Best regards,
OnlineAuction Team
            """
            send_mail(subject, message, settings.EMAIL_HOST_USER, [winning_bid.bidder.email], fail_silently=True)
        except:
            pass
        
        # Notify seller
        create_notification(
            user=item.owner,
            message=f"💰 Great news! Your item '{item.name}' has been sold to {winning_bid.bidder.username} for Rs.{winning_bid.bidder.bid_price}.",
            notification_type='item_sold',
            priority='high',
            related_item=item
        )
        
        # Send seller email
        try:
            subject = "💰 Your Item Has Been Sold!"
            message = f"""
Dear {item.owner.username},

Your auction has completed successfully!

Sale Details:
- Item: {item.name}
- Winning Bid: Rs.{winning_bid.bid_price}
- Winner: {winning_bid.bidder.username}

The buyer will contact you for payment and delivery.

Best regards,
OnlineAuction Team
            """
            send_mail(subject, message, settings.EMAIL_HOST_USER, [item.owner.email], fail_silently=True)
        except:
            pass
        
        # Notify losing bidders
        losing_bidders = Bid.objects.filter(item=item).exclude(id=winning_bid.id).values_list('bidder', flat=True).distinct()
        for bidder_id in losing_bidders:
            try:
                bidder = winning_bid.bidder.__class__.objects.get(id=bidder_id)
                create_notification(
                    user=bidder,
                    message=f"⏰ The auction for '{item.name}' has ended. Better luck next time!",
                    notification_type='auction_lost',
                    priority='medium',
                    related_item=item
                )
            except:
                continue
                
    else:
        # No bids received
        create_notification(
            user=item.owner,
            message=f"⏰ Your auction for '{item.name}' has ended without any bids. Consider relisting with adjustments.",
            notification_type='general',
            priority='medium',
            related_item=item
        )

def check_and_complete_expired_auctions():
    """Check for expired auctions and complete them"""
    expired_items = Item.objects.filter(
        end_time__lt=timezone.now(),
        is_sold=False
    )
    
    for item in expired_items:
        notify_auction_completion(item)
    
    return expired_items.count()

@login_required
def check_expired_auctions(request):
    """Manual trigger for checking expired auctions (admin only)"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin only.")
        return redirect('home')
    
    count = check_and_complete_expired_auctions()
    if count > 0:
        messages.success(request, f"Successfully processed {count} expired auctions.")
    else:
        messages.info(request, "No expired auctions to process.")
    
    return redirect('home')

