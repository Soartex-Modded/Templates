import os
import shutil

from PIL import Image
import PIL
import numpy as np
from resource_manager.tasks.port_patches import infer_patch_name
from scipy.stats.stats import pearsonr

try:
    import tkinter
    from tkinter import filedialog
except ModuleNotFoundError:
    tkinter = False


DEFAULT_PREFIX = "__default_"


def find_similar(scale, resource_patches_dir, default_dir, develop_dir=None):
    """
    Finds similar files to the one selected, and copies placeholders together into a folder.
    Images can be edited together.
    Moves completed images back to the corresponding patch in resource_patches_dir.
    Do not change patch names given to matched assets in develop_dir.

    :param scale: size multiplier
    :param resource_patches_dir: resource pack patches
    :param default_dir: default resource pack
    :param develop_dir: temporary directory from which to work on assets
    """

    resource_patches_dir = os.path.expanduser(resource_patches_dir)
    default_dir = os.path.expanduser(default_dir)
    if not develop_dir:
        develop_dir = "~/Desktop/resource_manager_development"
    develop_dir = os.path.expanduser(develop_dir)
    print("Working from:", develop_dir)

    # set the criteria for matching
    similarity = {'metric': "correlation", 'threshold': 0.6}
    file_path = None

    while True:
        print()
        print("Similarity metric:", similarity)

        options = [
            "choose image (tkinter file picker)",
            "choose image (from path)",
            "change similarity metric",
            "quit"
        ]
        if file_path:
            print("File path:", file_path)
            options.insert(0, "run")

        selection = select(options)

        if selection == "choose image (tkinter file picker)" or selection == "choose image (from path)":

            candidate_path = None
            if selection == "choose image (tkinter file picker)":
                if not tkinter:
                    print("TKinter is not installed correctly. "
                          "Either fix TKinter or use \"choose image (from path)\"")
                    continue
                root = tkinter.Tk()
                root.withdraw()
                print("A file opener dialog window has been opened.")
                candidate_path = filedialog.askopenfilename(initialdir=default_dir)

            if selection == "choose image (from path)":
                candidate_path = input("Absolute image path: ")

            if not candidate_path or not os.path.exists(candidate_path):
                continue

            if not os.path.isfile(candidate_path):
                print("path must point to a file")
                continue

            if not candidate_path.endswith(".png"):
                print("file must be a .png")
                continue

            file_path = candidate_path
            continue

        if selection == "change similarity metric":
            similarity = get_similarity_metric()
            continue

        if selection == "quit":
            break

        # the only remaining selection should be "run"
        if selection != "run":
            continue

        # use the similarity metric to find similar default texture paths within default dir
        similar_file_paths = match_similar(default_dir, file_path, similarity)

        if os.path.exists(develop_dir):
            input("Development directory already exists. Hit return to delete it.")
            shutil.rmtree(develop_dir)
        os.makedirs(develop_dir, exist_ok=True)

        # mapping from development directory path to output directory path
        patch_name_paths = {}

        # copy matched assets into development directory
        for similar_file_path in similar_file_paths:

            relative_path = similar_file_path.replace(default_dir, "")
            patch_name = infer_patch_name(resource_patches_dir, relative_path)
            # cannot infer a patch name for this resource
            if not patch_name:
                continue

            relative_output_path = os.path.join(patch_name, relative_path)
            output_path = os.path.join(resource_patches_dir, relative_output_path)

            # texture has already been made. Don't bother presenting it
            if os.path.exists(output_path):
                continue

            # ~~ create paths to files in development directory
            # add a __default_ prefix to files to indicate they have not been textured yet
            modified_name = os.path.basename(relative_path)
            placeholder_path = os.path.join(develop_dir, patch_name, DEFAULT_PREFIX + modified_name)

            # iterate to ensure patches with multiple matches that share filenames are not overwritten
            count = 2
            base_name = modified_name.replace(".png", "")
            while True:
                if not os.path.exists(placeholder_path):
                    break
                modified_name = f"{base_name}_{count}.png"
                placeholder_path = os.path.join(develop_dir, patch_name, DEFAULT_PREFIX + modified_name)
                count += 1

            relative_modified_path = os.path.join(patch_name, modified_name)

            os.makedirs(os.path.dirname(placeholder_path), exist_ok=True)

            if scale != 1:
                image = Image.open(similar_file_path)
                image.resize((image.width * scale, image.height * scale), resample=PIL.Image.NEAREST)\
                    .save(placeholder_path)
            else:
                shutil.copy2(similar_file_path, placeholder_path)

            patch_name_paths[relative_modified_path] = relative_output_path

        if not patch_name_paths:
            print("No similar files found.")
            continue

        input(f"Similar files moved into: {develop_dir}\n"
              f"Open {DEFAULT_PREFIX}*.png files, edit, and save without the {DEFAULT_PREFIX} prefix.\n"
              f"Hit return when done editing.")

        # move files, then detect invalid files. Repeat until no invalid files
        while True:
            move_textured_files(patch_name_paths, develop_dir, resource_patches_dir)
            clear = True
            for walk_dir, _, file_names in os.walk(develop_dir):
                for file_name in file_names:
                    if '.git' in walk_dir or file_name == '.DS_Store':
                        continue
                    if file_name.startswith(DEFAULT_PREFIX):
                        continue
                    relative_path = os.path.join(walk_dir, file_name).replace(develop_dir, '')
                    input(f"Detected incorrectly-named file: {relative_path}. "
                          f"Either rename it properly or delete it.")
                    clear = False
            if clear:
                break
        shutil.rmtree(develop_dir)


