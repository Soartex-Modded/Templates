import os
import shutil
from collections import defaultdict
import hashlib
from PIL import Image
import numpy as np


def get_domain(relative_path):
    relative_path = relative_path.split(os.sep)
    if len(relative_path) <= 2 or relative_path[0] != 'assets':
        return

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

        patch_dir = os.path.join(patches_dir, patch, 'assets')
        if not os.path.isdir(patch_dir):
            continue

        if domain in os.listdir(patch_dir):
            return patch


def get_patch_paths(patches_dir, relative_path):
    """
    :param patches_dir: directory of mod patches
    :param relative_path: path to file in resource or mod patch
    :return: all matching relative paths from mod matches
    """
    matches = []
    for patch_name in os.listdir(patches_dir):
        patch_path = os.path.join(patches_dir, patch_name, *relative_path.split(os.sep))
        if os.path.exists(patch_path):
            matches.append(os.path.join(patch_name, *relative_path.split(os.sep)))
    return matches


def port_patches(default_prior_dir, default_post_dir, resource_prior_patches_dir, resource_post_patches_dir, resource_post_dir, action=None):
    """
    Detect file movements between mod/game versions based on image hashes.
    :param default_prior_dir: original default resource pack
    :param default_post_dir: ported default resource pack
    :param resource_prior_patches_dir: original resource patches
    :param resource_post_patches_dir: ported resource patches (output)
    :param resource_post_dir: ported resource pack dir
    :param action: one of [None, 'copy', 'move']
    """

    default_prior_dir = os.path.expanduser(default_prior_dir)
    default_post_dir = os.path.expanduser(default_post_dir)
    resource_prior_patches_dir = os.path.expanduser(resource_prior_patches_dir)
    resource_post_patches_dir = os.path.expanduser(resource_post_patches_dir)
    resource_post_dir = os.path.expanduser(resource_post_dir)

    os.makedirs(resource_post_patches_dir, exist_ok=True)
    os.makedirs(resource_post_dir, exist_ok=True)

    check_patches = set()

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

            relative_path = file_path.replace(default_post_dir, "")

            first_match = matches[0]

            poor_patch_name = False
            # inferring patch name:
            # 1. use matching texture domain in the posterior space
            # 2. use matching texture domain in the prior space
            # 3. use the patch the texture was moved from
            patch_name = infer_patch_name(resource_post_patches_dir, relative_path)
            if not patch_name and resource_prior_patches_dir != resource_post_patches_dir:
                patch_name = infer_patch_name(resource_prior_patches_dir, relative_path)
            if not patch_name:
                patch_name = first_match.split(os.sep)[0]
                poor_patch_name = True

            post_resource_path = os.path.join(resource_post_patches_dir, patch_name, *relative_path.split(os.sep))
            merged_post_resource_path = os.path.join(resource_post_dir, *relative_path.split(os.sep))
            if os.path.exists(merged_post_resource_path):
                continue

            if poor_patch_name:
                check_patches.add(patch_name)

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

            prior_resource_meta_path = prior_resource_path.replace('.png', '.mcmeta')
            if os.path.exists(prior_resource_meta_path):
                if action == 'move':
                    shutil.move(prior_resource_meta_path, post_resource_path.replace('.png', '.mcmeta'))
                if action == 'copy':
                    shutil.copy2(prior_resource_meta_path, post_resource_path.replace('.png', '.mcmeta'))

    print(f"Check these patches for unwanted texture domains: {check_patches}")
