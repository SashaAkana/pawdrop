# A small box, not a storage empire

PawDrop is a single FastAPI process behind Nginx. Docker Compose provides the private service network and persistent data volume. The Nginx port defaults to host loopback. An external TLS terminator is optional for local testing and required for remote use.

```text
browser -> HTTPS edge (optional locally) -> Nginx -> FastAPI -> /data
```

| Route | Access | Behavior |
|---|---|---|
| GET / | Anyone | Redirect to admin |
| GET /admin | Anyone | Login form or authenticated file list |
| POST /admin/login | Password | Replace the active session |
| POST /admin/logout | Session + CSRF | Revoke session |
| POST /admin/upload | Session + CSRF | Upload one file |
| POST /admin/delete | Session + CSRF | Revoke link and delete file |
| GET /admin/download/{key} | Session | Download attachment |
| GET /{key} | Bearer link | Download attachment |
| GET /health | Anyone | Basic application liveness |

The public route also rejects invalid keys. API docs and OpenAPI are disabled; this is not a security boundary.

## Files on disk

The original file format is retained: `/data/<key>` contains bytes, `/data/meta.json` maps keys to original filenames. Keys are not filenames supplied by the browser. New links use 32 random bytes encoded as URL-safe base64 (43 characters). Custom random keys of 22–128 allowed characters are accepted, but their entropy cannot be checked. Old keys of 8–128 characters remain readable to permit migration.

Writes use unique temporary files, restrictive permissions, fsync of file contents, and atomic replacement. A process-local lock serializes metadata changes and reads. Uploads reject duplicates (HTTP 409), rather than silently replacing existing content. Metadata failure rolls back a new file; deletion removes metadata first so an orphan cannot be downloaded by the public route. Downloads read bounded bytes under the same lock to avoid a concurrent delete race. No automatic expiration of links.

A crash can leave unreferenced files or temporary files; this is not a transactional database and directory entries are not explicitly fsynced. Back up data and inspect orphans offline. Do not edit the volume while the app is running. One worker and one replica are required: locks and sessions are process-local.
