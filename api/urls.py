from django.urls import path
from users.views import (
    SignupView,
    LoginView,
    SendOTPView,
    VerifyOTPView,
    ChangePasswordView,
    MyProfileView,
    UserListView,
)

urlpatterns = [
    # User authentication and registration
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),

    # OTP (One-Time Password) related endpoints
    path('send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),

    # Password management
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    # User profile and list
    path('profile/', MyProfileView.as_view(), name='my_profile'),
    path('users/', UserListView.as_view(), name='user_list'),
]
