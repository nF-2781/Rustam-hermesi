# MCP Servers

This is the only MCP server root for this project.

- `mars_lms/`: the unified MARS LMS server: 22 workflow/data tools, six retained read tools and eight
  scoped student progress/reception tools plus five COO tools, registered on one FastMCP instance.
  Default Hermes and both agent profiles run the same `server.py`, use the same
  `.venv`, and install the same `requirements.txt` (MCP SDK 1.30.0).
  Profiles retain their six/three allowed tools. See `mars_lms/README.md`.

From the repository root, verify discovery with:

```powershell
.\hermes.bat mcp test mars_lms
.\hermes.bat -p student-progress-auditor mcp test mars-lms
.\hermes.bat -p reception-request-router mcp test mars-lms
```

Restart Hermes or reload MCP connections after changing paths. Legacy top-level
`mcp/` and `mars-mcp-server/` directories have been removed.
