import json
import os
import shutil
from collections import defaultdict, Counter
import hashlib
from PIL import Image
import numpy as np

UNKNOWN_PATCH_NAME = "_UNKNOWN"


def port_patches(
        default_prior_dir,
        default_post_dir,
        resource_prior_patches_dir,
        resource_post_patches_dir,
        resource_post_dir,
        resource_prior_dir=None,
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
    :param resource_prior_dir: original resource pack (optional)
    :param default_post_patches_dir: ported default patches (optional)
    :param action: one of [None, 'copy', 'move']
    """

    default_prior_dir = os.path.expanduser(default_prior_dir)
    default_post_dir = os.path.expanduser(default_post_dir)
    resource_prior_patches_dir = os.path.expanduser(resource_prior_patches_dir)
    resource_post_patches_dir = os.path.expanduser(resource_post_patches_dir)
    resource_post_dir = os.path.expanduser(resource_post_dir)
    if resource_prior_dir:
        resource_prior_dir = os.path.expanduser(resource_prior_dir)
    if default_post_patches_dir:
        default_post_patches_dir = os.path.expanduser(default_post_patches_dir)

    os.makedirs(resource_post_patches_dir, exist_ok=True)
    os.makedirs(resource_post_dir, exist_ok=True)

    resource_prior_patch_map = {}
    resource_prior_patch_map_path = os.path.join(resource_prior_dir, "patch_map.json")
    if os.path.isfile(resource_prior_patch_map_path):
        with open(resource_prior_patch_map_path, "r") as resource_prior_patch_map_file:
            resource_prior_patch_map = json.load(resource_prior_patch_map_file)

    resource_post_patch_map = {}
    resource_post_patch_map_path = os.path.join(resource_post_dir, "patch_map.json")
    if os.path.isfile(resource_post_patch_map_path):
        with open(resource_post_patch_map_path, "r") as resource_post_patch_map_file:
            resource_post_patch_map = json.load(resource_post_patch_map_file)

    default_post_patch_map = {}
    default_post_patch_map_path = os.path.join(default_post_dir, "patch_map.json")
    if os.path.isfile(default_post_patch_map_path):
        with open(default_post_patch_map_path, "r") as default_post_patch_map_file:
            default_post_patch_map = json.load(default_post_patch_map_file)

    # used for printing completion state during long-running task
    file_total = sum([len(files) for r, d, files in os.walk(default_prior_dir)])
    file_count = 0
    file_checkpoint = 0

    # for each image in the original pack, list all textures in the resource pack
    image_hashes = defaultdict(list)  # [image_hash] => [resource_pack_paths]
    for file_dir, _, file_names in os.walk(default_prior_dir):
        for file_name in file_names:

            file_count += 1
            if file_count / file_total > file_checkpoint:
                print(f"Detection status: {file_checkpoint:.0%}")
                file_checkpoint += .05

            # .mcmeta files are also ported when the associated .png is ported
            if not file_name.endswith(".png"):
                continue

            file_path = os.path.join(file_dir, file_name)
            relative_path = file_path.replace(default_prior_dir, "")

            # don't include minecraft in ports
            if get_domain(relative_path) == "minecraft":
                continue

            # in most cases this will only contain one, as mod patches don't typically overwrite each other
            patch_names = get_patch_names(resource_prior_patches_dir, relative_path)

            # skip textures that have no patch that overwrites it
            if not patch_names:
                continue

            # skip transparent images. This check is done last because it is relatively heavy
            try:
                if np.array(Image.open(file_path).convert('RGBA').split()[-1]).sum() == 0:
                    # print(f"skipping transparent file: {file_path}")
                    continue
            except:
                pass

            # add this image/patch data to the [image_hash] => [resource_patch_paths] mapping
            with open(file_path, 'rb') as image_file:
                image_hash = hashlib.md5(image_file.read()).hexdigest()
            patch_paths = (os.path.join(patch_name, *relative_path.split(os.sep)) for patch_name in patch_names)
            image_hashes[image_hash].extend(patch_paths)

    # used for printing completion state during long-running task
    file_count = 0
    file_checkpoint = 0
    file_total = sum([len(files) for r, d, files in os.walk(default_post_dir)])

    # attempt to texture everything in the merged output space
    for file_dir, _, file_names in os.walk(default_post_dir):
        for file_name in file_names:
            file_count += 1
            if file_count / file_total > file_checkpoint:
                print(f"Remapping status: {file_checkpoint:.0%}")
                file_checkpoint += .05

            # .mcmeta files are also ported when the associated .png is ported
            if not file_name.endswith(".png"):
                continue

            file_path = os.path.join(file_dir, file_name)
            relative_path = file_path.replace(default_post_dir, "")

            # full path to the file in the output merged space
            merged_post_resource_path = os.path.join(resource_post_dir, *relative_path.split(os.sep))

            # skip if already textured
            if os.path.exists(merged_post_resource_path):
                continue

            # retrieve paths to all resource pack textures for this target image
            with open(file_path, 'rb') as image_file:
                image_hash = hashlib.md5(image_file.read()).hexdigest()
            matches = image_hashes.get(image_hash)

            if matches is None:
                continue
            # TODO: evaluate fitness of each match, and choose the best? seems very situational
            best_match = matches[0]

            # ~~~ DEFAULT PATCH NAME ~~~
            default_patch_name = None
            if default_post_patches_dir:
                # 1. patch name is recorded in the merged pack's patch_map file
                #       None if default patch_map file does not exist
                default_patch_name = get_most_frequent_patch_name(default_post_patch_map, relative_path.split(os.sep))
                # default_patch_name = get_deep(default_post_patch_map, relative_path.split(os.sep))

                # 2. patch name is the first patch that contains the same texture domain (lossy)
                if not default_patch_name:
                    default_patch_name = infer_patch_name(default_post_patches_dir, relative_path)

            if default_patch_name is None:
                # 3. patch name is a predefined constant
                default_patch_name = UNKNOWN_PATCH_NAME

            # ~~~ RESOURCE PACK PATCH NAME ~~~
            # 1. attempt to infer the patch name from the patch names of nearby files in the resource pack output space
            #       None if the resource patch_map file does not exist, or patch is not yet available in output space
            patch_name = get_most_frequent_patch_name(resource_post_patch_map, relative_path.split(os.sep))

            # 2. attempt to infer the patch name from the patch names of nearby files in the resource pack input space
            #       None if the resource_map file does not exist, or path has changed between versions
            if patch_name is None:
                patch_name = get_most_frequent_patch_name(resource_prior_patch_map, relative_path.split(os.sep))

            # 3. use the name of the first patch that contains the same texture domain (lossy)
            if patch_name is None:
                patch_name = infer_patch_name(resource_post_patches_dir, relative_path)

            # 4. find a the first match with the same texture domain, and use its patch name
            if patch_name is None:
                # if any match's domain is equal to relative path's domain, then use previous patch name
                # this is to give preference to patch names in the input space when transferring to the output space
                post_domain = get_domain(relative_path)
                for match in matches:
                    match_patch_name, *match_relative_path = match.split(os.sep)
                    if get_domain(os.path.join(*match_relative_path)) == post_domain:
                        patch_name = match_patch_name

            # 5. fall back to patch name extracted from mod jar
            if patch_name is None:
                patch_name = default_patch_name

            if patch_name is None:
                continue

            # full path to the file in the output patch space
            post_resource_path = os.path.join(resource_post_patches_dir, patch_name, *relative_path.split(os.sep))

            # if source is same as target, then this is a no-op
            prior_resource_path = os.path.join(resource_prior_patches_dir, best_match)
            if prior_resource_path == post_resource_path:
                continue

            if os.path.exists(post_resource_path):
                continue

            print()
            if len(matches) > 1:
                print(f"Multiple matches found ({len(matches)}). Mapping from first:")

            print(f'{action}: {best_match}\n'
                  f'   -> {os.path.join(patch_name, *relative_path.split(os.sep))}')

            os.makedirs(os.path.dirname(post_resource_path), exist_ok=True)

            # move or copy the file
            perform_action(prior_resource_path, post_resource_path, action)

            prior_resource_meta_path = prior_resource_path + '.mcmeta'
            if os.path.exists(prior_resource_meta_path):
                print(f'{action}: {prior_resource_meta_path.replace(resource_prior_patches_dir, "")}\n'
                      f'   -> {os.path.join(*post_resource_path.replace(resource_post_patches_dir, "").split(os.sep))}.mcmeta')

                perform_action(prior_resource_meta_path, post_resource_path + '.mcmeta', action)

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


def perform_action(from_path, to_path, action):
    if action == 'move':
        shutil.move(from_path, to_path)
    if action == 'copy':
        shutil.copy2(from_path, to_path)


def get_deep(tree, path):
    """
    Retrieve the element at the path in a tree of dictionaries.
    :param tree: nested dictionaries
    :param path: array of dictionary keys to follow
    :return: The value at the end of the path, or None
    """
    for key in path[:-1]:
        tree = tree.get(key, {})
    return tree.get(path[-1])


def flatten_values(d):
    """
    Flatten the leaves of a dictionary tree.
    :param d: tree of dictionaries
    :return: non-dictionary leaves
    """
    if isinstance(d, dict):
        for v in d.values():
            if isinstance(v, dict):
                yield from flatten_values(v)
            else:
                yield v
    else:
        yield d


def get_most_frequent_patch_name(patch_map, relative_path):
    """
    Detect the name of the patch, based on files near the relative path.
    The scope recursively broadens one step up the file tree until files are found.
    Returns None if there are no neighbors
    :param patch_map: tree of patch names for each file
    :param relative_path: location to assign a patch name
    :return: The most common patch name of the relative path's neighbors, or None if the are no neighbors
    """
    if len(relative_path) < 2:
        return
    subpatch_map = get_deep(patch_map, relative_path)
    if subpatch_map is None:
        return
    mode_meta = Counter(flatten_values(subpatch_map)).most_common(1)
    if mode_meta:
        return mode_meta[0][0]
    return get_most_frequent_patch_name(patch_map, relative_path[:-1])


def get_domain(relative_path, warn_assets=False):
    """
    Retrieve second element from relative path, with situational checks for domains
    :param relative_path: /assets/[domain]/textures/...
    :param warn_assets: warn for paths that do not start with "assets" (1.5 or nonstandard paths)
    :return: texture domain of asset behind path ("botania", "buildcraft", "ic2", etc)
    """
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

    # attempt to identify each patch name based on the domain of relative_path
    for patch_name in os.listdir(patches_dir):
        if patch_name == '.git':
            continue

        patch_dir = os.path.join(patches_dir, patch_name)
        if not os.path.isdir(patch_dir):
            continue

        for root_name in ["assets", "mods"]:  # "mods" for 1.5.x
            domain_dir = os.path.join(patch_dir, root_name)

            if not os.path.isdir(domain_dir):
                continue

            if domain in os.listdir(domain_dir):
                return patch_name


def get_patch_names(patches_dir, relative_path):
    """
    Find all patches that contain a file with the relative path.
    :param patches_dir: directory of mod patches
    :param relative_path: path to file in resource or mod patch
    :return: list of patch names
    """
    matches = []
    for patch_name in os.listdir(patches_dir):
        patch_path = os.path.join(patches_dir, patch_name, *relative_path.split(os.sep))
        if os.path.exists(patch_path):
            matches.append(patch_name)
    return matches
