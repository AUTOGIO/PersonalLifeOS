from rest_framework import serializers
from .models import Activity, AIProject, ProjectSession, DailyPlan, KiteSession


CATEGORY_COLORS = {
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


class ActivitySerializer(serializers.ModelSerializer):
    color = serializers.SerializerMethodField()
    # FullCalendar-compatible fields
    title = serializers.CharField(source='name', read_only=True)
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = '__all__'

    def get_color(self, obj):
        return CATEGORY_COLORS.get(obj.category, '#6b7280')

    def get_start(self, obj):
        if obj.start_time:
            return f"{obj.scheduled_date}T{obj.start_time}"
        return str(obj.scheduled_date)

    def get_end(self, obj):
        if obj.end_time:
            return f"{obj.scheduled_date}T{obj.end_time}"
        return None


class AIProjectSerializer(serializers.ModelSerializer):
    total_hours = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = AIProject
        fields = '__all__'

    def get_total_hours(self, obj):
        return obj.total_hours()


class ProjectSessionSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = ProjectSession
        fields = '__all__'


class DailyPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPlan
        fields = '__all__'


class KiteSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = KiteSession
        fields = '__all__'
