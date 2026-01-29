import re
import sys
from typing import Callable, TextIO

import click
import jinja2


@click.command()
@click.argument(
    "match_expr",
    required=True,
    # help="Regular expression to match",
)
@click.argument(
    "repl_expr",
    required=False,
    # help="Replacement expression or jinja template",
)
@click.option(
    "-i",
    "--ignore-case",
    is_flag=True,
    default=False,
    help="Do case-insensitive matching",
)
@click.option(
    "-o",
    "--only-matching",
    is_flag=True,
    default=False,
    help="Only output match results",
)
@click.option(
    "-g",
    "--grep",
    is_flag=True,
    default=False,
    help="Only output matching lines",
)
@click.option(
    "-j",
    "--jinja",
    "use_jinja",
    is_flag=True,
    default=False,
    help="Use a jinja template for replacement",
)
def main(
    match_expr: str,
    repl_expr: str | None,
    ignore_case: bool,
    only_matching: bool,
    grep: bool,
    use_jinja: bool,
):
    flags = 0
    if ignore_case:
        flags |= re.IGNORECASE
    pattern = re.compile(match_expr, flags=flags)

    if use_jinja and (repl_expr is not None):
        template = create_jinja_template(repl_expr)

        def replacement(m: re.Match):
            return template.render(m.groupdict())

    else:
        if repl_expr is None:
            # The backreference \g<0> substitutes in the entire
            # substring matched by the RE.
            repl_expr = r"\g<0>"

        def replacement(m: re.Match):
            return m.expand(repl_expr)

    run_stred(
        sys.stdin,
        sys.stdout,
        pattern=pattern,
        replacement=replacement,
        only_matching=only_matching,
        grep=grep,
    )


def create_jinja_template(text: str) -> jinja2.Template:
    env = jinja2.Environment(autoescape=False)
    return env.from_string(text)


def run_stred(
    stream: TextIO,
    outstream: TextIO,
    pattern: re.Pattern,
    replacement: str | None | Callable[[re.Match], str],
    only_matching=False,
    grep=False,
):
    for line in stream:
        line = line.strip()

        if only_matching:
            # Print each match individually, formatted as needed
            for m in pattern.finditer(line):
                outstream.write(replacement(m))
                outstream.write("\n")

        else:
            # Print every line, applying replacements
            (newl, cnt) = pattern.subn(replacement, line)
            if grep and cnt <= 0:
                # No matches -> skip
                continue
            outstream.write(newl)
            outstream.write("\n")
