# from ..core.element import create_element

from ..core.element import *
from ..core.element import ShapeType, ElementShape, IntegrationGeometry, Element
from ..core.material import Material

import numpy as np

def shape_error(name: str):
    raise RuntimeError(f"Must define {name} function in pyShape class")

def element_error(name: str):
    raise RuntimeError(f"Must define {name} function in pyElement class")

class pyShape(ElementShape):

    def __init__(self):
        super().__init__()

    def shape(self) -> ShapeType:
        try:
            if(self.number_of_dimensions()==2):
                if(self.number_of_nodes()==4):
                    return ShapeType.QUAD4
                elif(self.number_of_nodes()==3):
                    return ShapeType.TRI3
                else:
                    raise
            else:
                raise
        except:
            shape_error("shape()")

    def number_of_dimensions(self):
        try:
            if(self.shape() in [ShapeType.QUAD4, ShapeType.TRI3]):
                return 2
            else:
                raise
        except:
            shape_error("number_of_dimensions()")
    
    def shape_order(self):
        try:
            if(self.shape() == ShapeType.QUAD4):
                return 2
            elif(self.shape() == ShapeType.TRI3):
                return 2
            else:
                raise
        except:
            shape_error("shape_order()")
        
    
    def number_of_nodes(self):
        try:
            if(self.shape() == ShapeType.QUAD4):
                return 4
            elif(self.shape() == ShapeType.TRI3):
                return 3
            else:
                raise
        except:
            shape_error("number_of_nodes()")

    def number_of_vertices(self):
        try:
            return self.number_of_nodes()
        except:
            shape_error("number_of_vertices()")
            
    
    def integration_domain(self):
        try:
            if(self.shape() == ShapeType.QUAD4):
                return IntegrationGeometry.REGULAR
            elif(self.shape() == ShapeType.TRI3):
                return IntegrationGeometry.TRIANGULAR
            else:
                return IntegrationGeometry.REGULAR
        except:
            return IntegrationGeometry.REGULAR
    
    def N(self, loc: np.ndarray):
        shape_error("N(np.ndarray)")
    
    def dNdxi(self, loc: np.ndarray):
        shape_error("dNdxi(np.ndarray)")
    
    def J(self, element_nodes, loc):
        return self.dNdxi(loc) @ element_nodes[:,:self.number_of_dimensions()]
    
    def detJ(self, element_nodes, loc):
        return np.linalg.det(self.J(element_nodes, loc))
    
class pyMatrix:
    def __init__(self,value):
        self.value = value


class pyElement(Element):

    def __init__(self, material: Material):
        super().__init__()
        self.ke = pyMatrix(None)
        self.me = pyMatrix(None)
        self.material = material

    def copy(self,same_matrix: bool):
        new_type = type(self)
        new_el = new_type(self.material)
        self.copy_to(new_el)
        if same_matrix:
            new_el.ke = self.ke
            new_el.me = self.me
            
        return move_element_to_Cpp(new_el)

    ##################### SHAPE METHODS ##########################
    def get_shape(self)->ShapeType:
        element_error("get_shape()")

    def number_of_nodes(self):
        if(self.get_shape() == ShapeType.QUAD4):
            return 4
        elif(self.get_shape() == ShapeType.TRI3):
            return 3
        else:
            element_error("number_of_nodes()")
    
    def number_of_vertices(self):
        try:
            return self.number_of_nodes()
        except:
            element_error("number_of_vertices()")

    def number_of_dimensions(self):
        if(self.get_shape() in [ShapeType.QUAD4, ShapeType.TRI3]):
            return 2
        else:
            element_error("number_of_dimensions()")

    
    def get_integration_domain(self):
        if(self.get_shape() == ShapeType.QUAD4):
            return IntegrationGeometry.REGULAR
        elif(self.get_shape() == ShapeType.TRI3):
            return IntegrationGeometry.TRIANGULAR
        else:
            return IntegrationGeometry.REGULAR
        
    def J(self,loc: np.ndarray):
        return self.dNdxi_shape(loc) @ self.nodes[:,:self.number_of_dimensions()]

    def detJ(self,loc: np.ndarray) -> float:
        return np.linalg.det(self.J(loc))
    
    # def local_to_global(self, loc: np.ndarray):
    #     element_error("local_to_global(np.ndarray)")

    def N_shape(self, loc: np.ndarray):
        element_error("N_shape(np.ndarray)")

    def dNdxi_shape(self, loc: np.ndarray):
        element_error("dNdxi_shape(np.ndarray)")

    def dNdx_shape(self, loc: np.ndarray):
        element_error("dNdx_shape(np.ndarray)")

    ##################### CONSTITUTIVE METHODS ##########################
    def get_constitutive_model(self):
        element_error("get_constitutive_model()")

    def linear_material(self) -> bool:
        return True

    def get_property(self, prop):
        element_error("get_property(finelpy.MaterialProperties)")

    def D(self, ue: np.ndarray,loc: np.ndarray):
        element_error("D(np.ndarray,np.ndarray)")

    ##################### PHYSICS METHODS ##########################
    def get_model(self):
        element_error("get_model()")

    def dofs(self):
        element_error("dofs()")

    def dofs_per_node(self):
        try:
            return len(self.dofs())
        except:
            element_error("dofs_per_node()")

    
    def linear_physics(self):
        return True

    def N(self, loc: np.ndarray, ue: np.ndarray):
        element_error("N(np.ndarray,np.ndarray)")

    def dNdx(self, loc: np.ndarray, ue: np.ndarray):
        element_error("dNdx(np.ndarray,np.ndarray)")

    def B(self, loc: np.ndarray, ue: np.ndarray):
        element_error("B(np.ndarray,np.ndarray)")
        
    ##################### MATRIX METHODS ##########################

    def Ke(self, ue: np.ndarray=None):
        # try:
        if self.ke.value is None:
            n = self.dofs_per_node() * self.number_of_nodes()
            ke = np.zeros((n,n),dtype=float)
            for loci, wi in self.integration_pair():
                
                B = self.B(loci,ue)
                detJ = self.detJ(loci)

                D = self.D(ue,loci)

                ke += B.T @ D @ (B * (detJ * wi))

            self.ke.value = ke

        return self.ke.value
        # except:
        #     element_error("Ke(np.ndarray)")

    def Me(self, ue: np.ndarray):
        element_error("Ke(np.ndarray)")


    ################## RESULT ACCESS METHODS ######################

    def supports_strain(self):
        return self.get_strain.__func__ is not pyElement.get_strain

    def get_strain(self, loc: np.ndarray, ue: np.ndarray):
        element_error("get_strain(np.ndarray,np.ndarray)")

    def supports_stress(self):
        return self.get_stress.__func__ is not pyElement.get_stress

    def get_stress(self, loc: np.ndarray, ue: np.ndarray):
        element_error("get_stress(np.ndarray,np.ndarray)")
    
    def supports_NX(self):
        return self.get_NX.__func__ is not pyElement.get_NX

    def get_NX(self, loc: np.ndarray, ue: np.ndarray):
        element_error("get_NX(np.ndarray,np.ndarray)")

    def supports_MZ(self):
        return self.get_MZ.__func__ is not pyElement.get_MZ

    def get_MZ(self, loc: np.ndarray, ue: np.ndarray):
        element_error("get_MZ(np.ndarray,np.ndarray)")


    def supports_VY(self):
        return self.get_VY.__func__ is not pyElement.get_VY

    def get_VY(self, loc: np.ndarray, ue: np.ndarray):
        element_error("get_VY(np.ndarray,np.ndarray)")


    