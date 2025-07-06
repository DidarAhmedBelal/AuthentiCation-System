from rest_framework import serializers

class CheckoutRequestSerializer(serializers.Serializer):
    price_id = serializers.CharField()

class TestSerializer(serializers.Serializer): 
    id = serializers.CharField()

class StripeSessionResponseSerializer(serializers.Serializer):
    sessionId = serializers.CharField()

class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
