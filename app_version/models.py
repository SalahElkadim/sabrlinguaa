from django.db import models


class AppVersion(models.Model):
    PLATFORM_CHOICES = (
        ('android', 'Android'),
        ('ios', 'iOS'),
    )

    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, unique=True)
    latest_version = models.CharField(max_length=20)
    minimum_version = models.CharField(max_length=20)
    update_message = models.CharField(
        max_length=255,
        blank=True,
        default="يوجد إصدار جديد من التطبيق، برجاء التحديث."
    )
    force_update_message = models.CharField(
        max_length=255,
        blank=True,
        default="يجب تحديث التطبيق للاستمرار في استخدامه."
    )
    store_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.platform} - latest: {self.latest_version} / min: {self.minimum_version}"
