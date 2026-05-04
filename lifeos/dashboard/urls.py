from django.urls import path
from . import views

urlpatterns = [
    # ── Pages ────────────────────────────────────────────────────────────────
    path('', views.home, name='home'),
    path('dashboard/', views.home, name='dashboard'),
    path('planner/', views.planner, name='planner'),
    path('analytics/', views.analytics, name='analytics'),
    path('activities/', views.activities_list, name='activities_list'),
    path('activities/export/', views.activities_export_csv, name='activities_export'),
    path('activities/bulk/', views.activities_bulk, name='activities_bulk'),

    # ── API (FullCalendar + Chart.js) ─────────────────────────────────────────
    path('api/events/', views.api_events, name='api_events'),
    path('api/events/<int:pk>/', views.api_event_update, name='api_event_update'),
    path('api/analytics/heatmap/', views.api_analytics_heatmap, name='api_heatmap'),
    path('api/analytics/monthly/', views.api_analytics_monthly, name='api_monthly'),
    path('api/analytics/ai-donut/', views.api_analytics_ai_donut, name='api_ai_donut'),
    path('api/analytics/weekly-ai/', views.api_analytics_weekly_ai, name='api_weekly_ai'),
    path('api/analytics/mood/', views.api_analytics_mood, name='api_mood'),
    path('api/analytics/kite/', views.api_analytics_kite, name='api_kite'),
    path('api/analytics/time-distribution/', views.api_analytics_time_distribution, name='api_time_dist'),
    path('api/analytics/habit-streak/', views.api_analytics_habit_streak, name='api_habit_streak'),

    # ── HTMX Partials ─────────────────────────────────────────────────────────
    path('htmx/tide/card/', views.htmx_tide_card, name='htmx_tide_card'),
    path('api/tide/day/', views.api_tide_day, name='api_tide_day'),
    path('htmx/daily-plan/save/', views.htmx_save_daily_plan, name='htmx_save_daily_plan'),
    path('htmx/session/start/', views.htmx_session_start, name='htmx_session_start'),
    path('htmx/session/stop/', views.htmx_session_stop, name='htmx_session_stop'),
    path('htmx/activity/add/', views.htmx_activity_modal, name='htmx_activity_add'),
    path('htmx/activity/conflicts/', views.htmx_activity_conflicts, name='htmx_activity_conflicts'),
    path('htmx/activity/<int:pk>/modal/', views.htmx_activity_modal, name='htmx_activity_modal'),
    path('htmx/activity/save/', views.htmx_activity_save, name='htmx_activity_save'),
    path('htmx/activity/<int:pk>/save/', views.htmx_activity_save, name='htmx_activity_save_pk'),
    path('htmx/activity/<int:pk>/toggle/', views.htmx_toggle_status, name='htmx_toggle_status'),
    path('htmx/activity/<int:pk>/delete/', views.htmx_activity_delete, name='htmx_activity_delete'),
]
