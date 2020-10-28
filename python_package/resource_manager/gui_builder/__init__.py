from .utilities import TemplateLoader, Region
from .detector import detect_regions
from .builder import build_gui

# Two stages:
# 1. detector.py scans an image for known-textured templates
#                each detected template is a "region"
#                returns a list of detected regions
# 2. builder.py  uses a list of regions to construct a GUI
#                each region points to a template,
#                and each template has replacement textures
