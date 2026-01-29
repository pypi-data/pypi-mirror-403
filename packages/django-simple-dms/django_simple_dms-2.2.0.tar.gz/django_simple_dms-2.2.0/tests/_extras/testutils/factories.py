from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from factory import Sequence, PostGenerationMethodCall, post_generation
from factory.base import FactoryMetaClass
import factory.fuzzy

from factory.django import DjangoModelFactory

factories_registry = {}


class AutoRegisterFactoryMetaClass(FactoryMetaClass):
    def __new__(cls, class_name, bases, attrs):
        new_class = super().__new__(cls, class_name, bases, attrs)
        factories_registry[new_class._meta.model] = new_class
        return new_class


class AutoRegisterModelFactory(factory.django.DjangoModelFactory, metaclass=AutoRegisterFactoryMetaClass):
    pass


def get_factory_for_model(_model):
    class Meta:
        model = _model

    if _model in factories_registry:
        return factories_registry[_model]
    return type(f'{_model._meta.model_name}AutoFactory', (AutoRegisterModelFactory,), {'Meta': Meta})


class DocumentTagFactory(DjangoModelFactory):
    title = Sequence(lambda n: f't_{n}')

    class Meta:
        model = 'django_simple_dms.DocumentTag'


class UserFactory(DjangoModelFactory):
    username = Sequence(lambda n: f'test_user_{n}')
    email = Sequence(lambda n: f'test_user_{n}@nomail.com')
    password = PostGenerationMethodCall('set_password', 'password')

    class Meta:
        model = get_user_model()
        django_get_or_create = ('username',)


class GroupFactory(DjangoModelFactory):
    name = Sequence(lambda n: f'test_group_{n}')

    class Meta:
        model = Group

    @post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return

        # Check if extracted is a list/iterable (not None and not the manager itself)
        if extracted is not None and not hasattr(extracted, 'add'):
            # extracted is a list of permissions passed in
            for perm in extracted:
                self.permissions.add(perm)
        else:
            # No permissions passed, create a default one
            self.permissions.add(Permission.objects.filter(codename='view_user').first())


class DocumentFactory(DjangoModelFactory):
    admin = factory.SubFactory(UserFactory)
    document = factory.django.FileField(filename=factory.fuzzy.FuzzyText(length=12).fuzz() + '.pdf')

    class Meta:
        model = 'django_simple_dms.Document'


class UserGrantFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    group = None
    document = factory.SubFactory(DocumentFactory)

    class Meta:
        model = 'django_simple_dms.DocumentGrant'


class GroupGrantFactory(DjangoModelFactory):
    user = None
    group = factory.SubFactory(GroupFactory)
    document = factory.SubFactory(DocumentFactory)

    class Meta:
        model = 'django_simple_dms.DocumentGrant'


class TagGrantFactory(DjangoModelFactory):
    group = factory.SubFactory(GroupFactory)
    defaults = ['R']
    tag = factory.SubFactory(DocumentTagFactory)

    class Meta:
        model = 'django_simple_dms.TagGrant'
