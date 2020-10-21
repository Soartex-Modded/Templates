import os
import json


def detect_overwrites(patches_dir):
    """
    Detect file locations that are present in multiple patches.
    :param patches_dir: directory of resource patches
    """
    patches_dir = os.path.expanduser(patches_dir)
    patch_map = {}

    for patch_name in os.listdir(patches_dir):
        if patch_name == '.git':
            continue
        patch_dir = os.path.join(patches_dir, patch_name)

        for walk_dir, _, file_names in os.walk(patch_dir):
            relative_dir = [i for i in walk_dir.replace(patch_dir, "").split(os.sep) if i]
            for file_name in file_names:
                if file_name == '.DS_Store' or file_name == 'mod.json':
                    continue
                file_path = os.path.join(*relative_dir, file_name)
                append_deep(patch_map, file_path.split(os.sep), patch_name)

    for patch_name in os.listdir(patches_dir):
        if patch_name == '.git':
            continue
        patch_dir = os.path.join(patches_dir, patch_name)

        for walk_dir, folder_names, file_names in os.walk(patch_dir, topdown=False):
            num_items = len([i for i in file_names if i != '.DS_Store' and i != 'mod.json']) + len(folder_names)

            relative_dir = [i for i in walk_dir.replace(patch_dir, "").split(os.sep) if i]
            if not relative_dir:
                continue

            folder_patches = get_deep(patch_map, relative_dir)
            if not folder_patches or isinstance(folder_patches, list):
                continue

            if any(isinstance(i, dict) for i in folder_patches.values()):
                continue

            unique_patches = set(json.dumps(i) for i in folder_patches.values())
            if len(unique_patches) == 1 and len(folder_patches) == num_items:
                # print("collapsing:", relative_dir)
                set_deep(patch_map, relative_dir, json.loads(next(iter(unique_patches))))

    patch_map_pruned = erase_singletons(patch_map)
    print(json.dumps(patch_map_pruned, indent=2))


def append_deep(tree, path, value):
    """
    1. Create empty array at path if not exists
    2. Append value to array at path
    :param tree: nested dictionaries
    :param path: array of dictionary keys to follow
    :param value:
    """
    for key in path[:-1]:
        tree = tree.setdefault(key, {})
    tree.setdefault(path[-1], [])
    if isinstance(tree[path[-1]], list):
        tree[path[-1]].append(value)


def get_deep(tree, path):
    """
    Retrieve the element at the path in a tree of dictionaries.
    :param tree: nested dictionaries
    :param path: array of dictionary keys to follow
    :return: The value at the end of the path, or None
    """
    for key in path[:-1]:
        if key in tree and isinstance(tree[key], list):
            return
        tree = tree.get(key, {})
    return tree.get(path[-1])


def set_deep(tree, path, value):
    """
    Set the value at path in a tree of dictionaries.
    :param tree: nested dictionaries
    :param path: array of dictionary keys to follow
    :return: The value at the end of the path, or None
    """
    for key in path[:-1]:
        tree = tree.setdefault(key, {})
    tree[path[-1]] = value


def erase_singletons(tree):
    """
    1. remove leaf nodes that are singleton arrays
    2. Remove empty (falsey) branches

    Does not modify input.
    :param tree: nested dictionaries
    :return: pruned tree
    """
    response = {}
    for key, value in tree.items():
        if isinstance(value, dict):
            value = erase_singletons(value)
            if value:
                response[key] = value
        if not (isinstance(value, list) and len(value) == 1):
            response[key] = value

    return response
