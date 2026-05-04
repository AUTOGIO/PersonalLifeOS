from django.db import models


class Activity(models.Model):
    CATEGORY_CHOICES = [
        ('MUAY_THAI', 'Muay Thai'),
        ('GYM', 'Gym'),
        ('DOG_TRAINING', 'Dog Training'),
        ('KITESURFING', 'Kitesurfing'),
        ('AI_DEV_CORE', 'AI Dev Core'),
        ('AI_DEV_BUSINESS', 'AI Dev Business'),
        ('AI_DEV_MACOS', 'AI Dev macOS'),
        ('AI_DEV_TOOLS', 'AI Dev Tools'),
        ('SLEEP', 'Sleep'),
        ('CUSTOM', 'Custom'),
    ]
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
        ('SKIPPED', 'Skipped'),
        ('RESCHEDULED', 'Rescheduled'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='CUSTOM')
    scheduled_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            from datetime import datetime, date as date_type
            start = datetime.combine(date_type.today(), self.start_time)
            end = datetime.combine(date_type.today(), self.end_time)
            diff = end - start
            if diff.total_seconds() > 0:
                self.duration_minutes = int(diff.total_seconds() / 60)
        super().save(*args, **kwargs)

    def get_category_color(self):
        colors = {
            'MUAY_THAI': '#dc2626',
            'GYM': '#f97316',
            'DOG_TRAINING': '#22c55e',
            'KITESURFING': '#22c55e',
            'AI_DEV_CORE': '#2563eb',
            'AI_DEV_BUSINESS': '#eab308',
            'AI_DEV_MACOS': '#3b82f6',
            'AI_DEV_TOOLS': '#ec4899',
            'SLEEP': '#1f2937',
            'CUSTOM': '#a855f7',
        }
        return colors.get(self.category, '#6b7280')

    def __str__(self):
        return f"{self.name} ({self.scheduled_date})"

    class Meta:
        ordering = ['scheduled_date', 'start_time']
        verbose_name_plural = 'Activities'


class AIProject(models.Model):
    CATEGORY_CHOICES = [
        ('CORE_OS', 'Core OS'),
        ('BUSINESS_DATA', 'Business Data'),
        ('MACOS_NATIVE', 'macOS Native'),
        ('TOOLS_SCRIPTS', 'Tools & Scripts'),
    ]
    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    github_repo = models.URLField(blank=True, null=True)

    def total_hours(self):
        from django.db.models import Sum
        total = self.sessions.aggregate(total=Sum('duration_minutes'))['total'] or 0
        return round(total / 60, 1)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['priority', 'name']


class ProjectSession(models.Model):
    project = models.ForeignKey(AIProject, on_delete=models.CASCADE, related_name='sessions')
    activity = models.ForeignKey(
        Activity, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            diff = self.end_time - self.start_time
            self.duration_minutes = int(diff.total_seconds() / 60)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project.name} — {self.start_time.date()}"

    class Meta:
        ordering = ['-start_time']


class DailyPlan(models.Model):
    date = models.DateField(unique=True)
    morning_intention = models.TextField(blank=True, default='')
    evening_review = models.TextField(blank=True, default='')
    mood_score = models.IntegerField(null=True, blank=True)
    energy_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plan for {self.date}"

    class Meta:
        ordering = ['-date']


class Habit(models.Model):
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('CUSTOM', 'Custom'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='DAILY')
    target_days = models.JSONField(default=list, help_text='e.g. ["MON","WED"] for Muay Thai')
    streak_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class KiteSession(models.Model):
    date = models.DateField()
    location = models.CharField(max_length=200, default='Cabedelo, PB')
    wind_speed_knots = models.FloatField(null=True, blank=True)
    duration_minutes = models.IntegerField()
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Kite — {self.date} @ {self.wind_speed_knots}kn"

    class Meta:
        ordering = ['-date']


