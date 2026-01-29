# Utilities

This section describes the available utility functions and classes in `django-simple-dms`.

## Functions

### `solve_tags(tags=None)`

Converts a mixed list of tag identifiers into `DocumentTag` objects.

This utility function is used throughout the codebase to normalize tag input, allowing users to specify tags either as strings or as `DocumentTag` objects.

**Parameters:**

* `tags` (list[str | DocumentTag], optional): A list of tags where each element can be:
    * `str`: Tag title as string (will be converted to lowercase and looked up in the database)
    * `DocumentTag`: Already instantiated DocumentTag object (returned as-is)
    * `None`: If the parameter is None, returns an empty list

**Returns:**

* `list[DocumentTag]`: A list of `DocumentTag` objects

**Raises:**

* `DocumentTag.DoesNotExist`: If a string tag doesn't exist in the database

**Example:**

```python
from django_simple_dms.utils import solve_tags
from django_simple_dms.models import DocumentTag

# Create some tags
tag1 = DocumentTag.objects.create(title='invoices')
tag2 = DocumentTag.objects.create(title='reports')

# Mix of string and object references
mixed_tags = ['invoices', tag2, 'REPORTS']  # Case-insensitive
resolved = solve_tags(mixed_tags)

# All elements are now DocumentTag objects
assert all(isinstance(t, DocumentTag) for t in resolved)
assert len(resolved) == 3
```

**Implementation Details:**

Tag strings are automatically converted to lowercase before lookup, ensuring case-insensitive tag resolution:

```python
# These are equivalent
solve_tags(['Invoices.2024'])
solve_tags(['invoices.2024'])
solve_tags(['INVOICES.2024'])
```

## Type Definitions

### `AnyFileLike`

Type alias defined in `django_simple_dms.types` that represents acceptable file input types for document upload.

**Definition:**

```python
AnyFileLike = io.BufferedReader | str | Path | UploadedFile
```

**Accepted Types:**

* `io.BufferedReader`: Open file handle from `open(file, 'rb')`
* `str`: File path as string
* `pathlib.Path`: Pathlib Path object
* `django.core.files.uploadedfile.UploadedFile`: Django uploaded file (e.g., from `request.FILES`)

**Usage:**

Used as the type hint for the `document` parameter in `Document.add()`:

```python
from django_simple_dms.models import Document
from pathlib import Path

# String path
Document.add(document='/path/to/file.pdf', actor=user)

# Path object
Document.add(document=Path('/path/to/file.pdf'), actor=user)

# File handle
with open('/path/to/file.pdf', 'rb') as f:
    Document.add(document=f, actor=user)

# Uploaded file
Document.add(document=request.FILES['file'], actor=user)
```

## Exception Classes

### `ForbiddenException`

Raised when a user attempts to perform an action they don't have permission for.

**Base Class:** `Exception`

**Common Scenarios:**

* User tries to create a document with tags they don't have `create` permission for
* Raised by `Document.add()` when TagGrant validation fails

**Example:**

```python
from django_simple_dms.models import Document
from django_simple_dms.exceptions import ForbiddenException

try:
    doc = Document.add(
        document='/path/to/file.pdf',
        actor=user,
        tags=['restricted.tag']
    )
except ForbiddenException as e:
    print(f"Permission denied: {e}")
    # Output: Unable to create document with tags: restricted.tag
```

### `ImporterError`

Raised when an error occurs during atomic batch import operations.

**Base Class:** `RuntimeError`

**Usage:**

Used in conjunction with the `Importer` abstract class when `atomic=True` and an import operation fails.

**Example:**

```python
from django_simple_dms.impexp import Importer, ImporterError

class MyImporter(Importer):
    def import_documents(self, atomic=True, **kwargs):
        if atomic and error_occurred:
            raise ImporterError("Failed to import document batch")
```

### `UnmodifiableRecord`

Raised when attempting to modify an immutable record.

**Base Class:** `RuntimeError`

**Usage:**

Used to signal that a particular record should not be modified after creation.

## Import/Export Classes

### `ImporterResultStatus`

Enum representing the outcome of an import operation.

**Values:**

* `SUCCESS` (0): All documents imported successfully
* `WARNING` (1): Some documents imported, others failed (non-atomic mode only)

### `ImporterResult`

Dataclass containing the results of an import operation.

**Fields:**

* `status` (ImporterResultStatus): The overall status of the import
* `documents` (list[Document | str]): List of successfully imported `Document` objects or error message strings for failed imports

### `Importer` (Abstract Base Class)

Abstract base class for implementing custom document importers.

**Abstract Methods:**

#### `import_documents(atomic=True, **kwargs)`

Must be implemented by subclasses to perform the actual import logic.

**Parameters:**

* `atomic` (bool): If `True`, either all documents are imported or none (raises `ImporterError` on failure). If `False`, partial imports are allowed (returns `ImporterResult` with `WARNING` status).
* `**kwargs`: Custom parameters for specific importer implementations

**Returns:**

* `ImporterResult`: Contains status and list of imported documents or error messages

**Raises:**

* `ImporterError`: When `atomic=True` and any document fails to import

**Example Implementation:**

```python
from django_simple_dms.impexp import Importer, ImporterResult, ImporterResultStatus, ImporterError
from django_simple_dms.models import Document
from django_simple_dms.exceptions import ForbiddenException

class DirectoryImporter(Importer):
    def __init__(self, directory, actor, tags):
        self.directory = directory
        self.actor = actor
        self.tags = tags

    def import_documents(self, atomic=True, **kwargs):
        results = []
        status = ImporterResultStatus.SUCCESS

        for file_path in self.directory.glob('*.pdf'):
            try:
                doc = Document.add(
                    document=file_path,
                    actor=self.actor,
                    tags=self.tags
                )
                results.append(doc)
            except ForbiddenException as e:
                if atomic:
                    raise ImporterError(str(e))
                status = ImporterResultStatus.WARNING
                results.append(str(e))

        return ImporterResult(status=status, documents=results)
```
