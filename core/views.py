from datetime import timedelta

from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from habits.models import Habit, HabitLog
from calendar_app.services import get_today_events, get_week_events
from planner.forms import DailyTaskForm
from planner.models import DailyTask


def _load_tide_days(today):
    """Return tide entries for today and the next 2 days, reading from the PDF."""
    import re
    from calendar_app.tide_wind import _extract_pdf_row_text

    def _parse_row(d, row_text):
        normalized = " ".join(row_text.split())
        anchor = normalized.find(f"{d.day:02d}")
        if anchor != -1:
            normalized = normalized[anchor:]
        pairs = re.findall(r"(\d{4})\s+(-?\d+\.\d{2})", normalized)
        return [{"t": hhmm[:2] + ":" + hhmm[2:], "h": float(h)} for hhmm, h in pairs]

    days = []
    for offset, label in enumerate(["Today", "Tomorrow", None]):
        d = today + timedelta(days=offset)
        if label is None:
            label = d.strftime("%a %b %-d")
        try:
            entries = _parse_row(d, _extract_pdf_row_text(d))
        except Exception:
            entries = []
        days.append({"date": d.isoformat(), "label": label, "entries": entries})
    return days


def _get_base_context():
    """Shared context for dashboard and terminal views."""
    today = timezone.localdate()
    habits = Habit.objects.filter(is_active=True).order_by('order', 'name')
    logs_today = HabitLog.objects.filter(date=today, completed=True).values_list('habit_id', flat=True)
    completed_ids = list(logs_today)
    completed_count = len(completed_ids)
    total_habits = habits.count()

    calendar_error = None
    try:
        events_today = get_today_events()
    except Exception as exc:
        events_today = []
        calendar_error = str(exc)

    try:
        week_events = get_week_events()
    except Exception as exc:
        week_events = []
        if calendar_error is None:
            calendar_error = str(exc)

    try:
        from planner.models import NudgeNotification
        pending_nudges = list(
            NudgeNotification.objects.filter(
                channel=NudgeNotification.CHANNEL_IN_APP,
                read_at__isnull=True,
            ).order_by('-created_at')[:5]
        )
    except Exception:
        pending_nudges = []

    # Enrich habits with streak + completion rate + done-today flag
    habits_data = []
    for h in habits:
        streak = h.get_streak()
        rate = h.completion_rate_30d()
        done = h.id in completed_ids
        # Block-char progress bar (24 chars wide)
        filled = round(rate / 100 * 24)
        bar = '\u2588' * filled + '\u2591' * (24 - filled)
        habits_data.append({
            'habit': h,
            'streak': streak,
            'rate': rate,
            'done': done,
            'bar': bar,
        })

    avg_rate_30d = round(
        sum(item['rate'] for item in habits_data) / len(habits_data), 1
    ) if habits_data else 0.0
    best_streak = max((item['streak'] for item in habits_data), default=0)

    hour = timezone.localtime().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    tide_days = _load_tide_days(today)
    daily_task_context = _get_daily_task_context(today=today)

    return {
        'greeting': greeting,
        'today': today,
        'tide_days': tide_days,
        'habits': habits,
        'habits_data': habits_data,
        'completed_ids': completed_ids,
        'completed_count': completed_count,
        'total_habits': total_habits,
        'events': events_today,
        'week_events': week_events,
        'calendar_error': calendar_error,
        'error': calendar_error,
        'pending_nudges': pending_nudges,
        'avg_rate_30d': avg_rate_30d,
        'best_streak': best_streak,
        **daily_task_context,
    }


def _get_daily_task_context(today=None, category=None, task_errors=None):
    today = today or timezone.localdate()
    tasks = DailyTask.objects.filter(date=today)
    if category:
        valid_categories = {choice[0] for choice in DailyTask.CATEGORY_CHOICES}
        if category in valid_categories:
            tasks = tasks.filter(category=category)
        else:
            category = None

    return {
        'daily_tasks': tasks,
        'daily_task_form': DailyTaskForm(),
        'daily_task_categories': DailyTask.CATEGORY_CHOICES,
        'daily_task_priorities': DailyTask.PRIORITY_CHOICES,
        'selected_task_category': category or '',
        'daily_task_errors': task_errors or [],
    }


def _render_daily_task_list(request, *, category=None, task_errors=None, status=200):
    context = _get_daily_task_context(category=category, task_errors=task_errors)
    return render(request, 'dashboard/partials/daily_task_list.html', context, status=status)


