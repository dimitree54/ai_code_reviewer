from pathlib import Path
from typing import Dict

from git import Repo, GitCommandError


def add_line_numbers(diff: str) -> str:
    result = ""
    for line_number, line in enumerate(diff.splitlines()):
        result += f"{line_number}: {line}\n"
    return result


def strip_diff_header(diff_text: str) -> str:
    result_lines = []
    still_header = True
    for line in diff_text.splitlines():
        if still_header:
            if "@@" in line:
                still_header = False
            continue
        result_lines.append(line)
    return "\n".join(result_lines)


def get_files_diff(repository_path: Path, other: str) -> Dict[str, str]:
    repo = Repo(repository_path)
    diffs = {}

    changed_files = repo.git.diff(other, name_only=True).split('\n')
    for file in changed_files:
        try:
            file_diff = repo.git.diff(other, file, unified=100000000)  # hack to get full file
            file_diff = strip_diff_header(file_diff)
        except GitCommandError:
            raise ValueError(f"No diff with {other}. Introduce diff or provide different compare_with tag")
        diffs[file] = file_diff
    return diffs
