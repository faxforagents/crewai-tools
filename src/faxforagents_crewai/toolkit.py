"""Toolkit configuration shared by all canonical tools."""

from __future__ import annotations

from crewai.tools import BaseTool
from pydantic import BaseModel, ConfigDict, PrivateAttr, SecretStr

from faxforagents_crewai.tool import TOOL_CLASSES, _Connection, _connection


class FaxForAgentsToolkit(BaseModel):
    """Create all fifteen tools. Credentials are resolved once and hidden from serialization."""

    model_config = ConfigDict(frozen=True)
    _connection: _Connection = PrivateAttr()

    def __init__(self, *, api_key: str | SecretStr | None = None, sandbox: bool = True) -> None:
        super().__init__()
        self._connection = _connection(api_key, sandbox)

    def get_tools(self) -> list[BaseTool]:
        return [
            cls(api_key=self._connection.api_key, sandbox=self._connection.sandbox)
            for cls in TOOL_CLASSES
        ]
