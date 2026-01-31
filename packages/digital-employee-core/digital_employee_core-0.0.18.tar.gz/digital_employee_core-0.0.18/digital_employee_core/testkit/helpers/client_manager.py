"""Client manager for singleton Client instance.

Authors:
    Gunawan Christianto (gunawan.christianto@gdplabs.id)

References:
    NONE
"""

from glaip_sdk import Client


class ClientManager:
    """Singleton manager for Client instances to prevent memory leaks."""

    _instance = None
    _client = None

    def __new__(cls):
        """Create or return the singleton instance of ClientManager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_client(cls) -> Client:
        """Get the singleton Client instance.

        Returns:
            Client: The singleton Client instance.
        """
        if cls._client is None:
            cls._client = Client()
        return cls._client
