import os
import shutil


def link_resource(link_dirs, output_dir):
    """
    Create symlinks from multiple game instances to a single generated folder
    """
    output_dir = os.path.expanduser(output_dir)
    for from_dir in link_dirs:
        from_dir = os.path.expanduser(from_dir)
        if not os.path.exists(from_dir):
            os.symlink(output_dir, from_dir)


def unlink_resource(link_dirs):
    """
    Remove symlinks from multiple game instances to a single generated folder
    """
    for from_dir in link_dirs:
        from_dir = os.path.expanduser(from_dir)
        if os.path.exists(from_dir):
            os.unlink(from_dir)
