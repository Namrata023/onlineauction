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
