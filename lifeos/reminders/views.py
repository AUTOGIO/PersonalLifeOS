from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def telegram_webhook(request):
    """Webhook endpoint for Telegram updates (optional – polling mode is default)."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Process update asynchronously if needed
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


def bot_status(request):
    """Quick health-check for the bot."""
    from django.conf import settings
    return JsonResponse({
        'bot_configured': bool(settings.TELEGRAM_BOT_TOKEN),
        'chat_configured': bool(settings.TELEGRAM_CHAT_ID),
    })
