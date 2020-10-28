import os

from resource_manager.gui_builder import detect_regions, build_gui
from resource_manager.main import run


def test_gui_builder():
    template_dir = "/Users/michael/graphics/fanver/Templates/python_package/resource_manager/configs/gui_templates/"

    test_path = "/Users/michael/graphics/fanver/Templates/python_package/app_test.png"
    colossal_gui_path = "/Users/michael/graphics/default/Modded-1.15.x/Colossal_Chests/assets/colossalchests/textures/gui/colossal_chest.png"

    default_template_dir = os.path.join(template_dir, "default")
    fanver_wood_template_dir = os.path.join(template_dir, "fanver_wood")

    regions, size = detect_regions(
        default_gui_path=colossal_gui_path,
        default_template_dir=default_template_dir,
        debug_path=test_path)

    output_image = build_gui(
        regions=regions,
        size=size,
        resource_template_dir=fanver_wood_template_dir)

    output_image.save(test_path)



run("build_guis_fanver_1.7")

