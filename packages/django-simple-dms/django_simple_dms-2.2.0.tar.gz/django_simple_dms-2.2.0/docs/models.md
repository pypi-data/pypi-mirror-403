# Models

Data-Model diagram:
![models.png](models.png)

This section describes the models used by `django-simple-dms`.

## DocumentTag

A `DocumentTag` is a logical namespace for Documents.

A tag is defined in a hierarchical taxonomy. Each tag is identified by a unique slug prefixed by a dot-separated list of its ancestors tags and a dot. Example: `alfa.beta.charlie` where `charlie` is the tag and `beta` and `alfa` are its ancestors tags in ascending order.

A document can have 0..n tags. The first tag in the list identifies the document primary "nature" (i.e., the structural folder in a strictly hierarchical classification).

### Fields

* `title` (CharField, unique): A dot-separated slug. Validated with a regex pattern that accepts letters, numbers, underscores, and hyphens separated by dots.

### Validation

* Tags are automatically converted to lowercase
* Leading and trailing dots are stripped
* Must match the pattern: `^([-a-zA-Z0-9_]+(\.)?)+$`

### Example

```python
from django_simple_dms.models import DocumentTag

# Create hierarchical tags
invoices = DocumentTag.objects.create(title='invoices')
invoices_2024 = DocumentTag.objects.create(title='invoices.2024')
invoices_2024_q1 = DocumentTag.objects.create(title='invoices.2024.q1')
```

## DocumentGrant

Represents the permissions granted to a user **or** a group for a specific document.

Permissions are:
* `R`: Read
* `U`: Update
* `D`: Delete
* `S`: Share (a user can share the same permissions they own directly or via a group to other users or groups)

The document `admin` implicitly owns all `RUDS` permissions.

### Fields

* `user` (ForeignKey, nullable): The user receiving the grant. Either `user` or `group` must be set, but not both.
* `group` (ForeignKey, nullable): The group receiving the grant. Either `user` or `group` must be set, but not both.
* `granted_permissions` (ArrayField): An array of characters representing the granted permissions. Defaults to `['R']` if empty.
* `grantor` (ForeignKey, nullable): The user who granted the permissions.
* `document` (ForeignKey): The document for which permissions are granted.

### Unique Constraint

A unique constraint exists on `['grantor', 'user', 'group', 'document']` with `nulls_distinct=False` (Django 5.0+/PostgreSQL 15+), meaning NULL values are treated as equal for uniqueness checks.

### Validation

* Exactly one of `user` or `group` must be set
* Permissions are automatically converted to uppercase
* Only valid permissions are `R`, `U`, `D`, `S`
* For Django < 5.0, uniqueness is enforced programmatically in the `save()` method

### String Representation

The string format shows whether it's a user grant (U:) or group grant (D:), followed by permissions and document:
```
U:john:RU:document.pdf
D:editors:RUDS:document.pdf
```

When granted by a user (not the system), permissions are shown in lowercase.

## TagGrant

Represents the permissions granted to a group for creating documents with a specific tag and the default permissions those documents will receive.

### Fields

* `group` (ForeignKey, nullable): The group receiving the grant.
* `create` (BooleanField): Whether the group can create documents with this tag. Defaults to `True`.
* `defaults` (ArrayField, nullable): Default permissions (`R`, `U`, `D`, `S`) automatically applied to documents created with this tag. Empty array means no automatic grants.
* `grantor` (ForeignKey, nullable): The user who created this grant.
* `tag` (ForeignKey): The tag this grant applies to.

### Unique Constraint

A unique constraint exists on `['grantor', 'group', 'tag']` with `nulls_distinct=False` (Django 5.0+/PostgreSQL 15+), meaning NULL values are treated as equal for uniqueness checks.

### Validation

* Default permissions are automatically converted to uppercase
* Only valid permissions are `R`, `U`, `D`, `S`
* For Django < 5.0, uniqueness is enforced programmatically in the `save()` method

### Custom Manager: TagGrantQuerySet

The `TagGrant` model has a custom manager with the following method:

