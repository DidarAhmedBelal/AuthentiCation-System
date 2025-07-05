from rest_framework import serializers
from .models import Plan

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id',
            'title',
            'description',
            'plan_type',
            'date',
            'time',
            'is_pinned',
            'created_at',
        ]
        read_only_fields = ['created_at']
