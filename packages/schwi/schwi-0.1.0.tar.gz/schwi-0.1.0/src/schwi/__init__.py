"""schwi package entry point."""

import asyncio
import sys

import schwi.commands  # noqa: F401 - Register commands for side effect import
from schwi.app import app

# import schwi.commands.filesystem
# import schwi.commands.coder

__version__ = '0.1.0'


def main():
    """Run the schwi CLI loop."""
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
