from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Skip DRF's CSRF enforcement — CORS already gates cross-origin requests."""

    def enforce_csrf(self, request):
        pass
