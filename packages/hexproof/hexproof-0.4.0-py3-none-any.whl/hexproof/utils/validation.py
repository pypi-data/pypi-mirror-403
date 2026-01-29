"""
* Utils: Validation
"""
# Third Party Imports
from pydantic_core import ErrorDetails


def format_validation_error_report(errors: list[ErrorDetails], dedupe: bool = True) -> str:
    """Return a sorted list of formatted validation errors."""
    grouped: list[tuple[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    def _loc_to_dot_sep(loc: tuple[str | int, ...]) -> str:
        path = ''
        for i, x in enumerate(loc):
            if isinstance(x, str):
                if i > 0:
                    path += '.'
                path += x
            elif isinstance(x, int):
                path += '[]'
            else:
                raise TypeError('Unexpected type')
        return path

    # Check and format each error report
    for e in errors:
        _reason = e.get("type", "unknown_error")
        _path = _loc_to_dot_sep(e.get("loc", ()))
        _input_value = e.get("input", None)
        _input_type = type(_input_value).__name__
        # Check if we've already reported this field issue
        if dedupe:
            key = (_reason, _path, _input_type)
            if key in seen:
                continue
            seen.add(key)
        grouped.append((_path, f"{_path} / {_reason} / {_input_type} / {_input_value}"))

    # Return output
    return '\n'.join(v for k, v in sorted(sorted(grouped, key=lambda x: x[0]), key=lambda x: len(x[0])))
