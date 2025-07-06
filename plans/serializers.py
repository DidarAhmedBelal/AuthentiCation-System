from rest_framework import serializers
from .models import Plan
from chat.models import Chat  # Import Chat model

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
            'chat',
        ]
        read_only_fields = ['created_at', 'chat']

    def validate(self, data):
        user = self.context['request'].user
        current_plan_count = Plan.objects.filter(user=user).count()
        subscription = getattr(user, 'subscription', None)

        max_allowed = subscription.max_plans if subscription and subscription.is_active else 10
        if current_plan_count >= max_allowed:
            raise serializers.ValidationError("You have reached your plan limit. Upgrade your subscription to create more.")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user

        plan = super().create(validated_data)

        if plan.plan_type == 'chat':
            chat = Chat.objects.create()
            chat.participants.add(user)
            chat.save()
            plan.chat = chat
            plan.save()

        return plan
