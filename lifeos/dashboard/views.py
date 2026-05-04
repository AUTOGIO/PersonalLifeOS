import csv
import json
import random
from datetime import date, datetime, time, timedelta
from typing import List, Optional
from urllib.parse import urlencode

from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum, Count, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    Activity, AIProject, ProjectSession,
    DailyPlan, Habit, KiteSession, TelegramReminder,
    ScheduleBlock,
)
from .services.tide_service import build_tide_card_payload
from .serializers import ActivitySerializer, AIProjectSerializer, ProjectSessionSerializer
from .schedule_engine import ScheduleEngine

def _time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _parse_time(val) -> Optional[time]:
    if val is None or val == '':
        return None
    if isinstance(val, time):
        return val
    if isinstance(val, str):
        try:
            return datetime.strptime(val.strip(), '%H:%M').time()
        except ValueError:
            return None
    return None


def _activity_slot_end_minutes(a: Activity) -> Optional[int]:
    """Return end minute-of-day for activity block, or None if no start."""
    if not a.start_time:
        return None
    s = _time_to_minutes(a.start_time)
    if a.end_time:
        return _time_to_minutes(a.end_time)
    if a.duration_minutes:
        return s + int(a.duration_minutes)
    return s + 60


def find_activity_schedule_conflicts(
    scheduled_date,
    start_time,
    end_time,
    *,
    exclude_pk=None,
    default_duration_min: int = 120,
) -> List[Activity]:
    """
    Return Activity rows on the same date whose time window overlaps the proposed slot.
    Proposed end defaults to start + default_duration_min when end_time is missing.
    Activities without start_time are skipped. SKIPPED activities are ignored.
    """
    if scheduled_date is None:
        return []
    if isinstance(scheduled_date, str):
        try:
            scheduled_date = date.fromisoformat(scheduled_date)
        except ValueError:
            return []

    st = _parse_time(start_time)
    if st is None:
        return []

    st_min = _time_to_minutes(st)
    en = _parse_time(end_time)
    if en is not None:
        en_min = _time_to_minutes(en)
        if en_min <= st_min:
            en_min = st_min + default_duration_min
    else:
        en_min = st_min + default_duration_min

    qs = Activity.objects.filter(scheduled_date=scheduled_date).exclude(status='SKIPPED')
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)

    conflicts = []
    for a in qs:
        if not a.start_time:
            continue
        a_start = _time_to_minutes(a.start_time)
        a_end = _activity_slot_end_minutes(a)
        if a_end is None or a_end <= a_start:
            a_end = a_start + 60
        if st_min < a_end and a_start < en_min:
            conflicts.append(a)
    return conflicts


ROCK_QUOTES = [
    "Highway to Hell — on my way, crushing every goal! 🤘",
    "Thunderstruck — that's how I feel after a morning workout! ⚡",
    "Fear of the Dark? Not when you're coding past midnight! 🖥️",
    "Iron Man doesn't skip gym day. Neither do I. 🏋️",
    "Crazy Train — my schedule, fully optimized and on the rails! 🚂",
    "We're not gonna take it — we're gonna BUILD it! 💪",
    "Born to Run... to the kite beach! 🪁",
    "Rock and Roll All Nite — then code all day! ⚡",
    "Run to the Hills — or at least to the gym! 🏔️",
    "The Trooper never misses a session. Neither should you. ⚔️",
    "Black Dog energy — focused, powerful, unstoppable! 🐕‍🦺",
    "Master of Puppets? Nah — Master of my Schedule! 🎸",
    "Back in Black — back on track! 🖤",
    "War Pigs? Nope. War Plans. Executed daily. 📋",
    "Paranoid? Only about missing my AI dev block! 💻",
]

# ── HOME DASHBOARD ────────────────────────────────────────────────────────────

