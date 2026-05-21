import requests
from django.conf import settings


def verify_token(request):
    """
    Verify JWT token by calling User & Auth Service.
    Returns user info if valid, None if invalid.
    """
    token = request.META.get('HTTP_AUTHORIZATION', '')

    if not token or not token.startswith('Bearer '):
        return None

    try:
        response = requests.get(
            f"{settings.AUTH_SERVICE_URL}/api/auth/verify/",
            headers={
                'Authorization': token,
            },
            timeout=5
        )

        if response.status_code == 200:
            return response.json()
        return None

    except Exception:
        return None


def require_auth(request):
    """
    Returns (user_info, None) if authenticated.
    Returns (None, error_dict) if not authenticated.
    """
    user = verify_token(request)
    if not user:
        return None, {
            'error': 'Authentication credentials were not provided or are invalid.'
        }
    return user, None


def require_role(request, role):
    """
    Returns (user_info, None) if authenticated and correct role.
    Returns (None, error_dict) if not authenticated or wrong role.
    """
    user, error = require_auth(request)
    if error:
        return None, error
    if user.get('role') != role:
        return None, {'error': f'Only {role} can perform this action.'}
    return user, None