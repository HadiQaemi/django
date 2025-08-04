from rest_framework import serializers
from django.contrib.auth import get_user_model
from rolepermissions.roles import assign_role

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=["admin", "editor", "viewer"], default="viewer"
    )

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name", "role")

    def create(self, validated_data):
        role = validated_data.pop("role")
        user = User.objects.create_user(**validated_data)

        # Assign role to user
        assign_role(user, role)

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "is_active")
        read_only_fields = ("id", "email", "is_active")
