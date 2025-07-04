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
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
User = get_user_model()


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieves a list of all users.
        Requires authentication.
        Optimized to fetch only needed fields.
        """
        # Example: If you only show id, username, email, first_name, last_name
        # Optimized to only fetch the specified fields
        users = User.objects.all().only('id', 'username', 'email', 'first_name', 'last_name')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieves the authenticated user's profile information.
        Requires authentication.
        """
        # No queryset needed — just serialize request.user
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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
    
class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Sends an OTP to the user's email.
        - First-time request sends OTP immediately.
        - Max 5 OTPs/hour/user.
        - Wait 60 seconds between OTPs.
        """
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.only(
                    'id', 'email', 'otp', 'otp_created_at',
                    'otp_request_count', 'otp_request_reset_time'
                ).get(email=email)

                now = timezone.now()

                # Reset OTP count if more than 1 hour passed
                if not user.otp_request_reset_time or now > user.otp_request_reset_time + timedelta(hours=1):
                    user.otp_request_count = 0
                    user.otp_request_reset_time = now

                # Rate limit: Max 5 OTP/hour
                if user.otp_request_count >= 5:
                    return Response(
                        {'error': 'Too many OTP requests. Try again after 1 hour.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )

                # 60-second wait check (only if OTP was previously sent)
                if user.otp_created_at and now < user.otp_created_at + timedelta(seconds=60):
                    return Response(
                        {'error': 'Please wait 60 seconds before requesting a new OTP.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )

                # Generate and send OTP
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

                return Response({'message': 'OTP sent successfully', 'email': email}, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]  # OTP verification is pre-authentication

    def post(self, request):
        """
        Verifies the provided OTP for a given email.
        Marks the user as verified upon successful verification.
        """
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']

            try:
                # Only fetch relevant fields for performance
                user = User.objects.only('id', 'email', 'otp', 'otp_created_at', 'is_verified').get(email=email, otp=otp)

                # Check OTP expiration (1-minute validity)
                if not user.otp_created_at or timezone.now() > user.otp_created_at + timedelta(minutes=1):
                    return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

                # Mark user as verified and clear OTP
                user.is_verified = True
                user.otp = ''
                user.otp_created_at = None
                # Use update_fields to only save the changed fields
                user.save(update_fields=['is_verified', 'otp', 'otp_created_at'])

                return Response({'message': 'OTP Verified successfully', 'email': email}, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({'error': 'Invalid OTP or email'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Allows an authenticated user to change their password.
        Validates the old password and enforces password policy.
        """
        serializer = ChangePasswordSerializer(data=request.data)
        user = request.user

        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            # Validate old password
            if not user.check_password(old_password):
                return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate new password policy
            try:
                validate_password(new_password, user=user)
            except DjangoValidationError as e:
                # Raise DRF ValidationError to conform to API error handling
                raise ValidationError({'new_password': list(e.messages)})

            # Change password
            user.set_password(new_password)
            # Use update_fields to only save the password field
            user.save(update_fields=["password"])

            full_name = f"{user.first_name} {user.last_name}".strip()
            return Response({'message': 'Password changed successfully', 'full_name': full_name}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)