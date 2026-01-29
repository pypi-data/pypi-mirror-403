import typing

import pytest

from django_simple_dms.exceptions import ImporterError, ForbiddenException
from django_simple_dms.impexp import ImporterResultStatus, Importer, ImporterResult

from testutils.factories import TagGrantFactory, UserFactory
from contextlib import nullcontext as does_not_raise

from django.contrib.auth import get_user_model
from django_simple_dms.models import Document, TagGrant, DocumentTag

User = get_user_model()


if typing.TYPE_CHECKING:
    User = get_user_model()


class DummyImporter(Importer):
    def __init__(self, actor: User, tags: list[list[DocumentTag]]):
        self.actor = actor
        self.tags = tags

    def import_documents(self, atomic: bool = True, **kwargs) -> ImporterResult:
        ret = []

        status = ImporterResultStatus.SUCCESS
        for i in range(2):
            try:
                obj = Document.add(actor=self.actor, document=__file__, tags=self.tags[i])
                ret.append(obj)
            except ForbiddenException as e:
                if atomic:
                    raise ImporterError(str(e))
                status = ImporterResultStatus.WARNING
                ret.append(str(e))
        return ImporterResult(status=status, documents=ret)


@pytest.fixture
def importer_actor_fx(db):
    def fx(grants: list[TagGrant]):
        u: User = UserFactory()
        for tg in grants:
            u.groups.add(tg.group)
        return u

    return fx


@pytest.mark.parametrize(
    'atomic, file_tags_ok, expectation',
    [
        pytest.param(True, True, does_not_raise(), id='atomic-ok'),
        pytest.param(False, True, does_not_raise(), id='non-atomic-ok'),
        pytest.param(True, False, pytest.raises(ImporterError), id='atomic-nok'),
        pytest.param(False, False, does_not_raise(), id='non-atomic-nok'),
    ],
)
def test_import_grants_ok(atomic, file_tags_ok, expectation, importer_actor_fx, self_cleaning_add):
    grants = [TagGrantFactory(), TagGrantFactory(), TagGrantFactory(create=False)]
    user = importer_actor_fx(grants=grants)

    tags = [tg.tag for tg in grants]

    tags = [tags[0:2], tags[0:2]] if file_tags_ok else [tags[0:2], tags[1:3]]

    with expectation:
        result = DummyImporter(actor=user, tags=tags).import_documents(atomic=atomic)
        if not file_tags_ok:  # 2nd file caused an error
            assert result.status == ImporterResultStatus.WARNING
            results = list(map(type, result.documents))
            assert results == [Document, str]
            assert result.documents[1].startswith('Unable to create document with tags: ')
        else:
            assert result.status == ImporterResultStatus.SUCCESS
            assert list(result.documents) == list(Document.objects.all())
