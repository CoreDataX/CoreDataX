"""CSV/CDX loading -- kept as a thin, deprecated wrapper over :class:`Client`.

Up to 0.9.0 ``CsvLoader`` built each CDX document client-side and pushed the
rows straight at the database through the retired port-4242 endpoints. The
server now does that conversion itself (``/api/v1/upload_csv``), so the loader
is a wrapper: it authenticates with a username and password rather than the
validation-token UUID, and it raises when an upload fails instead of
returning quietly.

    from CoreDataX import Client
    Client("my-user", "my-password").upload_csv("measurements.csv")
"""

import sys
import warnings

from .client import Client, CoreDataXError, REQUIRED_CSV_COLUMNS


class CsvLoader:
    """Deprecated. Use ``Client(username, password).upload_csv(path)``."""

    def __init__(self, username, password=None, base_url=None):
        warnings.warn(
            "CsvLoader is deprecated; use CoreDataX.Client(username, password).upload_csv().",
            DeprecationWarning,
            stacklevel=2,
        )
        if password is None:
            raise CoreDataXError(
                "CsvLoader now takes a username and password. The validation-token "
                "UUID accepted by 0.9.0 no longer authenticates uploads."
            )
        self.client = Client(username, password, base_url)

    def check_columns(self, columns):
        missing = [column for column in REQUIRED_CSV_COLUMNS if column not in columns]
        if missing:
            raise ImportError(f"Missing columns: {missing}")
        return True

    def load(self, filepath):
        """Upload a CSV file. Returns ``{'success', 'inserted', 'errors'}``."""
        return self.client.upload_csv(filepath)


class CdxLoader:
    """Deprecated. Use ``Client(username, password).upload_cdx(path)``."""

    def __init__(self, username, password=None, base_url=None):
        warnings.warn(
            "CdxLoader is deprecated; use CoreDataX.Client(username, password).upload_cdx().",
            DeprecationWarning,
            stacklevel=2,
        )
        if password is None:
            raise CoreDataXError(
                "CdxLoader now takes a username and password. The validation-token "
                "UUID accepted by 0.9.0 no longer authenticates uploads."
            )
        self.client = Client(username, password, base_url)

    def load(self, filepath):
        """Upload a .cdx/.json document. Returns ``{'success', 'inserted', 'errors'}``."""
        return self.client.upload_cdx(filepath)


if __name__ == "__main__":  # pragma: no cover
    from .__main__ import main

    sys.exit(main())
