from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.telegram_webhook, name='telegram_webhook'),
    path('status/', views.bot_status, name='bot_status'),
]
