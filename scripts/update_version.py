#!/usr/bin/env python3
"""Update manifest version for release packaging.

This script sets the "version" key in the manifest to the
value provided on the command line.
"""

import json
import sys
from pathlib import Path

MANIFEST_PATH = (
    Path(__file__).parent.parent
    / "custom_components"
    / "historical_stats"
    / "manifest.json"
)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: update_version.py <version>")
        sys.exit(1)

    version = sys.argv[1]

    # Load manifest JSON
    data = json.loads(MANIFEST_PATH.read_text())

    # Update version key
    data["version"] = version

    # Write back with 2-space indentation
    MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
