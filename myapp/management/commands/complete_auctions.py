from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from myapp.models import Item, Bid, Notification


class Command(BaseCommand):
    help = 'Check and complete expired auctions, send notifications to winners and sellers'

    def handle(self, *args, **options):
        # Find all items where auction has expired but not yet marked as sold
        expired_items = Item.objects.filter(
            end_time__lt=timezone.now(),
            is_sold=False
        )

        completed_auctions = 0
        
        for item in expired_items:
            # Get the highest bid for this item
            winning_bid = Bid.objects.filter(item=item).order_by('-bid_price').first()
            
            if winning_bid:
                # Mark item as sold
                item.is_sold = True
                item.save()
                
                # Notify winner
                self.notify_winner(winning_bid)
                
                # Notify seller
                self.notify_seller(item, winning_bid)
                
                # Notify other bidders who didn't win
                self.notify_losing_bidders(item, winning_bid)
                
                completed_auctions += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Completed auction for "{item.name}" - Winner: {winning_bid.bidder.username} (Rs.{winning_bid.bid_price})'
                    )
                )
            else:
                # No bids received, just mark as ended
                item.is_sold = False  # Keep as false since no sale occurred
                item.save()
                
                # Notify seller that no bids were received
                self.notify_seller_no_bids(item)
                
                self.stdout.write(
                    self.style.WARNING(f'Auction ended for "{item.name}" with no bids')
                )

        if completed_auctions == 0:
            self.stdout.write(self.style.SUCCESS('No expired auctions to process'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully processed {completed_auctions} expired auctions')
            )

    def notify_winner(self, winning_bid):
        """Send notification to auction winner"""
        user = winning_bid.bidder
        item = winning_bid.item
        
        # Create in-app notification
        Notification.objects.create(
            user=user,
            message=f"🎉 Congratulations! You won the auction for '{item.name}' with a bid of Rs.{winning_bid.bid_price}. Please proceed with payment to complete your purchase."
        )
        
        # Send email notification
        try:
            subject = "🎉 Congratulations! You Won the Auction!"
            message = f"""
Dear {user.username},

Congratulations! You have successfully won the auction for "{item.name}".

Auction Details:
- Item: {item.name}
- Your Winning Bid: Rs.{winning_bid.bid_price}
- Auction End Time: {item.end_time.strftime('%B %d, %Y at %I:%M %p')}

Please log in to your account to proceed with the payment and complete your purchase.

Thank you for using OnlineAuction!

Best regards,
OnlineAuction Team
            """
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=True)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email to winner {user.username}: {str(e)}'))

    def notify_seller(self, item, winning_bid):
        """Send notification to item seller"""
        seller = item.owner
        
        # Create in-app notification
        Notification.objects.create(
            user=seller,
            message=f"💰 Great news! Your item '{item.name}' has been sold to {winning_bid.bidder.username} for Rs.{winning_bid.bid_price}. The buyer will contact you for payment and delivery."
        )
        
        # Send email notification
        try:
            subject = "💰 Your Item Has Been Sold!"
            message = f"""
Dear {seller.username},

Great news! Your auction has completed successfully.

Sale Details:
- Item: {item.name}
- Winning Bid: Rs.{winning_bid.bid_price}
- Winner: {winning_bid.bidder.username}
- Winner Email: {winning_bid.bidder.email}

The winning bidder will contact you to arrange payment and delivery. Please ensure you provide excellent service to maintain our platform's reputation.

Thank you for using OnlineAuction!

Best regards,
OnlineAuction Team
            """
            send_mail(subject, message, settings.EMAIL_HOST_USER, [seller.email], fail_silently=True)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email to seller {seller.username}: {str(e)}'))

    def notify_losing_bidders(self, item, winning_bid):
        """Send notification to bidders who didn't win"""
        losing_bids = Bid.objects.filter(item=item).exclude(id=winning_bid.id).values('bidder').distinct()
        
        for bid_info in losing_bids:
            try:
                user = winning_bid.bidder.__class__.objects.get(id=bid_info['bidder'])
                
                # Create in-app notification
                Notification.objects.create(
                    user=user,
                    message=f"⏰ The auction for '{item.name}' has ended. Unfortunately, you didn't win this time, but there are many more exciting auctions waiting for you!"
                )
                
                # Send email notification
                subject = "Auction Ended - Better Luck Next Time!"
                message = f"""
Dear {user.username},

The auction for "{item.name}" has ended.

Unfortunately, your bid was not the highest, but don't worry! There are many more exciting auctions on our platform waiting for you.

Keep bidding and good luck with your next auction!

Best regards,
OnlineAuction Team
                """
                send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=True)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to notify losing bidder: {str(e)}'))

    def notify_seller_no_bids(self, item):
        """Send notification to seller when no bids were received"""
        seller = item.owner
        
        # Create in-app notification
        Notification.objects.create(
            user=seller,
            message=f"⏰ Your auction for '{item.name}' has ended without any bids. Consider relisting with a lower starting price or better description."
        )
        
        # Send email notification
        try:
            subject = "Auction Ended - No Bids Received"
            message = f"""
Dear {seller.username},

Your auction for "{item.name}" has ended without receiving any bids.

Don't be discouraged! Here are some suggestions for better results:
- Consider lowering the starting price
- Add more detailed descriptions and better photos
- Choose appropriate categories and tags
- List during peak hours when more users are online

You can relist your item anytime from your profile page.

Best regards,
OnlineAuction Team
            """
            send_mail(subject, message, settings.EMAIL_HOST_USER, [seller.email], fail_silently=True)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email to seller {seller.username}: {str(e)}'))
