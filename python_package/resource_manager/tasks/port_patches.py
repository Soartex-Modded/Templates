import json
import os
import shutil
from collections import defaultdict
import hashlib
from PIL import Image
import numpy as np

UNKNOWN_PATCH_NAME = "_UNKNOWN"


def get_domain(relative_path, warn_assets=False):
    relative_path = relative_path.split(os.sep)
    if len(relative_path) <= 2:
        return
    if warn_assets and relative_path[0] != 'assets':
        print('Texture domain used in non-"asset" directory.')

    return relative_path[1]


def infer_patch_name(patches_dir, relative_path):
    """
    Guess the patch a relative path belongs to, based on the texture domain
    :param patches_dir: directory of mod patches
    :param relative_path: path to file in resource or mod patch
    :return: patch name
    """
    domain = get_domain(relative_path)
    if not domain:
        return

    for patch in os.listdir(patches_dir):

        if patch == '.git':
            continue

        patch_dir = os.path.join(patches_dir, patch)
        if not os.path.isdir(patch_dir):
            continue

        for root_name in os.listdir(patch_dir):

            patch_dir = os.path.join(patches_dir, patch, root_name)
            if not os.path.isdir(patch_dir):
                continue

            if domain in os.listdir(patch_dir):
                return patch


def get_patch_paths(patches_dir, relative_path):
    """
    :param patches_dir: directory of mod patches
    :param relative_path: path to file in resource or mod patch
    :return: all matching relative paths from mod matches (path includes the patch name)
    """
    matches = []
    for patch_name in os.listdir(patches_dir):
        patch_path = os.path.join(patches_dir, patch_name, *relative_path.split(os.sep))
        if os.path.exists(patch_path):
            matches.append(os.path.join(patch_name, *relative_path.split(os.sep)))
    return matches


