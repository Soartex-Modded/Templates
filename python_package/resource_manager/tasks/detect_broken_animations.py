import os
from PIL import Image


def detect_broken_animations(pack_dir):
    """
    Print relative paths to rectangular block/item files missing .mcmeta files

    :param pack_dir: directory of a resource pack
    """

    for walk_dir, _, file_names in os.walk(pack_dir):
        for file_name in file_names:
            file_path = os.path.join(walk_dir, file_name)

            if not (f"textures{os.sep}blocks" in file_path or f"textures{os.sep}items" in file_path):
                continue

            if not file_name.endswith(".png"):
                continue

            image = Image.open(file_path)
            if image.width == image.height:
                continue

            if os.path.exists(file_path + ".mcmeta"):
                continue

            # relative_path = pack_dir.replace(file_path, walk_dir)
            print("Missing .mcmeta file:", file_path)
