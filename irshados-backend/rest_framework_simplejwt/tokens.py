from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from datetime import timedelta
from typing import Any, Dict

from django.apps import apps
from django.conf import settings
from django.utils import timezone


class TokenError(Exception):
    """Exception raised when a token is invalid or expired."""


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def _secret() -> bytes:
    return settings.SECRET_KEY.encode("utf-8")


class Token(dict):
    token_type: str = "token"
    lifetime: timedelta = timedelta(minutes=5)

    def __init__(self, token: str | None = None, payload: Dict[str, Any] | None = None):
        if token is not None:
            payload = self.decode(token)
        elif payload is None:
            payload = {}
        super().__init__(payload)
        self._token = token
        self._dirty = token is None

    @classmethod
    def now(cls) -> int:
        return int(timezone.now().timestamp())

    @classmethod
    def encode(cls, payload: Dict[str, Any]) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        signature = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
        signature_b64 = _b64encode(signature)
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    @classmethod
    def decode(cls, token: str) -> Dict[str, Any]:
        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
        except ValueError as exc:  # pragma: no cover - defensive
            raise TokenError("Invalid token format") from exc
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        signature = _b64decode(signature_b64)
        expected = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise TokenError("Invalid token signature")
        payload = json.loads(_b64decode(payload_b64))
        if payload.get("token_type") != cls.token_type:
            raise TokenError("Incorrect token type")
        exp = payload.get("exp")
        if exp and cls.now() > int(exp):
            raise TokenError("Token has expired")
        jti = payload.get("jti")
        if jti and _blacklist().objects.filter(jti=jti).exists():
            raise TokenError("Token has been revoked")
        return payload

    @classmethod
    def for_user(cls, user):
        lifetime = cls.lifetime
        seconds = int(lifetime.total_seconds())
        now_ts = cls.now()
        payload: Dict[str, Any] = {
            "token_type": cls.token_type,
            "exp": now_ts + seconds,
            "iat": now_ts,
            "jti": uuid.uuid4().hex,
            "user_id": str(user.id),
        }
        return cls(payload=payload)

    def __setitem__(self, key: str, value: Any) -> None:
        self._dirty = True
        super().__setitem__(key, value)

    def __str__(self) -> str:
        if self._dirty or self._token is None:
            self._token = self.encode(dict(self))
            self._dirty = False
        return self._token


class AccessToken(Token):
    token_type = "access"
    lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]


class RefreshToken(Token):
    token_type = "refresh"
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]

    def blacklist(self) -> None:
        _blacklist().objects.get_or_create(jti=self["jti"])

    @property
    def access_token(self) -> AccessToken:
        payload = dict(self)
        payload["token_type"] = AccessToken.token_type
        payload["exp"] = AccessToken.now() + int(AccessToken.lifetime.total_seconds())
        payload["iat"] = AccessToken.now()
        payload["parent_jti"] = self["jti"]
        return AccessToken(payload=payload)


def _blacklist():
    return apps.get_model("api", "BlacklistedToken")
