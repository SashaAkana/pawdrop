# PawDrop

*Small files. Big secrets. Tiny paws.*

![Python](https://img.shields.io/badge/Python-3.12-3776ab?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-f59e42)

A tiny self-hosted text-file drop. Sign in, upload a `.txt` file, and hand someone a link. No accounts for recipients, no public file listing, no cloud storage subscription. Just a small box with a lid.

```text
admin uploads note.txt
       │
       ▼
   [ PawDrop ] ── secret link ──> recipient downloads note.txt
       (=^･ω･^=)
```

## Quick start

Requires Docker Engine and the Compose plugin.

```sh
cp .env.example .env
# Edit .env: replace ADMIN_PASSWORD with a unique, strong password.
docker compose up -d --build
```

Open **http://127.0.0.1:18076/admin** on the host. Sign in, click **Add file**, and leave the key field empty for an automatically generated link.

This is a loopback-only HTTP demo. For remote access, use HTTPS and secure cookies as described in [deployment](docs/deployment.md).

## What fits in the box?

- `.txt` uploads up to 5 MiB.
- Random, reusable download links; delete a file to revoke its link.
- One password-protected administrator session, with logout and expiry.
- Local files and JSON metadata on a persistent volume.
- No default API documentation or public file index.

## The boring bits (with fewer claws)

- [Architecture and storage](docs/architecture.md)
- [Deploy, configure and migrate](docs/deployment.md)
- [Security and limitations](docs/security.md)
- [Tests and CI](docs/testing.md)
- [Changelog](CHANGELOG.md)

A link is a bearer credential, not encryption. Anyone who has it can download the file until deletion. This is a small, single-admin utility, not a password manager or an encrypted vault.

[MIT License](LICENSE).

*The cat doesn't judge your filenames. The upload validator does.*