def port_patches(
        default_prior_dir,
        default_post_dir,
        resource_prior_patches_dir,
        resource_post_patches_dir,
        resource_post_dir,
        default_post_patches_dir=None,
        action=None):
    """
    Detect file movements between mod/game versions via image hashes.

    When default_post_patches_dir is specified, the script can create new mod patches

    :param default_prior_dir: original default resource pack
    :param default_post_dir: ported default resource pack
    :param resource_prior_patches_dir: original resource patches
    :param resource_post_patches_dir: ported resource patches (output)
    :param resource_post_dir: ported resource pack dir
    :param default_post_patches_dir: ported default patches (optional)
    :param action: one of [None, 'copy', 'move']
    """

    default_prior_dir = os.path.expanduser(default_prior_dir)
    default_post_dir = os.path.expanduser(default_post_dir)
    resource_prior_patches_dir = os.path.expanduser(resource_prior_patches_dir)
    resource_post_patches_dir = os.path.expanduser(resource_post_patches_dir)
    resource_post_dir = os.path.expanduser(resource_post_dir)
    default_post_patches_dir = os.path.expanduser(default_post_patches_dir)

    os.makedirs(resource_post_patches_dir, exist_ok=True)
    os.makedirs(resource_post_dir, exist_ok=True)

    image_hashes = defaultdict(list)
    file_total = sum([len(files) for r, d, files in os.walk(default_prior_dir)])
    file_count = 0
    file_checkpoint = 0

    for file_dir, _, file_names in os.walk(default_prior_dir):
        for file_name in file_names:

            file_count += 1
            if file_count / file_total > file_checkpoint:
                print(f"Detection status: {file_checkpoint:.0%}")
                file_checkpoint += .05

            if not file_name.endswith(".png"):
                continue

            file_path = os.path.join(file_dir, file_name)
            relative_path = file_path.replace(default_prior_dir, "")

            # don't include minecraft in ports
            if get_domain(relative_path) == "minecraft":
                continue

            patch_paths = get_patch_paths(resource_prior_patches_dir, relative_path)

            # if the texture has not been made in the resource pack, then skip it
            if not patch_paths:
                continue

            # skip transparent images
            try:
                if np.array(Image.open(file_path).convert('RGBA').split()[-1]).sum() == 0:
                    continue
            except:
                pass
            with open(file_path, 'rb') as image_file:
                image_hash = hashlib.md5(image_file.read()).hexdigest()
            image_hashes[image_hash].extend(patch_paths)

    file_count = 0
    file_checkpoint = 0

    file_total = sum([len(files) for r, d, files in os.walk(default_post_dir)])
    for file_dir, _, file_names in os.walk(default_post_dir):
        for file_name in file_names:
            file_count += 1
            if file_count / file_total > file_checkpoint:
                print(f"Remapping status: {file_checkpoint:.0%}")
                file_checkpoint += .05

            if not file_name.endswith(".png"):
                continue

            file_path = os.path.join(file_dir, file_name)

            with open(file_path, 'rb') as image_file:
                image_hash = hashlib.md5(image_file.read()).hexdigest()

            matches = image_hashes.get(image_hash)

            if matches is None:
                continue
            first_match = matches[0]

            relative_path = file_path.replace(default_post_dir, "")

            default_patch_name = UNKNOWN_PATCH_NAME
            if default_post_patches_dir:
                default_patch_name = infer_patch_name(default_post_patches_dir, relative_path)

            patch_name = infer_patch_name(resource_post_patches_dir, relative_path)

            if patch_name is None:
                # if any match's domain is equal to relative path's domain, then use previous patch name
                post_domain = get_domain(relative_path)
                for match in matches:
                    match_patch_name, *match_relative_path = match.split(os.sep)
                    if get_domain(os.path.join(*match_relative_path)) == post_domain:
                        patch_name = match_patch_name

                # fall back to patch name extracted from mod jar
                if patch_name is None:
                    patch_name = default_patch_name
                    if patch_name is None:
                        continue

            post_resource_path = os.path.join(resource_post_patches_dir, patch_name, *relative_path.split(os.sep))
            merged_post_resource_path = os.path.join(resource_post_dir, *relative_path.split(os.sep))
            if os.path.exists(merged_post_resource_path):
                continue

            prior_resource_path = os.path.join(resource_prior_patches_dir, first_match)
            if prior_resource_path == post_resource_path:
                continue

            print()
            if len(matches) > 1:
                print(f"Multiple matches found ({len(matches)}). Mapping from first:")

            print(f'{action}: {first_match}\n'
                  f'   -> {os.path.join(patch_name, *relative_path.split(os.sep))}')

            if action == 'move':
                os.makedirs(os.path.dirname(post_resource_path), exist_ok=True)
                shutil.move(prior_resource_path, post_resource_path)
            if action == 'copy':
                os.makedirs(os.path.dirname(post_resource_path), exist_ok=True)
                shutil.copy2(prior_resource_path, post_resource_path)

            prior_resource_meta_path = prior_resource_path + '.mcmeta'
            if os.path.exists(prior_resource_meta_path):
                if action == 'move':
                    shutil.move(prior_resource_meta_path, post_resource_path + '.mcmeta')
                if action == 'copy':
                    shutil.copy2(prior_resource_meta_path, post_resource_path + '.mcmeta')

            # use all available info to build an updated mod.json
            mod_info_path = os.path.join(resource_post_patches_dir, patch_name, 'mod.json')
            current_mod_info = {}
            if os.path.exists(mod_info_path):
                with open(mod_info_path, 'r') as mod_info_file:
                    current_mod_info = json.load(mod_info_file)

            prior_mod_info = {}
            prior_patch_name = infer_patch_name(resource_prior_patches_dir, relative_path)
            if prior_patch_name:
                prior_mod_info_path = os.path.join(resource_prior_patches_dir, prior_patch_name, 'mod.json')
                if os.path.exists(prior_mod_info_path):
                    with open(prior_mod_info_path, 'r') as prior_mod_info_file:
                        prior_mod_info = json.load(prior_mod_info_file)

            default_mod_info_path = os.path.join(default_post_patches_dir, default_patch_name, 'mod.json')
            default_mod_info = {}
            if os.path.exists(default_mod_info_path):
                with open(default_mod_info_path, 'r') as default_mod_info_file:
                    default_mod_info = json.load(default_mod_info_file)

            mod_info = {
                # default priorities
                **default_mod_info, **prior_mod_info, **current_mod_info,

                # custom priorities
                'mod_version': default_mod_info.get('mod_version', current_mod_info.get('mod_version')),
                'mc_version': default_mod_info.get('mc_version', current_mod_info.get('mc_version')),
                'mod_authors': default_mod_info.get('mod_authors', current_mod_info.get('mod_authors', prior_mod_info.get('mod_authors'))),
                'url_website': default_mod_info.get('url_website', current_mod_info.get('url_website', prior_mod_info.get('url_website'))),
                'description': default_mod_info.get('description', current_mod_info.get('description', prior_mod_info.get('description'))),

                'mod_dir': f"/{patch_name}/",
            }
            mod_info = {k: v for k, v in mod_info.items() if v is not None}

            post_mod_info_path = os.path.join(resource_post_patches_dir, patch_name, 'mod.json')
            with open(post_mod_info_path, 'w') as post_mod_info_file:
                json.dump(mod_info, post_mod_info_file, indent=4)

    if os.path.exists(os.path.join(resource_post_patches_dir, UNKNOWN_PATCH_NAME)):
        print("Check the _UNKNOWN folder for textures ported into domains that did not belong to a previous patch.")

