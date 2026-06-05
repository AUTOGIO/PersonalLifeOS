"""
LIFE OS — APScheduler scheduled reminders
Run standalone: python -c "from reminders.tasks import start_scheduler; start_scheduler()"
"""
import os
import django
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lifeos.settings')
django.setup()

import requests
from datetime import date, datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

TOKEN = settings.TELEGRAM_BOT_TOKEN
CHAT_ID = settings.TELEGRAM_CHAT_ID


def send_message(text: str, parse_mode: str = 'Markdown') -> bool:
    """Send a Telegram message via HTTP API."""
    if not TOKEN or not CHAT_ID:
        logger.warning("Telegram not configured — skipping message.")
        return False
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    resp = requests.post(url, json={
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': parse_mode,
    }, timeout=10)
    if not resp.ok:
        logger.error(f"Telegram send failed: {resp.text}")
    return resp.ok


def job_morning_greeting():
    """07:15 — Good morning + today's schedule."""
    from dashboard.models import Activity
    today = date.today()
    activities = Activity.objects.filter(scheduled_date=today).order_by('start_time')
    STATUS_EMOJI = {'PLANNED':'⬜','IN_PROGRESS':'🔄','DONE':'✅','SKIPPED':'⏭️','RESCHEDULED':'🔁'}
    lines = [f"🌅 *Good morning! Here's your LIFE OS schedule for {today.strftime('%A, %d %b')}:*\n"]
    for a in activities:
        t = a.start_time.strftime('%H:%M') if a.start_time else '——'
        emoji = STATUS_EMOJI.get(a.status, '⬜')
        lines.append(f"{emoji} `{t}` {a.name}")
    lines.append("\n🤘 _Make it count!_")
    send_message('\n'.join(lines))
    logger.info("Morning greeting sent.")


def job_evening_review():
    """22:30 — Evening review prompt."""
    today = date.today()
    send_message(
        f"🌙 *Evening Review — {today.strftime('%d %b')}*\n\n"
        "How did your day go? Log your mood: /mood [1-10]\n"
        "Check your plan: /today\n\n"
        "_Rock on! 🤘_"
    )
    logger.info("Evening review sent.")


def job_activity_reminders():
    """Run every minute — send reminder 30 min before each activity."""
    from dashboard.models import Activity, TelegramReminder
    now = timezone.now()
    target = now + timedelta(minutes=30)
    target_time = target.time().replace(second=0, microsecond=0)

    activities = Activity.objects.filter(
        scheduled_date=date.today(),
        start_time__hour=target_time.hour,
        start_time__minute=target_time.minute,
        status='PLANNED',
    )
    for a in activities:
        # Avoid duplicate reminders
        already_sent = TelegramReminder.objects.filter(
            activity=a, is_sent=True
        ).exists()
        if not already_sent:
            msg = f"⏰ *Reminder:* You have *{a.name}* in 30 minutes!\n`{a.start_time.strftime('%H:%M')}` — {a.get_category_display()}"
            if send_message(msg):
                TelegramReminder.objects.create(
                    activity=a,
                    message=msg,
                    remind_at=now,
                    is_sent=True,
                    chat_id=CHAT_ID,
                )


def start_scheduler():
    """Start the APScheduler with all jobs."""
    scheduler = BlockingScheduler(timezone='America/Fortaleza')

    # Morning greeting at 07:15
    scheduler.add_job(
        job_morning_greeting,
        CronTrigger(hour=7, minute=15, timezone='America/Fortaleza'),
        id='morning_greeting',
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Evening review at 22:30
    scheduler.add_job(
        job_evening_review,
        CronTrigger(hour=22, minute=30, timezone='America/Fortaleza'),
        id='evening_review',
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Activity reminders — every minute
    scheduler.add_job(
        job_activity_reminders,
        'interval',
        minutes=1,
        id='activity_reminders',
        replace_existing=True,
    )

    logger.info("📅 APScheduler started with 3 jobs.")
    print("📅 LIFE OS Scheduler running... (Ctrl+C to stop)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")


if __name__ == '__main__':
    start_scheduler()
