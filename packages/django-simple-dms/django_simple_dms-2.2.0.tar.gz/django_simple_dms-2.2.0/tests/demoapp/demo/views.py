from __future__ import annotations

import typing

from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import FormView

from django_simple_dms.exceptions import ForbiddenException, ImporterError
from django_simple_dms.impexp import Importer, ImporterResult, ImporterResultStatus
from django_simple_dms.models import DocumentTag, Document
from .forms import UploadFileForm


if typing.TYPE_CHECKING:
    from django.contrib.auth import get_user_model
    from django.core.files.uploadedfile import UploadedFile

    User = get_user_model()


class ViewDummyImporter(Importer):
    """This dummy importer will just load a single file twice.

    More elaborated importer can parse the document to import files referred from the parsed document.
    """

    def __init__(self, actor: User, tags: list[DocumentTag], document: UploadedFile):
        self.actor = actor
        self.tags = tags
        self.document = document

    def import_documents(self, atomic: bool = True, **kwargs) -> ImporterResult:
        ret = []

        status = ImporterResultStatus.SUCCESS
        for _i in range(2):
            try:
                obj = Document.add(actor=self.actor, document=self.document, tags=self.tags)
                ret.append(obj)
            except ForbiddenException as e:
                if atomic:
                    raise ImporterError(str(e))
                status = ImporterResultStatus.WARNING
                ret.append(str(e))
        return ImporterResult(status=status, documents=ret)


class FileUploadView(FormView):
    template_name = 'upload.html'
    form_class = UploadFileForm
    success_url = reverse_lazy('upload_file')  # or wherever you want to redirect

    def form_valid(self, form):
        uploaded_file = form.cleaned_data['file']
        tags = form.cleaned_data['tags'].split(',')

        ViewDummyImporter(actor=self.request.user, tags=tags, document=uploaded_file).import_documents(atomic=True)

        return HttpResponse('File uploaded')