class TelegramReminder(models.Model):
    activity = models.ForeignKey(
        Activity, on_delete=models.SET_NULL, null=True, blank=True, related_name='reminders'
    )
    message = models.TextField()
    remind_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    chat_id = models.CharField(max_length=100)

    def __str__(self):
        return f"Reminder @ {self.remind_at}: {self.message[:50]}"

    class Meta:
        ordering = ['remind_at']


# ── WEEKLY SCHEDULE (Planner v2) ───────────────────────────────────────────────

class ScheduleBlock(models.Model):
    """A fixed, repeating weekly time block derived from the scheduling rule engine."""

    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]
    CATEGORY_CHOICES = [
        ('Core',     'AI Dev — Core OS'),
        ('macOS',    'AI Dev — macOS Native'),
        ('Business', 'AI Dev — Business Data'),
        ('Tools',    'AI Dev — Tools/Scripts'),
        ('Physical', 'Physical'),
        ('Meta',     'Meta / Admin'),
        ('Recovery', 'Recovery'),
    ]

    day_of_week   = models.CharField(max_length=3, choices=DAY_CHOICES)
    activity      = models.CharField(max_length=200)
    start_time    = models.TimeField()
    end_time      = models.TimeField()
    duration_min  = models.IntegerField()
    category      = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_anchor     = models.BooleanField(default=False, help_text='Muay Thai / immovable blocks')
    is_active     = models.BooleanField(default=True)
    notes         = models.TextField(blank=True, default='')

    # Sort order within a day (for display)
    display_order = models.PositiveSmallIntegerField(default=0)

    def get_category_color(self):
        colors = {
            'Core':     '#7c3aed',
            'macOS':    '#3b82f6',
            'Business': '#f59e0b',
            'Tools':    '#ec4899',
            'Physical': '#dc2626',
            'Meta':     '#6b7280',
            'Recovery': '#22c55e',
        }
        return colors.get(self.category, '#6b7280')

    def get_category_icon(self):
        icons = {
            'Core':     'fa-solid fa-brain',
            'macOS':    'fa-brands fa-apple',
            'Business': 'fa-solid fa-chart-line',
            'Tools':    'fa-solid fa-screwdriver-wrench',
            'Physical': 'fa-solid fa-fist-raised',
            'Meta':     'fa-solid fa-clipboard-list',
            'Recovery': 'fa-solid fa-bed',
        }
        return icons.get(self.category, 'fa-solid fa-circle')

    def duration_display(self):
        h, m = divmod(self.duration_min, 60)
        if h and m:
            return f"{h}h {m}min"
        if h:
            return f"{h}h"
        return f"{m}min"

    def __str__(self):
        return f"{self.get_day_of_week_display()} | {self.start_time.strftime('%H:%M')} {self.activity}"

    class Meta:
        ordering = ['day_of_week', 'display_order', 'start_time']
        verbose_name = 'Schedule Block'
        verbose_name_plural = 'Schedule Blocks'


class TideEvent(models.Model):
    TIDE_TYPE_CHOICES = [
        ('HIGH', 'High Tide'),
        ('LOW', 'Low Tide'),
        ('UNKNOWN', 'Unknown'),
    ]
    port_name = models.CharField(max_length=100, default='Porto de Cabedelo')
    date = models.DateField(db_index=True)
    time = models.TimeField()
    datetime_local = models.DateTimeField()
    height_m = models.FloatField()
    tide_type = models.CharField(max_length=10, choices=TIDE_TYPE_CHOICES, default='UNKNOWN')
    source = models.CharField(max_length=200, default='Porto de Cabedelo 2026 tide table')
    timezone = models.CharField(max_length=50, default='America/Fortaleza')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.port_name} {self.date} {self.time} {self.tide_type} {self.height_m}m"

    class Meta:
        ordering = ['date', 'time']
        unique_together = [('port_name', 'date', 'time')]
        verbose_name = 'Tide Event'
        verbose_name_plural = 'Tide Events'
