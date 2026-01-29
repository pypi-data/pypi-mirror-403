from pathlib import Path

import pytest

from testutils.factories import DocumentTagFactory


@pytest.fixture
def document_tags(db):
    return [
        DocumentTagFactory(),
        DocumentTagFactory(),
        DocumentTagFactory(),
    ]


@pytest.fixture
def self_cleaning_add(db):
    from django_simple_dms.models import Document

    _to_delete = []
    original = Document.add

    @classmethod
    def fx(cls, *args, **kwargs):
        result: Document = original(*args, **kwargs)
        if result:
            _to_delete.append(result.document.file.name)
        return result

    Document.add = fx
    yield
    Document.add = original
    for file in _to_delete:
        Path(file).unlink(missing_ok=True)
