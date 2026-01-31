"""Command line interface for :mod:`figshare_client`."""

import click

__all__ = [
    "main",
]


@click.command()
def main() -> None:
    """CLI for figshare_client."""


if __name__ == "__main__":
    main()
