"""Client for the CoreDataX REST API (https://coredatax.com).

Talks to the JWT-protected ``/api/v1`` surface: log in once, then upload
measurements as CSV, as CDX documents, or one record at a time.

    from CoreDataX import Client

    cdx = Client("my-user", "my-password")
    print(cdx.upload_csv("measurements.csv"))     # {'success': True, 'inserted': 120, 'errors': []}

Every call raises :class:`CoreDataXError` on an HTTP error instead of
returning a body the caller has to inspect -- a failed upload must never
look like a successful one.
"""

import json
import os

import requests

DEFAULT_BASE_URL = "https://coredatax.com"

#: Columns every uploaded CSV must carry. The excitation ones are not
#: decoration: they become label / offset on the stored CDX document, which is
#: what CoreDataX reads back as waveform / dcBias -- a measurement without them
#: is dropped from the Herbert curves. ``dutyCycle`` is the one optional extra.
REQUIRED_CSV_COLUMNS = (
    "magneticReference",
    "setupReference",
    "frequency",
    "magneticFluxDensityPeak",
    "magneticFieldDcBias",
    "magneticFieldWaveformType",
    "temperature",
    "volumetricLosses",
)


class CoreDataXError(RuntimeError):
    """An API call failed. Carries the HTTP status and the server's detail."""

    def __init__(self, message, status_code=None, detail=None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class Client:
    """Authenticated CoreDataX API client.

    Args:
        username: CoreDataX username. Falls back to ``$COREDATAX_USERNAME``.
        password: CoreDataX password. Falls back to ``$COREDATAX_PASSWORD``.
        base_url: API root. Falls back to ``$COREDATAX_URL``, then
            ``https://coredatax.com``.
        timeout: per-request timeout in seconds.

    The access token lives 15 minutes; the client refreshes it automatically
    with the refresh token when a request comes back 401.
    """

    def __init__(self, username=None, password=None, base_url=None, timeout=120):
        self.base_url = (base_url or os.environ.get("COREDATAX_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._username = username or os.environ.get("COREDATAX_USERNAME")
        self._password = password or os.environ.get("COREDATAX_PASSWORD")
        if not self._username or not self._password:
            raise CoreDataXError(
                "No credentials: pass username/password, or set "
                "COREDATAX_USERNAME and COREDATAX_PASSWORD."
            )
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.login()

    # ------------------------------------------------------------------ auth

    def login(self):
        """Exchange username/password for an access + refresh token pair."""
        body = self._request(
            "POST", "/api/v1/auth/login",
            json={"username": self._username, "password": self._password},
            authenticated=False,
        )
        self.access_token = body["access_token"]
        self.refresh_token = body["refresh_token"]
        self.user_id = body["user_id"]
        return self

    def refresh(self):
        """Get a fresh access token from the refresh token."""
        body = self._request(
            "POST", "/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token},
            authenticated=False,
        )
        self.access_token = body["access_token"]
        return self

    # --------------------------------------------------------------- uploads

    def upload_csv(self, csv):
        """Upload measurements from a CSV file path, file object, or CSV text.

        The CSV needs a header row carrying every column in
        :data:`REQUIRED_CSV_COLUMNS`; ``dutyCycle`` may be added for
        non-sinusoidal excitation. Max 10 000 rows per call. The rows are
        attributed to the authenticated user -- a ``userId`` column, if any,
        is ignored.

        Returns the server's ``{'success', 'inserted', 'errors'}``; ``errors``
        holds one entry per rejected row (with its 1-based CSV line number).
        """
        text = _read_text(csv)
        header = text.lstrip().splitlines()[0] if text.strip() else ""
        missing = [c for c in REQUIRED_CSV_COLUMNS if c not in header]
        if missing:
            raise CoreDataXError(f"CSV is missing required columns: {', '.join(missing)}")
        return self._request("POST", "/api/v1/upload_csv", json={"csv": text})

    def upload_cdx(self, cdx):
        """Upload one CDX document or a list of them (file path, text, or object).

        Each record needs ``magnetic`` (an existing magnetic's reference),
        ``operatingPoint`` and ``result``. Max 5 000 records per call.
        Returns ``{'success', 'inserted', 'errors'}`` -- a record that fails
        does not abort the rest, it shows up in ``errors``.
        """
        if isinstance(cdx, (dict, list)):
            payload = cdx
        else:
            payload = json.loads(_read_text(cdx))
        return self._request("POST", "/api/v1/upload_cdx", json=payload)

    def insert(self, record):
        """Insert a single CDX measurement record. Returns ``{'success', 'count'}``."""
        return self._request("POST", "/api/v1/data", json={"data": record})

    # ----------------------------------------------------------------- reads

    def get_data(self, **filters):
        """Read measurements. Accepts the API's filters: ``users``, ``materials``,
        ``skip``, ``limit``, ``min_frequency``, ``max_frequency``, ``min_temp``,
        ``max_temp``, ``min_b_peak``, ``max_b_peak``."""
        return self._request("GET", "/api/v1/data", params=filters)

    def get_materials(self):
        """List the core materials that have measurements."""
        return self._request("GET", "/api/v1/materials")

    # -------------------------------------------------------------- internal

    def _request(self, method, path, authenticated=True, _retried=False, **kwargs):
        headers = kwargs.pop("headers", {})
        if authenticated:
            headers["Authorization"] = f"Bearer {self.access_token}"
        try:
            response = requests.request(
                method, f"{self.base_url}{path}",
                headers=headers, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as error:
            raise CoreDataXError(f"Could not reach {self.base_url}{path}: {error}") from error

        # An expired access token: refresh once, then replay the request.
        if response.status_code == 401 and authenticated and self.refresh_token and not _retried:
            self.refresh()
            return self._request(method, path, authenticated=True, _retried=True, **kwargs)

        if not response.ok:
            detail = _detail_of(response)
            raise CoreDataXError(
                f"{method} {path} failed with HTTP {response.status_code}: {detail}",
                status_code=response.status_code,
                detail=detail,
            )
        return response.json()


def _read_text(source):
    """Accept a path, an open file object, or the text itself."""
    if hasattr(source, "read"):
        return source.read()
    if isinstance(source, (bytes, bytearray)):
        return source.decode("utf-8")
    if "\n" not in source and os.path.exists(source):
        with open(source, "r", encoding="utf-8") as handle:
            return handle.read()
    return source


def _detail_of(response):
    try:
        body = response.json()
    except ValueError:
        return response.text[:500]
    if isinstance(body, dict) and "detail" in body:
        return body["detail"]
    return body


def upload_csv(csv, username=None, password=None, base_url=None):
    """One-shot CSV upload: log in, upload, return the server's response."""
    return Client(username, password, base_url).upload_csv(csv)


def upload_cdx(cdx, username=None, password=None, base_url=None):
    """One-shot CDX upload: log in, upload, return the server's response."""
    return Client(username, password, base_url).upload_cdx(cdx)
