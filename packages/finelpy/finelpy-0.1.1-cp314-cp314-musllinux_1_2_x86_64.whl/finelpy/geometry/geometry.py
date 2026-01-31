import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from ..core.geometry import IGeometry
from ..core.geometry import Rectangle, Line

from ..utils import add_method

@add_method(Rectangle)
def plot(self, facecolor='skyblue', edgecolor='darkblue'):

    fig, ax = plt.subplots()
    rec = patches.Rectangle(self.origin,self.dimensions[0],self.dimensions[1], facecolor=facecolor, edgecolor=edgecolor, linewidth=2, alpha=0.7)
    ax.add_patch(rec)

    ax.set_xlim([self.origin[0]-(self.origin[0]+1)*0.1, self.dimensions[0]+(self.dimensions[0]+1)*0.1])
    ax.set_ylim([self.origin[1]-(self.origin[1]+1)*0.1, self.dimensions[1]+(self.dimensions[1]+1)*0.1])

    return fig,ax
