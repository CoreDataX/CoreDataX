"""Command line uploader:

    python -m CoreDataX measurements.csv --username U --password P
    COREDATAX_USERNAME=U COREDATAX_PASSWORD=P python -m CoreDataX data.cdx

The file type is taken from the extension: ``.csv`` goes to the CSV
endpoint, anything else is treated as a CDX/JSON document.
"""

import argparse
import getpass
import json
import os
import sys

from .client import Client, CoreDataXError, DEFAULT_BASE_URL


def main(argv=None):
    parser = argparse.ArgumentParser(prog="CoreDataX", description="Upload measurements to CoreDataX.")
    parser.add_argument("file", help="a .csv of measurements, or a .cdx/.json document")
    parser.add_argument("-u", "--username", default=os.environ.get("COREDATAX_USERNAME"))
    parser.add_argument("-p", "--password", default=os.environ.get("COREDATAX_PASSWORD"))
    parser.add_argument("--url", default=os.environ.get("COREDATAX_URL", DEFAULT_BASE_URL),
                        help=f"API root (default: {DEFAULT_BASE_URL})")
    args = parser.parse_args(argv)

    if not args.username:
        args.username = input("CoreDataX username: ")
    if not args.password:
        args.password = getpass.getpass("CoreDataX password: ")

    try:
        client = Client(args.username, args.password, args.url)
        if os.path.splitext(args.file)[1].lower() == ".csv":
            result = client.upload_csv(args.file)
        else:
            result = client.upload_cdx(args.file)
    except CoreDataXError as error:
        print(f"Upload failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    # Rows the server rejected are a partial failure, and the exit code says so.
    return 1 if result.get("errors") else 0


if __name__ == "__main__":
    sys.exit(main())
