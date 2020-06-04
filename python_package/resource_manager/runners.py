import os
import shutil

import resource_manager.tasks as tasks
import time
import json


def run_pipeline(config, resources, pipelines):
    print(f"Running pipeline: {config['pipeline']}.")
    if config['pipeline'] not in pipelines:
        raise ValueError(f"Pipeline not recognized: {config['pipeline']}")
    for task in pipelines[config['pipeline']]:
        {
            'extract_default': run_extract_default,
            'merge_patches': run_merge_patches,
            'link_resources': run_link_resource,
            'watch_changes': run_watch_changes,
            'port_patches': run_port_patches,
            'prune_files': run_prune_files,
            'download_mods': run_download_mods,
            'download_resource': run_download_resource,
            'run_pipeline': run_pipeline,
        }[task['task']](task, resources, pipelines)


def run_extract_default(config, resources, pipelines):
    resource = resources[config['resource']]
    print("Extracting mods.")
    tasks.extract_default(resource['mods_dirs'], resource['patches_dir'])


def run_link_resource(config, resources, pipelines):
    resource = resources[config['resource']]
    print("Linking resources.")
    tasks.link_resource(resource['link_dirs'], resource['pack_dir'])


def run_unlink_resource(config, resources, pipelines):
    resource = resources[config['resource']]
    print("Unlinking resources.")
    tasks.unlink_resource(resource['link_dirs'])


def run_merge_patches(config, resources, pipelines):
    resource = resources[config['resource']]
    print(f"Resource: {json.dumps(resource, indent=4)}")
    print("Merging patches.")
    start_time = time.time()
    tasks.merge_patches(resource['patches_dir'], resource['pack_dir'], resource['pack_format'])
    elapsed_time = time.time() - start_time
    print(f"Patches merged in {round(elapsed_time)} seconds.")


def run_watch_changes(config, resources, pipelines):
    resources = [resources[resource_id] for resource_id in config['resources']]
    print(f"Watching for changes in {[res['patches_dir'] for res in resources]}.")
    tasks.watch_changes(resources)


def run_port_patches(config, resources, pipelines):
    print(f"Porting {config}.")
    tasks.port_patches(
        default_prior_dir=resources[config['default_prior']]['pack_dir'],
        default_post_dir=resources[config['default_post']]['pack_dir'],
        resource_prior_patches_dir=resources[config['resource_prior']]['patches_dir'],
        resource_post_patches_dir=resources[config['resource_post']]['patches_dir'],
        resource_post_dir=resources[config['resource_post']]['pack_dir'],
        action=config.get('action')
    )


def run_prune_files(config, resources, pipelines):
    print("Pruning files.")
    tasks.prune_files(
        patches_dir=resources[config['resource']]['patches_dir'],
        default_pack_dir=resources[config['resource_default']]['pack_dir'],
        pruned_dir=config['pruned_dir'],
        action=config.get('action')
    )


def run_download_mods(config, resources, pipelines):
    print("Downloading mods.")
    tasks.download_mods(
        mods_dirs=config['mods_dirs'],
        database_path=config['database_path'],
        mod_limit=config['mod_limit']
    )


def run_download_resource(config, resources, pipelines):
    print("Downloading resource.")
    tasks.download_resource(
        resources[config['resource']]
    )


def run_remove_resource(config, resources, pipelines):
    print(f"Removing {config['folder']}")

    folder_dirs = resources[config['resource']][config['folder']]

    # somewhat hacky normalization of dicts and scalars to lists of paths
    if type(folder_dirs) is dict:
        folder_dirs = list(folder_dirs.values())

    if type(folder_dirs) is not list:
        folder_dirs = [folder_dirs]

    for folder_dir in folder_dirs:
        folder_dir = os.path.expanduser(folder_dir)
        if os.path.exists(folder_dir):
            shutil.rmtree(os.path.dirname(folder_dir))
