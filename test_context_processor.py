#!/usr/bin/env python
"""
Test script to verify the context processor functionality
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlineauction.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from myapp.models import CustomUser, Notification
from myapp.context_processors import notifications_context

def test_context_processor():
    """Test the notifications context processor"""
    print("Testing notifications context processor...")
    
    factory = RequestFactory()
    
    # Test with anonymous user
    request = factory.get('/')
    request.user = AnonymousUser()
    
    context = notifications_context(request)
    print(f"Anonymous user unread_count: {context['unread_count']}")
    assert context['unread_count'] == 0, "Anonymous user should have 0 unread notifications"
    
    # Test with authenticated user
    user = CustomUser.objects.first()
    if user:
        request.user = user
        
        # Get current unread count
        actual_unread = Notification.objects.filter(user=user, is_read=False).count()
        
        context = notifications_context(request)
        print(f"User {user.username} unread_count: {context['unread_count']}")
        print(f"Actual unread notifications: {actual_unread}")
        
        assert context['unread_count'] == actual_unread, "Context processor should return correct unread count"
        
        # Create a test notification
        test_notification = Notification.objects.create(
            user=user,
            message="Test notification for context processor"
        )
        
        # Test again
        context = notifications_context(request)
        new_actual_unread = Notification.objects.filter(user=user, is_read=False).count()
        print(f"After adding notification - unread_count: {context['unread_count']}")
        print(f"Actual unread notifications: {new_actual_unread}")
        
        assert context['unread_count'] == new_actual_unread, "Context processor should reflect new notification"
        
        # Clean up
        test_notification.delete()
        
    print("Context processor test passed!")

if __name__ == "__main__":
    test_context_processor()
