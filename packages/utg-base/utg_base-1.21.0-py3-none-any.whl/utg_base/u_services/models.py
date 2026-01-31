from urllib.parse import urljoin

from django.db import models

from utg_base.env import env


class UServiceManager(models.Manager):
    def get_queryset(self):
        if env('DB_NAME') == 'uztransgaz':
            return super().get_queryset()
        return super().get_queryset().using('uztransgaz')


class UService(models.Model):
    class Type(models.TextChoices):
        FILE_UPLOAD = 'FILE_UPLOAD'
        API_INTEGRATION = 'API_INTEGRATION'
        ADMIN = 'ADMIN'

    objects = UServiceManager()
    name = models.CharField(max_length=255)
    title_translate_key = models.CharField(max_length=255)
    logo = models.FileField(upload_to='media/logo')
    type = models.CharField(max_length=20, choices=Type.choices)
    ip = models.GenericIPAddressField()
    port = models.PositiveSmallIntegerField()

    def get_url(self, prefix: str):
        return urljoin(f'http://{self.ip}:{self.port}', prefix)

    def get_file_upload_status_url(self):
        return self.get_url('/api/file-upload-status/')

    def get_external_api_status_url(self):
        return self.get_url('/api/admin/external-api/status/')

    @staticmethod
    def get_by_name(name: str):
        return UService.objects.filter(name=name).first()

    class Meta:
        ordering = ['name']
        app_label = 'u_services'
