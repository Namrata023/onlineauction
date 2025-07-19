#!/usr/bin/env python
import os
import sys
import django
import shutil

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlineauction.settings')
django.setup()

from django.contrib.auth import get_user_model
from myapp.models import Item, Bid, ItemImage

User = get_user_model()

def remove_sample_data():
    print("Removing sample data...")
    
    # Sample usernames to remove
    sample_usernames = [
        'alice', 'bob', 'charlie', 'ram', 'shyam', 'hari', 
        'sita', 'gita', 'krishna', 'radha'
    ]
    
    # Sample item names to remove
    sample_item_names = [
        'Vintage Camera', 'Gaming Laptop', 'Antique Furniture Set', 
        'Art Painting', 'Mountain Bike', 'Designer Watch', 'Smartphone',
        'Traditional Dhaka Topi', 'Himalayan Singing Bowl', 'Electric Guitar',
        'Vintage Books Collection', 'Gaming Chair', 'Drone with Camera',
        'Yoga Mat Set', 'Cooking Pot Set'
    ]
    
    # Remove all bids for sample items first
    print("Removing sample bids...")
    sample_items = Item.objects.filter(name__in=sample_item_names)
    bids_count = 0
    for item in sample_items:
        item_bids = Bid.objects.filter(item=item)
        bids_count += item_bids.count()
        item_bids.delete()
    print(f"✅ Removed {bids_count} sample bids")
    
    # Remove ItemImages and their files
    print("Removing sample item images...")
    images_count = 0
    for item in sample_items:
        item_images = ItemImage.objects.filter(item=item)
        for item_image in item_images:
            # Delete the actual image file
            if item_image.image:
                try:
                    if os.path.exists(item_image.image.path):
                        os.remove(item_image.image.path)
                        print(f"  Deleted image file: {item_image.image.name}")
                except Exception as e:
                    print(f"  ⚠️ Could not delete image file: {e}")
            images_count += 1
        item_images.delete()
    print(f"✅ Removed {images_count} sample item images")
    
    # Remove sample items
    print("Removing sample items...")
    items_count = sample_items.count()
    sample_items.delete()
    print(f"✅ Removed {items_count} sample items")
    
    # Remove sample users
    print("Removing sample users...")
    sample_users = User.objects.filter(username__in=sample_usernames)
    users_count = sample_users.count()
    sample_users.delete()
    print(f"✅ Removed {users_count} sample users")
    
    # Clean up downloaded images from media/images/ directory
    print("Cleaning up downloaded image files...")
    sample_image_files = [
        'vintage_camera.jpg', 'gaming_laptop.jpg', 'antique_furniture_set.jpg',
        'art_painting.jpg', 'mountain_bike.jpg', 'designer_watch.jpg',
        'smartphone.jpg', 'traditional_dhaka_topi.jpg', 'himalayan_singing_bowl.jpg',
        'electric_guitar.jpg', 'vintage_books_collection.jpg', 'gaming_chair.jpg',
        'drone_with_camera.jpg', 'yoga_mat_set.jpg', 'cooking_pot_set.jpg'
    ]
    
    images_dir = os.path.join('media', 'images')
    cleaned_files = 0
    if os.path.exists(images_dir):
        for filename in sample_image_files:
            file_path = os.path.join(images_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"  Deleted: {filename}")
                    cleaned_files += 1
                except Exception as e:
                    print(f"  ⚠️ Could not delete {filename}: {e}")
    print(f"✅ Cleaned up {cleaned_files} image files")
    
    print("\n🎉 Sample data removal completed!")
    print("All sample users, items, bids, and images have been removed.")
    print("Your database is now clean and ready for fresh data.")

def confirm_removal():
    """Ask for confirmation before removing data"""
    print("⚠️  WARNING: This will remove ALL sample data including:")
    print("   - 10 sample users (alice, bob, charlie, ram, shyam, hari, sita, gita, krishna, radha)")
    print("   - 15 sample items with their images")
    print("   - All bids on sample items")
    print("   - Downloaded image files")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        remove_sample_data()
    elif response in ['no', 'n']:
        print("❌ Operation cancelled. No data was removed.")
    else:
        print("❌ Invalid response. Please enter 'yes' or 'no'.")
        confirm_removal()

if __name__ == '__main__':
    confirm_removal()
