from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError


@pytest.fixture(autouse=True)
def models_cleanup(self_cleaning_add):
    return


def test_document_grant_lower_str_for_user_granted(db):
    from testutils.factories import UserGrantFactory

    grant = UserGrantFactory.build(granted_permissions=['R', 'U'])
    g_system = str(grant).split(':')[2]
    grant.granted_by_system = False
    g_user = str(grant).split(':')[2]

    assert g_system == g_user.upper()


def test_document_tag_to_lower(db):
    from testutils.factories import DocumentTagFactory

    dt = DocumentTagFactory(title='aNy-_.woRld0.')
    assert str(dt) == 'any-_.world0'


def test_tag_grant_clean(db):
    from testutils.factories import UserGrantFactory, GroupFactory

    with pytest.raises(ValidationError, match=r'.*Invalid permissions\: [Z0]{2}.*'):
        UserGrantFactory.build(granted_permissions=['z', '0', 'U']).save()

    with pytest.raises(ValidationError, match='.*Cannot set both user and group.*'):
        UserGrantFactory.build(group=GroupFactory()).save()

    with pytest.raises(ValidationError, match='.*Must set either user or group.*'):
        UserGrantFactory.build(user=None).save()


def test_document_unique_tag(db):
    from testutils.factories import DocumentTagFactory, DocumentFactory
    from django_simple_dms.models import Document2Tag

    tg = DocumentTagFactory()
    doc = DocumentFactory()
    Document2Tag.objects.create(document=doc, tag=tg)
    with pytest.raises(IntegrityError, match=r'duplicate key value violates unique constraint "unique_tag_document"'):
        Document2Tag.objects.create(document=doc, tag=tg)


TAG_GRANT_EXIST_ERROR = pytest.raises(
    ValidationError, match=r'Tag grant with this Grantor, Group and Tag already exists.'
)


@pytest.fixture
def scenario_uk_tag(db):
    # Create shared objects for "same" references
    from testutils.factories import UserFactory, GroupFactory, DocumentTagFactory

    return dict(  # noqa: C408
        # Create shared objects for "same" references
        same_grantor=UserFactory(),
        same_group=GroupFactory(),
        same_tag=DocumentTagFactory(),
        # Create first/second objects for "first"/"second" references,
        first_grantor=UserFactory(),
        second_grantor=UserFactory(),
        first_group=GroupFactory(),
        second_group=GroupFactory(),
        first_tag=DocumentTagFactory(),
        second_tag=DocumentTagFactory(),
    )


