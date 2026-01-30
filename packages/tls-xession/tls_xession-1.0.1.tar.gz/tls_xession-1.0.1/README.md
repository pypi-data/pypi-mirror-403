# tls_session

A TLS-fingerprinted HTTP client.

## Features
- Custom JA3
- Akamai HTTP/2 fingerprint
- TLS signature algorithms
- Drop-in `requests.Session` replacement

## Usage

```python
from tls_session import Session

session = Session()
r = session.get("https://example.com")
print(r.text)
