import io
from pathlib import Path

from django.core.files.uploadedfile import UploadedFile

AnyFileLike = io.BufferedReader | str | Path | UploadedFile
