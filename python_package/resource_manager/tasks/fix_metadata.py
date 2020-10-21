import os
import unicodedata
import difflib
import json
import re
import shutil


def fix_mod_jsons(patches_dir):
    """
    Ensure all mod ids within mod.json files have valid slugs.
    :param patches_dir:
    """
    patches_dir = os.path.expanduser(patches_dir)
    for patch_name in os.listdir(patches_dir):

        patch_dir = os.path.join(patches_dir, patch_name)
        if patch_name == ".git" or not os.path.isdir(patch_dir):
            continue

        ideal_patch_name = patch_name.replace(" ", "_")
        if ideal_patch_name != patch_name:
            print(f"Modified patch folder: {patch_name}\n"
                  f"                    -> {ideal_patch_name}")
            new_patch_dir = os.path.join(patches_dir, ideal_patch_name)
            shutil.move(patch_dir, new_patch_dir)
            patch_dir = new_patch_dir
            patch_name = ideal_patch_name

        mod_json_path = os.path.join(patch_dir, "mod.json")
        if not os.path.exists(mod_json_path):
            print('missing mod.json:', patch_name)
            continue

        try:
            with open(mod_json_path, "r") as mod_json_file:
                mod_json = json.load(mod_json_file)
        except json.decoder.JSONDecodeError as err:
            print("Invalid mod.json:", patch_name)
            print(err)
            continue

        mod_id = mod_json.get('mod_id')
        if not mod_id:
            print("Missing mod_id:", patch_name)
            if 'mod_name' in mod_json:
                mod_id = mod_json.get("mod_name")
            else:
                continue

        ideal_mod_id = slugify(mod_id)
        if ideal_mod_id != mod_id:
            print(f"Modified mod_id: {mod_id}\n"
                  f"              -> {ideal_mod_id}")
            mod_json['mod_id'] = ideal_mod_id

        ideal_mod_dir = f"/{patch_name}/"
        if mod_json['mod_dir'] != ideal_mod_dir:
            print(f"Modified mod_dir: {mod_json['mod_dir']}\n"
                  f"               -> {ideal_mod_dir}")
            mod_json['mod_dir'] = ideal_mod_dir

        with open(mod_json_path, 'w') as mod_json_file:
            json.dump(mod_json, mod_json_file, indent=4)


def slugify(value):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)


def _fix_server_data():
    """
    1. Renames mod ids to be valid.
    2. Identifies potentially mislabeled mod ids.
    """
    pack_list_dir = os.path.expanduser("~/graphics/fanver/Modded-Server-Data/packs")
    for walk_dir, _, file_names in os.walk(pack_list_dir):
        for file_name in file_names:
            if not file_name.endswith(".json"):
                continue

            config_path = os.path.join(walk_dir, file_name)

            print("Loading:", config_path)
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)

            if not config.get('mods'):
                continue

            for mod_id in config['mods']:
                ideal_mod_id = slugify(mod_id)
                if ideal_mod_id != mod_id:
                    print(f"Modified mod_id: {mod_id}\n"
                          f"              -> {ideal_mod_id}")

            config['mods'] = [slugify(mod_id) for mod_id in config['mods']]

            all_mod_ids = set()
            for mc_version in config['minecraft']:
                patches_dir = os.path.join(os.path.expanduser("~/graphics/fanver/"), f"Modded-{mc_version}")
                if not os.path.exists(patches_dir):
                    print("Missing path:", patches_dir)
                    continue

                print("\nMC Version:", mc_version)
                patch_mod_ids = []
                for patch_name in os.listdir(patches_dir):
                    patch_dir = os.path.join(patches_dir, patch_name)
                    if patch_name == ".git" or not os.path.isdir(patch_dir):
                        continue
                    with open(os.path.join(patch_dir, "mod.json"), "r") as mod_json_file:
                        patch_mod_ids.append(json.load(mod_json_file)["mod_id"])

                for mod_id in config['mods']:
                    if mod_id not in patch_mod_ids:
                        print(f"Missing patch: {mod_id}")
                        mod_id = input_best_mod_id(mod_id, patch_mod_ids)
                    all_mod_ids.add(mod_id)

            config['mods'] = list(all_mod_ids)

            with open(config_path, 'w') as config_file:
                json.dump(config, config_file, indent=4)


def input_best_mod_id(mod_id, patch_mod_ids):
    close_matches = difflib.get_close_matches(mod_id, patch_mod_ids, n=5, cutoff=0.7)
    if close_matches:
        selection = input("\n".join([
            "    (ret) *keep*",
            *[f"    ( {idx + 1} ) {match}" for idx, match in enumerate(close_matches)]
        ]) + "\n    ")
        try:
            mod_id = close_matches[int(selection) - 1]
            print("    switched to", mod_id)
        except ValueError:
            print("    no change")
        print()
    return mod_id


# _slugify_server_data()