def dashboard(request):
    context = _get_base_context()
    return render(request, 'dashboard.html', context)


@require_GET
def dashboard_tasks_list(request):
    category = request.GET.get('filter_category') or request.GET.get('category', '')
    return _render_daily_task_list(request, category=category.strip())


@require_POST
def add_dashboard_task(request):
    form = DailyTaskForm(request.POST)
    category = request.POST.get('filter_category', '').strip()
    if form.is_valid():
        task = form.save(commit=False)
        task.date = timezone.localdate()
        task.completed = False
        task.save()
        return _render_daily_task_list(request, category=category)

    errors = []
    for field_errors in form.errors.values():
        errors.extend(field_errors)
    return _render_daily_task_list(request, category=category, task_errors=errors, status=400)


@require_POST
def complete_dashboard_task(request, task_id):
    task = get_object_or_404(DailyTask, id=task_id, date=timezone.localdate())
    task.completed = request.POST.get('completed') == 'true'
    task.save(update_fields=['completed'])
    return _render_daily_task_list(request, category=request.POST.get('filter_category', '').strip())


@require_POST
def delete_dashboard_task(request, task_id):
    task = get_object_or_404(DailyTask, id=task_id, date=timezone.localdate())
    task.delete()
    return _render_daily_task_list(request, category=request.POST.get('filter_category', '').strip())


