import subprocess
import sys
import os


def link_resource(link_dirs, output_dir):
    """
    Create symlinks from multiple game instances to a single generated folder
    """
    output_dir = os.path.expanduser(output_dir)
    for from_dir in link_dirs:
        from_dir = os.path.expanduser(from_dir)
        if not os.path.exists(from_dir):
            os.symlink(output_dir, from_dir, target_is_directory=True)


def unlink_resource(link_dirs):
    """
    Remove symlinks from multiple game instances to a single generated folder
    """
    for from_dir in link_dirs:
        from_dir = os.path.expanduser(from_dir)
        if os.path.exists(from_dir):
            os.unlink(from_dir)


def run_subprocess(cmd, cwd):
    """
    Execute cmd at cwd
    :param cwd: directory to execute command at
    :param cmd: plaintext command
    """
    subprocess.check_call(cmd, shell=True, cwd=os.path.expanduser(cwd), stdout=sys.stdout, stderr=subprocess.STDOUT)
