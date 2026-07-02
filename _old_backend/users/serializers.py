from rest_framework import serializers

from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'institution', 'max_concurrent_jobs', 'storage_quota_gb',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'is_active', 'date_joined', 'profile',
        ]
        read_only_fields = fields

    def get_profile(self, obj: User):
        try:
            profile = obj.profile
        except UserProfile.DoesNotExist:
            return None
        return UserProfileSerializer(profile).data
