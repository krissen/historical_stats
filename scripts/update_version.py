#!/usr/bin/env python3
"""Update the manifest version for release packaging.

This script sets the ``version`` key in ``manifest.json`` to the
value provided on the command line. Existing version entries are
removed and the key is inserted after ``name`` and before
``codeowners`` as required by Home Assistant's manifest format.
"""

import json
import sys
from collections import OrderedDict
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

    # Load manifest JSON preserving key order
    data = json.loads(MANIFEST_PATH.read_text())

    # Convert to list of pairs and remove any existing version key
    items = [(k, v) for k, v in data.items() if k != "version"]

    # Determine position after the "name" key
    insert_at = 0
    for i, (k, _) in enumerate(items):
        if k == "name":
            insert_at = i + 1
            break

    # Insert the version key at the correct position
    items.insert(insert_at, ("version", version))

    # Build an ordered dictionary from items
    ordered = OrderedDict(items)

    # Write back with 2-space indentation and trailing newline
    MANIFEST_PATH.write_text(json.dumps(ordered, indent=2) + "\n")


if __name__ == "__main__":
    main()
