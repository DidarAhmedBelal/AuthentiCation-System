from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import transaction
from .models import Plan
from .serializers import PlanSerializer
from chat.models import Chat

class PlanListCreateView(generics.ListCreateAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Plan.objects.none()

        queryset = Plan.objects.filter(user=user).order_by('date')
        start_date = self.request.query_params.get('start')
        end_date = self.request.query_params.get('end')

        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        plan_count = Plan.objects.filter(user=user).count()
        subscription = getattr(user, 'subscription', None)
        max_plans = subscription.max_plans if subscription and subscription.is_active else 10

        if plan_count >= max_plans:
            raise ValidationError("Plan limit reached. Please upgrade your subscription.")

        with transaction.atomic():
            chat = None
            if serializer.validated_data.get("plan_type") == "chat":
                chat = Chat.objects.create()
                chat.participants.add(user)

            serializer.save(user=user, chat=chat)

class PlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Plan.objects.none()
        return Plan.objects.filter(user=self.request.user)
