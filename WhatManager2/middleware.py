import base64

from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured
from django.http.response import HttpResponse


class HttpBasicAuthMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
    
    def get_response_401(self):
        response = HttpResponse('Unauthorized\r\n')
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm="What Manager"'
        return response

    def process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class.")

        if 'HTTP_AUTHORIZATION' in request.META:
            authorization = request.META['HTTP_AUTHORIZATION'].split()
            if len(authorization) == 2:
                # NOTE: We are only support basic authentication for now.
                if authorization[0].lower() == "basic":
                    username, password = base64.b64decode(authorization[1]).decode('utf-8').split(':')

                    if request.user.is_authenticated:
                        if request.user.get_username() == username:
                            return

                    user = auth.authenticate(username=username, password=password)
                    if user is not None and user.is_active:
                        request.user = user
                        auth.login(request, user)
                    else:
                        return self.get_response_401()
        elif request.GET.get('auth') == 'http':
            return self.get_response_401()
