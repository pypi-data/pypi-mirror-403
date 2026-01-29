"""Methods for working with files."""

from rwskit.io_ import PathLike


def count_lines(filename: PathLike) -> int:
    """Count the lines of a file."""
    # See this Stack Overflow post: https://stackoverflow.com/a/27518377

    lines = 0
    buffer_size = 1024 * 1024

    with open(str(filename), "rb") as fh:
        read_f = fh.raw.read
        buffer = read_f(buffer_size)

        while buffer:
            lines += buffer.count(b"\n")
            buffer = read_f(buffer_size)

    return lines
