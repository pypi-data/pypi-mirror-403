# tls_sessions

A TLS-fingerprinted HTTP client.

## Features
- Custom JA3
- Akamai HTTP/2 fingerprint
- TLS signature algorithms
- Drop-in `requests` replacement

## Usage

`pip install tls_sessions` 

```python
from tls_session import Session

session = Session(fingerprint="chrome_144")
r = session.get("https://example.com")
print(r.text)
