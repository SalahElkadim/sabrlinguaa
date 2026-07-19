from rest_framework import serializers
from .models import AppVersion


class AppVersionUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = [
            'platform', 'latest_version', 'minimum_version',
            'update_message', 'force_update_message', 'store_url',
        ]


class CheckVersionRequestSerializer(serializers.Serializer):
    platform = serializers.ChoiceField(choices=AppVersion.PLATFORM_CHOICES)
    version = serializers.CharField(max_length=20)