def home(request):
    today = date.today()
    activities_today = Activity.objects.filter(
        scheduled_date=today
    ).order_by('start_time')

    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    gym_this_week = Activity.objects.filter(
        category='GYM', scheduled_date__gte=week_start, status='DONE'
    ).count()

    muay_thai_month = Activity.objects.filter(
        category='MUAY_THAI', scheduled_date__gte=month_start, status='DONE'
    ).count()

    ai_minutes_today = ProjectSession.objects.filter(
        start_time__date=today
    ).aggregate(total=Sum('duration_minutes'))['total'] or 0
    ai_hours_today = round(ai_minutes_today / 60, 1)

    kite_month = KiteSession.objects.filter(date__gte=month_start).count()

    daily_plan, _ = DailyPlan.objects.get_or_create(date=today)
    ai_projects = AIProject.objects.filter(status='ACTIVE')
    active_session = ProjectSession.objects.filter(end_time__isnull=True).first()

    context = {
        'activities_today': activities_today,
        'gym_this_week': gym_this_week,
        'muay_thai_month': muay_thai_month,
        'ai_hours_today': ai_hours_today,
        'kite_month': kite_month,
        'daily_plan': daily_plan,
        'ai_projects': ai_projects,
        'active_session': active_session,
        'today': today,
        'quote': random.choice(ROCK_QUOTES),
    }
    return render(request, 'dashboard/home.html', context)


# ── PLANNER ───────────────────────────────────────────────────────────────────

def planner(request):
    ai_projects = AIProject.objects.filter(status='ACTIVE')
    return render(request, 'dashboard/planner.html', {'ai_projects': ai_projects})


@api_view(['GET'])
def api_events(request):
    """Return all activities as FullCalendar-compatible JSON events."""
    qs = Activity.objects.all()
    serializer = ActivitySerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
def api_event_update(request, pk):
    """Update activity date/time after FullCalendar drag-and-drop."""
    activity = get_object_or_404(Activity, pk=pk)
    data = request.data
    if 'scheduled_date' in data:
        activity.scheduled_date = data['scheduled_date']
    if 'start_time' in data:
        activity.start_time = data['start_time'] or None
    if 'end_time' in data:
        activity.end_time = data['end_time'] or None
    if 'status' in data:
        activity.status = data['status']
    activity.save()
    return Response(ActivitySerializer(activity).data)


# ── ANALYTICS ─────────────────────────────────────────────────────────────────

def analytics(request):
    return render(request, 'dashboard/analytics.html')


# ── WEEKLY SCHEDULE ───────────────────────────────────────────────────────────

def weekly_schedule(request):
    """Weekly Schedule page — renders the 7-day planner widget."""
    DAY_ORDER = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    blocks = ScheduleBlock.objects.filter(is_active=True)
    schedule = {}
    for day in DAY_ORDER:
        schedule[day] = list(blocks.filter(day_of_week=day))
    return render(request, 'dashboard/weekly_schedule.html', {
        'schedule': schedule,
        'day_order': DAY_ORDER,
    })


@api_view(['GET'])
def api_weekly_schedule(request):
    """Return all active ScheduleBlocks as JSON, grouped by day."""
    DAY_ORDER = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    blocks = ScheduleBlock.objects.filter(is_active=True)
    result = {}
    for day in DAY_ORDER:
        result[day] = [
            {
                'id':          b.pk,
                'activity':    b.activity,
                'start':       b.start_time.strftime('%H:%M'),
                'end':         b.end_time.strftime('%H:%M'),
                'duration':    b.duration_min,
                'category':    b.category,
                'color':       b.get_category_color(),
                'icon':        b.get_category_icon(),
                'is_anchor':   b.is_anchor,
                'duration_display': b.duration_display(),
            }
            for b in blocks.filter(day_of_week=day)
        ]
    return Response(result)


