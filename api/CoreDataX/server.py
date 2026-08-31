"""Removed in 0.10.0 -- the transport these functions used no longer exists.

Up to 0.9.0 this module POSTed to ``https://coredatax.com:4242/`` and
authenticated with the account's validation-token UUID in the request body.
CoreDataX now serves its API over HTTPS on the standard port and protects
writes with a JWT, so those calls return 401 and no data is stored. Worse,
``insert_data`` never checked the status code, so a rejected upload looked
exactly like a successful one.

Use :class:`CoreDataX.Client` instead::

    from CoreDataX import Client
    cdx = Client("my-user", "my-password")
    cdx.upload_csv("measurements.csv")
"""

from .client import CoreDataXError

_MIGRATION = (
    "CoreDataX.server.{name}() was removed in 0.10.0: it used the retired "
    "port-4242 endpoints with token-in-body auth, which the API now rejects "
    "with 401. Use CoreDataX.Client(username, password) instead -- "
    "Client.upload_csv(), .upload_cdx(), .insert() and .get_data()."
)


def _removed(name):
    raise CoreDataXError(_MIGRATION.format(name=name))


def get_magnetic_data(reference, token):
    _removed("get_magnetic_data")


def get_setup_data(reference, token):
    _removed("get_setup_data")


def get_user_data(token):
    _removed("get_user_data")


def insert_data(data):
    _removed("insert_data")
