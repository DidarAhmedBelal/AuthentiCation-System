from rest_framework import viewsets
from .models import Plan
from .serializers import PlanSerializer
from django.utils import timezone

class PlanViewSet(viewsets.ModelViewSet):
    serializer_class = PlanSerializer

    def get_queryset(self):
        queryset = Plan.objects.only('id', 'title', 'date', 'time').order_by('date')
        
        # Optional filtering by future plans only
        show_future = self.request.query_params.get('future')
        if show_future == 'true':
            queryset = queryset.filter(date__gte=timezone.now().date())

        return queryset
