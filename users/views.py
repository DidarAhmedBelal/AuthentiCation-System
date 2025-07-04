from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.generics import (
    GenericAPIView,
    CreateAPIView,
    RetrieveAPIView,
    ListAPIView
)
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema
import random
from datetime import timedelta
from rest_framework import viewsets

from .serializers import (
    UserSerializer,
    LoginSerializer,
    LoginResponseSerializer,
    OTPSerializer,
    VerifyOTPSerializer,
    ChangePasswordSerializer
)

User = get_user_model()



class UserList(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class SignupView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            'message': 'User created successfully',
            'user': response.data
        }, status=status.HTTP_201_CREATED)


class MyProfileView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
        description="Login endpoint returning access and refresh JWT tokens."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful",
            "username": user.username,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)


class SendOTPView(GenericAPIView):
    serializer_class = OTPSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.only(
                'id', 'email', 'otp', 'otp_created_at',
                'otp_request_count', 'otp_request_reset_time'
            ).get(email=email)

            now = timezone.now()
            if not user.otp_request_reset_time or now > user.otp_request_reset_time + timedelta(hours=1):
                user.otp_request_count = 0
                user.otp_request_reset_time = now

            if user.otp_request_count >= 5:
                return Response({'error': 'Too many OTP requests. Try again after 1 hour.'}, status=429)

            if user.otp_created_at and now < user.otp_created_at + timedelta(seconds=60):
                return Response({'error': 'Please wait 60 seconds before requesting a new OTP.'}, status=429)

            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.otp_created_at = now
            user.otp_request_count += 1
            user.save(update_fields=['otp', 'otp_created_at', 'otp_request_count', 'otp_request_reset_time'])

            try:
                send_mail(
                    subject='Your OTP Code',
                    message=f'Your OTP code is {otp}',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False
                )
            except Exception as e:
                return Response({'error': 'Email Failed', 'detail': str(e)}, status=500)

            return Response({'message': 'OTP sent successfully', 'email': email}, status=200)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


class VerifyOTPView(GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.only('id', 'email', 'otp', 'otp_created_at', 'is_verified').get(email=email, otp=otp)
            if not user.otp_created_at or timezone.now() > user.otp_created_at + timedelta(minutes=1):
                return Response({'error': 'OTP has expired'}, status=400)

            user.is_verified = True
            user.otp = ''
            user.otp_created_at = None
            user.save(update_fields=['is_verified', 'otp', 'otp_created_at'])

            return Response({'message': 'OTP Verified successfully', 'email': email}, status=200)

        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP or email'}, status=400)


class ChangePasswordView(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        user = request.user

        if not user.check_password(old_password):
            return Response({'error': 'Old password is incorrect'}, status=400)

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            raise ValidationError({'new_password': list(e.messages)})

        user.set_password(new_password)
        user.save(update_fields=["password"])

        full_name = f"{user.first_name} {user.last_name}".strip()
        return Response({'message': 'Password changed successfully', 'full_name': full_name}, status=200)