# Trust, but verify the paws

Run the application tests on Python 3.12:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r app/requirements.txt -r requirements-dev.txt
python -m pytest -q
```

On Windows PowerShell, activate with `.\.venv\Scripts\Activate.ps1` instead. Tests use isolated temporary storage and synthetic credentials. They do not start Docker or contact a live service.

Coverage includes login, Unicode password handling, CSRF, session replacement/revocation/expiry, generated keys, invalid keys, file round trips, old metadata, size boundaries, filename escaping, duplicate uploads, metadata-write rollback and concurrent requests.

CI runs those tests, builds the Compose stack on Linux and executes a gateway smoke test. Review the Actions results before release. To test Docker locally, copy `.env.example`, replace the placeholder, run `docker compose up -d --build`, then check `/health`, sign in, upload a test file, download and delete it. Verify HTTPS/cookie settings and upstream logging separately in the target environment.
