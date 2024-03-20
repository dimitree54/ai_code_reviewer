import os
from pathlib import Path
from typing import Dict, Set

from git import Repo, GitCommandError

from ai_code_reviewer.run_review import FileDiffReview


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
        if not Path(file).is_file():
            continue
        try:
            file_diff = repo.git.diff(other, file, unified=100000000)  # noqa hack to get full file
            file_diff = strip_diff_header(file_diff)
        except GitCommandError:
            raise ValueError(f"No diff with {other}. Introduce diff or provide different compare_with tag")
        diffs[file] = file_diff
    return diffs


def get_repo_diff(
        repo_path: Path,
        compare_with: str,
        allowed_extensions: Set[str],
) -> Dict[str, str]:
    per_file_diff = get_files_diff(repo_path, compare_with)
    per_file_diff = {
        file_name: file_diff for file_name, file_diff in per_file_diff.items()
        if os.path.splitext(file_name)[1] in allowed_extensions
    }
    return per_file_diff


def get_all_files(
        repo_path: Path,
        allowed_extensions: Set[str],
) -> Dict[str, str]:
    files_content = {}
    for item in repo_path.rglob('*'):
        if item.is_file() and item.suffix in allowed_extensions:
            with open(item, 'r', encoding='utf-8') as file:
                files_content[str(item.absolute())] = file.read()
    return files_content


def suppress_irrelevant_comments(
        review: FileDiffReview
) -> FileDiffReview:
    filtered_comments = [comment for comment in review.comments if comment.is_violating_principle]
    return review.model_copy(update={"comments": filtered_comments})


def suppress_not_changed_lines_comments(
        review: FileDiffReview,
        per_file_diff: Dict[str, str]
) -> FileDiffReview:
    filtered_comments = []
    for comment in review.comments:
        file_content = per_file_diff[review.file_name]
        commented_line = file_content[comment.line_number]
        if "+" in commented_line:
            filtered_comments.append(comment)
    return review.model_copy(update={"comments": filtered_comments})


def suppress_noqa_line_comments(
        review: FileDiffReview,
        per_file_diff: Dict[str, str]
) -> FileDiffReview:
    filtered_comments = []
    for comment in review.comments:
        file_content = per_file_diff[review.file_name]
        commented_line = file_content[comment.line_number]
        if "noqa" not in commented_line:
            filtered_comments.append(comment)
    return review.model_copy(update={"comments": filtered_comments})
