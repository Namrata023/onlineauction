#!/usr/bin/env python
import os
import sys
import django
import requests
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlineauction.settings')
django.setup()

from django.contrib.auth import get_user_model
from myapp.models import Item, Bid, ItemImage
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def download_sample_image(url, filename):
    """Download a sample image from URL and save to media/images/"""
    try:
        print(f"Downloading image from {url}...")
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Create media/images directory if it doesn't exist
            images_dir = os.path.join('media', 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # Save the image
            image_path = os.path.join(images_dir, filename)
            with open(image_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Downloaded: {filename}")
            return image_path
        else:
            print(f"❌ Failed to download image: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error downloading image: {str(e)}")
    return None

def add_sample_data():
    print("Adding sample data for testing recommendations...")
    
    # Create some sample users if they don't exist
    users_data = [
        {'username': 'alice', 'email': 'alice@test.com'},
        {'username': 'bob', 'email': 'bob@test.com'},
        {'username': 'charlie', 'email': 'charlie@test.com'},
    ]
    
    users = {}
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'password': 'password123'
            }
        )
        users[user_data['username']] = user
        if created:
            print(f"Created user: {user.username}")
    
    # Create sample items if they don't exist
    items_data = [
        {
            'name': 'Vintage Camera',
            'category': 'electronics',
            'description': 'Classic film camera in excellent condition',
            'tags': 'vintage,camera,photography,film',
            'minimum_price': 150.00,
            'image_url': 'https://images.unsplash.com/photo-1606983340126-99ab4feaa64a?w=600&h=400&fit=crop'
        },
        {
            'name': 'Gaming Laptop',
            'category': 'electronics',
            'description': 'High-performance gaming laptop with RTX graphics',
            'tags': 'laptop,gaming,computer,electronics',
            'minimum_price': 800.00,
            'image_url': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600&h=400&fit=crop'
        },
        {
            'name': 'Antique Furniture Set',
            'category': 'home_garden',
            'description': 'Beautiful antique dining table and chairs',
            'tags': 'antique,furniture,dining,wood',
            'minimum_price': 500.00,
            'image_url': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=600&h=400&fit=crop'
        },
        {
            'name': 'Art Painting',
            'category': 'collectibles',
            'description': 'Original oil painting by local artist',
            'tags': 'art,painting,original,decor',
            'minimum_price': 200.00,
            'image_url': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=600&h=400&fit=crop'
        },
        {
            'name': 'Mountain Bike',
            'category': 'sports',
            'description': 'Professional mountain bike, barely used',
            'tags': 'bike,mountain,sports,outdoor',
            'minimum_price': 300.00,
            'image_url': 'https://images.unsplash.com/photo-1571068316344-75bc76f77890?w=600&h=400&fit=crop'
        },
        {
            'name': 'Designer Watch',
            'category': 'jewelry',
            'description': 'Luxury designer watch with certificate',
            'tags': 'watch,luxury,designer,accessories',
            'minimum_price': 1200.00,
            'image_url': 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=600&h=400&fit=crop'
        }
    ]
    
    items = {}
    for item_data in items_data:
        item, created = Item.objects.get_or_create(
            name=item_data['name'],
            defaults={
                'owner': users['alice'],  # Alice owns all items
                'category': item_data['category'],
                'description': item_data['description'],
                'tags': item_data['tags'],
                'minimum_price': item_data['minimum_price'],
                'end_time': timezone.now() + timedelta(days=7)
            }
        )
        
        # Download and add image if item was created and doesn't have images
        if created or not item.images.exists():
            image_filename = f"{item.name.lower().replace(' ', '_')}.jpg"
            image_path = download_sample_image(item_data['image_url'], image_filename)
            
            if image_path:
                # Create ItemImage object
                with open(image_path, 'rb') as f:
                    item_image = ItemImage.objects.create(item=item)
                    item_image.image.save(image_filename, File(f), save=True)
                print(f"✅ Added image to {item.name}")
            else:
                print(f"⚠️ Could not add image to {item.name}")
        
        items[item_data['name']] = item
        if created:
            print(f"Created item: {item.name}")
    
    # Create some sample bids to make recommendations work
    bids_data = [
        {'bidder': 'bob', 'item': 'Vintage Camera', 'price': 160.00},
        {'bidder': 'bob', 'item': 'Gaming Laptop', 'price': 850.00},
        {'bidder': 'charlie', 'item': 'Vintage Camera', 'price': 170.00},
        {'bidder': 'charlie', 'item': 'Art Painting', 'price': 220.00},
        {'bidder': 'bob', 'item': 'Mountain Bike', 'price': 320.00},
        {'bidder': 'charlie', 'item': 'Designer Watch', 'price': 1250.00},
    ]
    
    for bid_data in bids_data:
        bidder = users[bid_data['bidder']]
        item = items[bid_data['item']]
        
        # Check if bid already exists
        existing_bid = Bid.objects.filter(bidder=bidder, item=item).first()
        if not existing_bid:
            bid = Bid.objects.create(
                bidder=bidder,
                item=item,
                bid_price=bid_data['price']
            )
            print(f"Created bid: {bidder.username} bid ${bid_data['price']} on {item.name}")
    
    print("Sample data added successfully!")
    print("You can now test the recommendation system.")
    print("Try logging in as 'bob' or 'charlie' to see personalized recommendations.")

if __name__ == '__main__':
    add_sample_data()
