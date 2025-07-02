# auctions/utils.py

from .models import Bid, Item
from django.db.models import Count

# --- Content-Based Recommender ---
def get_similar_items(item, all_items):
    item_tags = set((item.tags or "").lower().split(","))
    similarity_scores = []

    for other in all_items:
        if other.id == item.id:
            continue
        other_tags = set((other.tags or "").lower().split(","))
        score = len(item_tags.intersection(other_tags))
        similarity_scores.append((other, score))

    sorted_items = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    return [i for i, _ in sorted_items[:5]]



def get_user_based_recommendations(user):
    user_items = Bid.objects.filter(bidder=user).values_list('item_id', flat=True)
    similar_users = Bid.objects.filter(item_id__in=user_items).exclude(bidder=user)

    recommended_items = Bid.objects.filter(
        bidder__in=similar_users
    ).exclude(item_id__in=user_items)

    recommended_items = recommended_items.values('item').annotate(freq=Count('item')).order_by('-freq')
    item_ids = [r['item'] for r in recommended_items[:5]]

    return Item.objects.filter(id__in=item_ids)


# --- New Homepage Recommendation Functions ---
def get_popular_items(limit=6):
    """Get items with most bids (popular items)"""
    popular_items = Item.objects.annotate(
        bid_count=Count('bid')
    ).filter(
        bid_count__gt=0,  # Only items with at least one bid
        is_sold=False     # Exclude sold items
    ).order_by('-bid_count')[:limit]
    
    return popular_items


def get_homepage_recommendations_for_user(user, limit=6):
    """Get personalized recommendations for homepage"""
    if not user.is_authenticated:
        return Item.objects.none()
    
    # Get user's bidding history
    user_bid_items = Bid.objects.filter(bidder=user).values_list('item_id', flat=True)
    
    if not user_bid_items:
        # If user has no bids, return recently added items
        return Item.objects.filter(is_sold=False).order_by('-created_at')[:limit]
    
    # Get categories user has bid on
    user_categories = Item.objects.filter(
        id__in=user_bid_items
    ).values_list('category', flat=True).distinct()
    
    # Find items in similar categories that user hasn't bid on
    recommended = Item.objects.filter(
        category__in=user_categories,
        is_sold=False
    ).exclude(
        id__in=user_bid_items
    ).exclude(
        owner=user  # Don't recommend user's own items
    ).order_by('-created_at')[:limit]
    
    # If not enough recommendations, fill with popular items
    if recommended.count() < limit:
        popular = get_popular_items(limit - recommended.count())
        # Combine and remove duplicates
        recommended_ids = list(recommended.values_list('id', flat=True))
        additional_popular = popular.exclude(id__in=recommended_ids)
        recommended = list(recommended) + list(additional_popular)
    
    return recommended[:limit]


def get_recently_added_items(limit=6):
    """Get recently added items for homepage"""
    return Item.objects.filter(is_sold=False).order_by('-created_at')[:limit]
