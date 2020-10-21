import os
import shutil

import resource_manager.tasks as tasks
import time
import json


def run_pipeline(config, resources, pipelines):
    print("Running pipeline:", config['pipeline'])
    task_runners = {
        'extract_default': run_extract_default,
        'merge_patches': run_merge_patches,
        'link_resources': run_link_resource,
        'watch_changes': run_watch_changes,
        'port_patches': run_port_patches,
        'prune_files': run_prune_files,
        'detect_overwrites': run_detect_overwrites,
        'remove_resource': run_remove_resource,
        'download_mods': run_download_mods,
        'download_resource': run_download_resource,
        'run_pipeline': run_pipeline,
        'run_parallel': run_parallel,
        'run_apply': run_apply,
        'run_subprocess': run_run_subprocess
    }

    if config['pipeline'] not in pipelines:
        # if any individual task is passed to the run_pipeline task, direct it to the proper task
        if 'task' in config and config['task'] in task_runners:
            task_runners[config['task']](config, resources, pipelines)
        else:
            raise ValueError(f"Pipeline not recognized: {config['pipeline']}")

    # run every step in the pipeline
    for task in pipelines[config['pipeline']]:
        task_runners[task['task']](task, resources, pipelines)


def run_parallel(config, resources, pipelines):
    # This task probably doesn't have great benefits, as most of these tasks are bound by disk transfer
    print("Running in parallel:", config['pipeline'])
    if config['pipeline'] not in pipelines:
        raise ValueError(f"Pipeline not recognized: {config['pipeline']}")

    tasks.parallel(pipelines[config['pipeline']], run_pipeline, args=(resources, pipelines))


def run_apply(config, resources, pipelines):
    print("Applying task to multiple resources.")

    # construct a new pipeline
    resource_names = config['resources']
    del config['resources']
    pipeline = [{**config, 'resource': resource_name, 'task': config['apply_task']} for resource_name in resource_names]

    # register pipeline
    pipeline_name = json.dumps(pipeline, indent=4)
    pipelines[pipeline_name] = pipeline

    # call registered pipeline
    run_pipeline({"task": "run_pipeline", "pipeline": pipeline_name}, resources, pipelines)


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
    print("Resource:", json.dumps(resource, indent=4))
    print("Merging patches.")
    start_time = time.time()
    tasks.merge_patches(
        patches_dir=resource['patches_dir'],
        pack_dir=resource['pack_dir'],
        pack_format=resource['pack_format'],
        enable_patch_map=True)
    elapsed_time = time.time() - start_time
    print(f"Patches merged in {round(elapsed_time)} seconds.")


def run_watch_changes(config, resources, pipelines):
    resources = [resources[resource_id] for resource_id in config['resources']]
    print(f"Watching for changes in {[res['patches_dir'] for res in resources]}.")
    tasks.watch_changes(resources)


def run_port_patches(config, resources, pipelines):
    print("Porting", config)
    tasks.port_patches(
        default_prior_dir=resources[config['default_prior']]['pack_dir'],
        default_post_dir=resources[config['default_post']]['pack_dir'],
        resource_prior_patches_dir=resources[config['resource_prior']]['patches_dir'],
        resource_post_patches_dir=resources[config['resource_post']]['patches_dir'],
        resource_post_dir=resources[config['resource_post']]['pack_dir'],
        resource_prior_dir=resources[config['resource_prior']]['pack_dir'],
        default_post_patches_dir=resources[config['default_post']]['patches_dir'],
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


def run_detect_overwrites(config, resources, pipelines):
    print("Detecting overwritten files.")
    tasks.detect_overwrites(patches_dir=resources[config['resource']]['patches_dir'])


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
    print("Removing", config['folder'])

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


def run_run_subprocess(config, resources, pipelines):
    print("Running subprocess.")
    print("cmd:", config['cmd'])
    print("pwd:", config['folder'])
    tasks.run_subprocess(cmd=config['cmd'], cwd=resources[config['resource']][config['folder']])