def move_textured_files(patch_name_paths, develop_dir, resource_patches_dir):
    """
    Use the patch_name paths mapping to move assets from develop_dir to resource_patches_dir

    :param patch_name_paths: mapping of relative paths in develop_dir to relative paths in resource_patches_dir
    :param develop_dir: from directory
    :param resource_patches_dir: to directory
    """
    for relative_modified_path, relative_output_path in patch_name_paths.items():
        modified_path = os.path.join(develop_dir, relative_modified_path)
        output_path = os.path.join(resource_patches_dir, relative_output_path)

        if os.path.exists(modified_path):
            print(f"move: {relative_modified_path}\n"
                  f"   -> {relative_output_path}")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.move(modified_path, output_path)

            meta_modified_path = modified_path + '.mcmeta'
            if os.path.exists(meta_modified_path):
                meta_output_path = output_path + '.mcmeta'
                print(f"move: {meta_modified_path.replace(develop_dir, '')}\n"
                      f"   -> {meta_output_path.replace(patch_name_paths, '')}")
                shutil.move(meta_modified_path, meta_output_path)


def get_perceived_luminance(image):
    """
    Compute a luminance channel for an image based on http://alienryderflex.com/hsp.html
    :param image: numpy array of dimensions [h, w, 4], where channels are [R, G, B, A]
    :return: numpy array of dimensions [h, w]
    """
    return np.sqrt(image ** 2 @ np.array([.299, .587, .114, 0.]))


def match_similar(default_dir, file_path, similarity: dict):
    """
    Return paths to all files in default_dir that are sufficiently similar to file_path under the similarity criteria
    :param default_dir: search for matches within this folder
    :param file_path: search for matches against this image
    :param similarity: 'metric' is "correlation" or "alpha", and correlation has a 'threshold'.
    :return: list of paths to matched files
    """

    # preprocess file_path to match against
    image = np.array(Image.open(file_path).convert("RGBA"))
    if similarity['metric'] == "correlation":
        description = get_perceived_luminance(image).flatten()
    elif similarity['metric'] == "alpha":
        description = image[..., 3]
    else:
        raise ValueError(f"unsupported similarity metric: {similarity['metric']}")

    matches = []
    for walk_dir, _, file_names in os.walk(default_dir):
        for file_name in file_names:
            if not file_name.endswith(".png"):
                continue
            file_path = os.path.join(walk_dir, file_name)

            try:
                candidate = np.array(Image.open(file_path).convert("RGBA"))
            except PIL.UnidentifiedImageError:
                continue

            if candidate.shape != image.shape:
                continue

            if similarity['metric'] == "correlation":
                candidate_description = get_perceived_luminance(candidate).flatten()
                if pearsonr(candidate_description, description)[0] > similarity['threshold']:
                    print("Found match:", file_path.replace(default_dir, ""))
                    matches.append(file_path)
            elif similarity['metric'] == "alpha":
                candidate_description = candidate[..., 3]
                if np.array_equal(candidate_description, description):
                    print("Found match:", file_path.replace(default_dir, ""))
                    matches.append(file_path)

    return matches


def get_similarity_metric():
    """Solicit input from a user to select a similarity metric and threshold"""
    similarity = {'metric': select(["correlation", "alpha"]) or "correlation"}

    if similarity['metric'] == "correlation":
        similarity['threshold'] = float(input("Choose threshold in (0, 1), defaults to 0.9:") or 0.9)
    return similarity


def select(options):
    """
    Solicit input from a user to select one option from a list of options
    :param options: values to select from
    :return: an option, or None
    """
    selection = input("\n".join([f"    ( {idx + 1} ) {match}" for idx, match in enumerate(options)]) + "\n      ")
    try:
        selection = options[int(selection) - 1]
        print(f"    selected \"{selection}\"")
        return selection
    except ValueError:
        print("    skipped")
