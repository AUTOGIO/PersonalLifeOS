# Reference

Information-oriented lookup for Life OS. Paths are relative to the **`lifeos/`** package root unless noted.

---

## Environment variables

Defined via `python-decouple` in `lifeos/settings.py` (see `.env.example`).

| Variable | Default (if unset) | Purpose |
|----------|---------------------|---------|
| `SECRET_KEY` | Insecure dev default | Django signing; **override in production**. |
| `DEBUG` | `True` | Debug mode; set `False` in production. |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated host list. |
| `DB_NAME` | `db.sqlite3` | SQLite filename under `BASE_DIR`. |
| `TELEGRAM_BOT_TOKEN` | empty | Bot API token. |
| `TELEGRAM_CHAT_ID` | empty | Destination chat for scheduler/bot. |

---

## HTTP routes (dashboard)

Mounted at site root via `lifeos/urls.py` → `dashboard.urls`.

| Path | Name (selected) | Notes |
|------|-----------------|-------|
| `''`, `dashboard/` | `home`, `dashboard` | Main dashboard. |
| `planner/` | `planner` | FullCalendar planner. |
| `analytics/` | `analytics` | Charts. |
| `activities/` | `activities_list` | Table, filters, bulk. |
| `activities/export/` | `activities_export_csv` | CSV download. |
| `activities/bulk/` | `activities_bulk` | POST bulk actions. |
| `api/events/` | `api_events` | Calendar JSON. |
| `api/events/<id>/` | `api_event_update` | PATCH/update event. |
| `api/analytics/heatmap/` | `api_heatmap` | Chart data. |
| `api/analytics/monthly/` | `api_monthly` | Chart data. |
| `api/analytics/ai-donut/` | `api_ai_donut` | Chart data. |
| `api/analytics/weekly-ai/` | `api_weekly_ai` | Chart data. |
| `api/analytics/mood/` | `api_mood` | Chart data. |
| `api/analytics/kite/` | `api_kite` | Chart data. |
| `api/analytics/time-distribution/` | `api_time_dist` | Chart data. |
| `api/analytics/habit-streak/` | `api_habit_streak` | Chart data. |
| `api/tide/day/` | `api_tide_day` | Tide JSON for a day. |
| `htmx/tide/card/` | `htmx_tide_card` | Tide partial. |
| `htmx/daily-plan/save/` | `htmx_save_daily_plan` | Save daily plan fields. |
| `htmx/session/start/`, `htmx/session/stop/` | `htmx_session_start`, `htmx_session_stop` | Project session timer. |
| `htmx/activity/add/`, `htmx/activity/<id>/modal/` | `htmx_activity_add`, `htmx_activity_modal` | Activity modal. |
| `htmx/activity/conflicts/` | `htmx_activity_conflicts` | Overlap check. |
| `htmx/activity/save/`, `htmx/activity/<id>/save/` | `htmx_activity_save` | Create/update activity. |
| `htmx/activity/<id>/toggle/` | `htmx_toggle_status` | Status toggle. |
| `htmx/activity/<id>/delete/` | `htmx_activity_delete` | Delete activity. |

---

## HTTP routes (reminders)

Prefix: `reminders/` (from project `urls.py`).

| Path | Purpose |
|------|---------|
| `reminders/webhook/` | Telegram webhook endpoint (if used). |
| `reminders/status/` | Bot status probe. |

---

## Django admin

| Path | Purpose |
|------|---------|
| `/admin/` | Standard Django admin for models. |

---

## Data model summary

High-level fields; see `dashboard/models.py` for exact definitions.

### Activity

- **category:** `MUAY_THAI`, `GYM`, `DOG_TRAINING`, `KITESURFING`, `AI_DEV_*`, `SLEEP`, `CUSTOM`
- **status:** `PLANNED`, `IN_PROGRESS`, `DONE`, `SKIPPED`, `RESCHEDULED`
- **scheduled_date**, optional **start_time** / **end_time**, auto **duration_minutes** when both times set

### AIProject

- **category:** `CORE_OS`, `BUSINESS_DATA`, `MACOS_NATIVE`, `TOOLS_SCRIPTS`
- **priority:** `HIGH`, `MEDIUM`, `LOW`
- **status:** `ACTIVE`, `PAUSED`, `COMPLETED`
- **github_repo** (optional URL)

### ProjectSession

- **project** → `AIProject`; optional **activity** → `Activity`
- **start_time**, optional **end_time**, **duration_minutes**

### DailyPlan

- Unique **date**; **morning_intention**, **evening_review**; optional **mood_score**, **energy_score**

### Habit

- **frequency:** `DAILY`, `WEEKLY`, `CUSTOM`; **target_days** JSON; **streak_count**, **is_active**

### KiteSession

- **date**, **location**, optional **wind_speed_knots**, **duration_minutes**, **notes**

### TelegramReminder

- Optional **activity**; **message**, **remind_at**, **is_sent**, **chat_id**

### ScheduleBlock

- **day_of_week:** `MON` … `SUN`
- **category:** `Core`, `macOS`, `Business`, `Tools`, `Physical`, `Meta`, `Recovery`
- **activity**, **start_time**, **end_time**, **duration_min**, **is_anchor**, **is_active**, **display_order**, **notes**

### TideEvent

- **port_name**, **date**, **time**, **datetime_local**, **height_m**, **tide_type** (`HIGH` / `LOW` / `UNKNOWN`), **source**, **timezone**
- **unique_together:** `(port_name, date, time)`

---

## Management commands

| Command | Module | Purpose |
|---------|--------|---------|
| `seed_schedule` | `dashboard/management/commands/seed_schedule.py` | Seed AI projects + 30-day activities (`--clear` optional). |
| `seed_weekly_schedule` | `dashboard/management/commands/seed_weekly_schedule.py` | Seed `ScheduleBlock` weekly template. |
| `import_tides` | `dashboard/management/commands/import_tides.py` | Import `TideEvent` from JSON. |
| `validate_tides` | `dashboard/management/commands/validate_tides.py` | Validate tide data integrity. |
| `tui_calendar` | `dashboard/management/commands/tui_calendar.py` | Terminal calendar view. |

---

## Python dependencies

Pinned in `requirements.txt`:

- Django 4.2.11  
- djangorestframework 3.15.1  
- django-htmx 1.17.3  
- python-decouple 3.8  
- requests 2.31.0  
- python-telegram-bot 20.8  
- APScheduler 3.10.4  
- Pillow 10.3.0  

---

## REST framework defaults

From `settings.py`:

- `DEFAULT_PERMISSION_CLASSES`: `AllowAny`
- `DEFAULT_RENDERER_CLASSES`: `JSONRenderer` only

Adjust before any non-local deployment.
