from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class TenantCursorPagination(CursorPagination):
    """Cursor pagination that emits `items` + `next_cursor` payloads for SPA lists."""

    page_size = 50
    page_size_query_param = "pageSize"
    max_page_size = 200
    ordering = "-created_at"

    def get_paginated_response(self, data):
        return Response(
            {
                "items": data,
                "next_cursor": self._extract_cursor(self.get_next_link()),
            }
        )

    def _extract_cursor(self, link: str | None) -> str | None:
        if not link:
            return None
        parsed = urlparse(link)
        query = parse_qs(parsed.query)
        token = query.get(self.cursor_query_param)
        if token:
            return token[0]
        # Fallback for encoded links without explicit query parsing.
        if link and f"{self.cursor_query_param}=" in link:
            return link.split(f"{self.cursor_query_param}=", 1)[1]
        return None
