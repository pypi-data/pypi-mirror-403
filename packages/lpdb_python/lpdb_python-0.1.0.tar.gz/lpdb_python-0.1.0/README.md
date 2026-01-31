# LPDB_python

[![CI](https://github.com/ElectricalBoy/LPDB_python/actions/workflows/ci.yml/badge.svg)](https://github.com/ElectricalBoy/LPDB_python/actions/workflows/ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![GitHub License](https://img.shields.io/github/license/ElectricalBoy/LPDB-python)

LPDB_python provides Python interfaces for the [Liquipedia Database API](https://liquipedia.net/api) (LPDB API).

## LPDB Session

Python wrapper for LPDB session is defined in [session.py](src/lpdb/session.py). The wrapper provides the following
differences from making your own requests:

- Type hints
- Validation of data type names being requested  
  If an invalid data type is supplied, then the session will raise `ValueError` before attempting to make a request.
- Error / warning handling  
  If an error is returned by LPDB, then they will be converted to and raised as a Python exception.
- Pre-configured request header, including formatting of your API key in the request header  
  
  ```python
  import lpdb_python as lpdb

  # These are equivalent
  session = lpdb.LpdbSession("your_lpdb_api_key")
  session = lpdb.LpdbSession("Apikey your_lpdb_api_key")
  ```

## LPDB Data Types

Data types in LPDB can be found in <https://liquipedia.net/commons/Help:LiquipediaDB>.

The raw data returned from LPDB may not be in the corresponding Python types. To help easily access the data,
[defs.py](src/lpdb/defs.py) file provides wrappers for each available data types that offers converted data
as object properties.

A property provided by the wrapper may be `None` if the raw data passed to the constructor of the wrapper
did not contain the data, or if it contained an empty string. Thus, the user should be checking for `None`
where appropriate.

### Example

```python
import lpdb_python as lpdb

session = lpdb.LpdbSession("your_lpdb_api_key")

matches = [
    lpdb.Match(lpdb_raw_match)
    for lpdb_raw_match in session.make_request(
        "match",
        "leagueoflegends",
        conditions="[[parent::World_Championship/2025]]",
        streamurls="true",
    )
]
```

## License

This library is licensed under the [MIT License](./LICENSE), unless otherwise stated in the header of a file.  
It should be noted, however, that the data you will be fetching from LPDB API is licensed under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
See Liquipedia API Terms of Use [here](https://liquipedia.net/api-terms-of-use).

## Disclaimer

"Liquipedia" is a registered trademark of Team Liquid. Liquipedia does not endorse or sponsor this project.
