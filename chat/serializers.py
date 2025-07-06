from rest_framework import serializers
from .models import Chat, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']  
        ref_name = "ChatUserSerializer"  


class ChatSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True, source='participants'
    )

    class Meta:
        model = Chat
        fields = [
            'id',
            'participants',
            'participant_ids',
            'created_at',
            'topic_summary',
            'total_chat_duration'
        ]
        read_only_fields = ['id', 'created_at', 'total_chat_duration']


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    chat = serializers.PrimaryKeyRelatedField(queryset=Chat.objects.all())

    class Meta:
        model = Message
        fields = [
            'id',
            'chat',
            'sender',
            'content',
            'timestamp',
            'is_pinned'
        ]
        read_only_fields = ['id', 'timestamp', 'sender']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['sender'] = request.user
        return super().create(validated_data)



class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
    class Meta: 
        ref_name = "paymentsErrorResponse"