from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes

from drf_yasg.utils import swagger_auto_schema

from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer, ChatBotResponseSerializer, UserSerializer
from chat.ai_logic import generate_response_from_chat
from Game_plan_chatbot.lama import demo_chatbot

User = get_user_model()


# List and create chats for logged-in user
class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Chat.objects.none()
        return Chat.objects.filter(participants=self.request.user)

    def perform_create(self, serializer):
        chat = serializer.save()
        chat.participants.add(self.request.user)


# Retrieve, update, delete chat if user is participant
class ChatDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Chat.objects.none()
        return Chat.objects.filter(participants=self.request.user)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        plan_id = self.kwargs.get('plan_id')
        if plan_id:
            return Message.objects.filter(
                chat__plan_id=plan_id,
                chat__participants=self.request.user
            ).order_by('timestamp')
        return Message.objects.none()

    def perform_create(self, serializer):
        plan_id = self.kwargs.get('plan_id')
        chat_id = self.request.data.get('chat')

        chat = get_object_or_404(Chat, id=chat_id, plan_id=plan_id)

        user_message = serializer.save(sender=self.request.user, chat=chat)
        self.generate_ai_reply(chat, user_message)

    def generate_ai_reply(self, chat, user_message):
        user = self.request.user
        user_input = user_message.content

        try:
            reply, _ = generate_response_from_chat(chat, user, user_input)
        except Exception as e:
            print(f"[AI LOGIC ERROR] {e}")
            reply = demo_chatbot.generate_response(user_input)

        bot_user, _ = User.objects.get_or_create(username="chatbot")
        chat.participants.add(bot_user)
        Message.objects.create(chat=chat, sender=bot_user, content=reply)

# Retrieve, update, or delete individual message
class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        plan_id = self.kwargs.get('plan_id')
        if plan_id:
            return Message.objects.filter(
                chat__plan_id=plan_id,
                chat__participants=self.request.user
            )
        return Message.objects.none()

# Generic view for chatbot interaction (for browsable API form support)
class ChatRespondSerializer(serializers.Serializer):
    chat_id = serializers.IntegerField()
    message = serializers.CharField()


class ChatRespondAPIView(generics.CreateAPIView):
    serializer_class = ChatRespondSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChatRespondSerializer,
        responses={200: ChatBotResponseSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat_id = serializer.validated_data['chat_id']
        message = serializer.validated_data['message']
        user = request.user

        try:
            chat = Chat.objects.prefetch_related('participants').get(id=chat_id)
        except Chat.DoesNotExist:
            return Response({"error": "Chat not found."}, status=404)

        user_msg = Message.objects.create(chat=chat, sender=user, content=message)

        try:
            reply_text, _ = generate_response_from_chat(chat, user, message)
        except Exception as e:
            reply_text = f"[Error generating response]: {e}"

        bot_user, _ = User.objects.get_or_create(username='chatbot')
        chat.participants.add(bot_user)
        bot_msg = Message.objects.create(chat=chat, sender=bot_user, content=reply_text)

        return Response({
            "user": UserSerializer(user).data,
            "user_message": message,
            "bot_response": MessageSerializer(bot_msg).data
        }, status=200)


# # Smart AI chat logic endpoint
# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def chat_with_assistant(request, chat_id):
#     user = request.user
#     user_input = request.data.get("message")

#     if not user_input:
#         return Response({"error": "No message provided."}, status=status.HTTP_400_BAD_REQUEST)

#     chat = get_object_or_404(Chat, id=chat_id, participants=user)

#     try:
#         reply, chat_log = generate_response_from_chat(chat, user, user_input)
#         return Response({
#             "reply": reply,
#             "chat_log": chat_log,
#         }, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from chat.models import Chat, Message
from chat.ai_logic import generate_response_from_chat

User = get_user_model()

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_with_assistant(request, chat_id):
    user = request.user
    user_input = request.data.get("message")
    if not user_input:
        return Response({"error": "No message provided."}, status=status.HTTP_400_BAD_REQUEST)

    # Get the chat ensuring user is a participant
    chat = get_object_or_404(Chat, id=chat_id, participants=user)

    try:
        # Call your AI logic function (returns reply and updated chat text)
        reply, chat_log = generate_response_from_chat(chat, user, user_input)

        # Ensure chatbot user is participant and save messages (already done in ai_logic)
        bot_user, _ = User.objects.get_or_create(username="chatbot")
        if bot_user not in chat.participants.all():
            chat.participants.add(bot_user)

        # Return AI reply and chat log
        return Response({
            "reply": reply,
            "chat_log": chat_log,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"AI logic error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Serializers
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


class ChatBotResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    user_message = serializers.CharField()
    bot_response = MessageSerializer()
