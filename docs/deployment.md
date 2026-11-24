# Put the box somewhere safe

## Local installation

Copy `.env.example` to `.env`, set a unique random password (at least 16 characters; more entropy is better), then run `docker compose up -d --build`. The placeholder is rejected by the app. `.env` and local `data/` are ignored by Git. Compose uses a named volume `data`; `docker compose down` preserves it, while `docker compose down -v` destroys it.

| Setting | Default/example | Purpose |
|---|---|---|
| ADMIN_PASSWORD | Required | One admin password; use a password manager |
| BASE_URL | http://127.0.0.1:18076 in example | Public origin, or empty for relative links |
| COOKIE_SECURE | true in code, false in local example | Secure cookie flag; false is restricted to loopback demos |
| COOKIE_MAX_AGE | 86400 | Session lifetime in seconds, 1–86400 |
| MAX_UPLOAD_BYTES | 5242880 | Maximum file size, 1–5242880 |
| BIND_HOST | 127.0.0.1 | Host address for Nginx |
| BIND_PORT | 18076 | Host port for Nginx |
| DATA_DIR | /data | Internal data location; keep default in Compose |

Use the supplied Nginx gateway. It enforces a 6 MiB request cap (room for multipart framing around a 5 MiB file), a smaller login body cap and a login rate limit. The app is not published directly. Set any upstream request-size limits to at least 6 MiB.

## HTTPS deployment example

Use a real domain you control instead of the reserved example domain below. For a TLS proxy on the same host, keep `BIND_HOST=127.0.0.1` and set:

```dotenv
BASE_URL=https://drop.example.com
COOKIE_SECURE=true
```

Example Caddyfile:

```caddyfile
drop.example.com {
    reverse_proxy 127.0.0.1:18076
}
```

Do not enable request/access logging containing URL paths at the edge. Check that any existing global logging configuration does not collect links. If the edge runs on another host, bind to a specific private interface, restrict the port to the edge with a firewall, and retain HTTPS for clients. Never expose the plain HTTP backend to the internet. Proxy source IPs are not trusted: the bundled login limit counts the immediate Nginx peer, so clients behind the same edge share a limit. For a larger deployment enforce per-client limits at a trusted edge and review the shared inner limit.

## Migrating from the original filedrop

1. Stop the original service and back up its `data/` directory and metadata. Keep old credentials and backups outside the repository. Set a fresh password and your actual public origin in the new `.env`.
2. Build with `docker compose build app`. Copy the existing data into the named volume before starting the new service. For example, on Linux with the backed-up directory at `../legacy-data`:

```sh
docker compose run --rm --no-deps --user root \
  -v "$(pwd)/../legacy-data:/legacy:ro" app \
  sh -c 'cp -a /legacy/. /data/ && chown -R 10001:10001 /data && chmod 700 /data && find /data -type f -exec chmod 600 {} +'
```

3. Start the stack and verify the admin list and a known test file. Existing valid keys and filenames are preserved; old short keys should be replaced by new generated links. Existing links remain usable if the same public origin is retained.
4. Stop the stack before copying raw storage for consistent backups. Check volume permissions, disk space, and restore procedures.

The app runs as UID/GID 10001; if replacing the volume with a bind mount, grant this UID access. Do not scale the app or increase Uvicorn workers. If migrating a live instance, test against a copy first.
