from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import AppVersion
from .serializers import AppVersionUpsertSerializer, CheckVersionRequestSerializer
from .utils.versioning import compare_versions


class AppVersionUpsertView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        platform = request.data.get('platform')
        instance = AppVersion.objects.filter(platform=platform).first()

        serializer = AppVersionUpsertSerializer(
            instance=instance, data=request.data, partial=bool(instance)
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class CheckVersionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        req_serializer = CheckVersionRequestSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)

        platform = req_serializer.validated_data['platform']
        current_version = req_serializer.validated_data['version']

        app_version = AppVersion.objects.filter(platform=platform).first()
        if not app_version:
            return Response({
                "status": "up_to_date",
                "force_update": False,
                "message": None,
            })

        if compare_versions(current_version, app_version.minimum_version) < 0:
            return Response({
                "status": "force_update",
                "force_update": True,
                "message": app_version.force_update_message,
                "store_url": app_version.store_url,
                "latest_version": app_version.latest_version,
            })

        if compare_versions(current_version, app_version.latest_version) < 0:
            return Response({
                "status": "update_available",
                "force_update": False,
                "message": app_version.update_message,
                "store_url": app_version.store_url,
                "latest_version": app_version.latest_version,
            })

        return Response({
            "status": "up_to_date",
            "force_update": False,
            "message": None,
        })
