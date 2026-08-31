"""CoreDataX -- Python client for the PSMA's CoreDataeXchange (https://coredatax.com).

    from CoreDataX import Client
    cdx = Client("my-user", "my-password")
    cdx.upload_csv("measurements.csv")
"""

from .client import (
    Client,
    CoreDataXError,
    DEFAULT_BASE_URL,
    REQUIRED_CSV_COLUMNS,
    upload_cdx,
    upload_csv,
)

__version__ = "0.10.2"

__all__ = [
    "Client",
    "CoreDataXError",
    "DEFAULT_BASE_URL",
    "REQUIRED_CSV_COLUMNS",
    "upload_csv",
    "upload_cdx",
    "__version__",
]
