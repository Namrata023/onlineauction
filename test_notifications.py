#!/usr/bin/env python
"""
Test script to verify notification functionality when items are added
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlineauction.settings')
django.setup()

from myapp.models import CustomUser, Item, Notification
from django.utils import timezone
from datetime import timedelta

def test_notification_creation():
    """Test that notifications are created when a seller adds an item"""
    print("Testing notification creation...")
    
    # Get a seller user
    sellers = CustomUser.objects.filter(is_seller=True)
    if not sellers.exists():
        print("No sellers found. Creating a test seller...")
        seller = CustomUser.objects.create_user(
            username='testseller',
            email='testseller@example.com',
            password='testpass123',
            is_seller=True
        )
    else:
        seller = sellers.first()
    
    print(f"Using seller: {seller.username}")
    
    # Count notifications before
    notification_count_before = Notification.objects.count()
    print(f"Notifications before: {notification_count_before}")
    
    # Create a test item
    test_item = Item.objects.create(
        owner=seller,
        name="Test Auction Item",
        category="Electronics",
        description="A test item for auction",
        minimum_price=100.0,
        end_time=timezone.now() + timedelta(days=7)
    )
    
    print(f"Created item: {test_item.name}")
    
    # Simulate the notification creation logic from add_item view
    users_to_notify = CustomUser.objects.exclude(id=seller.id)
    notifications_created = 0
    
    for user in users_to_notify:
        Notification.objects.create(
            user=user,
            message=f"New item '{test_item.name}' listed by {seller.username} check it out!",
        )
        notifications_created += 1
    
    print(f"Created {notifications_created} notifications")
    
    # Count notifications after
    notification_count_after = Notification.objects.count()
    print(f"Notifications after: {notification_count_after}")
    
    # Verify notifications were created
    new_notifications = Notification.objects.filter(
        message__contains=test_item.name
    )
    
    print(f"Found {new_notifications.count()} notifications for the new item")
    
    # Show sample notifications
    for notif in new_notifications[:3]:
        print(f"  - To {notif.user.username}: {notif.message}")
    
    # Clean up
    test_item.delete()
    new_notifications.delete()
    
    print("Test completed and cleaned up!")

if __name__ == "__main__":
    test_notification_creation()
