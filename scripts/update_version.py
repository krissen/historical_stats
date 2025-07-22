#!/usr/bin/env python3
"""Update manifest version for release packaging.

This script sets the "version" key in the manifest to the value
provided on the command line and ensures it appears after the
"name" key without duplicates.
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

    # Load manifest JSON
    data = json.loads(MANIFEST_PATH.read_text(), object_pairs_hook=OrderedDict)

    # Rebuild to ensure "version" is after "name" and unique
    new_data = OrderedDict()
    for key, value in data.items():
        if key == "version":
            continue
        new_data[key] = value
        if key == "name":
            new_data["version"] = version

    if "version" not in new_data:
        new_data["version"] = version

    MANIFEST_PATH.write_text(json.dumps(new_data, indent=2) + "\n")


if __name__ == "__main__":
    main()
