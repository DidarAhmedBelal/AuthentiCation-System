from django.urls import path, include
from rest_framework.routers import DefaultRouter

# --- User
from users.views import (
    SignupView, LoginView, SendOTPView, VerifyOTPView,
    ChangePasswordView, MyProfileView, UserList, CustomTokenObtainPairView,
)

# --- Chat
from chat.views import (
    ChatListCreateView, ChatDetailView,
    MessageListCreateView, MessageDetailView,
    chat_with_assistant, ChatRespondAPIView
)

# --- Plans
from plans.views import PlanListCreateView, PlanDetailView

# --- About
from about.views import AboutView, AboutCreateView

# --- Payments
from payments.views import (
    CreateCheckoutSessionView, StripeWebhookView, CancelSubscriptionView
)

# --- Admin/User Router
router = DefaultRouter()
router.register('users', UserList, basename='user-admin')

urlpatterns = [
    path('', include(router.urls)),

    # 🔐 Auth + Profile
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('profile/', MyProfileView.as_view(), name='my_profile'),

    # 💬 Chat
    path('chats/', ChatListCreateView.as_view(), name='chat-list-create'),
    path('chats/<int:pk>/', ChatDetailView.as_view(), name='chat-detail'),

    # 💬 Messages
    path('messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),

    # 🤖 AI Chatbot
    path('chat-respond/', ChatRespondAPIView.as_view(), name='chat-respond'),
    path("bot/<int:chat_id>/", chat_with_assistant, name="chat-with-assistant"),

    # 📅 Plans
    path('plans/', PlanListCreateView.as_view(), name='plan-list-create'),
    path('plans/<int:pk>/', PlanDetailView.as_view(), name='plan-detail'),

    # 👤 About
    path('about/', AboutView.as_view(), name='user-about'),
    path('about/create/', AboutCreateView.as_view(), name='about-create'),

    # 💳 Payments
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create_checkout_session'),
    path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('cancel-subscription/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
]
