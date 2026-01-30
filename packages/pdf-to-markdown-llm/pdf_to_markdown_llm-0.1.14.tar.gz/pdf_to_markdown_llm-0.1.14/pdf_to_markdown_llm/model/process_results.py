from pathlib import Path
from dataclasses import dataclass


@dataclass
class ProcessResult:
    paths: list[Path]
    exceptions: list[Exception]
    final_path: Path | None = None


@dataclass
class ProcessResults:
    process_result_list: list[ProcessResult]
    files_dict: dict[Path, list[Path]]
