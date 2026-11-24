# Changelog

## 0.2.0

- Renamed the original filedrop prototype to PawDrop; public documentation and MIT license.
- Removed deployment-specific addresses and private configuration from distribution.
- Added random keys by default, server-side session expiry/revocation and CSRF checks.
- Serialized storage mutations, unique temporary files, duplicate-key rejection and safer metadata failure handling.
- Disabled access logging, added response security headers and a gateway login limit; adjusted multipart limits.
- Non-root application container, loopback-only default binding, named storage volume and pinned direct Python dependencies.
- Added regression tests and CI. Original on-disk file and metadata format remains supported.

## Original prototype (unversioned, unpublished)

- Password-protected admin, `.txt` uploads, bearer-link downloads, JSON metadata and Docker Compose deployment.
