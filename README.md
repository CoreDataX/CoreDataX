# CoreDataX

Python client for the PSMA's [CoreDataeXchange](https://coredatax.com) — upload and
read magnetic-core loss measurements.

```bash
pip install CoreDataX
```

## Upload

```python
from CoreDataX import Client

cdx = Client("my-user", "my-password")

cdx.upload_csv("measurements.csv")   # {'success': True, 'inserted': 120, 'errors': []}
cdx.upload_cdx("measurements.cdx")   # one CDX document, or a list of them
```

Or from the command line:

```bash
python -m CoreDataX measurements.csv --username my-user --password my-password
# or set COREDATAX_USERNAME / COREDATAX_PASSWORD and just:
python -m CoreDataX measurements.csv
```

### CSV format

A header row is required. These columns must be present:

| column | unit | meaning |
| --- | --- | --- |
| `magneticReference` | — | the reference of a magnetic already registered in CoreDataX |
| `frequency` | Hz | excitation frequency |
| `magneticFluxDensityPeak` | T | peak flux density |
| `temperature` | °C | ambient temperature |
| `volumetricLosses` | W/m³ | measured core losses per unit volume |

Optional: `setupReference`, `magneticFieldDcBias` (A/m), `magneticFieldWaveformType`
(e.g. `Sinusoidal`). Up to 10 000 rows per call. Rows are attributed to the
authenticated user — a `userId` column is ignored.

```csv
magneticReference,setupReference,frequency,magneticFluxDensityPeak,magneticFieldDcBias,magneticFieldWaveformType,temperature,volumetricLosses
3C90 --- TX-25-15-10,my-setup,100000,0.1,0,Sinusoidal,25,42000
```

A row the server rejects (unknown magnetic reference, unparseable number) does not
abort the upload — it comes back in `errors` with its CSV line number, while the
good rows are stored.

## Read

```python
cdx.get_data(materials=["3C90"], min_frequency=50e3, max_frequency=500e3, limit=1000)
cdx.get_materials()
```

## Errors

Every call raises `CoreDataXError` on an HTTP failure — a failed upload never
looks like a successful one:

```python
from CoreDataX import Client, CoreDataXError

try:
    Client("my-user", "wrong-password")
except CoreDataXError as error:
    print(error.status_code, error.detail)   # 401 Invalid credentials
```

## Migrating from 0.9.0

0.9.0 talked to `https://coredatax.com:4242/` and authenticated with the account's
validation-token UUID in the request body. The API now serves over standard HTTPS and
protects writes with a JWT, so those calls fail with 401 — and 0.9.0 did not check the
status code, so uploads silently stored nothing.

| 0.9.0 | 0.10.0 |
| --- | --- |
| `server.insert_data(rows)` | `Client(user, password).insert(record)` |
| `loader.CsvLoader(token).load("f.csv")` | `Client(user, password).upload_csv("f.csv")` |
| `python loader.py <token> f.csv` | `python -m CoreDataX f.csv -u <user> -p <password>` |

`CsvLoader`/`CdxLoader` still exist as deprecated wrappers, and they now take a
username and password. The `server` module's functions raise `CoreDataXError`
explaining the migration rather than failing silently.

## License

MIT.
