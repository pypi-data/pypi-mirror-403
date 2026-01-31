from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional

from dumpster.const import FILE_SEPARATOR


class DumpsterConfig(BaseModel, extra="allow"):
    name: Optional[str] = Field(default=None, description="Dump profile name")

    extensions: Optional[List[str]] = Field(
        default=None, description="List of file extensions to include in the dump"
    )

    contents: List[str] = Field(default=[], description="Patterns of files to include")
    exclude: List[str] = Field(default=[], description="Patterns of files to exclude")

    output: str = Field(default=".dumpster/sources.txt", description="Output file path")

    prompt: Optional[str] = Field(default=None, description="sources prompt")

    header: Optional[str] = Field(
        default=f"# Code repository dump, each file is separated by {FILE_SEPARATOR} <name of file>",
        description="Header text to include at the top of the dump",
    )
    footer: Optional[str] = Field(
        default=None, description="Footer text to include at the bottom of the dump"
    )


class DumpItem(DumpsterConfig):
    pass


class DumpsterBatchConfig(DumpsterConfig):
    dumps: List[DumpItem] = Field(
        default_factory=list, description="Batch dump profiles"
    )
