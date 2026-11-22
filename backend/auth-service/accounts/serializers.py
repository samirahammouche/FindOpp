
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import FileExtensionValidator
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Organization

User = get_user_model()
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    email = serializers.EmailField()
    organization_name = serializers.CharField(max_length=200, write_only=True)
    organization_type = serializers.ChoiceField(
        choices=Organization.Type.choices,
        write_only=True,
    )
    city = serializers.CharField(max_length=100, write_only=True)
    website = serializers.URLField(max_length=255, write_only=True)
    official_document = serializers.FileField(
        write_only=True,
        validators=[FileExtensionValidator(["pdf", "png", "jpg", "jpeg"])],
    )
    verification_status = serializers.CharField(
        source="organization.verification_status",
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "organization_name",
            "organization_type",
            "city",
            "website",
            "official_document",
            "verification_status",
        ]
        extra_kwargs = {
            "first_name": {"write_only": True},
            "last_name": {"write_only": True},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return value

    def validate_official_document(self, value):
        if value.size > MAX_DOCUMENT_SIZE:
            raise serializers.ValidationError(
                "The supporting document must be 10 MB or smaller."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        organization_data = {
            "name": validated_data.pop("organization_name"),
            "organization_type": validated_data.pop("organization_type"),
            "city": validated_data.pop("city"),
            "website": validated_data.pop("website"),
            "official_document": validated_data.pop("official_document"),
        }
        user = User.objects.create_user(
            **validated_data,
            role=User.Role.ORGANIZER,
            is_active=False,
        )
        Organization.objects.create(organizer=user, **organization_data)
        return user



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "date_joined"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["role"] = user.role
        token["email"] = user.email

        return token
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    def validate_old_password(self, value):
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "The current password is incorrect."
            )

        return value
