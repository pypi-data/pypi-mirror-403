import webbrowser
from importlib.metadata import version

import click

# Package name
PACKAGE_NAME = "ts-ids-core"

# Public documentation URL
DOCS_BASE_URL = "https://ids.tetrascience.com/"


def get_docs_url() -> str:
    """Build the docs URL with package and version query parameters."""
    package_version = version(PACKAGE_NAME)
    return f"{DOCS_BASE_URL}?package={PACKAGE_NAME}&version={package_version}"


@click.command(help="Open the programmatic IDS documentation in your browser.")
def docs():
    """Open the public IDS documentation site in the default browser."""
    webbrowser.open(get_docs_url())


if __name__ == "__main__":
    docs()
