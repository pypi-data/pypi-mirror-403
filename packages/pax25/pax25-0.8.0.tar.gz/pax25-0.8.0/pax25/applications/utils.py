"""
Helper utilities for application building.
"""

from collections import defaultdict
from collections.abc import Iterable
from itertools import zip_longest

from pax25.services.connection.connection import Connection


def send_message(
    connection: Connection, message: str, append_newline: bool = True
) -> None:
    """
    Send a message string to a particular connection.
    """
    if append_newline:
        message += "\r"
    connection.send_bytes(message.encode("utf-8"))


def build_columns(
    entries_list: Iterable[str],
    num_columns: int = 6,
    column_width: int = 9,
) -> list[str]:
    """
    Build a list of items into columns. Set num_columns to the number of columns to sort
    the entries into.

    If an entry is longer than the width, the width of that column will be expanded.
    """
    columns: list[list[str]] = [[] for _ in range(num_columns)]
    widths: defaultdict[int, int] = defaultdict(lambda: column_width)
    column_number = 0
    for entry in entries_list:
        columns[column_number].append(entry)
        length = len(entry)
        if widths[column_number] < length:
            widths[column_number] = length
        column_number += 1
        if column_number >= num_columns:
            column_number = 0
    # This might truncate some commands, but since there's autocomplete, it's
    # unlikely to matter.
    lines: list[str] = []
    for row in zip_longest(*columns, fillvalue=""):
        lines.append(
            " ".join(
                column.ljust(widths[index]) for index, column in enumerate(row)
            ).strip()
        )
    return lines


def build_table(
    entries_list: Iterable[Iterable[str]],
) -> list[str]:
    """
    Build a table with automatic column sizing. You must set your own separator when
    joining them afterward.
    """
    column_sizes: defaultdict[int, int] = defaultdict(lambda: 0)
    # First, we must measure the column widths.
    for line in entries_list:
        for index, item in enumerate(line):
            if len(item) > column_sizes[index]:
                column_sizes[index] = len(item)
    lines = []
    for line in entries_list:
        lines.append(
            " ".join(
                (item.ljust(column_sizes[index]) for index, item in enumerate(line))
            )
        )
    return lines
