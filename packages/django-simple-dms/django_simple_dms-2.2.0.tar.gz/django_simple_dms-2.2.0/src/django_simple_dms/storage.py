"""Configurable storage backend for Document files.

This module provides a callable storage function that can be configured
via Django settings, allowing users to specify custom storage backends
for document files without requiring migrations.

Usage:
    In your Django settings, set DMS_DOCUMENT_STORAGE to a dotted path
    of a storage class:

    DMS_DOCUMENT_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    If not set, Django's default storage will be used.
"""

from django.conf import settings
from django.core.files.storage import Storage, default_storage
from django.utils.module_loading import import_string


def get_document_storage() -> Storage:
    """Return the storage backend for Document files.

    Looks up the DMS_DOCUMENT_STORAGE setting and returns an instance
    of the specified storage class. If not configured, returns Django's
    default storage.

    Returns:
        A storage instance to be used for Document file uploads.

    """
    storage_setting = getattr(settings, 'DMS_DOCUMENT_STORAGE', None)

    if storage_setting is None:
        return default_storage

    if isinstance(storage_setting, str):
        storage_class = import_string(storage_setting)
        return storage_class()

    # Allow passing an already instantiated storage or a class
    if callable(storage_setting):
        return storage_setting()

    return storage_setting
