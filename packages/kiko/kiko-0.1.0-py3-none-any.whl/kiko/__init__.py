"""kiko package entry point."""

import asyncio
import sys

import kiko.commands  # noqa: F401 - Register commands for side effect import
from kiko.app import app

# import kiko.commands.filesystem
# import kiko.commands.coder

__version__ = '0.1.0'


def main():
    """Run the kiko CLI loop."""
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
