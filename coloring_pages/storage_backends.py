from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class MediaStorage(S3Boto3Storage):
    """
    Custom storage backend for storing media files in S3.
    """
    location = 'media'
    file_overwrite = False
    default_acl = 'public-read'
    
    def __init__(self, *args, **kwargs):
        kwargs['bucket_name'] = settings.AWS_STORAGE_BUCKET_NAME
        kwargs['region_name'] = settings.AWS_S3_REGION_NAME
        super().__init__(*args, **kwargs)


class StaticStorage(S3Boto3Storage):
    """
    Custom storage backend for storing static files in S3.
    """
    location = 'static'
    default_acl = 'public-read'
    
    def __init__(self, *args, **kwargs):
        kwargs['bucket_name'] = settings.AWS_STORAGE_BUCKET_NAME
        kwargs['region_name'] = settings.AWS_S3_REGION_NAME
        super().__init__(*args, **kwargs)
