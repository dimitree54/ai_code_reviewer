def add_line_numbers(patch: str) -> str:
    result = ""
    for line_number, line in enumerate(patch.splitlines()):
        result += f"{line_number}: {line}\n"
    return result