def _fetch_wind_multi_source(today, now_local):
    """
    Fetch current wind speed from 4 independent sources for Cabedelo, PB, Brazil.
    Each source is best-effort — failures are caught and logged individually.
    Final speed_kts = average of all successful responses.
    Hourly forecast = per-slot average of Open-Meteo (1h) and wttr.in (3h).

    Sources:
      1. wttr.in          — JSON, no auth, 3-hour slots
      2. Open-Meteo       — JSON, no auth, 1-hour slots, wind in knots
      3. Windguru         — internal JSON API, spot 57134 (Cabedelo), m/s → kts
      4. wind.com         — JSON API (endpoint guessed; fails gracefully if wrong)
    """
    import json
    import urllib.request
    from collections import defaultdict
    from datetime import datetime as _dt

    LAT, LON    = "-6.967", "-34.833"
    KMPH_TO_KTS = 0.539957
    MS_TO_KTS   = 1.94384

    speeds_kts      = []     # successful current-speed readings
    sources         = {}     # per-source status dict returned to template
    direction_deg   = None
    direction_label = None
    temp_c          = None
    hourly_slots    = defaultdict(list)   # {(date_str, hour): [speed_kts, ...]}
    hourly_dirs     = {}                  # {(date_str, hour): dir_label}
    now_hhmm        = now_local.hour * 100 + now_local.minute

    # ── Source 1: wttr.in ─────────────────────────────────────────────────────
    try:
        req = urllib.request.Request(
            "https://wttr.in/Cabedelo,Brazil?format=j1",
            headers={"User-Agent": "PersonalLifeOS/1.0"},
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        cur = data["current_condition"][0]
        spd = round(float(cur["windspeedKmph"]) * KMPH_TO_KTS, 1)
        sources["wttr.in"]  = {"speed_kts": spd, "ok": True}
        speeds_kts.append(spd)
        direction_deg   = int(cur["winddirDegree"])
        direction_label = cur["winddir16Point"]
        temp_c          = float(cur["temp_C"])
        # Collect 3-hour forecast slots
        for day_data in data["weather"][:2]:
            date_str = day_data["date"]
            for slot in day_data.get("hourly", []):
                slot_time = int(slot["time"])
                hour      = slot_time // 100
                if date_str == str(today) and slot_time < now_hhmm:
                    continue
                slot_spd = round(float(slot["windspeedKmph"]) * KMPH_TO_KTS, 1)
                key = (date_str, hour)
                hourly_slots[key].append(slot_spd)
                hourly_dirs.setdefault(key, slot["winddir16Point"])
    except Exception as exc:
        sources["wttr.in"] = {"ok": False, "error": str(exc)[:80]}

    # ── Source 2: Open-Meteo ──────────────────────────────────────────────────
    # current_weather=true gives current speed; hourly gives 1-h resolution.
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={LAT}&longitude={LON}"
            f"&current_weather=true"
            f"&hourly=windspeed_10m,winddirection_10m"
            f"&wind_speed_unit=kn"
            f"&timezone=America%2FFortaleza"
            f"&forecast_days=2"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "PersonalLifeOS/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        cw  = data["current_weather"]
        spd = round(float(cw["windspeed"]), 1)   # already in knots
        sources["open-meteo"] = {"speed_kts": spd, "ok": True}
        speeds_kts.append(spd)
        if direction_deg is None:
            direction_deg = int(cw.get("winddirection", 0))
        # Collect 1-hour forecast slots
        times  = data["hourly"]["time"]
        speeds = data["hourly"]["windspeed_10m"]
        dirs   = data["hourly"].get("winddirection_10m", [])
        for i, (ts_str, h_spd) in enumerate(zip(times, speeds)):
            dt       = _dt.fromisoformat(ts_str)
            date_str = dt.date().isoformat()
            hour     = dt.hour
            if date_str == str(today) and dt.hour * 100 + dt.minute < now_hhmm:
                continue
            key = (date_str, hour)
            hourly_slots[key].append(round(float(h_spd), 1))
            if key not in hourly_dirs and dirs:
                try:
                    hourly_dirs[key] = _deg_to_compass(int(dirs[i]))
                except Exception:
                    pass
    except Exception as exc:
        sources["open-meteo"] = {"ok": False, "error": str(exc)[:80]}

    # ── Source 3: Windguru (spot 57134 — Cabedelo, PB) ───────────────────────
    # Internal iapi — public read-only for listed spots; WINDSPD in m/s.
    try:
        req = urllib.request.Request(
            "https://www.windguru.cz/int/iapi.php?q=forecast&id_spot=57134&lang=en",
            headers={
                "User-Agent":        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Referer":           "https://www.windguru.cz/57134",
                "X-Requested-With":  "XMLHttpRequest",
            },
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        windspd_arr = data.get("WINDSPD", [])
        if not windspd_arr:
            raise ValueError("Empty WINDSPD array in response")
        # Slot 0 = nearest forecast hour; convert m/s → knots
        spd = round(float(windspd_arr[0]) * MS_TO_KTS, 1)
        sources["windguru"] = {"speed_kts": spd, "ok": True}
        speeds_kts.append(spd)
        # Windguru also provides SMER (direction degrees) and HOURS arrays
        hours_arr = data.get("hours", [])
        smer_arr  = data.get("SMER", [])
        for i, (wg_hour, wg_spd) in enumerate(zip(hours_arr, windspd_arr)):
            try:
                wg_dt    = _dt.fromisoformat(str(wg_hour)) if isinstance(wg_hour, str) else None
            except Exception:
                wg_dt = None
            if wg_dt is None:
                continue
            date_str = wg_dt.date().isoformat()
            hour     = wg_dt.hour
            if date_str == str(today) and wg_dt.hour * 100 < now_hhmm:
                continue
            key = (date_str, hour)
            hourly_slots[key].append(round(float(wg_spd) * MS_TO_KTS, 1))
            if key not in hourly_dirs and smer_arr and i < len(smer_arr):
                try:
                    hourly_dirs[key] = _deg_to_compass(int(smer_arr[i]))
                except Exception:
                    pass
    except Exception as exc:
        sources["windguru"] = {"ok": False, "error": str(exc)[:80]}

    # ── Source 4: wind.com ────────────────────────────────────────────────────
    # NOTE: wind.com API endpoint/format is unconfirmed — fails gracefully.
    # Update WIND_COM_URL and the parsing block below once confirmed.
    WIND_COM_URL = f"https://api.wind.com/v1/forecast?lat={LAT}&lon={LON}&units=kt"
    try:
        req = urllib.request.Request(
            WIND_COM_URL, headers={"User-Agent": "PersonalLifeOS/1.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        # Attempt common response shapes; extend as API format is confirmed
        spd = (
            data.get("wind_speed_kts")
            or data.get("windspeed")
            or (data.get("current") or {}).get("wind_speed_kts")
        )
        if spd is None:
            raise ValueError(f"Unrecognised response shape: {list(data.keys())[:6]}")
        spd = round(float(spd), 1)
        sources["wind.com"] = {"speed_kts": spd, "ok": True}
        speeds_kts.append(spd)
    except Exception as exc:
        sources["wind.com"] = {"ok": False, "error": str(exc)[:80]}

    # ── Average current speed ─────────────────────────────────────────────────
    avg_speed = round(sum(speeds_kts) / len(speeds_kts), 1) if speeds_kts else None

    # ── Kite status from averaged speed ───────────────────────────────────────
    if avg_speed is None:
        kite_status = "FEED ERR"
    elif avg_speed >= 18:
        kite_status = "STRONG"
    elif avg_speed >= 14:
        kite_status = "OPTIMAL"
    elif avg_speed >= 10:
        kite_status = "MARGINAL"
    else:
        kite_status = "INSUFFICIENT"

    # ── Averaged hourly forecast (sorted, capped at 16 slots) ────────────────
    hourly_wind = []
    for key in sorted(hourly_slots.keys()):
        date_str, hour = key
        slot_speeds = hourly_slots[key]
        avg_slot    = round(sum(slot_speeds) / len(slot_speeds), 1)
        hourly_wind.append({
            "label":      f"{hour:02d}:00",
            "date":       date_str,
            "speed_kts":  avg_slot,
            "dir":        hourly_dirs.get(key, "—"),
            "n_sources":  len(slot_speeds),
        })
        if len(hourly_wind) >= 16:
            break

    return {
        "speed_kts":       avg_speed,
        "direction_deg":   direction_deg,
        "direction_label": direction_label,
        "temp_c":          temp_c,
        "kite_status":     kite_status,
        "hourly":          hourly_wind,
        "sources":         sources,
        "n_sources_ok":    len(speeds_kts),
        "error":           None if speeds_kts else "All wind sources failed",
    }


def _deg_to_compass(deg: int) -> str:
    """Convert wind direction degrees to 16-point compass label."""
    labels = [
        "N","NNE","NE","ENE","E","ESE","SE","SSE",
        "S","SSW","SW","WSW","W","WNW","NW","NNW",
    ]
    return labels[round(deg / 22.5) % 16]


def _get_terminal_extra(today):
    """Extra context only needed for the Bloomberg terminal view."""
    extra = {}

    # ── Wind telemetry — multi-source averaged ────────────────────────────────
    from zoneinfo import ZoneInfo
    brt       = ZoneInfo("America/Fortaleza")
    now_local = timezone.localtime().astimezone(brt)
    try:
        extra["wind"] = _fetch_wind_multi_source(today, now_local)
    except Exception as exc:
        extra["wind"] = {"error": str(exc), "speed_kts": None, "kite_status": "FEED ERR", "hourly": [], "sources": {}, "n_sources_ok": 0}

    # ── Planner: today's tasks + this week's sessions ──────────────────────
    try:
        from planner.models import DailyTask, WeeklyPlan, PlannedSession
        tasks_today = list(DailyTask.objects.filter(date=today))
        total_energy    = sum(t.energy_cost for t in tasks_today)
        used_energy     = sum(t.energy_cost for t in tasks_today if t.completed)
        cat_counts = {}
        for t in tasks_today:
            cat_counts[t.category] = cat_counts.get(t.category, 0) + 1

        week_start = today - timedelta(days=today.weekday())
        week_end   = week_start + timedelta(days=7)
        current_plan = WeeklyPlan.objects.filter(
            week_start=week_start
        ).order_by('-generated_at').first()

        sessions = list(
            PlannedSession.objects.filter(
                start_at__date__gte=week_start,
                start_at__date__lt=week_end,
            ).select_related('habit').order_by('start_at')[:30]
        )
        extra["planner"] = {
            "tasks_today": tasks_today,
            "total_energy": total_energy,
            "used_energy": used_energy,
            "cat_counts": cat_counts,
            "current_plan": current_plan,
            "sessions_this_week": sessions,
            "error": None,
        }
    except Exception as exc:
        extra["planner"] = {
            "tasks_today": [], "total_energy": 0, "used_energy": 0,
            "cat_counts": {}, "current_plan": None, "sessions_this_week": [],
            "error": str(exc),
        }

    return extra


def _render_terminal(request, active_tab):
    context = _get_base_context()
    context['active_tab'] = active_tab
    context.update(_get_terminal_extra(timezone.localdate()))
    return render(request, 'terminal.html', context)


def terminal(request):
    return _render_terminal(request, active_tab='dashboard')


def terminal_habits(request):
    return _render_terminal(request, active_tab='habits')


def terminal_calendar(request):
    return _render_terminal(request, active_tab='calendar')


def terminal_analytics(request):
    return _render_terminal(request, active_tab='analytics')
