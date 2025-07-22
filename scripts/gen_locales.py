#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Adjust this path if your repository structure differs
TRANSLATIONS_DIR = (
    Path(__file__).parent.parent / "custom_components/historical_stats/translations"
)

MASTER = "en.json"

PY_FILES_TO_SCAN = [
    Path(__file__).parent.parent / "custom_components/historical_stats/config_flow.py",
    Path(__file__).parent.parent / "custom_components/historical_stats/sensor.py",
]

ICON_OK = "✅"
ICON_WARN = "⚠️"
ICON_ADD = "➕"
ICON_DEL = "❌"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def flatten(d, parent_key="", sep="."):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep=sep))
        else:
            items.append((new_key, v))
    return items


def unflatten(flat, sep="."):
    result = {}
    for key, value in flat.items():
        keys = key.split(sep)
        d = result
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
    return result


def find_missing_and_redundant():
    files = sorted([f for f in TRANSLATIONS_DIR.glob("*.json")])
    master_path = TRANSLATIONS_DIR / MASTER
    if not master_path.exists():
        print(f"{ICON_WARN} Master file {master_path} not found.")
        sys.exit(1)
    master = load_json(master_path)
    master_flat = dict(flatten(master))
    missing_per_lang = defaultdict(list)
    redundant_per_lang = defaultdict(list)
    for file in files:
        if file.name == MASTER:
            continue
        data = load_json(file)
        data_flat = dict(flatten(data))
        for key in master_flat:
            if key not in data_flat:
                missing_per_lang[file.stem].append(key)
        for key in data_flat:
            if key not in master_flat:
                redundant_per_lang[file.stem].append(key)
    return master, master_flat, missing_per_lang, redundant_per_lang


def find_used_keys_in_py():
    used_keys = set()
    for py_file in PY_FILES_TO_SCAN:
        if py_file.exists():
            content = py_file.read_text(encoding="utf-8")
            # Extract translation keys (simplified; adjust regex as needed)
            # Example: hass.config_entries.async_show_form(..., errors={"no_sensors_for_country": ...})
            found = re.findall(r'["\']([a-zA-Z0-9_.-]+)["\']', content)
            for match in found:
                # Assume only keys containing a dot are translation keys
                if "." in match:
                    used_keys.add(match)
    return used_keys


def scan_missing():
    master, master_flat, missing_per_lang, redundant_per_lang = (
        find_missing_and_redundant()
    )

    # Check keys used in Python files
    used_keys = find_used_keys_in_py()
    missing_in_master = sorted(k for k in used_keys if k not in master_flat)
    if missing_in_master:
        print(f"{ICON_WARN} Keys used in .py files but missing in {MASTER}:")
        for key in missing_in_master:
            print(
                f"  {ICON_WARN} '{key}' is used in .py files but not present in {MASTER}"
            )

    # Report missing keys per language
    if not missing_per_lang:
        print(f"{ICON_OK} All language files contain all keys from the master file.")
    else:
        print(f"{ICON_ADD} Missing keys:")
        for key in master_flat:
            missing_in = [
                lang for lang, keys in missing_per_lang.items() if key in keys
            ]
            if missing_in:
                print(
                    f"  {ICON_WARN} '{key}' (\"{master_flat[key]}\" in {MASTER}) missing in:\n      {', '.join(missing_in)}"
                )
    # Report redundant keys
    all_redundant_keys = defaultdict(list)
    for lang, keys in redundant_per_lang.items():
        for key in keys:
            all_redundant_keys[key].append(lang)
    if all_redundant_keys:
        print(f"\n{ICON_DEL} Redundant keys (not in {MASTER}):")
        for key, langs in all_redundant_keys.items():
            print(f"  {ICON_DEL} '{key}' found in: {', '.join(langs)}")


