import os
import shutil
from distutils.dir_util import copy_tree
import json


def set_deep(obj, path, value):
    for key in path[:-1]:
        obj = obj.setdefault(key, {})
    obj[path[-1]] = value


def merge_patches(patches_dir, pack_dir, pack_format: int, enable_patch_map: bool = True, delete_defaults: bool = True):
    """
    delete and (re)make the resource pack of merged patches
    :param patches_dir: location of patches
    :param pack_dir: location to output merged patches
    :param pack_format: necessary metadata to build pack.json
    :param enable_patch_map: create a patch_map.json file with the source patch of each texture
    :param delete_defaults: delete filenames starting with __default_
    """
    patches_dir = os.path.expanduser(patches_dir)
    pack_dir = os.path.expanduser(pack_dir)

    if os.path.exists(pack_dir):
        shutil.rmtree(pack_dir)

    os.makedirs(pack_dir, exist_ok=True)
    os.makedirs(patches_dir, exist_ok=True)

    patch_map = {}

    # copy all mods into resource pack
    for patch_name in os.listdir(patches_dir):
        patch_dir = os.path.join(patches_dir, patch_name)

        if patch_name == '.git' or not os.path.isdir(patch_dir):
            continue

        copy_tree(patch_dir, pack_dir)

        if enable_patch_map:
            for file_dir, _, file_names in os.walk(patch_dir):
                relative_dir = [i for i in file_dir.replace(patch_dir, "").split(os.sep) if i]
                for file_name in file_names:
                    if file_name.endswith(".png"):
                        set_deep(patch_map, [*relative_dir, file_name], patch_name)

    # delete the remaining mod.json
    mod_mcmeta = os.path.join(pack_dir, "mod.json")
    if os.path.exists(mod_mcmeta):
        os.remove(mod_mcmeta)

    # add pack metadata
    root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "root")
    copy_tree(root_dir, pack_dir)

    pack_mcmeta_path = os.path.join(pack_dir, "pack.mcmeta")
    with open(pack_mcmeta_path, 'w') as pack_mcmeta_file:
        json.dump({
            "pack": {
                "pack_format": pack_format,
                "description": f"Merged patches from {os.path.basename(os.path.normpath(patches_dir))}"
            }
        }, pack_mcmeta_file, indent=4)

    if enable_patch_map:
        patch_map_path = os.path.join(pack_dir, "patch_map.json")
        with open(patch_map_path, 'w') as patch_map_file:
            json.dump(patch_map, patch_map_file, indent=4)

    if delete_defaults:
        for file_dir, _, file_names in os.walk(pack_dir):
            for file_name in file_names:
                if file_name.startswith("__default_"):
                    os.remove(os.path.join(file_dir, file_name))
