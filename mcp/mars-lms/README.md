# MARS LMS MCP for Hermes

Local Python stdio MCP for Hermes AI employees. The deployed LMS backend is
`https://mars-backend-six.vercel.app`; the backend source repository is not
required to run this package.

## Location

```text
Rustam-hermesi/
  config.yaml
  hermes.bat
  runtime/
  mcp/
    mars-lms/
      .venv/
      server.py
      lms_client.py
      smoke.py
      requirements.txt
      tests/
      README.md
```

The token is stored only in this MCP process's memory. Call `login` once and
then use the GET tools. Restarting the process requires login again. Separate
processes can represent separate AI employees/accounts.

## Install or Rebuild

Run from the `Rustam-hermesi` home directory. Use its bundled Python to create
the package environment instead of copying a virtual environment from another
location:

```powershell
runtime/venv/Scripts/python.exe -m venv mcp/mars-lms/.venv
mcp/mars-lms/.venv/Scripts/python.exe -m pip install -r mcp/mars-lms/requirements.txt
```

Alternatively use an installed Python 3.11+ to create `.venv`. The tested adapter
dependencies are mcp 2.3.0 and httpx 0.28.1. The Hermes host has its own separate
MCP client dependencies; do not replace the host environment with this one.

## Hermes Configuration

The root launchers (`hermes.bat` on Windows, `sh hermes.sh` on Linux/macOS)
derive `HERMES_HOME` from their own location and set `MARS_MCP_PYTHON` to the
platform's MCP virtual-environment interpreter. Hermes expands these variables
when loading MCP configuration. Launch from any working directory through these
wrappers; calling a different installation's bare `hermes` does not set them.
Merge only this entry into the project's `config.yaml`, preserving other settings:

```yaml
mcp_servers:
  mars-lms:
    command: "${MARS_MCP_PYTHON}"
    args:
      - "${HERMES_HOME}/mcp/mars-lms/server.py"
    env:
      MARS_API_URL: "https://mars-backend-six.vercel.app"
```

No configuration path edits are needed when the project root changes. Recreate
the virtual environments after relocation or an OS change; virtual environments
are not portable. A ready snippet is in `hermes-config.yaml`.

For a Linux server, install Python 3.11-3.13 and the required Node.js/npm versions,
then run from the project root:

```bash
python3 -m venv runtime/venv
runtime/venv/bin/python -m pip install -e './hermes-agent[web,mcp]'
python3 -m venv mcp/mars-lms/.venv
mcp/mars-lms/.venv/bin/python -m pip install -r mcp/mars-lms/requirements.txt
cd hermes-agent
npm install --workspace web --workspace ui-tui
npm run build --workspace web
npm run build --workspace ui-tui
cd ..
sh hermes.sh mcp test mars-lms
sh hermes.sh dashboard --skip-build --port 1920 --no-open
```

The dashboard binds to server loopback by default. For access from your computer,
use an SSH tunnel (for example `ssh -L 1920:127.0.0.1:1920 user@server`) and open
`http://127.0.0.1:1920` locally.

From PowerShell in the Hermes home:

```powershell
./hermes.bat mcp test mars-lms
./hermes.bat chat
```

Open a fresh Hermes session after changing the configuration. Hermes starts
the stdio process automatically; no separate background server or backend
checkout is necessary. To launch manually:

```powershell
mcp/mars-lms/.venv/Scripts/python.exe mcp/mars-lms/server.py
```

A quiet terminal is normal: the process waits for MCP input, not ordinary chat
messages. Logs go to stderr; stdout carries only protocol messages.

## Tools

| Tool | Request | Arguments |
| --- | --- | --- |
| login | POST /api/auth/login | phone, password, optional role |
| branch_me | GET /api/branch/me | None |
| groups | GET /api/branch/groups | Optional query object |
| students | GET /api/branch/students | Optional query object |
| mentors | GET /api/branch/mentors | Optional query object |
| payments | GET /api/branch/payments | Optional query object |
| finance_overview | GET /api/finance/overview | Optional query object |
| finance_salaries | GET /api/finance/salaries | Optional query object |

Example Hermes tool sequence:

```text
login(phone="YOUR_PHONE", password="YOUR_PASSWORD")
branch_me()
groups()
students(query={"page": 1, "limit": 10})
```

If role is omitted, the backend determines it. No token is written to a file or
returned by login. Each GET uses `Authorization: Bearer <token>`; login itself
is POST without a token. A 401 or failed account switch clears the saved token.
The adapter does not automatically refresh tokens or log in again on every call.

## Errors

Both structured MCP content and JSON text include `success`, `status`, `message`
and `source`. Successful reads also include the backend response in `data`.
Failures set MCP `isError: true` and retain the actual HTTP status/message.
Network failures have `status: null`; a local missing login returns
`status: 401, source: mcp` without calling the backend. Role-based 403 responses
are returned unchanged. The optional `MARS_API_TIMEOUT_SECONDS` defaults to 20.

## Tests and Live Smoke

From the Hermes home:

```powershell
mcp/mars-lms/.venv/Scripts/python.exe -m unittest discover -s mcp/mars-lms/tests -v
mcp/mars-lms/.venv/Scripts/python.exe mcp/mars-lms/smoke.py --fixture
mcp/mars-lms/.venv/Scripts/python.exe mcp/mars-lms/smoke.py --fixture --mode legacy
```

The fixture test starts the real stdio server and performs one login followed
by seven GET requests using that token. The suite also checks HTTP errors,
timeout, token expiry and failed account switches.

For a live demonstration, use environment variables or a private
`mcp/mars-lms/.env.local` file with `MARS_PHONE`, `MARS_PASSWORD` and optional
`MARS_ROLE`. Copy the empty `.env.example` if needed. Only the smoke script
reads the credential file; the server receives credentials through its login
tool. You can also select another existing file for a one-time test:

```powershell
mcp/mars-lms/.venv/Scripts/python.exe mcp/mars-lms/smoke.py
mcp/mars-lms/.venv/Scripts/python.exe mcp/mars-lms/smoke.py --env-file C:/path/to/private.env
```

The smoke client reports statuses without dumping people/payment data or JWTs.
Supplying an existing env file for verification does not create a runtime
dependency on that file or on the backend repository.

## Uninstall and Scope

Remove only `mcp_servers.mars-lms` and restart the Hermes session to disconnect.
Keep unrelated settings intact. This package provides eight LMS tools; agent
workflows, schedules and message-sending integrations are separate features.

SDK reference: https://py.sdk.modelcontextprotocol.io/
