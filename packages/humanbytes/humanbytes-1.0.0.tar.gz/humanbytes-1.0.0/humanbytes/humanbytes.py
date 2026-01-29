def humanbytes(num: int | float, binary: bool = False) -> str:
    """
    Convert a number of bytes into a human-readable string.

    Args:
        num (int | float): The number of bytes to convert.
        binary (bool, optional): If True, use binary units (KiB, MiB, GiB, ...).
            If False, use decimal units (KB, MB, GB, ...). Defaults to False.

    Returns:
        str: Human-readable string representation.
    """
    if not isinstance(num, (int, float)):
        raise TypeError(f"num must be int or float, got {type(num).__name__}")
    if not isinstance(binary, bool):
        raise TypeError(f"binary must be a bool, got {type(binary).__name__}")

    units = [
        ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"],
        ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    ]
    step = 1024.0 if binary else 1000.0
    unit_list = units[1] if binary else units[0]

    abs_num = abs(num)
    if abs_num < step:
        return f"{num} {unit_list[0]}"

    for unit in unit_list[1:]:
        num /= step
        if abs(num) < step:
            return f"{num:.2f} {unit}"
    return f"{num:.2f} {unit_list[-1]}"