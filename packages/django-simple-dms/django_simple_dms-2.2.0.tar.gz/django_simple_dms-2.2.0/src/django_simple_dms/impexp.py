from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from django_simple_dms.models import Document


class ImporterResultStatus(Enum):
    SUCCESS = 0
    WARNING = 1


@dataclass
class ImporterResult:
    status: ImporterResultStatus
    documents: list[Document | str] = field(default_factory=list)


class Importer(ABC):
    """Abstract class for importers."""

    @abstractmethod
    def import_documents(self, atomic: bool = True, **kwargs) -> ImporterResult:
        """To be implemented in subclasses.

        atomic: if true either all documents are imported or none at all resulting in an ImporterResult with
                status SUCCESS or an ImporterError.
                If atomic==False the outcome will be an ImporterResult with
                status WARNING if at least one document is imported. ImporterError will be raised otherwise.
        """
        raise NotImplementedError()
