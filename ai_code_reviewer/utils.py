from typing import Dict

from git import Repo


def add_line_numbers(patch: str) -> str:
    result = ""
    for line_number, line in enumerate(patch.splitlines()):
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


def get_files_diff(repository_path: str, other: str) -> Dict[str, str]:
    repo = Repo(repository_path)
    diffs = {}

    changed_files = repo.git.diff(other, name_only=True).split('\n')
    for file in changed_files:
        file_diff = repo.git.diff(other, file, unified=100000000)  # hack to get full file
        file_diff = strip_diff_header(file_diff)
        diffs[file] = file_diff
    return diffs
