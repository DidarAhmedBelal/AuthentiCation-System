from rest_framework import generics, permissions, serializers 
from .models import About
from .serializers import AboutSerializer

class AboutView(generics.RetrieveUpdateAPIView):
    serializer_class = AboutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        try:
            return user.about 
        except About.DoesNotExist:
            return About.objects.create(user=user)

class AboutCreateView(generics.CreateAPIView):
    serializer_class = AboutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'about'):
            raise serializers.ValidationError("About already exists.")
        serializer.save(user=self.request.user)
