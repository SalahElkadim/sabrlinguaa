from django.contrib import admin
from .models import AppVersion


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = (
        'platform',
        'latest_version',
        'minimum_version',
        'store_url',
        'updated_at',
    )
    list_editable = (
        'latest_version',
        'minimum_version',
    )
    fields = (
        'platform',
        'latest_version',
        'minimum_version',
        'update_message',
        'force_update_message',
        'store_url',
    )
