from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import Plan
from .serializers import PlanSerializer


class PlanViewSet(viewsets.ModelViewSet):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            # Return empty queryset for unauthenticated access
            return Plan.objects.none()

        queryset = Plan.objects.filter(user=user).order_by('date')

        start_date = self.request.query_params.get('start')
        end_date = self.request.query_params.get('end')

        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])

        return queryset

    def perform_create(self, serializer):
        """
        Automatically attach the logged-in user to the new plan.
        """
        serializer.save(user=self.request.user)
