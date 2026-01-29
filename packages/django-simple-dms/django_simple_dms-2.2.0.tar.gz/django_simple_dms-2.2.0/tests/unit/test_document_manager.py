from pathlib import Path

import pytest


@pytest.fixture
def scenario(db):
    from testutils.factories import UserGrantFactory, GroupFactory, DocumentFactory, UserFactory, GroupGrantFactory

    u1 = UserFactory()
    u2 = UserFactory()
    u3 = UserFactory()

    group = GroupFactory()

    # u3 will have read permission via group
    u3.groups.add(group)

    # accessible by the admin
    document = DocumentFactory()

    # Not accessible
    other_document = DocumentFactory(admin=None)

    # u1 can read document
    UserGrantFactory(user=u1, document=document)

    # u2 can Update and Delete document
    UserGrantFactory(user=u2, document=document, granted_permissions=['U', 'D'])

    # group can read and share document
    GroupGrantFactory(document=document, group=group, granted_permissions=['R', 'S'])

    # u3 can update and share other_document
    UserGrantFactory(user=u3, document=other_document, granted_permissions=['U', 'S'])

    yield {
        'u1': u1,
        'u2': u2,
        'u3': u3,
        'group': group,
        'other_document': other_document,
        'document': document,
    }
    for doc in [document, other_document]:
        Path(doc.document.file.name).unlink()


@pytest.mark.parametrize(
    'user, access, read, update, delete, share',
    [
        pytest.param(1, 'd', 'd', '', '', '', id='u1'),
        pytest.param(2, 'd', '', 'd', 'd', '', id='u2'),
        pytest.param(3, 'do', 'd', 'o', '', 'do', id='u3'),
    ],
)
def test_user_can_do(user, access, read, update, delete, share, scenario) -> None:
    from django_simple_dms.models import Document

    document: Document = scenario['document']
    other_document: Document = scenario['other_document']

    user = scenario[f'u{user}']

    ac = ({document.id} if 'd' in access else set()).union({other_document.id} if 'o' in access else set())
    rd = ({document.id} if 'd' in read else set()).union({other_document.id} if 'o' in read else set())
    up = ({document.id} if 'd' in update else set()).union({other_document.id} if 'o' in update else set())
    de = ({document.id} if 'd' in delete else set()).union({other_document.id} if 'o' in delete else set())
    sh = ({document.id} if 'd' in share else set()).union({other_document.id} if 'o' in share else set())

    assert (v := set(Document.objects.accessible_by(user).values_list('id', flat=True))) == ac, (
        f'Unexpected access: {v} != {ac}'
    )
    assert (v := set(Document.objects.can_read(user).values_list('id', flat=True))) == rd, (
        f'Unexpected read: {v} != {rd}'
    )
    assert (v := set(Document.objects.can_update(user).values_list('id', flat=True))) == up, (
        f'Unexpected update: {v} != {up}'
    )
    assert (v := set(Document.objects.can_delete(user).values_list('id', flat=True))) == de, (
        f'Unexpected delete: {v} != {de}'
    )
    assert (v := set(Document.objects.can_share(user).values_list('id', flat=True))) == sh, (
        f'Unexpected share: {v} != {sh}'
    )


def test_admin_can_all(scenario):
    from django_simple_dms.models import Document

    admin = scenario['document'].admin
    document = scenario['document']

    assert list(Document.objects.accessible_by(admin).values_list('id', flat=True)) == [document.id]
    assert list(Document.objects.can_read(admin).values_list('id', flat=True)) == [document.id]
    assert list(Document.objects.can_update(admin).values_list('id', flat=True)) == [document.id]
    assert list(Document.objects.can_delete(admin).values_list('id', flat=True)) == [document.id]
    assert list(Document.objects.can_share(admin).values_list('id', flat=True)) == [document.id]
