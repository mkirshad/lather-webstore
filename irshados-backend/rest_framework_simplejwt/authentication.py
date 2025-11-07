from __future__ import annotations

from typing import Any, Optional

from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from .tokens import AccessToken, TokenError


class JWTAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request) -> Optional[tuple[Any, str]]:
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header:
            return None
        parts = header.split(" ", 1)
        if len(parts) != 2 or parts[0] != self.keyword:
            return None
        token_value = parts[1].strip()
        try:
            token = AccessToken(token_value)
        except TokenError as exc:
            raise exceptions.AuthenticationFailed(str(exc)) from exc

        user_model = get_user_model()
        try:
            user = user_model.objects.get(id=token.get("user_id"))
        except user_model.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("User not found.") from exc

        return (user, token_value)
