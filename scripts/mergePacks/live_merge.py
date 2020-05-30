import time
from watchdog.observers import Observer
from watchdog import events
import os
import shutil
from distutils.dir_util import copy_tree
import json


def set_symlinks(config):
    """
    Create symlinks from multiple game instances to a single generated folder
    """
    for from_dir in config['links']:
        if not os.path.exists(from_dir):
            os.symlink(config['output_dir'], from_dir)


def unset_symlinks(config):
    """
    Remove symlinks from multiple game instances to a single generated folder
    """
    for from_dir in config['links']:
        if os.path.exists(from_dir):
            os.unlink(from_dir)


def build_pack(config):
    """
    delete the entire modded texture pack and completely remake it
    """

    repository_dir = config['repository_dir']
    output_dir = config['output_dir']
    pack_format = config['pack_format']

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    # copy all mods into resource pack
    for mod_name in os.listdir(repository_dir):
        if mod_name == '.git':
            continue

        mod_dir = os.path.join(repository_dir, mod_name)
        if os.path.isdir(mod_dir):
            copy_tree(mod_dir, output_dir)

    # delete the remaining mod.json
    mod_mcmeta = os.path.join(output_dir, "mod.json")
    if os.path.exists(mod_mcmeta):
        os.remove(mod_mcmeta)

    # add pack metadata
    root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "root")
    copy_tree(root_dir, output_dir)

    pack_mcmeta_path = os.path.join(output_dir, "pack.mcmeta")
    with open(pack_mcmeta_path, 'w') as pack_mcmeta_file:
        json.dump({
            "pack": {
                "pack_format": pack_format,
                "description": f"Merged patches from {os.path.basename(os.path.normpath(repository_dir))}"
            }
        }, pack_mcmeta_file, indent=4)


def watch_pack(config):
    """
    Start file watcher to maintain the resource pack with changes made to a resource repository
    :param config: contains paths to the repository and output directories
    """

    repository_dir = config['repository_dir']
    output_dir = config['output_dir']

    def translate(path):
        """
        :param path: absolute path to a folder/file in a mod patch
        :return: absolute path to a folder/file in the autogenerated resource pack
        """

        if repository_dir not in path:
            raise ValueError("paths outside of mod dirs are ignored")

        relative_path = os.path.normpath(path.replace(repository_dir, "")).split(os.sep)

        if len(relative_path) < 2:
            raise ValueError("paths outside of mod dirs are ignored")

        return os.path.join(output_dir, *relative_path[1:])

    class ResourcePackHandler(events.PatternMatchingEventHandler):
        def on_any_event(self, event):
            """
            Handler for modifying files whenever a file-system event occurs
            """

            try:
                src_path = translate(event.src_path)
            except ValueError as err:
                print(err)
                return

            relative_src_path = src_path.replace(output_dir, "")

            if event.event_type == events.EVENT_TYPE_CREATED:
                if event.is_directory:
                    shutil.copytree(event.src_path, src_path)
                else:
                    shutil.copyfile(event.src_path, src_path)
                print(f"\ncreated: {relative_src_path}")

            if event.event_type in events.EVENT_TYPE_MODIFIED:
                if event.is_directory:
                    return
                else:
                    shutil.copyfile(event.src_path, src_path)
                    print(f"\nmodified: {relative_src_path}")

            if event.event_type == events.EVENT_TYPE_MOVED:
                try:
                    dest_path = translate(event.dest_path)
                except ValueError as err:
                    print(err)
                    return

                relative_dest_path = dest_path.replace(output_dir, "")

                shutil.move(src_path, dest_path)
                print(f"""\nmoved: {relative_src_path}\n    -> {relative_dest_path}""")

            if event.event_type == events.EVENT_TYPE_DELETED:
                if event.is_directory:
                    shutil.rmtree(src_path)
                    print(f"\ndeleted: {relative_src_path}")
                else:
                    try:
                        os.remove(src_path)
                    except OSError:
                        pass

    event_handler = ResourcePackHandler(
        patterns=['*'],
        ignore_patterns=["*/.git/*", "*/.git", "*/.DS_Store"])

    observer = Observer()
    observer.schedule(event_handler, path=repository_dir, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":

    #
    # LOAD CONFIG
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
    config = config['versions'][config['active_version']]

    print(f"Config: {json.dumps(config, indent=4)}")

    #
    # REBUILD PACK
    print("Regenerating pack.")
    start_time = time.time()
    build_pack(config)
    elapsed_time = time.time() - start_time
    print(f"Pack regenerated in {round(elapsed_time)} seconds.")

    #
    # RESET SYMLINKS
    if 'links' in config:
        # unset_symlinks(config)
        set_symlinks(config)

    #
    # START FILE WATCHER
    print(f"Watching for changes in {config['repository_dir']}")
    watch_pack(config)
