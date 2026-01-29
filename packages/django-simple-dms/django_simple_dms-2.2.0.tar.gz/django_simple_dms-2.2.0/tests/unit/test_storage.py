"""Tests for configurable storage backend."""

from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage, default_storage
from django.test import override_settings

from django_simple_dms.storage import get_document_storage


class TestGetDocumentStorage:
    """Tests for the get_document_storage function."""

    def test_returns_default_storage_when_setting_not_configured(self):
        """When DMS_DOCUMENT_STORAGE is not set, default_storage should be returned."""
        storage = get_document_storage()

        assert storage is default_storage

    @override_settings(DMS_DOCUMENT_STORAGE=None)
    def test_returns_default_storage_when_setting_is_none(self):
        """When DMS_DOCUMENT_STORAGE is explicitly None, default_storage should be returned."""
        storage = get_document_storage()

        assert storage is default_storage

    @override_settings(DMS_DOCUMENT_STORAGE='django.core.files.storage.InMemoryStorage')
    def test_imports_storage_class_from_string_path(self):
        """When DMS_DOCUMENT_STORAGE is a dotted path string, it should import and instantiate the class."""
        storage = get_document_storage()

        assert isinstance(storage, InMemoryStorage)

    def test_calls_callable_storage_setting(self):
        """When DMS_DOCUMENT_STORAGE is a callable, it should be called to get the storage."""
        custom_storage = InMemoryStorage()

        with override_settings(DMS_DOCUMENT_STORAGE=lambda: custom_storage):
            storage = get_document_storage()

        assert storage is custom_storage

    def test_returns_instance_directly_if_not_callable(self):
        """When DMS_DOCUMENT_STORAGE is already a storage instance, it should be returned directly."""
        custom_storage = InMemoryStorage()

        with override_settings(DMS_DOCUMENT_STORAGE=custom_storage):
            storage = get_document_storage()

        assert storage is custom_storage


class TestDocumentModelWithCustomStorage:
    """Tests for the Document model with custom storage configuration."""

    def test_document_uses_default_storage_by_default(self, db):
        """Document should use default storage when DMS_DOCUMENT_STORAGE is not set."""
        from django_simple_dms.models import Document

        doc = Document()
        doc.document.save('test_default.txt', ContentFile(b'test content'), save=True)

        try:
            assert doc.document.storage is not None
            assert doc.id is not None
        finally:
            Path(doc.document.path).unlink(missing_ok=True)

    def test_document_add_with_custom_storage(self, db, tmp_path, monkeypatch):
        """Document.add() should work correctly with custom storage (InMemoryStorage)."""
        from django_simple_dms.models import Document

        custom_storage = InMemoryStorage()

        # Create a test file to upload
        test_file = tmp_path / 'test_upload.txt'
        test_file.write_text('test content for upload')

        # Monkeypatch the storage on the FileField itself, since the storage callable
        # is evaluated at model class definition time, not at runtime
        monkeypatch.setattr(Document.document.field, 'storage', custom_storage)
        doc = Document.add(document=str(test_file))

        assert doc.id is not None
        # Verify the file exists in the in-memory storage
        assert custom_storage.exists(doc.document.name)
        # Verify content is correct
        with custom_storage.open(doc.document.name) as f:
            content = f.read()
            assert b'test content for upload' in content
