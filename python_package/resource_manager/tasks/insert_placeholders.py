import os
import shutil

from PIL import Image
import PIL

from resource_manager.tasks.port_patches import get_domain, infer_patch_name

default_prefix = "__default_"


def insert_placeholders(
        scale,
        resource_dir,
        resource_patches_dir,
        default_dir):
    """
    Add placeholder files among resource pack assets.
    The placeholders start with a prefix __default_, so they can be differentiated against actual textured files.
    Files starting with __default_ are .gitignored.
    This script deletes placeholders that are not backed by default textures, or have been textured.

    :param scale: size multiplier
    :param resource_dir: merged resource pack
    :param resource_patches_dir: resource pack patches
    :param default_dir: default resource pack
    """
    resource_dir = os.path.expanduser(resource_dir)
    resource_patches_dir = os.path.expanduser(resource_patches_dir)
    default_dir = os.path.expanduser(default_dir)

    # used for printing completion state during long-running task
    file_total = sum([len(files) for r, d, files in os.walk(default_dir)])
    file_count = 0
    file_checkpoint = 0

    for walk_dir, _, file_names in os.walk(default_dir):
        for file_name in file_names:

            file_count += 1
            if file_count / file_total > file_checkpoint:
                print(f"Placeholders status: {file_checkpoint:.0%}")
                file_checkpoint += .05

            if not file_name.endswith(".png"):
                continue

            file_path = os.path.join(walk_dir, file_name)
            relative_path = file_path.replace(default_dir, "")

            # texture has already been made
            if os.path.exists(os.path.join(resource_dir, relative_path)):
                continue

            # don't add defaults for minecraft
            if get_domain(relative_path) == "minecraft":
                continue

            # detect which patch the default texture belongs to
            patch_name = infer_patch_name(resource_patches_dir, relative_path)

            if not patch_name:
                continue

            # (over)write this file
            output_path = os.path.join(
                resource_patches_dir,
                patch_name,
                os.path.dirname(relative_path), f"{default_prefix}{file_name}")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if os.path.exists(output_path):
                os.remove(output_path)

            if scale != 1:
                image = Image.open(file_path)
                image.resize((image.width * scale, image.height * scale), resample=PIL.Image.NEAREST).save(output_path)
            else:
                shutil.copy2(file_path, output_path)

    # remove placeholder textures
    for walk_dir, _, file_names in os.walk(resource_patches_dir):
        for file_name in file_names:

            if not file_name.startswith(default_prefix):
                continue

            file_path = os.path.join(walk_dir, file_name)
            relative_path = file_path.replace(resource_patches_dir, "")

            # delete placeholder if textured
            resource_path = os.path.join(walk_dir, file_name.replace(default_prefix, ""))
            if os.path.exists(resource_path):
                os.remove(file_path)

            # delete placeholder if not backed by default texture
            default_path = os.path.join(default_dir, relative_path)
            if not os.path.exists(default_path):
                os.remove(file_path)


def delete_placeholders(resource_patches_dir):
    """
    Delete all files starting with __default_
    """
    for walk_dir, _, file_names in os.walk(resource_patches_dir):
        for file_name in file_names:
            if file_name.startswith(default_prefix):
                os.remove(os.path.join(walk_dir, file_name))
