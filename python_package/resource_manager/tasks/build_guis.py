import os
import shutil
try:
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
except ModuleNotFoundError:
    plt = None


from resource_manager.gui_builder.builder import build_gui
from resource_manager.gui_builder.detector import detect_regions
from resource_manager.tasks.port_patches import get_patch_names


templates_dir = os.sep + os.path.join(
    *os.path.dirname(os.path.realpath(__file__)).split(os.sep)[:-1],
    'configs',
    'gui_templates')
default_template_dir = os.path.join(templates_dir, "default")


def build_guis(
        resource_dir,
        resource_patches_dir,
        default_dir,
        default_patches_dir=None,
        debug_path=None):
    """
    Construct GUIs based on templates mined from default textures

    When default_patches_dir is specified, the script can create new mod patches

    :param resource_dir: merged resource pack
    :param resource_patches_dir: resource pack patches
    :param default_dir: default resource pack
    :param default_patches_dir: ported default patches (optional)
    :param debug_path: path to output buggy textures (optional)
    """

    resource_dir = os.path.expanduser(resource_dir)
    resource_patches_dir = os.path.expanduser(resource_patches_dir)
    default_dir = os.path.expanduser(default_dir)
    default_patches_dir = os.path.expanduser(default_patches_dir)
    debug_path = os.path.expanduser(debug_path)

    # used for printing completion state during long-running task
    file_total = sum([len(files) for r, d, files in os.walk(default_dir)])
    file_count = 0
    file_checkpoint = 0

    for walk_dir, _, file_names in os.walk(default_dir):
        for file_name in file_names:

            file_count += 1
            if file_count / file_total > file_checkpoint:
                print(f"Builder status: {file_checkpoint:.0%}")
                file_checkpoint += .05

            if not file_name.endswith(".png"):
                continue

            # skip if not in gui directory
            if f"{os.sep}textures{os.sep}gui{os.sep}" not in walk_dir:
                continue

            file_path = os.path.join(walk_dir, file_name)
            relative_path = file_path.replace(default_dir, "")

            # texture has already been made
            if os.path.exists(os.path.join(resource_dir, relative_path)):
                continue

            # in most cases this will only contain one, as mod patches don't typically overwrite each other
            patch_names = get_patch_names(resource_patches_dir, relative_path)

            # skip textures that have no patch that overwrites it
            if not patch_names:
                if default_patches_dir:
                    patch_names = get_patch_names(default_patches_dir, relative_path)
                    if not patch_names:
                        continue

            detect_response = detect_wrapper(file_path, debug_path)
            if detect_response is None:
                continue
            regions, size = detect_response

            if len(patch_names) > 1:
                print("Choose patch name:")
                patch_name = select(patch_names)
            else:
                patch_name = patch_names[0]

            if patch_name is None:
                continue

            styles = [i for i in os.listdir(templates_dir)
                      if i != "default" and os.path.isdir(os.path.join(templates_dir, i))]
            if len(styles) > 1:
                print("Choose style:")
                style = select(styles)
            else:
                style = styles[0]
            resource_template_dir = os.path.join(templates_dir, style)

            output_image = build_gui(
                regions=regions,
                size=size,
                resource_template_dir=resource_template_dir)

            output_path = os.path.join(resource_patches_dir, patch_name, relative_path)
            print("Wrote to:", output_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            output_image.save(output_path)


def detect_wrapper(file_path, debug_path):
    while True:
        print("Scanning:", file_path)

        shutil.copy2(file_path, debug_path)
        try:
            return detect_regions(
                default_gui_path=file_path,
                default_template_dir=default_template_dir,
                debug_path=debug_path)
        except ValueError as error:
            if str(error) == "could not find nw corner":
                return
            print(error)
            if plt is not None:
                plt.imshow(mpimg.imread(debug_path))
                plt.show()
            else:
                print("Matplotlib is not available. Skipping plots.")

            print("    (ret) skip")
            if select(["retry"]) is None:
                return


def select(patch_names):
    selection = input("\n".join([f"    ( {idx + 1} ) {match}" for idx, match in enumerate(patch_names)]) + "\n    ")
    try:
        patch_name = patch_names[int(selection) - 1]
        print("    chose", patch_name)
        return patch_name
    except ValueError:
        print("    skipped")
