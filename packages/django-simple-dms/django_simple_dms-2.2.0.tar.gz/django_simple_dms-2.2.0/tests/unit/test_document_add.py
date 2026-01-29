from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from testutils.factories import TagGrantFactory, UserFactory

from django_simple_dms.exceptions import ForbiddenException


@pytest.mark.parametrize(
    'doc',
    [
        pytest.param('pathnamestr', id='pathnamestr'),
        pytest.param('open', id='handle'),
        pytest.param('path', id='path'),
        pytest.param('memory', id='memory'),
    ],
)
def test_document_add_local_file(doc, self_cleaning_add) -> None:
    from django_simple_dms.models import Document

    if doc == 'pathnamestr':
        doc_obj = Document.add(__file__)
    elif doc == 'path':
        doc_obj = Document.add(document=Path(__file__))
    elif doc == 'memory':
        doc_obj = Document.add(
            document=SimpleUploadedFile('file.txt', b'Example file_content', content_type='text/plain')
        )
    else:
        with open(__file__, 'rb') as f:
            doc_obj = Document.add(document=f)

    assert doc_obj.id is not None


@pytest.mark.parametrize(
    'create, error',
    [
        pytest.param(True, False, id='ok'),
        pytest.param(False, True, id='nok'),
    ],
)
def test_create_with_tags(create, error, self_cleaning_add) -> None:
    from django_simple_dms.models import Document, Document2Tag

    t1 = TagGrantFactory(create=create, defaults=['R', 'U'])
    t2 = TagGrantFactory(defaults=['D'])
    t3 = TagGrantFactory(create=create, defaults=[])  # will not create a DocumentGrant

    u = UserFactory()
    u.groups.add(t1.group)
    u.groups.add(t2.group)
    u.groups.add(t3.group)

    expectation = (
        pytest.raises(ForbiddenException, match=f'Unable to create document with tags: {t1.tag}, {t3.tag}')
        if error
        else does_not_raise()
    )

    with expectation:
        tags = [t1.tag, t2.tag.title.upper(), t3.tag]
        doc_obj = Document.add(actor=u, document=__file__, tags=tags)
        assert doc_obj.id is not None

        doc_grant_values = doc_obj.documentgrant_set.values_list('group', 'granted_permissions', 'grantor')
        assert sorted(doc_grant_values) == sorted(
            [
                (t1.group.id, ['R', 'U'], u.id),
                (t2.group.id, ['D'], u.id),
            ]
        )
        assert sorted(map(str, doc_obj.tags.all())) == sorted(map(str, [t1.tag, t2.tag.title, t3.tag]))
        assert sorted([t.split(':')[0] for t in (map(str, Document2Tag.objects.all()))]) == sorted(
            [t.tag.title for t in [t1, t2, t3]]
        )
        assert (
            sorted([t.split(':')[1].split('/')[-1] for t in (map(str, Document2Tag.objects.all()))])
            == [Path(__file__).name] * 3
        )
