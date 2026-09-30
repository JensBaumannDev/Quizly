def build_user_data(user):
    return {"id": user.pk, "username": user.username, "email": user.email}


def set_auth_cookies(response, refresh_token):
    response.set_cookie(
        "access_token", str(refresh_token.access_token), httponly=True, samesite="Lax"
    )
    response.set_cookie(
        "refresh_token", str(refresh_token), httponly=True, samesite="Lax"
    )