@pytest.mark.parametrize(
    'grantor_first,grantor_second,group_first,group_second,tag_first,tag_second,should_fail',
    [
        # Case 1: All fields NULL - should fail (duplicate)
        (None, None, None, None, 'same', 'same', TAG_GRANT_EXIST_ERROR),
        # Case 2: Same grantor (not NULL), both groups NULL, same tag - should fail
        ('same', 'same', None, None, 'same', 'same', TAG_GRANT_EXIST_ERROR),
        # Case 3: Both grantors NULL, same group (not NULL), same tag - should fail
        (None, None, 'same', 'same', 'same', 'same', TAG_GRANT_EXIST_ERROR),
        # Case 4: Same grantor, same group, same tag (all not NULL) - should fail
        ('same', 'same', 'same', 'same', 'same', 'same', TAG_GRANT_EXIST_ERROR),
        # Case 5: Different grantors, both groups NULL, same tag - should succeed
        ('first', 'second', None, None, 'same', 'same', does_not_raise()),
        # Case 6: Both grantors NULL, different groups, same tag - should succeed
        (None, None, 'first', 'second', 'same', 'same', does_not_raise()),
        # Case 7: Same grantor, same group, different tags - should succeed
        ('same', 'same', 'same', 'same', 'first', 'second', does_not_raise()),
        # Case 8: grantor NULL on first, not NULL on second, same group and tag - should succeed
        (None, 'second', 'same', 'same', 'same', 'same', does_not_raise()),
        # Case 9: grantor not NULL on first, NULL on second, same group and tag - should succeed
        ('first', None, 'same', 'same', 'same', 'same', does_not_raise()),
        # Case 10: group NULL on first, not NULL on second, same grantor and tag - should succeed
        ('same', 'same', None, 'second', 'same', 'same', does_not_raise()),
        # Case 11: group not NULL on first, NULL on second, same grantor and tag - should succeed
        ('same', 'same', 'first', None, 'same', 'same', does_not_raise()),
        # Case 12: All different - should succeed
        ('first', 'second', 'first', 'second', 'first', 'second', does_not_raise()),
    ],
)
def test_tag_grant_unique_constraint(
    grantor_first, grantor_second, group_first, group_second, tag_first, tag_second, should_fail, scenario_uk_tag
):
    """Test the unique constraint on TagGrant model with nulls_distinct=False.

    The constraint is on fields: ['grantor', 'group', 'tag']
    With nulls_distinct=False, NULL values are treated as equal for uniqueness checks.
    """
    from testutils.factories import TagGrantFactory

    # Map string markers to actual objects
    grantor_map = {
        None: None,
        'same': scenario_uk_tag['same_grantor'],
        'first': scenario_uk_tag['first_grantor'],
        'second': scenario_uk_tag['second_grantor'],
    }
    group_map = {
        None: None,
        'same': scenario_uk_tag['same_group'],
        'first': scenario_uk_tag['first_group'],
        'second': scenario_uk_tag['second_group'],
    }
    tag_map = {
        'same': scenario_uk_tag['same_tag'],
        'first': scenario_uk_tag['first_tag'],
        'second': scenario_uk_tag['second_tag'],
    }

    # Create first TagGrant
    first_grant = TagGrantFactory(
        grantor=grantor_map[grantor_first],
        group=group_map[group_first],
        tag=tag_map[tag_first],
    )

    # Try to create second TagGrant
    with should_fail:
        second_grant = TagGrantFactory(
            grantor=grantor_map[grantor_second],
            group=group_map[group_second],
            tag=tag_map[tag_second],
        )
        assert second_grant.id is not None
        assert second_grant.id != first_grant.id


@pytest.fixture
def scenario_uk_doc(db):
    from testutils.factories import UserFactory, GroupFactory, DocumentFactory

    # Create shared objects for "same" references
    return dict(  # noqa: C408
        same_grantor=UserFactory(),
        same_user=UserFactory(),
        same_group=GroupFactory(),
        same_document=DocumentFactory(),
        # Create first/second objects for "first"/"second" references
        first_grantor=UserFactory(),
        second_grantor=UserFactory(),
        first_user=UserFactory(),
        second_user=UserFactory(),
        first_group=GroupFactory(),
        second_group=GroupFactory(),
        first_document=DocumentFactory(),
        second_document=DocumentFactory(),
    )


DOCUMENT_GRANT_EXIST_ERROR = pytest.raises(
    ValidationError,
    match=r'Document grant with this Grantor, User, Group and Document already exists.',
)


