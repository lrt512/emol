from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.http import HttpResponse

from sso_user.models.user import SSOUser
from current_user.middleware import ThreadLocalUserMiddleware, get_current_user

def view_function(request):
    return HttpResponse()

class ThreadLocalUserMiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ThreadLocalUserMiddleware(view_function)

    def test_anonymous_user(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(get_current_user(), AnonymousUser)

    def test_authenticated_user(self):
        user = SSOUser.objects.create_user(email="testuser@example.com")
        request = self.factory.get('/')
        request.user = user

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_current_user(), user)

    def test_multiple_requests(self):
        user1 = SSOUser.objects.create_user(email="testuser1@example.com")
        user2 = SSOUser.objects.create_user(email="testuser2@example.com")

        request1 = self.factory.get('/')
        request1.user = user1
        response1 = self.middleware(request1)

        request2 = self.factory.get('/')
        request2.user = user2
        response2 = self.middleware(request2)

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(get_current_user(), user2)

    def test_missing_user_attribute(self):
        request = self.factory.get('/')

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(get_current_user())
