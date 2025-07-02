# Auction Completion Automation

This system includes enhanced notifications for auction completion. Here's how to set it up:

## Features

### Enhanced Notifications
- **Auction Won**: Winners get notifications with payment instructions
- **Item Sold**: Sellers get notifications with buyer details  
- **Outbid Notifications**: Real-time notifications when someone is outbid
- **Auction Lost**: Notifications for unsuccessful bidders
- **Priority Levels**: High, Medium, Low priority notifications
- **Notification Types**: Categorized by type (bid, auction_won, item_sold, etc.)

### Automatic Auction Completion

#### Manual Trigger (Admin Only)
Visit: `/check-expired-auctions/` to manually trigger auction completion

#### Management Command
Run: `python manage.py complete_auctions`

#### Automatic Scheduling (Recommended)

**Option 1: Windows Task Scheduler**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily, every 1 hour
4. Action: Start a program
5. Program: `python`
6. Arguments: `manage.py complete_auctions`
7. Start in: `C:\Users\Asus\Development\onlineauction`

**Option 2: Cron Job (Linux/Mac)**
Add to crontab:
```bash
# Check every 10 minutes
*/10 * * * * cd /path/to/onlineauction && python manage.py complete_auctions

# Or every hour
0 * * * * cd /path/to/onlineauction && python manage.py complete_auctions
```

**Option 3: Celery (Production)**
For production, set up Celery with Redis/RabbitMQ for background task processing.

## Notification System Usage

### Creating Notifications in Code
```python
from myapp.views import create_notification

create_notification(
    user=user_object,
    message="Your message here",
    notification_type='bid',  # bid, auction_won, item_sold, auction_lost, payment, general
    priority='high',          # urgent, high, medium, low
    related_item=item_object  # optional
)
```

### Email Integration
The system automatically sends emails for:
- Auction winners
- Item sellers  
- Outbid notifications
- Auction completion

Make sure to configure email settings in settings.py:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## Testing

1. Create an auction with a short end time
2. Place some bids
3. Wait for auction to expire OR run: `python manage.py complete_auctions`
4. Check notifications page to see completion notifications
5. Check email for notification emails
