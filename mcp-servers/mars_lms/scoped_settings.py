"""Read explicitly allowed private LMS account settings."""
import os
from pathlib import Path

def read_settings(file: Path) -> dict[str, str]:
    """Read only our four simple KEY=VALUE settings; never export backend secrets."""
    values = {}
    allowed = {"MARS_API_URL", "MARS_PHONE", "MARS_PASSWORD", "MARS_ROLE"}
    if file.exists():
        for line in file.read_text(encoding="utf-8-sig").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if key in allowed:
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                values[key] = value
    for key in allowed:
        if key in os.environ:
            values[key] = os.environ[key]
    return values