@pytest.mark.parametrize(
    'grantor_first,grantor_second,user_first,user_second,group_first,group_second,document_first,document_second,should_fail',
    [
        # Case 1: Both grantors NULL, same user, group NULL, same document - should fail (duplicate)
        (None, None, 'same', 'same', None, None, 'same', 'same', DOCUMENT_GRANT_EXIST_ERROR),
        # Case 2: Both grantors NULL, user NULL, same group, same document - should fail (duplicate)
        (None, None, None, None, 'same', 'same', 'same', 'same', DOCUMENT_GRANT_EXIST_ERROR),
        # Case 3: Same grantor, same user, group NULL, same document - should fail
        ('same', 'same', 'same', 'same', None, None, 'same', 'same', DOCUMENT_GRANT_EXIST_ERROR),
        # Case 4: Same grantor, user NULL, same group, same document - should fail
        ('same', 'same', None, None, 'same', 'same', 'same', 'same', DOCUMENT_GRANT_EXIST_ERROR),
        # Case 5: Different grantors, same user, group NULL, same document - should succeed
        ('first', 'second', 'same', 'same', None, None, 'same', 'same', does_not_raise()),
        # Case 6: Different grantors, user NULL, same group, same document - should succeed
        ('first', 'second', None, None, 'same', 'same', 'same', 'same', does_not_raise()),
        # Case 7: Both grantors NULL, different users, group NULL, same document - should succeed
        (None, None, 'first', 'second', None, None, 'same', 'same', does_not_raise()),
        # Case 8: Both grantors NULL, user NULL, different groups, same document - should succeed
        (None, None, None, None, 'first', 'second', 'same', 'same', does_not_raise()),
        # Case 9: Same grantor, same user, group NULL, different documents - should succeed
        ('same', 'same', 'same', 'same', None, None, 'first', 'second', does_not_raise()),
        # Case 10: Same grantor, user NULL, same group, different documents - should succeed
        ('same', 'same', None, None, 'same', 'same', 'first', 'second', does_not_raise()),
        # Case 11: grantor NULL on first, not NULL on second, same user, group NULL, same document - should succeed
        (None, 'second', 'same', 'same', None, None, 'same', 'same', does_not_raise()),
        # Case 12: grantor not NULL on first, NULL on second, same user, group NULL, same document - should succeed
        ('first', None, 'same', 'same', None, None, 'same', 'same', does_not_raise()),
        # Case 13: grantor NULL on first, not NULL on second, user NULL, same group, same document - should succeed
        (None, 'second', None, None, 'same', 'same', 'same', 'same', does_not_raise()),
        # Case 14: grantor not NULL on first, NULL on second, user NULL, same group, same document - should succeed
        ('first', None, None, None, 'same', 'same', 'same', 'same', does_not_raise()),
        # Case 15: Same grantor, different users, group NULL, same document - should succeed
        ('same', 'same', 'first', 'second', None, None, 'same', 'same', does_not_raise()),
        # Case 16: Same grantor, user NULL, different groups, same document - should succeed
        ('same', 'same', None, None, 'first', 'second', 'same', 'same', does_not_raise()),
        # Case 17: Both grantors NULL, same user (user grant), group NULL, different documents - should succeed
        (None, None, 'same', 'same', None, None, 'first', 'second', does_not_raise()),
        # Case 18: Both grantors NULL, user NULL, same group (group grant), different documents - should succeed
        (None, None, None, None, 'same', 'same', 'first', 'second', does_not_raise()),
        # Case 19: All different with user grants - should succeed
        ('first', 'second', 'first', 'second', None, None, 'first', 'second', does_not_raise()),
        # Case 20: All different with group grants - should succeed
        ('first', 'second', None, None, 'first', 'second', 'first', 'second', does_not_raise()),
    ],
)
def test_document_grant_unique_constraint(
    grantor_first,
    grantor_second,
    user_first,
    user_second,
    group_first,
    group_second,
    document_first,
    document_second,
    should_fail,
    scenario_uk_doc,
):
    """Test the unique constraint on DocumentGrant model with nulls_distinct=False.

    The constraint is on fields: ['grantor', 'user', 'group', 'document']
    With nulls_distinct=False, NULL values are treated as equal for uniqueness checks.
    """
    from testutils.factories import UserGrantFactory

    # Map string markers to actual objects
    grantor_map = {
        None: None,
        'same': scenario_uk_doc['same_grantor'],
        'first': scenario_uk_doc['first_grantor'],
        'second': scenario_uk_doc['second_grantor'],
    }
    user_map = {
        None: None,
        'same': scenario_uk_doc['same_user'],
        'first': scenario_uk_doc['first_user'],
        'second': scenario_uk_doc['second_user'],
    }
    group_map = {
        None: None,
        'same': scenario_uk_doc['same_group'],
        'first': scenario_uk_doc['first_group'],
        'second': scenario_uk_doc['second_group'],
    }
    document_map = {
        'same': scenario_uk_doc['same_document'],
        'first': scenario_uk_doc['first_document'],
        'second': scenario_uk_doc['second_document'],
    }

    # Create first DocumentGrant
    first_grant = UserGrantFactory(
        grantor=grantor_map[grantor_first],
        user=user_map[user_first],
        group=group_map[group_first],
        document=document_map[document_first],
    )

    # Try to create second DocumentGrant
    with should_fail:
        second_grant = UserGrantFactory(
            grantor=grantor_map[grantor_second],
            user=user_map[user_second],
            group=group_map[group_second],
            document=document_map[document_second],
        )
        assert second_grant.id is not None
        assert second_grant.id != first_grant.id
