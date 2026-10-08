from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def build_user_data(user):
    """Return the public account data included in login responses."""

    return {"id": user.pk, "username": user.username, "email": user.email}


def get_refresh_token(request):
    """Return a valid refresh token from the request cookie."""

    raw_refresh_token = request.COOKIES.get("refresh_token")
    if raw_refresh_token is None:
        return None
    try:
        return RefreshToken(raw_refresh_token)
    except TokenError:
        return None


def set_access_cookie(response, access_token):
    """Store an access token in an HTTP-only response cookie."""

    response.set_cookie(
        "access_token", str(access_token), httponly=True, samesite="Lax"
    )


def set_auth_cookies(response, refresh_token):
    """Store access and refresh tokens in HTTP-only cookies."""

    set_access_cookie(response, refresh_token.access_token)
    response.set_cookie(
        "refresh_token", str(refresh_token), httponly=True, samesite="Lax"
    )


def clear_auth_cookies(response):
    """Remove authentication cookies from the response."""

    response.delete_cookie("access_token", samesite="Lax")
    response.delete_cookie("refresh_token", samesite="Lax")