def gen_translation_json():
    master, master_flat, missing_per_lang, _ = find_missing_and_redundant()
    output = defaultdict(dict)
    for lang, keys in missing_per_lang.items():
        for key in keys:
            output[lang][key] = master_flat[key]
    if output:
        output_text = (
            "\n# Translate the block below for each language:\n\n"
            + json.dumps(output, ensure_ascii=False, indent=2)
            + "\n\n---\n"
            + "Save the translations to a file and run:\n\n"
            + f"  python3 {Path(__file__).name} update path/to/translation.json\n"
        )
        print(output_text)
        try:
            subprocess.run("pbcopy", input=output_text, text=True, check=True)
            print(f"{ICON_OK} JSON and instructions copied to clipboard (pbcopy)")
        except Exception as e:
            print(f"{ICON_WARN} Could not copy to clipboard: {e}")
    else:
        print(
            f"{ICON_OK} All language files already contain every key from the master file."
        )


def update_with_translation(json_path, force=False):
    with open(json_path, encoding="utf-8") as f:
        translation = json.load(f)
    for lang, keys in translation.items():
        loc_file = TRANSLATIONS_DIR / (lang + ".json")
        if not loc_file.exists():
            print(f"{ICON_WARN} Language file missing: {loc_file}")
            continue
        data = load_json(loc_file)
        data_flat = dict(flatten(data))
        count_new = 0
        count_updated = 0
        for key, val in keys.items():
            if key not in data_flat:
                data_flat[key] = val
                count_new += 1
            elif force:
                if data_flat[key] != val:
                    data_flat[key] = val
                    count_updated += 1
        if count_new or (force and count_updated):
            # Save again as nested JSON
            save_json(loc_file, unflatten(data_flat))
            msg = f"{ICON_OK} {lang}.json: {count_new} new keys added"
            if force and count_updated:
                msg += f", {count_updated} updated (force=True)"
            print(msg)
        else:
            msg = f"{ICON_OK} {lang}.json: no new keys added"
            if force:
                msg += " (force=True)"
            print(msg)


def delete_redundant():
    _, master_flat, _, redundant_per_lang = find_missing_and_redundant()
    files = sorted([f for f in TRANSLATIONS_DIR.glob("*.json")])
    total_removed = 0
    for file in files:
        if file.name == MASTER:
            continue
        data = load_json(file)
        data_flat = dict(flatten(data))
        redundant = [key for key in data_flat if key not in master_flat]
        if redundant:
            for key in redundant:
                del data_flat[key]
            save_json(file, unflatten(data_flat))
            print(
                f"{ICON_DEL} {file.name}: removed {len(redundant)} redundant keys: {', '.join(redundant)}"
            )
            total_removed += len(redundant)
        else:
            print(f"{ICON_OK} {file.name}: no redundant keys.")
    if total_removed == 0:
        print(f"{ICON_OK} No redundant keys to remove.")
    else:
        print(f"{ICON_DEL} Total removed keys: {total_removed}")


if __name__ == "__main__":
    cmds = []
    update_file = None
    force = False
    args = sys.argv[1:]

    for i, arg in enumerate(args):
        arg_l = arg.lower()
        if arg_l in ("scan", "gen", "update", "clean"):
            cmds.append(arg_l)
        elif arg_l in ("--force", "-f"):
            force = True
        elif arg.endswith(".json"):
            update_file = arg

    if not cmds:
        cmds = ["scan"]

    for cmd in cmds:
        if cmd == "scan":
            scan_missing()
        elif cmd == "gen":
            gen_translation_json()
        elif cmd == "update":
            if update_file:
                update_with_translation(update_file, force=force)
            else:
                print(f"{ICON_WARN} No translation file provided for update.")
        elif cmd == "clean":
            delete_redundant()
        else:
            print(f"{ICON_WARN} Unknown command: {cmd}")

    if not cmds or all(cmd not in ("scan", "gen", "update", "clean") for cmd in cmds):
        print(
            "\nUsage:\n"
            f"  python3 {Path(__file__).name} scan\n"
            f"  python3 {Path(__file__).name} gen\n"
            f"  python3 {Path(__file__).name} update translation.json [--force|-f]\n"
            f"  python3 {Path(__file__).name} clean\n"
            "\nYou can combine several commands in any order, e.g.\n"
            f"  python3 {Path(__file__).name} update translation.json clean\n"
        )
