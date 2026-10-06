from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DatasetMetadata:
    source_name: str
    rows: int
    columns: List[str]
    mapped_columns: Dict[str, str]
    generated_columns: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    has_usable_date: bool = True


@dataclass
class LoadResult:
    data: object
    message: str
    metadata: DatasetMetadata
