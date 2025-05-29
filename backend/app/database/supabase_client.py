"""
Supabase database client configuration
"""
from typing import Optional
from supabase import create_client, Client
from ..core.config import settings


class SupabaseClient:
    """Supabase client wrapper"""

    def __init__(self):
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Get regular Supabase client (uses anon key)"""
        if not self._client:
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return self._client

    @property
    def service_client(self) -> Client:
        """Get service role Supabase client (bypasses RLS)"""
        if not self._service_client:
            self._service_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._service_client

    def set_auth(self, token: str):
        """Set authentication token for the client"""
        self.client.auth.set_auth(token)

    def reset_auth(self):
        """Reset authentication"""
        self.client.auth.sign_out()


# Global Supabase client instance
supabase_client = SupabaseClient()


def get_supabase() -> SupabaseClient:
    """Dependency to get Supabase client"""
    return supabase_client
