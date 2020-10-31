import time
from watchdog.observers import Observer
from watchdog import events
import os
import shutil
from distutils.dir_util import copy_tree


class PatchSyncHandler(events.PatternMatchingEventHandler):
    def __init__(self, patches_dir, output_dir, *args, **kwargs):
        self.patches_dir = patches_dir
        self.output_dir = output_dir
        super().__init__(*args, **kwargs)

    def translate(self, path):
        """
        :param path: absolute path to a folder/file in the patches dir
        :return: absolute path to a folder/file in the output dir
        """

        relative_path = os.path.normpath(path.replace(self.patches_dir, ""))
        return os.path.join(self.output_dir, *relative_path.split(os.sep)[1:])

    def on_any_event(self, event):
        """
        Handler for modifying files whenever a file-system event occurs
        """

        if not event.src_path.startswith(self.patches_dir):
            print(f"skipping invalid path: {event.src_path}")
            return

        src_path = self.translate(event.src_path)

        relative_src_path = src_path.replace(self.output_dir, "")

        # ignore the soartex mod.json, and standalone assets directory
        #     (assets dir should always exist, and never be deleted)
        if relative_src_path in ["mod.json", "assets", ""]:
            return

        if event.event_type == events.EVENT_TYPE_CREATED:
            os.makedirs(os.path.dirname(src_path), exist_ok=True)
            if event.is_directory:
                copy_tree(event.src_path, src_path)
            else:
                shutil.copyfile(event.src_path, src_path)
            print(f"created: {relative_src_path}")

        if event.event_type == events.EVENT_TYPE_MODIFIED:
            if event.is_directory:
                return
            else:
                os.makedirs(os.path.dirname(src_path), exist_ok=True)
                shutil.copyfile(event.src_path, src_path)
                print(f"modified: {relative_src_path}")

        if event.event_type == events.EVENT_TYPE_MOVED:
            if not event.dest_path.startswith(self.patches_dir):
                print(f"skipping invalid destination path: {event.src_path}")
                return

            dest_path = self.translate(event.dest_path)
            relative_dest_path = dest_path.replace(self.output_dir, "")

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.move(src_path, dest_path)
            print(f"""moved: {relative_src_path}\n    -> {relative_dest_path}""")

        if event.event_type == events.EVENT_TYPE_DELETED:
            if event.is_directory and os.path.exists(src_path):
                shutil.rmtree(src_path)
                print(f"deleted: {relative_src_path}")
            else:
                try:
                    os.remove(src_path)
                    print(f"deleted: {relative_src_path}")
                except OSError:
                    pass


def watch_changes(resources):
    """
    Start a file watcher to maintain resource pack(s) with changes made to patch repositor(ies)
    Each resource is a dict containing the keys:
    {
        "patches_dir": absolute path to patches directory,
        "pack_dir": absolute path to merged directory, to be kept updated
    }

    :param resources: a list of pairings between patch directories and merged directories
    """

    observer = Observer()

    for resource in resources:
        event_handler = PatchSyncHandler(
            patches_dir=os.path.expanduser(resource['patches_dir']),
            output_dir=os.path.expanduser(resource['pack_dir']),
            patterns=['*'],
            ignore_patterns=["*/.git/*", "*/.git", "*/.DS_Store", "/"])

        observer.schedule(event_handler, path=os.path.expanduser(resource['patches_dir']), recursive=True)

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
