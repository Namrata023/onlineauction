from myapp.models import Notification

def notifications_context(request):
    """
    Context processor to add unread notification count to all templates
    """
    context = {'unread_count': 0}
    
    if request.user.is_authenticated:
        context['unread_count'] = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    
    return context
