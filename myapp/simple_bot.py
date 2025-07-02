import requests
import json
import os
from django.conf import settings

def get_fallback_response(user_input):
    """Fallback responses when OpenAI API is not available"""
    user_input_lower = user_input.lower()
    
    # Common auction-related keywords and responses
    if any(word in user_input_lower for word in ['bid', 'bidding', 'how to bid']):
        return "To place a bid, you need to be logged in. Go to any product page and enter your bid amount. Your bid must be higher than the current highest bid."
    
    elif any(word in user_input_lower for word in ['register', 'sign up', 'account']):
        return "To register, click the 'Register' button and fill out the form with your details. You'll need to provide a username, email, and password."
    
    elif any(word in user_input_lower for word in ['sell', 'list item', 'add item']):
        return "To sell items, you need to be registered as a seller. Go to your profile, enable seller status, then use the 'Add Item' feature to list your products."
    
    elif any(word in user_input_lower for word in ['payment', 'pay', 'money']):
        return "Payment is handled through Khalti. Once you win an auction, you'll receive instructions for completing your payment."
    
    elif any(word in user_input_lower for word in ['contact', 'support', 'help']):
        return "For additional support, you can contact us at support@auctionnepal.com or use the contact form on our website."
    
    elif any(word in user_input_lower for word in ['categories', 'what can i buy']):
        return "We have various categories including Electronics, Antiques, Vehicles, and more. Browse our homepage to see all available items."
    elif any(word in user_input_lower for word in ['auction', 'what is auction', 'how does it work']):
        return "An auction is a public sale where items are sold to the highest bidder. You can place bids on items you are interested in, and the highest bid at the end of the auction wins."
    elif any(word in user_input_lower for word in ['time remaining', 'how long', 'end time']):
        return "You can check the time remaining for each auction item on its product page. The auction ends when the timer reaches zero."
    elif any(word in user_input_lower for word in ['profile', 'my account', 'edit profile']):
        return "To view or edit your profile, go to the 'Profile' section in your account. Here you can update your personal information, view your bids, and manage your items."
    elif any(word in user_input_lower for word in ['notifications', 'alerts', 'updates']):
        return "You can view your notifications in the 'Notifications' section of your account. This includes updates on your bids, auction results, and other important alerts."
    elif any(word in user_input_lower for word in ['privacy', 'terms', 'policy']):
        return "You can find our Privacy Policy and Terms of Service in the footer of our website. They outline how we handle your data and the rules for using our platform."
    elif any(word in user_input_lower for word in ['feedback', 'suggestions', 'comments']):
        return "We value your feedback! You can send us your suggestions or comments through the contact form on our website or email us directly at auction.online07@gmail.com."
    elif any(word in user_input_lower for word in ['login', 'sign in', 'access account']):
        return "To log in, click the 'Login' button and enter your username and password. If you don't have an account, please register first."
    elif any(word in user_input_lower for word in ['outbid', 'notify outbid', 'outbid notification']):
        return "If you are outbid on an item, you will receive a notification in your account. You can then choose to place a new bid if you wish."
    else:
        return "I'm here to help with questions about AuctionNepal! You can ask me about bidding, registering, selling items, payments, or general auction information."

def get_bot_response(user_input):
    """
    Simple OpenAI API chatbot without langchain.
    Makes direct API calls to OpenAI's chat completions endpoint.
    """
    # Try to get API key from environment or Django settings
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key and hasattr(settings, 'OPENAI_API_KEY'):
        api_key = settings.OPENAI_API_KEY
    
    # If no API key, use fallback responses
    if not api_key:
        return get_fallback_response(user_input)
    
    # System prompt with auction website context - optimized for fewer tokens
    system_message = """You are a helpful assistant for AuctionNepal auction website. 
Context: Users register, browse, bid on items. Bidding requires login. Bids must be higher than previous. 
Categories: Electronics, Antiques, Vehicles. Support: support@auctionnepal.com
Keep responses very brief and helpful."""

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": 100,  # Reduced from 150 to save costs
            "temperature": 0.5  # Reduced from 0.7 for more consistent, shorter responses
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return get_fallback_response(user_input)
        elif response.status_code == 401:
            return get_fallback_response(user_input)
        elif response.status_code == 429:
            return get_fallback_response(user_input)
        else:
            return get_fallback_response(user_input)
            
    except requests.exceptions.Timeout:
        return get_fallback_response(user_input)
    except requests.exceptions.ConnectionError:
        return get_fallback_response(user_input)
    except Exception as e:
        # For debugging - you can remove this in production
        print(f"Chatbot error: {str(e)}")
        return get_fallback_response(user_input)
