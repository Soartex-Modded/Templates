import json
import os
import tempfile
import zipfile
import re
from distutils.dir_util import copy_tree


def extract_default(mods_dirs, output_dir):
    """
    Extract resource files from mods_dirs of .jar files into output_dir.

    :param mods_dirs: list of directories, each containing a collection of mod .zip files
    :param output_dir: location to place resource files
    """
    extensions = ('.info', '.mcmeta', '.png', '.properties', '.json')

    output_dir = os.path.expanduser(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    for mods_dir in mods_dirs:
        mods_dir = os.path.expanduser(mods_dir)

        patch_info_path = os.path.join(mods_dir, "patch_info.json")
        all_patch_info = {}
        if os.path.exists(patch_info_path):
            with open(patch_info_path, "r") as patch_info_file:
                all_patch_info = json.load(patch_info_file)

        for jar_name in os.listdir(mods_dir):
            jar_path = os.path.join(mods_dir, jar_name)

            # the temp directory is removed when the context manager exits
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    with zipfile.ZipFile(jar_path, 'r') as zip_file:
                        [zip_file.extract(file, temp_dir) for file in zip_file.namelist() if file.endswith(extensions)]
                except (zipfile.BadZipFile, IsADirectoryError):
                    continue

                # try to get metadata from mcmod.info
                # this is especially spotty on newer MC versions
                try:
                    mcmod_path = os.path.join(temp_dir, 'mcmod.info')
                    with open(mcmod_path, "r") as mcmod_file:
                        mcmod_info = json.load(mcmod_file)

                    # version 2 of mcmod.info
                    if type(mcmod_info) is dict:
                        mcmod_info = mcmod_info['modList']

                    if len(mcmod_info) > 1:
                        print(f'Multiple mods in mcmod.info file. Ignoring last {len(mcmod_info) - 1}.')

                    mcmod_info = mcmod_info[0]

                    patch_info = all_patch_info.get(jar_name, {})

                    # curseforge mod name is better, if exists
                    if 'mod_name' not in patch_info and 'name' in mcmod_info:
                        patch_info['mod_name'] = mcmod_info['name']

                    # curseforge mod id is better, if exists
                    if 'mod_id' not in patch_info and 'modid' in mcmod_info:
                        patch_info['mod_id'] = mcmod_info['modid']

                    # curseforge version does not exist
                    if 'version' in mcmod_info:
                        patch_info['mod_version'] = mcmod_info['version']

                    # mcmod.info mcversion is better, if exists
                    if 'mcversion' in mcmod_info:
                        patch_info['mc_version'] = mcmod_info['mcversion']

                    # mcmod.info authors is better, if exists
                    if 'authors' in mcmod_info:
                        patch_info['mod_authors'] = mcmod_info['authors']

                    # mcmod.info url is better, if exists
                    if 'url' in mcmod_info:
                        patch_info['url_website'] = mcmod_info['url']

                    # curseforge description is better, if exists
                    if 'description' not in patch_info and 'description' in mcmod_info:
                        patch_info['description'] = mcmod_info['description']

                # fall back to patch name from jar name
                except:
                    patch_info = {
                        'mod_filename': jar_name,
                        **all_patch_info.get(jar_name, {}),
                    }
                    print(f'Invalid mcmod.info file in {jar_name}')

                patch_dir_name = patch_info.get('mod_name',
                                            patch_info.get('mod_id',
                                                           patch_info.get('mod_filename', jar_name)))

                # ensure that the patch name is a proper filename
                patch_dir_name = re.sub('[^\w\-_\.]', '', patch_dir_name.replace(":", "").replace(" ", "_"))

                # skip mods without resources
                file_count = sum([len(files) for r, d, files in os.walk(temp_dir)])
                if file_count < 2:
                    print(f'No resources in {patch_dir_name}. Skipping.')
                    continue

                # copy mod patches into output dir
                patch_dir = os.path.join(output_dir, patch_dir_name)

                # if os.path.exists(patch_dir):
                #     shutil.rmtree(patch_dir)
                # shutil.copytree(temp_dir, patch_dir)

                # intentionally merge default textures from multiple mod versions together
                copy_tree(temp_dir, patch_dir)

                # create a mod.json
                patch_info_path = os.path.join(patch_dir, 'mod.json')
                with open(patch_info_path, 'w') as patch_info_file:
                    json.dump(patch_info, patch_info_file, indent=4)
