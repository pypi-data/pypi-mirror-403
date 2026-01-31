from typing import List

from bluer_options.terminal import show_usage


def help_get(
    tokens: List[str],
    mono: bool,
) -> str:
    args = [
        "[--include_comments 1]",
    ]

    return show_usage(
        [
            "@ugv",
            "get",
            "<ugv-name>",
            "computers.back | computers.front | computers.top | <what>",
        ]
        + args,
        "get ugv info.",
        mono=mono,
    )
