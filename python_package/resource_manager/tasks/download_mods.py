import json

import requests

import os
import math
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.sql import select


def download_mods(mods_dirs, database_path, mod_limit=100):
    """
    Collect the top mods from CurseForge into mods_dirs

    :param mods_dirs: {[minor_version]: [path to mods folder]}
    :param database_path: path to .db file with download history (will be created if not exists)
    :param mod_limit: maximum number of mods to collect
    """

    mods_dirs = {k: os.path.expanduser(v) for k, v in mods_dirs.items()}
    database_path = os.path.expanduser(database_path)

    patch_info = {}
    for minor_version in mods_dirs:
        patch_info[minor_version] = {}
        os.makedirs(mods_dirs[minor_version], exist_ok=True)
    os.makedirs(os.path.dirname(database_path), exist_ok=True)

    engine = create_engine('sqlite:///' + database_path)
    metadata = MetaData()
    mod_files = Table('mod_files', metadata,
                      Column('id', Integer, primary_key=True),
                      Column('file_name', String(250)),
                      Column('mod_id', Integer),
                      Column('vanilla_minor_version', Integer))
    metadata.create_all(engine)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    }

    page_size = 50
    mod_count = 0

    # download sets of mod information at a time
    for page_index in range(math.ceil(mod_limit / page_size)):
        mods = requests.get(
            "https://addons-ecs.forgesvc.net/api/v2/addon/search/",
            params={
                'gameId': 432,
                'index': page_index * page_size,
                'pageSize': page_size,
                'sort': 'TotalDownloads',
                'sortDescending': True
            },
            headers=headers).json()

        for mod_meta in mods:
            mod_count += 1
            if mod_count > mod_limit:
                return

            if mod_meta['categorySection']['name'] != 'Mods':
                continue

            versioned_mod_files = {}
            for mod_file_meta in mod_meta['gameVersionLatestFiles']:
                tokens = mod_file_meta['gameVersion'].split('.')
                minor_version = int(tokens[1])
                patch_version = 0 if len(tokens) == 2 else int(tokens[2])

                # find latest mod files
                if minor_version in versioned_mod_files:
                    if versioned_mod_files[minor_version]['patch_version'] > patch_version:
                        continue

                versioned_mod_files[minor_version] = {
                    'patch_version': patch_version,
                    'value': mod_file_meta
                }

            for minor_version in versioned_mod_files:

                if str(minor_version) not in mods_dirs:
                    continue

                mod_file_meta = versioned_mod_files[minor_version]['value']

                patch_info[str(minor_version)][mod_file_meta["projectFileName"]] = {
                    "mod_id": mod_meta['slug'],
                    "mod_name": mod_meta['name'],
                    # typically contains the mod version inside somewhere
                    "mod_filename": mod_file_meta['projectFileName'],
                    "mc_version": mod_file_meta['gameVersion'],
                    "mod_authors": [auth['name'] for auth in mod_meta['authors']],
                    "url_website": mod_meta['websiteUrl'],
                    "description": mod_meta.get('summary')
                }

                available_file_name = mod_file_meta['projectFileName']

                stored_file_name = engine.execute(select([mod_files.c.file_name])
                    .where((mod_files.c.mod_id == mod_meta['id']) & (mod_files.c.vanilla_minor_version == minor_version))).scalar()

                if stored_file_name == available_file_name:
                    # file is already current
                    # print(f'Skipping {mod_meta["name"]} for 1.{minor_version}')
                    continue

                mod_path = os.path.join(mods_dirs[str(minor_version)], mod_file_meta['projectFileName'])

                if os.path.exists(mod_path):
                    engine.execute(mod_files.insert(),
                                   file_name=available_file_name,
                                   mod_id=mod_meta['id'],
                                   vanilla_minor_version=minor_version)
                    continue

                download_url = requests.get(
                    f"https://addons-ecs.forgesvc.net/api/v2/addon/{mod_meta['id']}/file/{mod_file_meta['projectFileId']}/download-url",
                    headers=headers).text

                print(f'Downloading {mod_meta["name"]} for 1.{minor_version}')

                with open(mod_path, 'wb') as mod_file:
                    mod_file.write(requests.get(download_url, headers=headers).content)

                if stored_file_name is None:
                    engine.execute(mod_files.insert(),
                                   file_name=available_file_name,
                                   mod_id=mod_meta['id'],
                                   vanilla_minor_version=minor_version)
                else:
                    engine.execute(mod_files.update()
                                   .where((mod_files.c.mod_id == mod_meta['id']) & (mod_files.c.vanilla_minor_version == minor_version))
                                   .values(file_name=available_file_name))

    for minor_version in patch_info:
        with open(os.path.join(mods_dirs[str(minor_version)], "patch_info.json"), 'w') as patch_info_file:
            json.dump(patch_info[minor_version], patch_info_file, indent=4)
