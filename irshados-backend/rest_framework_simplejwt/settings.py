from dataclasses import dataclass


@dataclass
class APISettings:
    AUTH_HEADER_TYPES: tuple[str, ...] = ("Bearer",)
    AUTH_HEADER_NAME: str = "HTTP_AUTHORIZATION"
    USER_AUTHENTICATION_RULE = staticmethod(lambda user: True)


api_settings = APISettings()
