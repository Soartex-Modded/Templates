import json
import os
import tempfile
import zipfile
import shutil
import re


def extract_default(mods_dirs, output_dir):
    """
    Extract resource files from mods_dirs of .jar files into output_dir.

    :param mods_dirs: list of directories, each containing a collection of mod .zip files
    :param output_dir: location to place resource files
    """
    extensions = ('.info', '.mcmeta', '.png', '.properties')

    output_dir = os.path.expanduser(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    for mods_dir in mods_dirs:
        mods_dir = os.path.expanduser(mods_dir)

        for jar_name in os.listdir(mods_dir):
            jar_path = os.path.join(mods_dir, jar_name)
            if not jar_path.endswith(".jar"):
                continue

            # the temp directory is removed when the context manager exits
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(jar_path, 'r') as zip_file:
                    [zip_file.extract(file, temp_dir) for file in zip_file.namelist() if file.endswith(extensions)]

                # try to get patch name from mcmod.info
                try:
                    mcmod_path = os.path.join(temp_dir, 'mcmod.info')
                    with open(mcmod_path, "r") as mcmod_file:
                        mcmod_info = json.load(mcmod_file)

                    # version 2 of mcmod.info
                    if type(mcmod_info) is dict:
                        mcmod_info = mcmod_info['modList']

                    if len(mcmod_info) > 1:
                        print(f'Multiple mods in mcmod.info file. Ignoring: {mcmod_info[1:]}')

                    patch_name = mcmod_info[0]['name']

                # fall back to patch name from jar name
                except:
                    print(f'Invalid mcmod.info file in {jar_name}')
                    patch_name = jar_name

                # ensure that the patch name is a proper filename
                patch_name = re.sub('[^\w\-_\. ]', '_', patch_name.replace(":", ""))

                # skip mods without resources
                file_count = sum([len(files) for r, d, files in os.walk(temp_dir)])
                if file_count < 2:
                    print(f'No resources in {patch_name}. Skipping.')
                    continue

                # copy mod patches into output dir
                patch_dir = os.path.join(output_dir, patch_name)
                if os.path.exists(patch_dir):
                    shutil.rmtree(patch_dir)
                shutil.copytree(temp_dir, patch_dir)
