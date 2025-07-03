from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import UserSerializer, LoginSerializer, OTPSerializer, VerifyOTPSerializer, ChangePasswordSerializer
import random
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list(request):
    """
    Retrieves a list of all users.
    Requires authentication.
    """
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """
    Handles user registration.
    Allows any user to register.
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        response_data = UserSerializer(user).data
        return Response({
            'message': 'User created successfully',
            'user': response_data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_profile(request):
    """
    Retrieves the authenticated user's profile information.
    Requires authentication.
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Handles user login and provides JWT access and refresh tokens.
    Allows any user to log in.
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Login successful",
            "username": user.username,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """
    Generates and sends an OTP to the user's email for verification.
    Includes rate limiting:
    - Allows a maximum of 5 OTP requests per hour per user.
    - Prevents requesting a new OTP within 60 seconds of the last request.
    """
    serializer = OTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)

            # OTP request rate limiting logic
            if user.otp_request_reset_time is None or timezone.now() > user.otp_request_reset_time + timedelta(hours=1):
                user.otp_request_count = 0
                user.otp_request_reset_time = timezone.now()

            if user.otp_request_count >= 5:
                return Response({'error': 'Too many OTP requests. Please try again after 1 hour.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

            if user.otp_created_at and timezone.now() < user.otp_created_at + timedelta(seconds=60):
                return Response({'error': 'Please wait before requesting a new OTP.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Generate and save OTP
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.otp_request_count += 1
            user.save()

            # Send OTP via email
            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False, # Set to True in production to avoid raising errors for email issues
            )

            return Response({'message': 'OTP sent successfully', 'email': email}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny]) # Changed to AllowAny as OTP verification is usually pre-authentication
def verify_otp(request):
    """
    Verifies the provided OTP for a given email.
    Marks the user as verified upon successful verification.
    """
    serializer = VerifyOTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        try:
            user = User.objects.get(email=email, otp=otp)

            # Check if OTP has expired (1-minute validity)
            if user.otp_created_at and timezone.now() > user.otp_created_at + timedelta(minutes=1):
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

            # Mark user as verified and clear OTP data
            user.is_verified = True
            user.otp = ''
            user.otp_created_at = None
            user.save()
            return Response({'message': 'OTP Verified successfully', 'email': email}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP or email'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Allows an authenticated user to change their password.
    Validates the old password and enforces password policy for the new password.
    """
    serializer = ChangePasswordSerializer(data=request.data)
    user = request.user
    if serializer.is_valid():
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        # Check if the old password is correct
        if not user.check_password(old_password):
            return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the new password against Django's password validation rules
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            # Raise a DRF ValidationError to return proper error messages
            raise ValidationError({'new_password': list(e.messages)})

        # Set the new password and save the user
        user.set_password(new_password)
        user.save()

        full_name = f"{user.first_name} {user.last_name}".strip()

        return Response({'message': 'Password changed successfully', 'full_name': full_name}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)