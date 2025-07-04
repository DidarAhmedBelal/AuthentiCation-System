from rest_framework import serializers
from .models import About

class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = About
        fields = ['id', 'user', 'sport_coach', 'details']
        read_only_fields = ['user'] 
