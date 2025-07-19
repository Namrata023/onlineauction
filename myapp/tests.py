from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Item, Bid, Notification, Payment, ItemImage
from .forms import ItemForm, BidForm, UserCreationForm

User = get_user_model()

class UserAuthenticationTests(TestCase):
    """Test user registration, login, and authentication"""
    
    def setUp(self):
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '9801234567',
            'address': 'Test Address',
            'is_seller': True
        }
    
    def test_user_registration(self):
        """Test user can register successfully"""
        response = self.client.post(reverse('register'), self.user_data)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_seller)
    
    def test_user_login(self):
        """Test user can login successfully"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        response = self.client.post(reverse('login_view'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('home'))
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('login_view'), {
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        self.assertContains(response, 'Invalid credentials')

class ItemManagementTests(TestCase):
    """Test item creation, editing, and deletion"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass123',
            is_seller=True
        )
        self.client.login(username='seller', password='testpass123')
    
    def test_item_creation(self):
        """Test seller can create an item"""
        item_data = {
            'name': 'Test Item',
            'category': 'electronics',
            'description': 'Test Description',
            'minimum_price': 100.0,
            'end_time': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
        }
        response = self.client.post(reverse('add_item'), item_data)
        self.assertEqual(Item.objects.count(), 1)
        item = Item.objects.first()
        self.assertEqual(item.name, 'Test Item')
        self.assertEqual(item.owner, self.user)
        self.assertEqual(item.minimum_price, 100.0)
    
    def test_item_creation_requires_login(self):
        """Test item creation requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('add_item'))
        self.assertRedirects(response, reverse('login_view') + '?next=' + reverse('add_item'))
    
    def test_item_edit_by_owner(self):
        """Test item can be edited by owner"""
        item = Item.objects.create(
            owner=self.user,
            name='Original Item',
            category='electronics',
            description='Original Description',
            minimum_price=50.0,
            end_time=timezone.now() + timedelta(days=7)
        )
        
        edit_data = {
            'name': 'Updated Item',
            'category': 'clothing',
            'description': 'Updated Description',
            'minimum_price': 75.0,
            'end_time': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
        }
        
        response = self.client.post(reverse('edit_item', args=[item.id]), edit_data)
        item.refresh_from_db()
        self.assertEqual(item.name, 'Updated Item')
        self.assertEqual(item.category, 'clothing')
        self.assertEqual(item.minimum_price, 75.0)

class BiddingSystemTests(TestCase):
    """Test bidding functionality and validation"""
    
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass123',
            is_seller=True
        )
        self.bidder = User.objects.create_user(
            username='bidder',
            email='bidder@example.com',
            password='testpass123'
        )
        self.item = Item.objects.create(
            owner=self.seller,
            name='Test Item',
            category='electronics',
            description='Test Description',
            minimum_price=100.0,
            end_time=timezone.now() + timedelta(days=7)
        )
    
    def test_valid_bid(self):
        """Test valid bid placement"""
        self.client.login(username='bidder', password='testpass123')
        response = self.client.post(reverse('product', args=[self.item.id]), {
            'bid_price': 150.0
        })
        
        self.assertEqual(Bid.objects.count(), 1)
        bid = Bid.objects.first()
        self.assertEqual(bid.bidder, self.bidder)
        self.assertEqual(bid.item, self.item)
        self.assertEqual(bid.bid_price, 150.0)
    
    def test_bid_below_minimum(self):
        """Test bid below minimum price is rejected"""
        self.client.login(username='bidder', password='testpass123')
        response = self.client.post(reverse('product', args=[self.item.id]), {
            'bid_price': 50.0
        })
        self.assertEqual(Bid.objects.count(), 0)
    
    def test_owner_cannot_bid_on_own_item(self):
        """Test item owner cannot bid on their own item"""
        self.client.login(username='seller', password='testpass123')
        response = self.client.post(reverse('product', args=[self.item.id]), {
            'bid_price': 150.0
        })
        self.assertEqual(Bid.objects.count(), 0)
    
    def test_bid_on_expired_auction(self):
        """Test bidding on expired auction is rejected"""
        self.item.end_time = timezone.now() - timedelta(hours=1)
        self.item.save()
        
        self.client.login(username='bidder', password='testpass123')
        response = self.client.post(reverse('product', args=[self.item.id]), {
            'bid_price': 150.0
        })
        self.assertEqual(Bid.objects.count(), 0)

class NotificationSystemTests(TestCase):
    """Test notification creation and management"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_notification_creation(self):
        """Test notification is created properly"""
        notification = Notification.objects.create(
            user=self.user,
            message='Test notification',
            notification_type='general',
            priority='medium'
        )
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.message, 'Test notification')
        self.assertFalse(notification.is_read)
    
    def test_notifications_view(self):
        """Test notifications are displayed correctly"""
        Notification.objects.create(
            user=self.user,
            message='Test notification 1',
            notification_type='bid',
            priority='high'
        )
        Notification.objects.create(
            user=self.user,
            message='Test notification 2',
            notification_type='general',
            priority='low'
        )
        
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test notification 1')
        self.assertContains(response, 'Test notification 2')
    
    def test_notifications_marked_read(self):
        """Test notifications are marked as read when viewed"""
        notification = Notification.objects.create(
            user=self.user,
            message='Test notification',
            notification_type='general',
            priority='medium'
        )
        
        self.assertFalse(notification.is_read)
        response = self.client.get(reverse('notifications'))
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

