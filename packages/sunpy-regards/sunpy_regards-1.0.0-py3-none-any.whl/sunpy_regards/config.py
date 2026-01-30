from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RegardsConfig:
    """
    Configuration pour l'accès à REGARDS.

    En production, les valeurs sont lues dans les variables d'environnement :
      - REGARDS_BASE_URL
      - REGARDS_USERNAME
      - REGARDS_PASSWORD
      - REGARDS_TENANT
    """

    base_url: str
    username: str
    password: str
    tenant: str = "Solar"

    @classmethod
    def from_env(self) -> "RegardsConfig":
        base_url = os.getenv(
            "REGARDS_BASE_URL",
            "https://regards.osups.universite-paris-saclay.fr",
        )
        username = os.environ.get("REGARDS_USERNAME")
        password = os.environ.get("REGARDS_PASSWORD")
        tenant = os.getenv("REGARDS_TENANT", "Solar")

        if not username or not password:
            raise RuntimeError(
                "REGARDS_USERNAME and REGARDS_PASSWORD must be set in the environment."
            )

        return self(
            base_url=base_url.rstrip("/"),
            username=username,
            password=password,
            tenant=tenant,
        )