@csrf_exempt
@require_POST
def api_validate_block(request):
    """POST: Validate a proposed ScheduleBlock via the rule engine."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST.dict()

    engine = ScheduleEngine()
    result = engine.validate(data)
    return JsonResponse({
        'is_valid': result.is_valid,
        'errors':   result.errors,
        'warnings': result.warnings,
    })


@api_view(['GET'])
def api_analytics_heatmap(request):
    """7-day x 24-hour activity heatmap data."""
    today = date.today()
    week_start = today - timedelta(days=6)
    activities = Activity.objects.filter(
        scheduled_date__gte=week_start,
        scheduled_date__lte=today,
        status='DONE',
    )
    # Build a dict: {weekday: {hour: count}}
    data = {}
    for a in activities:
        day = a.scheduled_date.weekday()
        hour = a.start_time.hour if a.start_time else 0
        data.setdefault(day, {}).setdefault(hour, 0)
        data[day][hour] += 1
    return Response(data)


@api_view(['GET'])
def api_analytics_monthly(request):
    """Monthly activity counts grouped by category."""
    today = date.today()
    month_start = today.replace(day=1)
    from collections import defaultdict
    result = defaultdict(int)
    qs = Activity.objects.filter(scheduled_date__gte=month_start)
    for a in qs:
        result[a.get_category_display()] += 1
    return Response(result)


@api_view(['GET'])
def api_analytics_ai_donut(request):
    """AI dev hours by sub-category (Core, Business, macOS, Tools)."""
    cats = ['AI_DEV_CORE', 'AI_DEV_BUSINESS', 'AI_DEV_MACOS', 'AI_DEV_TOOLS']
    result = {}
    for cat in cats:
        mins = Activity.objects.filter(
            category=cat, status='DONE'
        ).aggregate(total=Sum('duration_minutes'))['total'] or 0
        result[cat] = round(mins / 60, 1)
    return Response(result)


@api_view(['GET'])
def api_analytics_weekly_ai(request):
    """AI dev hours per day for the last 7 days."""
    today = date.today()
    labels, values = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        mins = Activity.objects.filter(
            category__startswith='AI_DEV',
            scheduled_date=d,
            status='DONE',
        ).aggregate(total=Sum('duration_minutes'))['total'] or 0
        labels.append(d.strftime('%a %d'))
        values.append(round(mins / 60, 1))
    return Response({'labels': labels, 'values': values})


@api_view(['GET'])
def api_analytics_mood(request):
    """Mood & Energy scores for the last 30 days."""
    today = date.today()
    plans = DailyPlan.objects.filter(
        date__gte=today - timedelta(days=29)
    ).order_by('date')
    labels = [str(p.date) for p in plans]
    mood = [p.mood_score for p in plans]
    energy = [p.energy_score for p in plans]
    return Response({'labels': labels, 'mood': mood, 'energy': energy})


def htmx_tide_card(request):
    """HTMX: tide dashboard card for a given date (?date=YYYY-MM-DD&wind_kn=)."""
    ds = request.GET.get('date')
    try:
        target = datetime.strptime(ds, '%Y-%m-%d').date() if ds else None
    except ValueError:
        target = None
    wind_raw = request.GET.get('wind_kn')
    try:
        wind_kn = float(wind_raw) if wind_raw not in (None, '') else None
    except ValueError:
        wind_kn = None
    tide = build_tide_card_payload(target_date=target, wind_kn=wind_kn)
    planner_open_url = ''
    if tide.get('next_tide'):
        nt = tide['next_tide']
        planner_open_url = reverse('htmx_activity_add') + '?' + urlencode(
            {
                'name': 'Kitesurfing — Cabedelo',
                'category': 'KITESURFING',
                'scheduled_date': nt['date'],
                'start_time': nt['time'],
                'notes': (
                    f"Next tide ({nt['tide_type']}): {nt['time']} @ {nt['height_m']} m — "
                    f"from LifeOS tide card."
                ),
            }
        )
    tide['planner_open_url'] = planner_open_url
    return render(request, 'dashboard/partials/_tide_card.html', {'tide': tide})


@api_view(['GET'])
def api_tide_day(request):
    """JSON for Chart.js / clients: same payload as tide card."""
    ds = request.GET.get('date')
    try:
        target = datetime.strptime(ds, '%Y-%m-%d').date() if ds else None
    except ValueError:
        target = None
    wind_raw = request.GET.get('wind_kn')
    try:
        wind_kn = float(wind_raw) if wind_raw not in (None, '') else None
    except ValueError:
        wind_kn = None
    return Response(build_tide_card_payload(target_date=target, wind_kn=wind_kn))


@api_view(['GET'])
def api_analytics_kite(request):
    """Kite sessions scatter plot: date vs wind speed."""
    sessions = KiteSession.objects.all().order_by('date')
    data = [
        {'x': str(s.date), 'y': s.wind_speed_knots, 'duration': s.duration_minutes}
        for s in sessions if s.wind_speed_knots is not None
    ]
    return Response(data)


@api_view(['GET'])
def api_analytics_time_distribution(request):
    """% of time spent on each category this month."""
    from collections import defaultdict
    today = date.today()
    month_start = today.replace(day=1)
    qs = Activity.objects.filter(scheduled_date__gte=month_start, status='DONE')
    totals = defaultdict(int)
    for a in qs:
        totals[a.get_category_display()] += (a.duration_minutes or 0)
    grand_total = sum(totals.values()) or 1
    result = {k: round(v / grand_total * 100, 1) for k, v in totals.items()}
    return Response(result)


@api_view(['GET'])
def api_analytics_habit_streak(request):
    """Streak counts per habit."""
    habits = Habit.objects.filter(is_active=True)
    labels = [h.name for h in habits]
    streaks = [h.streak_count for h in habits]
    return Response({'labels': labels, 'streaks': streaks})


# ── ACTIVITIES & PROJECTS ─────────────────────────────────────────────────────

def activities_list(request):
    qs = Activity.objects.all().order_by('-scheduled_date', 'start_time')

    # Filters
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(scheduled_date__gte=date_from)
    if date_to:
        qs = qs.filter(scheduled_date__lte=date_to)

    ai_projects = AIProject.objects.all()

    context = {
        'activities': qs,
        'ai_projects': ai_projects,
        'category_choices': Activity.CATEGORY_CHOICES,
        'status_choices': Activity.STATUS_CHOICES,
        'filter_category': category,
        'filter_status': status,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
    }
    return render(request, 'dashboard/activities.html', context)


def activities_export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lifeos_activities.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Category', 'Date', 'Start', 'End', 'Duration (min)', 'Status', 'Notes'])
    for a in Activity.objects.all().order_by('-scheduled_date'):
        writer.writerow([
            a.name, a.get_category_display(), a.scheduled_date,
            a.start_time or '', a.end_time or '',
            a.duration_minutes or '', a.get_status_display(), a.notes,
        ])
    return response


@require_POST
def activities_bulk(request):
    action = request.POST.get('action')
    ids = request.POST.getlist('activity_ids')
    qs = Activity.objects.filter(pk__in=ids)
    if action == 'done':
        qs.update(status='DONE')
    elif action == 'skip':
        qs.update(status='SKIPPED')
    elif action == 'delete':
        qs.delete()
    from django.shortcuts import redirect
    return redirect('activities_list')


# ── HTMX PARTIALS ─────────────────────────────────────────────────────────────

@require_POST
def htmx_toggle_status(request, pk):
    """HTMX: cycle PLANNED → DONE → SKIPPED → PLANNED (returns table row)."""
    activity = get_object_or_404(Activity, pk=pk)
    cycle = {'PLANNED': 'DONE', 'DONE': 'SKIPPED', 'SKIPPED': 'PLANNED',
             'IN_PROGRESS': 'DONE', 'RESCHEDULED': 'PLANNED'}
    activity.status = cycle.get(activity.status, 'PLANNED')
    activity.save()
    # Return timeline item partial (used by home page) or table row
    referer = request.META.get('HTTP_REFERER', '')
    if '/dashboard' in referer or referer.endswith('/'):
        return render(request, 'dashboard/partials/_timeline_item.html', {'activity': activity})
    return render(request, 'dashboard/partials/_activity_row.html', {'activity': activity})


@require_POST
def htmx_save_daily_plan(request):
    today = date.today()
    plan, _ = DailyPlan.objects.get_or_create(date=today)
    plan.morning_intention = request.POST.get('morning_intention', plan.morning_intention)
    plan.evening_review = request.POST.get('evening_review', plan.evening_review)
    mood = request.POST.get('mood_score')
    energy = request.POST.get('energy_score')
    if mood:
        plan.mood_score = int(mood)
    if energy:
        plan.energy_score = int(energy)
    plan.save()
    return render(request, 'dashboard/partials/_daily_plan_form.html', {'daily_plan': plan})


@require_POST
def htmx_session_start(request):
    project_id = request.POST.get('project_id')
    project = get_object_or_404(AIProject, pk=project_id)
    # Stop any existing session
    ProjectSession.objects.filter(end_time__isnull=True).update(end_time=timezone.now())
    session = ProjectSession.objects.create(project=project, start_time=timezone.now())
    active_projects = AIProject.objects.filter(status='ACTIVE')
    return render(request, 'dashboard/partials/_session_panel.html', {
        'active_session': session,
        'ai_projects': active_projects,
    })


@require_POST
def htmx_session_stop(request):
    session = ProjectSession.objects.filter(end_time__isnull=True).first()
    if session:
        session.end_time = timezone.now()
        session.save()
    active_projects = AIProject.objects.filter(status='ACTIVE')
    return render(request, 'dashboard/partials/_session_panel.html', {
        'active_session': None,
        'ai_projects': active_projects,
    })


def htmx_activity_conflicts(request):
    """HTMX: recompute schedule overlap from current form GET params (debounced on client)."""
    sched = request.GET.get('scheduled_date')
    st = request.GET.get('start_time')
    en = request.GET.get('end_time')
    raw_ex = request.GET.get('exclude_pk')
    exclude_pk = None
    if raw_ex and str(raw_ex).isdigit():
        exclude_pk = int(raw_ex)
    conflicts = find_activity_schedule_conflicts(
        sched, st, en, exclude_pk=exclude_pk,
    )
    return render(
        request,
        'dashboard/partials/_activity_modal_conflicts.html',
        {'schedule_conflicts': conflicts},
    )


def htmx_activity_modal(request, pk=None):
    """GET: returns add/edit modal content."""
    activity = get_object_or_404(Activity, pk=pk) if pk else None
    prefill = {}
    if activity is None:
        for key in ('name', 'scheduled_date', 'start_time', 'end_time', 'category', 'notes'):
            val = request.GET.get(key)
            if val is not None and val != '':
                prefill[key] = val

    if activity is not None:
        schedule_conflicts = find_activity_schedule_conflicts(
            activity.scheduled_date,
            activity.start_time,
            activity.end_time,
            exclude_pk=activity.pk,
        )
    else:
        schedule_conflicts = find_activity_schedule_conflicts(
            prefill.get('scheduled_date'),
            prefill.get('start_time'),
            prefill.get('end_time'),
            exclude_pk=None,
        )

    return render(request, 'dashboard/partials/_activity_modal.html', {
        'activity': activity,
        'prefill': prefill,
        'schedule_conflicts': schedule_conflicts,
        'category_choices': Activity.CATEGORY_CHOICES,
        'status_choices': Activity.STATUS_CHOICES,
    })


@require_POST
def htmx_activity_save(request, pk=None):
    """POST: create or update an activity."""
    if pk:
        activity = get_object_or_404(Activity, pk=pk)
    else:
        activity = Activity()
    activity.name = request.POST.get('name', '')
    activity.category = request.POST.get('category', 'CUSTOM')
    activity.scheduled_date = request.POST.get('scheduled_date')
    activity.start_time = request.POST.get('start_time') or None
    activity.end_time = request.POST.get('end_time') or None
    activity.status = request.POST.get('status', 'PLANNED')
    activity.notes = request.POST.get('notes', '')
    activity.save()
    from django.shortcuts import redirect
    return redirect('planner')


@require_http_methods(['DELETE'])
def htmx_activity_delete(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    activity.delete()
    return HttpResponse('')
