from django.contrib import admin
from .models import (
    Activity, AIProject, ProjectSession,
    DailyPlan, Habit, KiteSession, TelegramReminder,
    ScheduleBlock, TideEvent,
)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'scheduled_date', 'start_time', 'end_time', 'status', 'duration_minutes')
    list_filter = ('category', 'status', 'scheduled_date')
    search_fields = ('name', 'notes')
    list_editable = ('status',)
    date_hierarchy = 'scheduled_date'
    ordering = ('scheduled_date', 'start_time')


@admin.register(AIProject)
class AIProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'priority', 'status', 'github_repo')
    list_filter = ('category', 'priority', 'status')
    search_fields = ('name',)


@admin.register(ProjectSession)
class ProjectSessionAdmin(admin.ModelAdmin):
    list_display = ('project', 'start_time', 'end_time', 'duration_minutes', 'activity')
    list_filter = ('project', 'start_time')
    search_fields = ('project__name', 'notes')
    raw_id_fields = ('activity',)


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ('date', 'mood_score', 'energy_score', 'created_at')
    list_filter = ('mood_score', 'energy_score')
    search_fields = ('morning_intention', 'evening_review')


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'frequency', 'streak_count', 'is_active')
    list_filter = ('frequency', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)


@admin.register(KiteSession)
class KiteSessionAdmin(admin.ModelAdmin):
    list_display = ('date', 'location', 'wind_speed_knots', 'duration_minutes')
    list_filter = ('location',)
    search_fields = ('location', 'notes')


@admin.register(TelegramReminder)
class TelegramReminderAdmin(admin.ModelAdmin):
    list_display = ('remind_at', 'message', 'is_sent', 'chat_id', 'activity')
    list_filter = ('is_sent', 'remind_at')
    search_fields = ('message',)


@admin.register(TideEvent)
class TideEventAdmin(admin.ModelAdmin):
    list_display = ('port_name', 'date', 'time', 'tide_type', 'height_m', 'source')
    list_filter = ('port_name', 'tide_type', 'date')
    search_fields = ('port_name', 'source')
    date_hierarchy = 'date'
    ordering = ('-date', 'time')


@admin.register(ScheduleBlock)
class ScheduleBlockAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'activity', 'start_time', 'end_time', 'duration_min', 'category', 'is_anchor', 'is_active')
    list_filter = ('day_of_week', 'category', 'is_anchor', 'is_active')
    search_fields = ('activity', 'notes')
    list_editable = ('is_active',)
    ordering = ('day_of_week', 'display_order', 'start_time')

