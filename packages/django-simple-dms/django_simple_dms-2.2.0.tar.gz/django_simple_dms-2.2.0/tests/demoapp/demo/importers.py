from django.contrib.auth import get_user_model

from django_simple_dms.exceptions import ForbiddenException, ImporterError
from django_simple_dms.impexp import Importer, ImporterResult, ImporterResultStatus
from django_simple_dms.models import DocumentTag, Document

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
