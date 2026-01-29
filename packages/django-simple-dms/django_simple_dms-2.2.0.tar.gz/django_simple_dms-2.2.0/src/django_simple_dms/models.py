from __future__ import annotations

import io
import typing

import django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.postgres.fields import DateRangeField, ArrayField
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import RegexValidator
from django.db import models, IntegrityError
from django.db.models import Q, UniqueConstraint
from django.utils.regex_helper import _lazy_re_compile

from django.utils.translation import gettext_lazy as _l
from pathlib import Path

from django_simple_dms.exceptions import ForbiddenException
from django_simple_dms.storage import get_document_storage
from django_simple_dms.utils import solve_tags

User = get_user_model()

if typing.TYPE_CHECKING:
    from django_simple_dms.types import AnyFileLike
    from django_simple_dms.models import Document
    from django.db.models.query import QuerySet


slug_re = _lazy_re_compile(r'^([-a-zA-Z0-9_]+(\.)?)+\Z')
validate_csslug = RegexValidator(
    slug_re,
    # Translators: "letters" means latin letters: a-z and A-Z.
    _l('Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.'),
    'invalid',
)


class CreationCheckResult:
    pass


class CreationCheckSuccess(CreationCheckResult):
    def __init__(self, grants: typing.Iterable[TagGrant] = None) -> None:
        self.grants = set(grants) if grants else set()


class CreationCheckFail(CreationCheckResult):
    def __init__(self, tags: typing.Iterable[DocumentTag]) -> None:
        self.tags = tags


class TagGrantQuerySet(models.QuerySet):
    def check_create(
        self, grantor: User = None, tags: list[str | DocumentTag] = None
    ) -> CreationCheckFail | CreationCheckSuccess:
        if grantor is None or grantor.is_superuser:
            return CreationCheckSuccess()

        tags = solve_tags(tags)

        user_groups = set(grantor.groups.distinct())
        found_grants = TagGrant.objects.filter(group__in=user_groups, tag__in=tags, create=True).distinct()
        failing_tags = [t for t in tags if t.id not in set(found_grants.values_list('tag', flat=True))]

        if failing_tags:
            return CreationCheckFail(failing_tags)

        return CreationCheckSuccess(grants=found_grants)


class DocumentTag(models.Model):
    """A Tag is a logical namespace for Documents.

    A tag is defined in a hierarchical taxonomy. Each tag is identified by a unique slug prefixed by a dot-separated
    list of its ancestors tags and a dot. Example: alfa.beta.charlie where charlie is the tag and beta and alfa are
    its ancestors tags in ascending order.

    A document can have 0..n tags. The first tag in the list identifies the document primary "nature" (ie the
    structural folder in a strictly hierarchical classification).
    """

    title = models.CharField(
        help_text=_l('A dot-separated slug'),
        unique=True,
        validators=[validate_csslug],
    )

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self) -> None:
        self.title = self.title.lower().strip('.')


class DocumentGrant(models.Model):
    """Represent the permissions granted to a grantor OR a group (Read, Update, Delete, Share).

    Share: means a grantor can share the same permissions he owns directly or via a group to other users OR groups.

    The owner implicitly owns RUDS grants.
    """

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    granted_permissions = ArrayField(
        models.CharField(max_length=1), default=list, help_text=_l('one or more of R,U,D,S')
    )
    grantor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='document_grants')
    document = models.ForeignKey('Document', on_delete=models.CASCADE)

    class Meta:
        if django.VERSION >= (5, 0):
            # nulls_distinct=False means that NULL is treated as a regular value for uniqueness checks
            # it has been intrdoduced from Postgres 15 and Django 5.0
            # see https://docs.djangoproject.com/en/5.2/releases/5.0/#models
            constraints = [
                UniqueConstraint(
                    name='unique_doc_grant', fields=['grantor', 'user', 'group', 'document'], nulls_distinct=False
                )
            ]

    def __str__(self) -> str:
        prefix = f'U:{self.user}' if self.user else f'D:{self.group}'
        granted_permissions = ''.join(self.granted_permissions)
        if self.grantor:
            granted_permissions = granted_permissions.lower()
        return f'{prefix}:{granted_permissions}:{self.document}'

    def save(self, *args, **kwargs) -> None:
        if self.granted_permissions == []:
            self.granted_permissions = ['R']
        self.full_clean()
        # Enforce uniqueness (with eventual null values) for Django versions < 5.0 and Postgres < 15
        if django.VERSION < (5, 0):
            qs = DocumentGrant.objects.filter(
                grantor=self.grantor, user=self.user, group=self.group, document=self.document
            )
            if self.id:
                qs.exclude(id=self.id)
            if qs.exists():
                raise ValidationError('Document grant with this Grantor, User, Group and Document already exists.')
        return super().save(*args, **kwargs)

    def clean(self) -> None:
        if not (self.user or self.group):
            raise ValidationError(_l('Must set either user or group'), '__all__')
        if self.user and self.group:
            raise ValidationError(_l('Cannot set both user and group'), '__all__')
        self.granted_permissions = [x.upper() for x in self.granted_permissions]
        if extra := (set(self.granted_permissions) - {'R', 'U', 'D', 'S'}):
            raise ValidationError(_l('Invalid permissions: %(extra)s') % {'extra': ''.join(extra)}, '__all__')


