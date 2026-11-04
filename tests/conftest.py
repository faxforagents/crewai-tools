"""Keep test runs local and independent of host credentials."""

import os
from pathlib import Path

_TMP = Path(__file__).resolve().parents[1] / ".coding-agent" / "tmp"
for _key, _directory in {
    "XDG_CONFIG_HOME": "config",
    "XDG_DATA_HOME": "data",
    "XDG_CACHE_HOME": "cache",
}.items():
    os.environ[_key] = str(_TMP / _directory)
os.environ["CREWAI_TELEMETRY_DISABLED"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"
