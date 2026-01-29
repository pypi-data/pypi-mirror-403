def humanbytes(num, binary=False):
    """
    Convert a number of bytes into a human-readable string.

    Args:
        num (int or float): The number to convert (e.g., bytes).
        binary (bool): If True, use binary units (KiB, MiB, GiB, ...).
                      If False, use decimal units (KB, MB, GB, ...).

    Returns:
        str: Human-readable string representation.
    """
    if binary:
        units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
        step = 1024.0
    else:
        units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
        step = 1000.0

    if num < step:
        return f"{num} {units[0]}"

    for i, unit in enumerate(units[1:], 1):
        num /= step
        if abs(num) < step:
            return f"{num:.2f} {unit}"
    return f"{num:.2f} {units[-1]}"