class TagGrant(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    create = models.BooleanField(default=True)
    defaults = ArrayField(
        models.CharField(max_length=1), default=list, help_text=_l('one or more of R,U,D,S'), blank=True, null=True
    )
    grantor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='tag_grants')
    tag = models.ForeignKey('DocumentTag', on_delete=models.CASCADE)

    objects = TagGrantQuerySet.as_manager()

    class Meta:
        # nulls_distinct=False means that NULL is treated as a regular value for uniqueness checks
        # it has been intrdoduced from Postgres 15 and Django 5.0
        # see https://docs.djangoproject.com/en/5.2/releases/5.0/#models
        if django.VERSION >= (5, 0):
            constraints = [
                UniqueConstraint(name='unique_tag_grant', fields=['grantor', 'group', 'tag'], nulls_distinct=False)
            ]

    def __str__(self) -> str:
        create = 'C' if self.create else ''
        defaults = ''.join(self.defaults)
        return f'{self.tag}-{self.group}-{create}{defaults}'

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        # Enforce uniqueness (with eventual null values) for Django versions < 5.0 and Postgres < 15
        if django.VERSION < (5, 0):
            qs = TagGrant.objects.filter(grantor=self.grantor, group=self.group, tag=self.tag)
            if self.id:
                qs = qs.exclude(id=self.id)
            if qs.exists():
                raise ValidationError('Tag grant with this Grantor, Group and Tag already exists.')
        return super().save(*args, **kwargs)

    def clean(self) -> None:
        self.defaults = [x.upper() for x in self.defaults]
        if extra := (set(self.defaults) - {'R', 'U', 'D', 'S'}):
            raise ValidationError(_l('Invalid defaults: %(extra)s') % {'extra': ''.join(extra)}, '__all__')


class DocumentQuerySet(models.QuerySet):
    def accessible_by(self, user: User) -> 'QuerySet[Document]':
        return self.filter(Q(admin=user) | Q(documentgrant__user=user) | Q(documentgrant__group__user=user)).distinct()

    def can_grant_contains(self, user: User, cruds: list[str]) -> 'QuerySet[Document]':
        return self.filter(
            Q(admin=user)
            | Q(documentgrant__user=user, documentgrant__granted_permissions__contains=cruds)
            | Q(documentgrant__group__user=user, documentgrant__granted_permissions__contains=cruds)
        ).distinct()

    def can_read(self, user: User) -> 'QuerySet[Document]':
        return self.can_grant_contains(user, ['R'])

    def can_update(self, user: User) -> 'QuerySet[Document]':
        return self.can_grant_contains(user, ['U'])

    def can_delete(self, user: User) -> 'QuerySet[Document]':
        return self.can_grant_contains(user, ['D'])

    def can_share(self, user: User) -> 'QuerySet[Document]':
        return self.can_grant_contains(user, ['S'])


class Document(models.Model):
    document = models.FileField(upload_to='documents/%Y/%m/%d', storage=get_document_storage)
    upload_date = models.DateTimeField(auto_now_add=True)
    admin = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    tags = models.ManyToManyField('DocumentTag', related_name='documents', through='Document2Tag')

    reference_period = DateRangeField(null=True, blank=True)

    objects = DocumentQuerySet.as_manager()

    def __str__(self) -> str:
        admin = f' ({self.admin})' if self.admin else ''
        return f'{self.document.name}{admin}'

    @classmethod
    def add(
        cls,
        document: AnyFileLike,
        actor: User | None = None,
        admin: User | None = None,
        tags: list[str | DocumentTag] | None = None,
    ) -> 'Document':
        """Create a new document and save it to the database.

        actor: is the grantor who is creating this document.
        admin: is the grantor who could administrate this document record.
        """
        tags = solve_tags(tags)

        check_result = TagGrant.objects.check_create(actor, tags)

        if isinstance(check_result, CreationCheckFail):
            errors = ', '.join(map(str, check_result.tags))
            raise ForbiddenException(_l('Unable to create document with tags: %(errors)s') % {'errors': errors})

        obj = Document(admin=admin)
        if isinstance(document, str):
            document = Path(document)
            with document.open() as f:
                obj.document.save(document.name, f, save=True)
        elif isinstance(document, io.BufferedReader):
            name = Path(document.name).name
            obj.document.save(name, document, save=True)
        elif isinstance(document, Path):
            with document.open() as f:
                obj.document.save(document.name, f, save=True)
        elif isinstance(document, UploadedFile):
            obj.document.save(document.name, document.file, save=True)
        obj.save()

        for grant in check_result.grants:
            if grant.defaults:
                DocumentGrant.objects.create(
                    document=obj, grantor=actor, group=grant.group, granted_permissions=grant.defaults
                )

        for tag in tags:
            Document2Tag.objects.create(document=obj, tag=tag)

        return obj


class Document2Tag(models.Model):
    tag = models.ForeignKey(DocumentTag, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)

    class Meta:
        if django.VERSION >= (5, 0):
            constraints = [models.UniqueConstraint(fields=['document', 'tag'], name='unique_tag_document')]

    def __str__(self) -> str:
        return f'{self.tag.title}:{self.document.document.name}'

    def save(self, *args, **kwargs) -> None:
        if django.VERSION < (5, 0):
            qs = Document2Tag.objects.filter(document=self.document, tag=self.tag)
            if self.id:
                qs.exclude(id=self.id)
            if qs.exists():
                raise IntegrityError('duplicate key value violates unique constraint "unique_tag_document"')
        super().save(*args, **kwargs)
