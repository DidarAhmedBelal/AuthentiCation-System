from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    Handles user creation (signup).
    """
    class Meta:
        model = User
        # Fields to be included in the serialization/deserialization
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        # Extra keyword arguments for specific fields
        extra_kwargs = {
            'password': {'write_only': True}  # Password should only be written, not read back
        }

    def create(self, validated_data):
        """
        Custom create method to handle password hashing when creating a new user.
        Uses Django's built-in create_user method for proper password management.
        """
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Validates username and password using Django's authenticate function.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)  # Password should only be written

    def validate(self, data):
        """
        Custom validation method to authenticate the user.
        Raises a ValidationError if authentication fails.
        """
        username = data.get('username')
        password = data.get('password')

        # Authenticate user using Django's built-in authentication system
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        # Attach the authenticated user object to the validated data
        data['user'] = user
        return data


class OTPSerializer(serializers.Serializer):
    """
    Serializer for sending OTP requests.
    Requires only the user's email.
    """
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    """
    Serializer for verifying OTPs.
    Requires the user's email and the OTP code.
    """
    email = serializers.EmailField()
    otp = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user passwords.
    Requires the old password and the new password.
    """
    old_password = serializers.CharField()
    new_password = serializers.CharField()