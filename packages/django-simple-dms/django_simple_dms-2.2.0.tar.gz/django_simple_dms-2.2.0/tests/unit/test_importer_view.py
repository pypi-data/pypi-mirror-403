from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django_webtest import WebTest

from testutils.factories import TagGrantFactory, UserFactory


class UploadViewTest(WebTest):
    def test_file_upload_view(self):
        actor = UserFactory()
        grants = [TagGrantFactory(), TagGrantFactory()]
        for grant in grants:
            actor.groups.add(grant.group)
        tags = ','.join(grant.tag.title for grant in grants)

        test_file = SimpleUploadedFile('hello.txt', b'hello world', content_type='text/plain')

        self.client.force_login(actor)
        response = self.client.post(
            reverse('upload_file'),  # URL name from urls.py
            {'tags': tags, 'file': test_file},
        )

        assert response.status_code == 200
        self.assertContains(response, 'File uploaded')
