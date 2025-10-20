from __future__ import annotations

from functools import lru_cache
from typing import Any

from supabase import Client, create_client


class SupabaseClientManager:
    """Singleton-like manager for Supabase clients."""

    def __init__(self, url: str, service_role_key: str, anon_key: str | None = None) -> None:
        self.url = url
        self.service_role_key = service_role_key
        self.anon_key = anon_key or service_role_key
        self._service_client: Client | None = None
        self._anon_client: Client | None = None

    @property
    def service_client(self) -> Client:
        if not self._service_client:
            self._service_client = create_client(self.url, self.service_role_key)
        return self._service_client

    @property
    def anon_client(self) -> Client:
        if not self._anon_client:
            self._anon_client = create_client(self.url, self.anon_key)
        return self._anon_client


@lru_cache(maxsize=1)
def build_supabase_client(url: str, service_role_key: str, anon_key: str | None = None) -> SupabaseClientManager:
    return SupabaseClientManager(url=url, service_role_key=service_role_key, anon_key=anon_key)
