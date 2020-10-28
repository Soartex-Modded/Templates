import json
import os
import numpy as np
from PIL import Image
from typing import List


class TemplateLoader(object):
    """
    Helper class to load templates and template metadata from a templates directory.
    """
    def __init__(self, template_dir):
        if not os.path.exists(template_dir):
            raise FileNotFoundError("template directory missing")
        self.template_dir = template_dir
        self.templates = {}
        self.sizes = {}
        self.metadata = {}

    def load_template(self, name):
        if not name.endswith(".png"):
            name += ".png"

        path = os.path.join(self.template_dir, name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"template missing: {os.path.basename(path)}")

        template_name = name.replace(".png", "")
        self.templates[template_name] = np.array(Image.open(path))
        self.sizes[template_name] = np.prod(self.templates[template_name].shape[:2])

        metadata_path = os.path.join(self.template_dir, f"{template_name}.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as metadata_file:
                self.metadata[template_name] = json.load(metadata_file)

    def __getitem__(self, item):
        if not item in self.templates:
            self.load_template(item)

        return self.templates[item]

    def __iter__(self):
        for filename in os.listdir(self.template_dir):
            self.load_template(filename)

        # return in largest-to-smallest order
        for template, _ in sorted(self.sizes.items(), key=lambda v: -v[1]):
            yield template, self[template]

    def sort(self, regions: List["Region"]) -> List["Region"]:
        return sorted(regions, key=lambda r: self.metadata.get(r.name, {}).get("layer", 100))


class Region(object):
    """
    Helper class to manipulate bounding boxes.
    """
    def __init__(self, y, x, dy, dx, mask=None, name=None):
        self.y = y
        self.x = x
        self.dy = dy
        self.dx = dx
        self.mask = mask
        self.name = name

    @property
    def lower(self):
        return self.y + self.dy

    @property
    def right(self):
        return self.x + self.dx

    @property
    def shape(self):
        return self.dy, self.dx

    @property
    def slice(self):
        return slice(self.y, self.lower), slice(self.x, self.right)

    @staticmethod
    def from_image(image, name=None):
        return Region(0, 0, *image.shape[:2], name=name)

    def remove_from(self, base):
        base[self.slice] = False if self.mask is None else ~self.mask

    def __repr__(self):
        return f"Region({self.y}, {self.x}, {self.dx}, {self.dy}, name={self.name})"

    def __mul__(self, other):
        # Masks are dropped. Not necessary at this point, and brings in another dependency. Could use:
        # skimage.transform.resize(self.mask, (self.dy * other, self.dx * other), order=0)
        return Region(int(self.y * other), int(self.x * other), int(self.dy * other), int(self.dx * other), name=self.name)

    def __imul__(self, other):
        return self * other