import json
import os

from resource_manager.gui_builder.utilities import TemplateLoader, Region
from typing import List
import numpy as np
import math
from PIL import Image


def build_gui(regions: List[Region], size, resource_template_dir):
    """
    Construct a GUI from a description of what it contains
    :param regions: each region points to a template, as well as the location and size
    :param size: The (width, height) of the default image that this script will replace
    :param resource_template_dir: directory of replacement textures
    :return: PIL.Image of the constructed GUI
    """
    resources = TemplateLoader(resource_template_dir)

    with open(os.path.join(resource_template_dir, "configuration.json"), 'r') as configuration_file:
        scale = json.load(configuration_file)['scale_multiplier']

    regions = resources.sort(regions)

    resource_gui = np.zeros((size[0] * scale, size[1] * scale, 4), dtype=np.uint8)
    for region in regions:
        # scale up the region
        region *= scale

        height, width = resources[region.name].shape[:2]
        meta = resources.metadata.get(region.name, {})
        y, x = region.y + meta.get("dy", 0), region.x + meta.get("dx", 0)

        mode = meta.get('mode')

        # assign the template to the constructed image
        if mode is None:
            resource_gui[y:y + height, x:x + width, :] = resources[region.name]
        elif mode == "tile":
            num_tilings = (math.ceil(region.dy / height), math.ceil(region.dx / width), 1)
            resource_gui[region.slice] = np.tile(resources[region.name], num_tilings)[:region.dy, :region.dx]
        elif mode == "tile-x":
            num_tilings = (1, math.ceil(region.dx / width), 1)
            resource_gui[y:y + height, region.x:region.right] = np.tile(resources[region.name], num_tilings)[:, :region.dx]
        elif mode == "tile-y":
            num_tilings = (math.ceil(region.dy / height), 1, 1)
            resource_gui[region.y:region.lower, x:x + width] = np.tile(resources[region.name], num_tilings)[:region.dy]

    return Image.fromarray(resource_gui, mode="RGBA")

