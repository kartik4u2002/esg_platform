from django.utils.deprecation import MiddlewareMixin


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware that attaches the current user's organization to the request
    as ``request.tenant``. Unauthenticated requests get ``tenant = None``
    so that DRF's authentication/permission layer can handle access control.
    """

    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.tenant = getattr(request.user, 'organization', None)
        else:
            request.tenant = None
