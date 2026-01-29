from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from django.contrib.admin.widgets import AdminDateWidget
from django.contrib.postgres.fields import DateRangeField
from django.contrib.postgres.forms import RangeWidget

from django_simple_dms.models import Document, DocumentTag, TagGrant, DocumentGrant, Document2Tag


class DocumentGrantInline(admin.TabularInline):
    model = DocumentGrant


class Document2TagInline(admin.TabularInline):
    model = Document2Tag
    extra = 1


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('document', 'admin', 'upload_date', 'reference_period', 'tags_list')

    list_filter = (
        'admin',
        ('upload_date', DateFieldListFilter),
    )

    search_fields = ('document', 'admin')
    inlines = [DocumentGrantInline, Document2TagInline]

    formfield_overrides = {
        # Tell Django to use our custom widget for all DateRangeFields in this admin.
        DateRangeField: {'widget': RangeWidget(base_widget=AdminDateWidget)},
    }

    def tags_list(self, obj: Document) -> str:
        return ', '.join([tag.title for tag in obj.tags.all()])

    tags_list.short_description = 'Tags'


class TagGrantInline(admin.TabularInline):
    model = TagGrant


@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    search_fields = ('id',)

    inlines = [TagGrantInline]
