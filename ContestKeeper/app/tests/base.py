from django.test import TestCase, Client

class SecureClient(Client):
    """A test client that defaults to HTTPS for all requests."""
    def request(self, **request):
        request['wsgi.url_scheme'] = 'https'
        request['SERVER_PORT'] = '443'
        return super().request(**request)

class BaseSecureTestCase(TestCase):
    client_class = SecureClient
