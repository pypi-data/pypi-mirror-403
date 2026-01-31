from .elements import pyElement

from ..core.element import ShapeType, eval_lagrange, eval_lagrange_derivative, move_element_to_Cpp
from ..core.analysis import DOFType

import numpy as np

class LineElement(pyElement):

    def __init__(self, material, order: int = 1):
        super().__init__(material)
        self.order_ = order
        N = int(np.ceil((2*order+1)/2))
        self.set_number_integration_points(N)
        self.L_ = None
    
    ##################### SHAPE METHODS ##########################

    def get_shape(self) -> ShapeType:
        return ShapeType.LINE
    
    def number_of_dimensions(self):
        return 1

    def number_of_nodes(self):
        return self.order_ + 1
    
    def number_of_vertices(self):
        return 2
    
    def J(self, *args, **kargs) -> np.ndarray:
        return np.array([self.L / 2])
    
    def detJ(self, *args, **kargs) -> float:
        return self.L / 2
    
    def N_shape(self, loc):
        return eval_lagrange(loc[0],self.order_)
    
    def dNdxi_shape(self, loc):
        return np.array([eval_lagrange_derivative(loc[0],self.order_)])
    
    def dNdx_shape(self, loc):
        return self.dNdxi_shape(loc)/ self.J()

    def B(self, loc, ue=None):
        return self.dNdx(loc, ue)
    
    
    ##################### CONSTITUTIVE METHODS ##########################

    @property
    def L(self) -> float:
        if self.L_ is None:
            self.L_ = np.linalg.norm(self.nodes[1]-self.nodes[0])
        return self.L_

    @property
    def theta(self)-> float:
        if self.theta_ is None:
            deltas = self.nodes[1]-self.nodes[0]
            self.theta_ = np.atan2(deltas[1],deltas[0])
        return self.theta_

    @property
    def A(self) -> float:
        return self.material.A

    @property
    def Izz(self) -> float:
        return self.material.IZZ
    
class BarElementExercise(LineElement):
    def __init__(self, material, order: int = 1):
        super().__init__(material, order)

    def copy(self,same_matrix: bool):
        new_type = type(self)
        new_el = new_type(self.material, self.order_)
        self.copy_to(new_el)
        if same_matrix:
            new_el.ke = self.ke
            new_el.me = self.me
            
        return move_element_to_Cpp(new_el)

    ##################### PHYSICS METHODS ##########################
    def dofs(self):
        return [DOFType.UX]
    
    def dofs_per_node(self):
        return 1
    
    def D(self, *args, **kargs):
        return np.array([[self.material.E * self.material.A]])
    
class BeamElementExercise(LineElement):
    def __init__(self, material, order: int = 1):
        super().__init__(material, order)

    def copy(self,same_matrix: bool):
        new_type = type(self)
        new_el = new_type(self.material)
        self.copy_to(new_el)
        if same_matrix:
            new_el.ke = self.ke
            new_el.me = self.me
            
        return move_element_to_Cpp(new_el)

    ##################### PHYSICS METHODS ##########################
    def dofs(self):
        return [DOFType.UY, DOFType.THETAZ]
    
    def dofs_per_node(self):
        return 2
    
    def D(self, *args, **kargs):
        return np.array([[self.material.E * self.Izz]])

class TrussElementExercise(LineElement):
    def __init__(self, material, order: int = 1):
        self.R_ = None
        self.theta_ = None
        super().__init__(material, order)

    def copy(self,same_matrix: bool):
        new_type = type(self)
        new_el = new_type(self.material)
        self.copy_to(new_el)
            
        return move_element_to_Cpp(new_el)
    
    @property
    def R(self):
        if self.R_ is None:
            cos = np.cos(self.theta)
            sin = np.sin(self.theta)

            self.R_ = np.array([
                [cos, sin, 0, 0],
                [-sin, cos, 0, 0],
                [0, 0, cos, sin],
                [0, 0, -sin, cos]
            ]
            )
        return self.R_
    
    def dofs(self):
        return [DOFType.UX, DOFType.UY]
    
    def dofs_per_node(self):
        return 2
    
    def local_to_global(self, loc):
        val = np.zeros(3,dtype=float)
        val[0:2] = self.R @ np.array([loc[0],0])
        return val

    
    def N(self, loc,ue=None):
        xi = loc[0]
        N = np.array([eval_lagrange(xi,self.order_)])
        return N

    def dNdx(self, loc, ue=None):
        return self.dNdxi_shape(loc)/ self.J()
    



class BarElement(BarElementExercise):

    def __init__(self, material, order: int = 1):
        super().__init__(material, order)
    
    
    def N(self, loc,ue=None):
        xi = loc[0]
        N = np.array([eval_lagrange(xi,self.order_)])
        return N
    
    def dNdx(self, loc, ue=None):
        return self.dNdxi_shape(loc)/ self.J()

    
    ################## RESULT ACCESS METHODS ######################
    
    def get_strain(self,loc, ue):
        strain = self.B(loc, ue) @ ue
        return strain
    
    def get_stress(self,loc, ue):
        stress = self.material.E * self.get_strain(loc, ue)
        return stress
    
    def get_NX(self,loc, ue):
        return self.A * self.get_stress(loc, ue)
    
class BeamElement(BeamElementExercise):

    def __init__(self, material):
        super().__init__(material, 1)



    def N(self,loc, ue=None):
        x = (loc[0]+1)/2
        he = self.L

        Nval = np.array([[
            2*x**3 - 3*x**2 + 1,
            he*(x**3 - 2*x**2 + x),
            -2*x**3 + 3*x**2,
            he*(x**3 - x**2)],
            [
            (6*x**2 - 6*x)/he,
            (3*x**2 - 4*x + 1),
            (-6*x**2 + 6*x)/he,
            (3*x**2 - 2*x)
            ]
        ])
        return Nval
    
    def dNdx(self, loc, ue=None):
        x = (loc[0]+1)/2
        he = self.L
        he2 = he**2

        ddNval = np.array([
            (12*x-6)/he2,
            (6*x-4)/he,
            (-12*x+6)/he2,
            (6*x-2)/he
        ])
        return np.array([ddNval])
    
    def dddN(self, loc):
        x = (loc[0]+1)/2
        he = self.L
        he2 = he**2
        he3 = he**3

        dddNval = np.array([
            12/he3,
            6/he2,
            -12/he3,
            6/he2
        ])
        return np.array([dddNval])
    
    def get_strain(self,loc, ue):
        strain = -self.B(loc, ue) @ ue
        return strain
    
    def get_stress(self,loc, ue):
        stress = self.material.E * self.get_strain(loc, ue)
        return stress
    
    def get_MZ(self,loc, ue):
        return self.material.E*self.Izz *self.B(loc, ue) @ ue
    
    def get_VY(self,loc, ue):
        return self.material.E*self.Izz * self.dddN(loc) @ ue