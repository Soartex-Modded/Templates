import argparse
import os

import toml
from resource_manager import runners

ENV_VAR_PIPELINES_CONFIG = "RESOURCE_MANAGER_PIPELINES_PATH"
ENV_VAR_RESOURCES_CONFIG = "RESOURCE_MANAGER_RESOURCES_PATH"


def run(pipeline: str, resources_path=None, pipelines_path=None):
    """
    Programmatic interface
    :param pipeline: name of pipeline to run
    :param resources_path: location to load resources from. Resources define pack and patches dirs, git url, etc.
    :param pipelines_path: location to load pipelines from. Pipelines are a list of tasks
    """

    if pipelines_path is None:
        pipelines_path = os.environ.get(ENV_VAR_PIPELINES_CONFIG)

    if pipelines_path is None:
        print("Using default package pipelines.")
        pipelines_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "pipelines.toml")

    if resources_path is None:
        resources_path = os.environ.get(ENV_VAR_RESOURCES_CONFIG)

    if resources_path is None:
        print("Using default package resources.")
        resources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "resources.toml")

    #
    # LOAD CONFIGS
    with open(resources_path, "r") as resources_file:
        resources = toml.load(resources_file)
    with open(pipelines_path, "r") as pipelines_file:
        pipelines = toml.load(pipelines_file)

    #
    # EXECUTE PIPELINE
    runners.run_pipeline({'pipeline': pipeline}, resources, pipelines)


if __name__ == "__main__":
    """Command line interface"""
    parser = argparse.ArgumentParser(description='Minecraft resource manager')
    parser.add_argument('-p', '--pipelines', help='Pipelines config', required=False)
    parser.add_argument('-r', '--resources', help='Resources config', required=False)
    parser.add_argument('pipeline', help='Choose a sequence of tasks')
    args = parser.parse_args()

    run(pipeline=args.pipeline, resources_path=args.resources, pipelines_path=args.pipelines)
