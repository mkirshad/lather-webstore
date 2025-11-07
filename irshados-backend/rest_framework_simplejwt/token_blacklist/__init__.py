from __future__ import annotations

from django.apps import AppConfig


class TokenBlacklistConfig(AppConfig):
    name = "rest_framework_simplejwt.token_blacklist"
    label = "rest_framework_simplejwt_token_blacklist"
