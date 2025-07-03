from django.urls import path
from users.views import (
    signup,
    login_view,
    send_otp,
    verify_otp,
    change_password,
    my_profile,
    user_list
)

urlpatterns = [
    # User authentication and registration
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),

    # OTP (One-Time Password) related endpoints
    path('send-otp/', send_otp, name='send_otp'),
    path('verify-otp/', verify_otp, name='verify_otp'),

    # Password management
    path('change-password/', change_password, name='change_password'),

    # User profile and list
    path('profile/', my_profile, name='my_profile'),
    path('users/', user_list, name='user_list'),
]