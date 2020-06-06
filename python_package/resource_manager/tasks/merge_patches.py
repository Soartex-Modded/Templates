import os
import shutil
from distutils.dir_util import copy_tree
import json


def merge_patches(patches_dir, pack_dir, pack_format):
    """
    delete and (re)make the resource pack of merged patches
    """
    patches_dir = os.path.expanduser(patches_dir)
    pack_dir = os.path.expanduser(pack_dir)

    if os.path.exists(pack_dir):
        shutil.rmtree(pack_dir)

    os.makedirs(pack_dir, exist_ok=True)
    os.makedirs(patches_dir, exist_ok=True)

    # copy all mods into resource pack
    for mod_name in os.listdir(patches_dir):
        if mod_name == '.git':
            continue

        mod_dir = os.path.join(patches_dir, mod_name)
        if os.path.isdir(mod_dir):
            copy_tree(mod_dir, pack_dir)

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
