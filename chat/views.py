from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from chat.ai_logic import generate_response_from_chat, get_or_create_bot_user

User = get_user_model()


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
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()

        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            return Message.objects.filter(chat_id=chat_id, chat__participants=self.request.user).order_by('timestamp')
        return Message.objects.none()

    def perform_create(self, serializer):
        user_message = serializer.save(sender=self.request.user)
        self.generate_ai_reply(user_message.chat, user_message)

    def generate_ai_reply(self, chat, user_message):
        user = self.request.user
        user_input = user_message.content

        try:
            reply, _ = generate_response_from_chat(chat, user, user_input)
            # AI message already saved inside generate_response_from_chat
        except Exception as e:
            print(f"[LLM ERROR] {e}")


class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        return Message.objects.filter(chat__participants=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_respond(request):
    user = request.user
    chat_id = request.data.get("chat_id")
    user_input = request.data.get("message")

    if not chat_id or not user_input:
        return Response({"error": "chat_id and message are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return Response({"error": "Chat not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        response_text = generate_response_from_chat(chat, user, user_input)
        return Response({"response": response_text}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_with_assistant(request, chat_id):
    user = request.user
    user_input = request.data.get("message")

    if not user_input:
        return Response({"error": "No message provided"}, status=400)

    chat = get_object_or_404(Chat, id=chat_id)

    reply, chat_log = generate_response_from_chat(chat, user, user_input)

    return Response({
        "reply": reply,
        "chat_log": chat_log
    })
