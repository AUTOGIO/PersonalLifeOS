"""
LIFE OS — Telegram Bot
Run standalone: python -c "from reminders.bot import run_bot; run_bot()"
"""
import os
import django
import logging
from datetime import date, datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lifeos.settings')
django.setup()

from django.conf import settings
from django.utils import timezone
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)
from dashboard.models import Activity, AIProject, ProjectSession, DailyPlan, KiteSession

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = settings.TELEGRAM_BOT_TOKEN
CHAT_ID = settings.TELEGRAM_CHAT_ID

# ── /start ────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤘 *LIFE OS Bot* is alive!\n\n"
        "Commands:\n"
        "/today — Today's schedule\n"
        "/done [name] — Mark activity done\n"
        "/skip [name] — Mark activity skipped\n"
        "/add [HH:MM] [name] — Add activity today\n"
        "/start\\_session [project] — Start AI Dev timer\n"
        "/stop — Stop active session\n"
        "/mood [1-10] — Log mood\n"
        "/kite — Log kite session\n",
        parse_mode='Markdown'
    )

# ── /today ────────────────────────────────────────────────────────────────
async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    today = date.today()
    activities = Activity.objects.filter(scheduled_date=today).order_by('start_time')
    if not activities:
        await update.message.reply_text("📅 No activities scheduled for today.")
        return

    STATUS_EMOJI = {'PLANNED':'⬜','IN_PROGRESS':'🔄','DONE':'✅','SKIPPED':'⏭️','RESCHEDULED':'🔁'}
    lines = [f"📅 *Schedule for {today.strftime('%A, %d %b')}*\n"]
    for a in activities:
        t = a.start_time.strftime('%H:%M') if a.start_time else '—'
        emoji = STATUS_EMOJI.get(a.status, '⬜')
        lines.append(f"{emoji} `{t}` — {a.name}")
    await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')

# ── /done ─────────────────────────────────────────────────────────────────
async def cmd_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /done [activity name]")
        return
    name = ' '.join(ctx.args)
    today = date.today()
    activities = Activity.objects.filter(
        scheduled_date=today, name__icontains=name
    )
    if not activities:
        await update.message.reply_text(f"❌ No activity found matching '{name}' today.")
        return
    for a in activities:
        a.status = 'DONE'
        a.save()
    await update.message.reply_text(f"✅ Marked as DONE: *{activities[0].name}*", parse_mode='Markdown')

# ── /skip ─────────────────────────────────────────────────────────────────
async def cmd_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /skip [activity name]")
        return
    name = ' '.join(ctx.args)
    today = date.today()
    activities = Activity.objects.filter(
        scheduled_date=today, name__icontains=name
    )
    if not activities:
        await update.message.reply_text(f"❌ No activity found matching '{name}' today.")
        return
    for a in activities:
        a.status = 'SKIPPED'
        a.save()
    await update.message.reply_text(f"⏭️ Skipped: *{activities[0].name}*", parse_mode='Markdown')

# ── /add ──────────────────────────────────────────────────────────────────
async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: /add [HH:MM] [activity name]")
        return
    time_str = ctx.args[0]
    name = ' '.join(ctx.args[1:])
    today = date.today()
    try:
        t = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        await update.message.reply_text("❌ Invalid time format. Use HH:MM (e.g. 15:30)")
        return
    Activity.objects.create(
        name=name, category='CUSTOM',
        scheduled_date=today, start_time=t, status='PLANNED'
    )
    await update.message.reply_text(f"➕ Added: *{name}* at `{time_str}`", parse_mode='Markdown')

# ── /start_session ────────────────────────────────────────────────────────
async def cmd_start_session(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        projects = AIProject.objects.filter(status='ACTIVE').values_list('name', flat=True)
        await update.message.reply_text(
            "Usage: /start\\_session [project name]\n\nActive projects:\n" +
            '\n'.join(f'• {p}' for p in projects),
            parse_mode='Markdown'
        )
        return
    name = ' '.join(ctx.args)
    project = AIProject.objects.filter(name__icontains=name, status='ACTIVE').first()
    if not project:
        await update.message.reply_text(f"❌ No active project matching '{name}'.")
        return
    ProjectSession.objects.filter(end_time__isnull=True).update(end_time=timezone.now())
    session = ProjectSession.objects.create(project=project, start_time=timezone.now())
    await update.message.reply_text(
        f"⏱️ Session started: *{project.name}*\nStarted at `{session.start_time.strftime('%H:%M')}`",
        parse_mode='Markdown'
    )

# ── /stop ─────────────────────────────────────────────────────────────────
async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    session = ProjectSession.objects.filter(end_time__isnull=True).first()
    if not session:
        await update.message.reply_text("⏹️ No active session to stop.")
        return
    session.end_time = timezone.now()
    session.save()
    mins = session.duration_minutes or 0
    await update.message.reply_text(
        f"⏹️ Session stopped: *{session.project.name}*\n"
        f"Duration: `{mins // 60}h {mins % 60}m`",
        parse_mode='Markdown'
    )

# ── /mood ─────────────────────────────────────────────────────────────────
async def cmd_mood(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("Usage: /mood [1-10]")
        return
    score = max(1, min(10, int(ctx.args[0])))
    plan, _ = DailyPlan.objects.get_or_create(date=date.today())
    plan.mood_score = score
    plan.save()
    emojis = ['😞','😟','😕','😐','🙂','😊','😁','😄','🤩','🤘']
    await update.message.reply_text(
        f"{emojis[score-1]} Mood logged: *{score}/10*", parse_mode='Markdown'
    )

# ── /kite ─────────────────────────────────────────────────────────────────
async def cmd_kite(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🪁 Logging kite session!\n\n"
        "Reply with: [wind speed in knots] [duration in minutes] [optional notes]\n"
        "Example: `18 90 Great session at Ponta de Campina`",
        parse_mode='Markdown'
    )
    ctx.user_data['awaiting_kite'] = True

async def handle_kite_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get('awaiting_kite'):
        return
    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 2:
        await update.message.reply_text("❌ Format: [wind_knots] [duration_min] [notes]")
        return
    try:
        wind = float(parts[0])
        duration = int(parts[1])
        notes = parts[2] if len(parts) > 2 else ''
        KiteSession.objects.create(
            date=date.today(),
            location='Cabedelo, PB',
            wind_speed_knots=wind,
            duration_minutes=duration,
            notes=notes
        )
        ctx.user_data['awaiting_kite'] = False
        await update.message.reply_text(
            f"🪁 Kite session logged!\nWind: `{wind}kn` | Duration: `{duration}min`",
            parse_mode='Markdown'
        )
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Try: 18 90 Great conditions!")


def run_bot():
    """Start the bot in polling mode."""
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('today', cmd_today))
    app.add_handler(CommandHandler('done', cmd_done))
    app.add_handler(CommandHandler('skip', cmd_skip))
    app.add_handler(CommandHandler('add', cmd_add))
    app.add_handler(CommandHandler('start_session', cmd_start_session))
    app.add_handler(CommandHandler('stop', cmd_stop))
    app.add_handler(CommandHandler('mood', cmd_mood))
    app.add_handler(CommandHandler('kite', cmd_kite))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_kite_reply))
    print("🤖 LIFE OS Bot started (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    run_bot()