* `check_create(grantor, tags)`: Checks if a user can create documents with the given tags.
    * Returns `CreationCheckSuccess` with applicable grants if allowed
    * Returns `CreationCheckFail` with failing tags if not allowed
    * Superusers always pass the check
    * Checks that the user's groups have `create=True` grants for all specified tags

### String Representation

Format: `tag-group-Cdefaults` where `C` appears if `create=True` and defaults are the permission letters.

### Example

```python
from django_simple_dms.models import TagGrant, DocumentTag
from django.contrib.auth.models import Group

# Allow 'editors' group to create invoices with default read/update permissions
grant = TagGrant.objects.create(
    tag=DocumentTag.objects.get(title='invoices'),
    group=Group.objects.get(name='editors'),
    create=True,
    defaults=['R', 'U'],
    grantor=admin_user
)
```

## Document

The `Document` model stores uploaded documents with permission management.

### Fields

* `document` (FileField): The uploaded file. Default upload path: `documents/%Y/%m/%d`
* `upload_date` (DateTimeField): Automatically set when the document is uploaded.
* `admin` (ForeignKey, nullable): The user who can administrate this document. Implicitly has all RUDS permissions.
* `tags` (ManyToManyField): Tags associated with the document, linked through `Document2Tag`.
* `reference_period` (DateRangeField, nullable): Optional date range for time-based document organization.

### DocumentQuerySet

The `Document` model has a custom `DocumentQuerySet` with the following methods:

* `accessible_by(user)`: Returns all documents accessible by the given user (as admin or through grants).
* `can_grant_contains(user, cruds)`: Returns all documents where the user has the specified permissions (list of permission characters).
* `can_read(user)`: Returns all documents the user can read (has 'R' permission).
* `can_update(user)`: Returns all documents the user can update (has 'U' permission).
* `can_delete(user)`: Returns all documents the user can delete (has 'D' permission).
* `can_share(user)`: Returns all documents the user can share (has 'S' permission).

### Class Methods

#### `add(document, actor=None, admin=None, tags=None)`

Creates a new document and saves it to the database with permission checks.

**Parameters:**

* `document` (AnyFileLike): The document to upload. Accepts:
    * `str`: File path as string
    * `Path`: Pathlib Path object
    * `io.BufferedReader`: Open file handle
    * `UploadedFile`: Django uploaded file
* `actor` (User, optional): The user creating the document. Used for permission checks. Superusers bypass checks.
* `admin` (User, optional): The user who will administrate this document record.
* `tags` (list[str | DocumentTag], optional): List of tags (as strings or DocumentTag objects) to associate with the document.

**Returns:** The created `Document` instance.

**Raises:**
* `ForbiddenException`: If the actor doesn't have permission to create documents with the specified tags.

**Behavior:**

1. Validates that the actor has `create=True` TagGrants for all specified tags
2. Creates the document
3. Automatically creates DocumentGrants based on TagGrant `defaults`
4. Associates tags with the document through Document2Tag

**Example:**

```python
from django_simple_dms.models import Document
from pathlib import Path

# From file path
doc = Document.add(
    document='/path/to/invoice.pdf',
    actor=request.user,
    admin=request.user,
    tags=['invoices.2024.q1']
)

# From Path object
doc = Document.add(
    document=Path('/path/to/report.pdf'),
    actor=request.user,
    tags=['reports', 'annual']
)

# From uploaded file
doc = Document.add(
    document=request.FILES['document'],
    actor=request.user,
    admin=request.user
)
```

## Document2Tag

An intermediate model representing the many-to-many relationship between `Document` and `DocumentTag`.

### Fields

* `tag` (ForeignKey): The DocumentTag.
* `document` (ForeignKey): The Document.

### Unique Constraint

A unique constraint exists on `['document', 'tag']` to prevent duplicate tag assignments (Django 5.0+). For earlier versions, this is enforced in the `save()` method.

### String Representation

Format: `tag.title:document.name`

Example: `invoices.2024:invoice_001.pdf`
