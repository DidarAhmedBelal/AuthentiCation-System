from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import (
    SignupView,
    LoginView,
    SendOTPView,
    VerifyOTPView,
    ChangePasswordView,
    MyProfileView,
    UserList
)
from chat.views import (
    ChatListCreateView,
    ChatDetailView,
    MessageListCreateView,
    MessageDetailView,
)
from plans.views import PlanListCreateView, PlanDetailView

router = DefaultRouter()
router.register('users', UserList, basename='user-admin')

urlpatterns = [
    path('', include(router.urls)),

    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),

    path('send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),

    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    path('profile/', MyProfileView.as_view(), name='my_profile'),

    path('chat-history/', ChatListCreateView.as_view(), name='chat-list-create'),
    path('chat-history/<int:pk>/', ChatDetailView.as_view(), name='chat-detail'),
    path('chat-detail/', MessageListCreateView.as_view(), name='message-list-create'),
    path('chat-detail/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),

    path('plans/', PlanListCreateView.as_view(), name='plan-list-create'),
    path('plans/<int:pk>/', PlanDetailView.as_view(), name='plan-detail'),
]