class SearchAndFilterTests(TestCase):
    """Test search functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass123',
            is_seller=True
        )
        
        # Create test items
        Item.objects.create(
            owner=self.user,
            name='iPhone 13',
            category='electronics',
            description='Latest iPhone model',
            minimum_price=500.0,
            end_time=timezone.now() + timedelta(days=7)
        )
        Item.objects.create(
            owner=self.user,
            name='Samsung Galaxy',
            category='electronics',
            description='Android smartphone',
            minimum_price=400.0,
            end_time=timezone.now() + timedelta(days=7)
        )
        Item.objects.create(
            owner=self.user,
            name='Vintage Watch',
            category='collectibles',
            description='Antique timepiece',
            minimum_price=200.0,
            end_time=timezone.now() + timedelta(days=7)
        )
    
    def test_search_by_name(self):
        """Test search functionality by item name"""
        response = self.client.get(reverse('home'), {'q': 'iPhone'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'iPhone 13')
        self.assertNotContains(response, 'Samsung Galaxy')
    
    def test_search_by_description(self):
        """Test search functionality by description"""
        response = self.client.get(reverse('home'), {'q': 'smartphone'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Samsung Galaxy')
    
    def test_search_no_results(self):
        """Test search with no matching results"""
        response = self.client.get(reverse('home'), {'q': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No items found')

class ErrorHandlingTests(TestCase):
    """Test error handling in critical functions"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_invalid_item_access(self):
        """Test accessing non-existent item returns 404"""
        response = self.client.get(reverse('product', args=[999]))
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_bid_amount(self):
        """Test invalid bid amount handling"""
        seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass123',
            is_seller=True
        )
        item = Item.objects.create(
            owner=seller,
            name='Test Item',
            category='electronics',
            description='Test Description',
            minimum_price=100.0,
            end_time=timezone.now() + timedelta(days=7)
        )
        
        # Test negative bid
        response = self.client.post(reverse('product', args=[item.id]), {
            'bid_price': -50.0
        })
        self.assertEqual(Bid.objects.count(), 0)
        
        # Test zero bid
        response = self.client.post(reverse('product', args=[item.id]), {
            'bid_price': 0
        })
        self.assertEqual(Bid.objects.count(), 0)
    
    def test_unauthorized_item_edit(self):
        """Test unauthorized user cannot edit item"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123',
            is_seller=True
        )
        item = Item.objects.create(
            owner=other_user,
            name='Test Item',
            category='electronics',
            description='Test Description',
            minimum_price=100.0,
            end_time=timezone.now() + timedelta(days=7)
        )
        
        response = self.client.get(reverse('edit_item', args=[item.id]))
        self.assertEqual(response.status_code, 403)
