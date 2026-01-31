import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from ..core.solver import StaticResult, ResultData
from ..core import vtk_enabled

from ..utils import add_method

@add_method(StaticResult)
def plot_data1D(self,
            id: ResultData,
            internal_pts: int=10,
            show_nodes: bool=False,
            mult=1):

    import matplotlib.pyplot as plt 
    import matplotlib.tri as tri

    pdata, cdata = self.grid_data(id,internal_pts)
    if mult != 1:
        cdata*=mult
    xdata = pdata[:,0]

    fig, ax = plt.subplots()
    ax.plot(xdata,cdata)
        
    if show_nodes:
        xnode = self.analysis.mesh.nodes[:,0]
        node_data = np.interp(xnode,xdata,cdata)
        ax.scatter(xnode,node_data,color='black')

    return ax, xdata


if(not vtk_enabled()):

    @add_method(StaticResult)
    def plot_2D_grid(self,
                    id: ResultData,
                    internal_pts=10,
                    show_edges: bool=False,
                    show_nodes: bool=False):
        
        import vtk

        pdata, cdata = self.grid_data(id,internal_pts)

        vtk_points = vtk.vtkPoints()
        vtk_values = vtk.vtkFloatArray()
        vtk_values.SetName("Values")


        for i in range(pdata.shape[0]):
            pt = pdata[i,:]
            vtk_points.InsertNextPoint(pt)
            vtk_values.InsertNextValue(cdata[i])

        # Create a vtkPolyData to store points
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(vtk_points)
        polydata.GetPointData().SetScalars(vtk_values)

        # Create a glyph (sphere) for each point
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetRadius(0.1)  # Base radius

        glyph = vtk.vtkGlyph3D()
        glyph.SetSourceConnection(sphere_source.GetOutputPort())
        glyph.SetInputData(polydata)
        glyph.SetColorModeToColorByScalar()  # Use scalar values for color
        glyph.SetScaleModeToScaleByScalar()  # Optionally scale spheres by values
        glyph.Update()

        # Mapper and Actor
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(glyph.GetOutputPort())
        mapper.SetScalarRange(np.min(cdata), np.max(cdata))  # Map values to colors

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # Renderer, RenderWindow, Interactor
        renderer = vtk.vtkRenderer()
        renderer.AddActor(actor)
        renderer.SetBackground(0.2, 0.3, 0.4)  # Dark blue background

        render_window = vtk.vtkRenderWindow()
        render_window.AddRenderer(renderer)
        render_window.SetSize(800, 600)

        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(render_window)

        # Start visualization
        render_window.Render()
        interactor.Start()