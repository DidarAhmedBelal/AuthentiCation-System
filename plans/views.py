from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Plan
from .serializers import PlanSerializer

class PlanListCreateView(generics.ListCreateAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:  # 🔒 Swagger-safe
            return Plan.objects.none()

        queryset = Plan.objects.filter(user=user).order_by('date')

        start_date = self.request.query_params.get('start')
        end_date = self.request.query_params.get('end')

        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:  # 🔒 Swagger-safe
            return Plan.objects.none()
        return Plan.objects.filter(user=self.request.user)
