from typing import List, Union

from resource_manager.gui_builder.utilities import TemplateLoader, Region

import numpy as np
from PIL import Image


def detect_regions(default_gui_path, default_template_dir, debug_path=None) -> List[Region]:
    """
    Detect known patterns in default GUI image
    :param default_gui_path: location of default GUI
    :param default_template_dir: location of templates to match against
    :param debug_path: optional path to write debug images to
    :return: locations and descriptions of detected templates
    """
    default_gui = np.array(Image.open(default_gui_path).convert("RGBA"))
    mask = np.full(default_gui.shape[:2], True)

    default_gui[np.equal(default_gui[:, :, 3],0)] = 0

    # default templates
    defaults = TemplateLoader(default_template_dir)

    # match all templates for a panel
    template_matches = match_panel(default_gui, defaults)

    # mark matched regions of the image
    for region in template_matches:
        region.remove_from(mask)

    trimmed_region = get_bounding_box(default_gui[:, :, 3])
    for discovered_region in scan_for_templates(
            default_gui[trimmed_region.slice],
            mask[trimmed_region.slice],
            defaults, debug_path=debug_path):
        discovered_region.x += trimmed_region.x
        discovered_region.y += trimmed_region.y
        template_matches.append(discovered_region)

    print(template_matches)

    # ~~~ TESTING ~~~
    # delete matched area from image
    # default_gui *= mask[..., None].astype(np.uint8)
    # Image.fromarray(default_gui, mode="RGBA").save(output_path)
    # ~~~ END TESTING ~~~

    return template_matches, default_gui.shape[:2]


def match_panel(image: Image, defaults: TemplateLoader) -> List[Region]:
    """
    Detect the area bounded by the primary gray backing
    :param image: image to analyze
    :param defaults: images to match against
    :return: location and descriptions of detected templates
    """
    image_region = Region.from_image(image)
    corner_nw_region = Region(0, 0, *defaults['corner_nw'].shape[:2], name='corner_nw')

    if not np.array_equal(defaults["corner_nw"], image[corner_nw_region.slice]):
        raise ValueError("could not find nw corner")

    # NORTHEAST CORNER
    corner_ne_region = Region(
        corner_nw_region.y, corner_nw_region.right,
        *defaults['corner_ne'].shape[:2],
        name='corner_ne')

    # seek until the top right corner is found
    while corner_ne_region.right <= image_region.right:
        if np.array_equal(image[corner_ne_region.slice], defaults['corner_ne']):
            break
        corner_ne_region.x += 1
    else:
        raise ValueError("could not find ne corner")

    # SOUTHWEST CORNER
    corner_sw_region = Region(
        corner_nw_region.lower, corner_nw_region.x,
        *defaults['corner_sw'].shape[:2],
        name='corner_sw')

    # seek until the bottom left corner is found
    while corner_sw_region.lower <= image_region.lower:
        if np.array_equal(image[corner_sw_region.slice], defaults['corner_sw']):
            break
        corner_sw_region.y += 1
    else:
        raise ValueError("could not find sw corner")

    # SOUTHEAST CORNER
    corner_se_region = Region(
        corner_sw_region.y, corner_ne_region.x,
        *defaults['corner_se'].shape[:2],
        name='corner_se')
    if not np.array_equal(image[corner_se_region.slice], defaults['corner_se']):
        raise ValueError("could not find se corner")

    interior_region = Region(
        y=corner_nw_region.lower,
        x=corner_nw_region.right,
        dy=corner_se_region.y - corner_ne_region.lower,
        dx=corner_se_region.x - corner_sw_region.right,
        name='interior')

    # create a grey backing to check equality against
    backing = np.broadcast_to(np.array([198, 198, 198, 255])[None, None, :], (*interior_region.shape, 4))

    interior_region.mask = np.all(np.equal(backing, image[interior_region.slice]), axis=2)

    return [
        corner_nw_region, corner_ne_region, corner_sw_region, corner_se_region,
        interior_region,
        # NORTH EDGE
        Region(
            y=corner_nw_region.y,
            x=corner_nw_region.right,
            dy=defaults['edge_n'].shape[0],
            dx=corner_ne_region.x - corner_nw_region.right,
            name='edge_n'),
        # SOUTH EDGE
        Region(
            y=corner_sw_region.y,
            x=corner_sw_region.right,
            dy=defaults['edge_s'].shape[0],
            dx=corner_se_region.x - corner_sw_region.right,
            name='edge_s'),
        # WEST EDGE
        Region(
            y=corner_nw_region.lower,
            x=corner_nw_region.x,
            dy=corner_sw_region.y - corner_nw_region.lower,
            dx=defaults['edge_w'].shape[1],
            name='edge_w'),
        # EAST EDGE
        Region(
            y=corner_ne_region.lower,
            x=corner_ne_region.x,
            dy=corner_se_region.y - corner_ne_region.lower,
            dx=defaults['edge_e'].shape[1],
            name='edge_e')
    ]


def scan_for_templates(image: Image, mask, defaults: TemplateLoader, debug_path=None) -> List[Region]:
    """
    Detect scattered templates within the mask
    :param image: image to analyze
    :param mask: boolean indicator for each pixel that indicates if a pixel has already been matched by a prior region
    :param defaults: images to match against
    :return: location and descriptions of detected templates
    """
    matches = []
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            # skip pixels that have already been matched by a template
            if not mask[y, x]:
                continue

            # check templates for match
            region = match_single_template(image[y:, x:], defaults)
            if region is None:
                if image[y, x, 3]:
                    if debug_path:
                        Image.fromarray(image[y:, x:], mode="RGBA").save(debug_path)
                    raise ValueError(f"a solid pixel was left unmatched at ({x}, {y})")
            else:
                region.y, region.x = y, x
                matches.append(region)
                region.remove_from(mask)
                print("Found template:", region.name)
                if (image * mask[..., None].astype(np.uint8)).sum() == 0:
                    return matches
    return matches


def match_single_template(image: Image, defaults: TemplateLoader) -> Union[Region, None]:
    """
    Search for one template starting from the top left pixel
    :param image: image to analyze
    :param defaults: images to match against
    :return: optional description of detected template
    """
    for template_name, template in defaults:
        template_region = Region.from_image(template, name=template_name)
        if template_region.dy > image.shape[0]:
            continue
        if template_region.dx > image.shape[1]:
            continue

        if np.array_equal(image[template_region.slice], template):
            # some templates can expand arbitrarily
            if template_name == "scrollbar_middle":
                scrollbar_bottom_region = Region.from_image(defaults['scrollbar_bottom'])
                while template_region.dy < image.shape[0]:
                    if np.array_equal(
                            defaults['scrollbar_bottom'],
                            image[template_region.dy:template_region.dy + scrollbar_bottom_region.dy, :template_region.dx]):
                        break
                    template_region.dy += 1

            if template_name == "search_middle":
                search_right_region = Region.from_image(defaults['search_right'])
                while template_region.dx < image.shape[0]:
                    if np.array_equal(
                            defaults['search_right'],
                            image[:template_region.dy, template_region.dx:template_region.dx + search_right_region.dx]):
                        break
                    template_region.dx += 1

            return template_region


def get_bounding_box(image: Image) -> Region:
    """
    Detect the region describing a whitespace-trimmed image
    :param image: image to trim
    :return: trimmed region
    """
    rows = np.any(image, axis=1)
    cols = np.any(image, axis=0)
    row_min, row_max = np.where(rows)[0][[0, -1]]
    col_min, col_max = np.where(cols)[0][[0, -1]]
    return Region(row_min, col_min, row_max - row_min, col_max - col_min)
