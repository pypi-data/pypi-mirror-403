import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from ..core.material import MaterialCatalogue
from ..core.material import Material
from ..core.material import MaterialProperties


def create_material(name: str) -> Material:

    return MaterialCatalogue.get_catalogue().create_material(name)