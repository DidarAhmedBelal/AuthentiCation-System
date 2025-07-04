from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User



class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    Handles user creation with proper password hashing.
    Explicitly defines fields for security and clarity.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'topic',
            'description',
            'password',
            'is_verified',  
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'password': {'write_only': True},
            'is_verified': {'read_only': True},
        }
        ref_name = 'CustomUserSerializer'  

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance   



class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Validates username and password using Django's authenticate function.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")

        data['user'] = user
        return data


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for the login response including JWT tokens.
    """
    message = serializers.CharField()
    username = serializers.CharField()
    access = serializers.CharField()
    refresh = serializers.CharField()


class OTPSerializer(serializers.Serializer):
    """
    Serializer for requesting OTP via email.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """
    Serializer for verifying OTP codes.
    """
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user passwords.
    Requires the old password and a new password.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
