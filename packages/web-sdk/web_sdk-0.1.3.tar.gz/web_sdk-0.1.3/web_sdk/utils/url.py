"""Module for working with url."""


def join_path(*paths: str, **kwargs) -> str:
    """Join paths parts."""
    result = ""
    for path in paths:
        if not path:
            continue

        if not result:
            result = path
        else:
            result = f"{result.removesuffix('/')}/{path.removeprefix('/')}"

    if kwargs:
        return result.format(**kwargs)
    return result
