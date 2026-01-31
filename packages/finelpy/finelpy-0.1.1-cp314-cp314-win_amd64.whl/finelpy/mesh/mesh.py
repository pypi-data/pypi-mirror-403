import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as colors

from finelpy.geometry.geometry import IGeometry

from ..core.mesh import RectangularMesh, LineMesh, FrameMesh
from ..core.mesh import Mesh

from ..utils import add_method

@add_method(Mesh)
def plot_lines(self,values=None, 
                edgecolor='darkblue', 
                gauss_points=3,
                show_colorbar=False,
                colormap='viridis'):
   
    from matplotlib.collections import LineCollection
    import matplotlib.pyplot as plt 

    fig, ax = plt.subplots()

    nodes = self.nodes
    elements = nodes[self.element_nodes,:2]

    if values is None:
        pc = LineCollection(elements,
                            edgecolor=edgecolor)
    else:
        pc = LineCollection(elements,
                            array=values,
                            cmap=plt.get_cmap(colormap),
                            norm=colors.CenteredNorm())
        

    ax.add_collection(pc)

    if show_colorbar:
        plt.colorbar(pc)

    ax.set_axis_off()
    ax.autoscale()
    ax.set_aspect("equal")

    return fig,ax
   

@add_method(Mesh)
def plot_nodal2D(self,
            nodal_values,
            gauss_points=3,
            show_edges=False,
            show_colorbar=False):

    import matplotlib.pyplot as plt 
    import matplotlib.tri as tri

    nodes = self.nodes
    
    if nodal_values is None:
        nodal_values = np.ones(len(nodes))
        gauss_points = 0

    data = self.interpolate_gauss_point_values(nodal_values,gauss_points)

    xdata = data[:,0]
    ydata = data[:,1]
    cdata = data[:,3]


    fig, ax = plt.subplots()
        
    if not hasattr(self, "triangles") or self.triangles is None:
        self.triangles = tri.Triangulation(xdata, ydata)

    trip = ax.tripcolor(self.triangles,cdata)

    xmin = np.min(nodes[:,0])
    xmax = np.max(nodes[:,0])
    ymin = np.min(nodes[:,1])
    ymax = np.max(nodes[:,1])
    ax.set_xlim([xmin-abs(xmin+1)*0.1, xmax+abs(xmax+1)*0.1])
    ax.set_ylim([ymin-abs(ymin+1)*0.1, ymax+abs(ymax+1)*0.1])
    ax.autoscale()
    ax.set_aspect("equal")

    if show_colorbar:
        plt.colorbar(trip)

    if show_edges:
        self.plot_mesh2D(show_edges=True,fig=fig,ax=ax,facecolors='None')

    return fig,ax



@add_method(Mesh)
def plot_mesh2D(self,
                element_data = None,
                show_colorbar=False,
                show_edges = False,
                show_nodes=False,
                colormap=None,
                facecolors="gray",
                fig=None,
                ax=None):
    
    from matplotlib.collections import PolyCollection

    if (ax is None) or (fig is None):
        fig, ax = plt.subplots()

    if show_edges:
        edge_color = "blue"
    else:
        edge_color = "face"

    polygons = self.ravel_elements

    if element_data is None:
        pc = PolyCollection(polygons,facecolors=facecolors,edgecolors=edge_color)
    else:
        if np.max(element_data) <= 1 and np.min(element_data) >= 0 and colormap is None:
            colormap = 'binary'
        
        if colormap is None:
            colormap = 'viridis'
        pc = PolyCollection(polygons, array=element_data,cmap=colormap,edgecolors=edge_color)
        
    ax.add_collection(pc)
    ax.autoscale()
    ax.set_aspect("equal")
    ax.set_axis_off()

    if show_colorbar and element_data is not None:
        plt.colorbar(pc, ax=ax)

    if show_nodes:
        ax.plot(self.nodes[:,0],self.nodes[:,1],'ko',markersize=3)

    return fig, ax