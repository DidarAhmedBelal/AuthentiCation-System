# from django.conf import settings
# from django.shortcuts import get_object_or_404
# from django.contrib.auth import get_user_model

# from rest_framework import generics, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.decorators import api_view, permission_classes

# from .models import Chat, Message
# from .serializers import ChatSerializer, MessageSerializer
# from chat.ai_logic import generate_response_from_chat  # Assuming you want to use this for smart AI logic

# from Game_plan_chatbot.lama import demo_chatbot  # Simple fallback chatbot logic

# User = get_user_model()

# # ✅ List all chats for logged-in user or create a new one
# class ChatListCreateView(generics.ListCreateAPIView):
#     serializer_class = ChatSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if getattr(self, 'swagger_fake_view', False):
#             return Chat.objects.none()
#         return Chat.objects.filter(participants=self.request.user)

#     def perform_create(self, serializer):
#         chat = serializer.save()
#         chat.participants.add(self.request.user)


# # ✅ Retrieve, update, or delete a chat (if user is a participant)
# class ChatDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = ChatSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if getattr(self, 'swagger_fake_view', False):
#             return Chat.objects.none()
#         return Chat.objects.filter(participants=self.request.user)


# # ✅ List messages or create user message → AI auto replies
# class MessageListCreateView(generics.ListCreateAPIView):
#     serializer_class = MessageSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if getattr(self, 'swagger_fake_view', False):
#             return Message.objects.none()

#         chat_id = self.request.query_params.get('chat_id')
#         if chat_id:
#             return Message.objects.filter(chat_id=chat_id, chat__participants=self.request.user).order_by('timestamp')
#         return Message.objects.none()

#     def perform_create(self, serializer):
#         user_message = serializer.save(sender=self.request.user)
#         self.generate_ai_reply(user_message.chat, user_message)

#     def generate_ai_reply(self, chat, user_message):
#         user = self.request.user
#         user_input = user_message.content

#         try:
#             reply, _ = generate_response_from_chat(chat, user, user_input)
#             # Save AI reply
#             bot_user, _ = User.objects.get_or_create(username="chatbot")
#             chat.participants.add(bot_user)
#             Message.objects.create(chat=chat, sender=bot_user, content=reply)
#         except Exception as e:
#             print(f"[LLM ERROR] {e}")


# # ✅ Get, update, delete individual message
# class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = MessageSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if getattr(self, 'swagger_fake_view', False):
#             return Message.objects.none()
#         return Message.objects.filter(chat__participants=self.request.user)


# # ✅ Lightweight fallback AI response — demo_chatbot based
# class ChatRespondAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = request.user
#         chat_id = request.data.get("chat_id")
#         message = request.data.get("message")

#         if not chat_id or not message:
#             return Response({"error": "chat_id and message are required."}, status=400)

#         # Get chat and verify participant
#         try:
#             chat = Chat.objects.prefetch_related('participants').get(id=chat_id)
#             # if user not in chat.participants.all():
#             #     return Response({"error": "You are not a participant in this chat."}, status=403)
#         except Chat.DoesNotExist:
#             return Response({"error": "No Chat matches the given query."}, status=404)

#         # Save user message
#         Message.objects.create(chat=chat, sender=user, content=message)

#         # AI reply using demo chatbot
#         bot_response = demo_chatbot.generate_response(message)

#         # Save bot reply
#         bot_user, _ = User.objects.get_or_create(username='chatbot')
#         chat.participants.add(bot_user)
#         Message.objects.create(chat=chat, sender=bot_user, content=bot_response)

#         return Response({
#             "user_message": message,
#             "bot_response": bot_response
#         }, status=200)


# # ✅ Smart AI chat logic (e.g. logs, memory etc.)
# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def chat_with_assistant(request, chat_id):
#     user = request.user
#     user_input = request.data.get("message")

#     if not user_input:
#         return Response({"error": "No message provided"}, status=400)

#     chat = get_object_or_404(Chat, id=chat_id, participants=user)

#     try:
#         reply, chat_log = generate_response_from_chat(chat, user, user_input)
#         return Response({
#             "reply": reply,
#             "chat_log": chat_log
#         })
#     except Exception as e:
#         return Response({"error": str(e)}, status=500)





from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from chat.ai_logic import generate_response_from_chat  # Your smart AI chat logic function
from chat.ai_logic import generate_response_from_chat

User = get_user_model()


# List and create chats for logged-in user
class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Swagger UI workaround (if used)
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


# List messages and create user messages which trigger AI replies
class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()

        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            # Only show messages for chats user participates in
            return Message.objects.filter(chat_id=chat_id, chat__participants=self.request.user).order_by('timestamp')
        return Message.objects.none()

    def perform_create(self, serializer):
        user_message = serializer.save(sender=self.request.user)
        self.generate_ai_reply(user_message.chat, user_message)

    def generate_ai_reply(self, chat, user_message):
        user = self.request.user
        user_input = user_message.content

        try:
            # Use your smart AI logic to generate a reply
            reply, _ = generate_response_from_chat(chat, user, user_input)
            bot_user, _ = User.objects.get_or_create(username="chatbot")
            chat.participants.add(bot_user)  # Ensure bot is participant
            Message.objects.create(chat=chat, sender=bot_user, content=reply)
        except Exception as e:
            print(f"[AI LOGIC ERROR] {e}")
            # Optionally, fallback to demo chatbot
            bot_response = demo_chatbot.generate_response(user_input)
            bot_user, _ = User.objects.get_or_create(username="chatbot")
            chat.participants.add(bot_user)
            Message.objects.create(chat=chat, sender=bot_user, content=bot_response)


# Retrieve, update, or delete individual message
class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        return Message.objects.filter(chat__participants=self.request.user)


# Lightweight fallback AI response endpoint using demo_chatbot
class ChatRespondAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        chat_id = request.data.get("chat_id")
        message = request.data.get("message")

        if not chat_id or not message:
            return Response({"error": "chat_id and message are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            chat = Chat.objects.prefetch_related('participants').get(id=chat_id)
        except Chat.DoesNotExist:
            return Response({"error": "Chat not found."}, status=status.HTTP_404_NOT_FOUND)

        # # Optional: check user is participant
        # if user not in chat.participants.all():
        #     return Response({"error": "You are not a participant in this chat."}, status=status.HTTP_403_FORBIDDEN)

        # Save user message
        Message.objects.create(chat=chat, sender=user, content=message)

        # Generate bot response using fallback simple chatbot
        try:
            bot_response, _ = generate_response_from_chat(chat, user, message)
        except Exception as e:
            bot_response = f"[Error generating response]: {e}"


        # Save bot reply
        bot_user, _ = User.objects.get_or_create(username='chatbot')
        chat.participants.add(bot_user)
        Message.objects.create(chat=chat, sender=bot_user, content=bot_response)

        return Response({
            "user_message": message,
            "bot_response": bot_response,
        }, status=status.HTTP_200_OK)


# Smart AI chat endpoint using your advanced AI logic
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_with_assistant(request, chat_id):
    user = request.user
    user_input = request.data.get("message")

    if not user_input:
        return Response({"error": "No message provided."}, status=status.HTTP_400_BAD_REQUEST)

    chat = get_object_or_404(Chat, id=chat_id, participants=user)

    try:
        reply, chat_log = generate_response_from_chat(chat, user, user_input)
        return Response({
            "reply": reply,
            "chat_log": chat_log,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
