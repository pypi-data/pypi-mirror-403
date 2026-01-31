#include <finelc/matrix.h>
#include <finelc/enumerations.h>

#include <finelc/elements/element.h>
#include <finelc/elements/integration.h>
#include <finelc/elements/shape_func.h>

#include <finelc/binding/bindings.h>
#include <finelc/binding/matrix_binding.h>
#include <finelc/binding/geometry_binding.h>
#include <finelc/binding/element_binding.h>


#include <pybind11/pybind11.h>
#include <pybind11/numpy.h> 
#include <pybind11/stl.h>

#include <stdexcept>
#include <vector>
#include <memory>

using namespace finelc;
namespace py = pybind11;


void bind_element(py::module_& handle){

    py::enum_<ShapeType>(handle, "ShapeType")
        .value("PYTHON_SHAPE", ShapeType::PYTHON_SHAPE)
        .value("LINE", ShapeType::LINE)
        .value("TRI3", ShapeType::TRI3)
        .value("QUAD4", ShapeType::QUAD4)
        .value("QUAD9", ShapeType::QUAD9)
        .value("HEX8", ShapeType::HEX8)
        ;

    py::enum_<ModelType>(handle, "ModelType")
        .value("PYTHON_PHYSICS", ModelType::PYTHON_PHYSICS)
        .value("BAR_STRUCTURAL", ModelType::BAR_STRUCTURAL)
        .value("BEAM_STRUCTURAL", ModelType::BEAM_STRUCTURAL)
        .value("PLANE_STRUCTURAL", ModelType::PLANE_STRUCTURAL)
        .value("SOLID_STRUCTURAL", ModelType::SOLID_STRUCTURAL)
        .value("THERMAL_CONDUCTION_1D", ModelType::THERMAL_CONDUCTION_1D)
        .value("THERMAL_CONDUCTION_2D", ModelType::THERMAL_CONDUCTION_2D)
        .value("THERMAL_CONDUCTION_3D", ModelType::THERMAL_CONDUCTION_3D)
        ;

    py::enum_<ConstitutiveType>(handle, "ConstitutiveType")
        .value("PYTHON_CONSTITUTIVE", ConstitutiveType::PYTHON_CONSTITUTIVE)
        .value("BAR_LINEAR_ELASTIC", ConstitutiveType::BAR_LINEAR_ELASTIC)
        .value("BEAM_LINEAR_ELASTIC", ConstitutiveType::BEAM_LINEAR_ELASTIC)
        .value("PLANE_STRESS", ConstitutiveType::PLANE_STRESS)
        .value("PLANE_STRAIN", ConstitutiveType::PLANE_STRAIN)
        .value("SOLID_LINEAR_ELASTIC", ConstitutiveType::SOLID_LINEAR_ELASTIC)
        ;

    py::enum_<IntegrationGeometry>(handle, "IntegrationGeometry")
        .value("REGULAR", IntegrationGeometry::REGULAR)
        .value("TRIANGLE", IntegrationGeometry::TRIANGLE)
        ;


    handle.def("get_integration_points",
        [](int number_of_points, IntegrationGeometry geo = IntegrationGeometry::REGULAR,int dimensions=1) -> py::tuple {

            std::vector<PointWeight> pair = get_gauss_points(geo,number_of_points,dimensions);

            py::tuple out(pair.size());
            for(int i=0; i<pair.size(); i++){
                out[i] = py::make_tuple(pair[i].point,pair[i].weight);
            }

            return out;

        },
        py::arg("number_of_points"),
        py::arg("geometry") = IntegrationGeometry::REGULAR,
        py::arg("dimensions") = 1);

    handle.def("eval_lagrange", &eval_lagrange_polynomials,
        py::arg("xi"),
        py::arg("order"));

    handle.def("eval_lagrange_derivative", &eval_lagrange_polynomials_derivatives,
        py::arg("xi"),
        py::arg("order"));


    {
        py::class_<IElementShape, ElementShapeTrampoline, std::shared_ptr<IElementShape>>
        (handle, "ElementShape")

        .def(py::init<>())
        .def_property_readonly("shape", &IElementShape::shape)
        .def_property_readonly("integration_domain", &IElementShape::integration_domain)
        .def_property_readonly("dim", &IElementShape::number_of_dimensions)
        .def_property_readonly("shape_order", &IElementShape::shape_order)
        .def_property_readonly("number_of_nodes", &IElementShape::number_of_nodes)

        .def("J", &IElementShape::J,
            py::arg("element_nodes"),
            py::arg("loc")=py::none())

        .def("detJ", &IElementShape::detJ,
            py::arg("element_nodes"),
            py::arg("loc")=py::none())

        .def("N", &IElementShape::N,
            py::arg("loc"))

        .def("dNdxi", &IElementShape::dNdxi,
            py::arg("loc"))

        .def("dNdx", &IElementShape::dNdx,
            py::arg("element_nodes"),
            py::arg("loc"))
        ;
    }


    {
    py::class_<IElement, ElementTrampoline, std::shared_ptr<IElement>>
    (handle, "Element")

        .def(py::init<>())
        .def_property_readonly("shape", &IElement::get_shape)
        .def_property_readonly("constitutive", &IElement::get_constitutive_model)
        .def_property_readonly("model", &IElement::get_model)
        .def_property_readonly("dofs", &IElement::dofs)

        .def_property_readonly("number_of_integration", &IElement::get_number_integration_points)

        .def_property_readonly("nodes", &IElement::get_nodes)

        .def_property_readonly("edges", &IElement::edges)
        .def_property_readonly("surfaces", &IElement::surfaces)

        .def_property_readonly("number_of_nodes", &IElement::number_of_nodes)
        .def_property_readonly("dofs_per_node", &IElement::dofs_per_node)

        .def_property_readonly("is_linear", &IElement::is_linear)
        .def_property_readonly("linear_physics", &IElement::linear_physics)
        .def_property_readonly("linear_material", &IElement::linear_material)

        /**********************SET UP METHODS****************************/
        .def_property_readonly("node_numbering", &IElement::get_node_numbering)
        .def("set_node_numbering", 
            py::overload_cast<const std::vector<int>&, const VectorNodes&>(&IElement::set_node_numbering))

        .def("set_node_numbering",
            py::overload_cast<const std::vector<int>&>(&IElement::set_node_numbering))

        .def("copy", &IElement::copy)
        .def("copy_to", &IElement::copy_to)


        /**********************SHAPE METHODS****************************/
        .def("J", &IElement::J,
            py::arg("loc")=py::none())

        .def("detJ", &IElement::detJ,
            py::arg("loc")=py::none())

        .def("N_shape", &IElement::N_shape,
            py::arg("loc"))

        // .def("local_to_global",
        //     py::overload_cast<const Point&>(&IElement::local_to_global),
        //     py::arg("loc"))

        // .def("local_to_global",
        //     py::overload_cast<const Vector&>(&IElement::local_to_global),
        //     py::arg("loc"))

        .def("dNdxi_shape", &IElement::dNdxi_shape,
            py::arg("loc"))

        .def("dNdx_shape", &IElement::dNdx_shape,
            py::arg("loc"))

        /******************CONSTITUTIVE METHODS************************/
        .def("D", &IElement::D,
            py::arg("loc")=py::none(),
            py::arg("displacement")=py::none())

        /*********************PHYSICS METHODS**************************/
        .def("N", &IElement::N,
            py::arg("loc"),
            py::arg("displacement")=py::none())

        .def("dNdx", &IElement::dNdx,
            py::arg("loc"),
            py::arg("displacement")=py::none())

        .def("B", &IElement::B,
            py::arg("loc"),
            py::arg("displacement")=py::none())

        .def("Ke", &IElement::Ke,
            py::arg("displacement")=py::none())

        .def("Me", &IElement::Me,
            py::arg("displacement")=py::none())


        /************************INTEGRATION METHODS*****************************/
        .def("integration_pair", 
            [](const IElement& self, int num_points = 0) -> py::list {
                std::vector<PointWeight> pairs = self.integration_pair(num_points);

                py::list pair_list;

                for(auto& pair:pairs){
                    pair_list.append(py::make_tuple(pair.point, pair.weight));
                }

                return pair_list;

            },
            py::arg("num_points")=0)

        .def_property_readonly("integration_points", &IElement::integration_points)
        .def_property_readonly("integration_weights", &IElement::integration_weights)
        .def("set_number_integration_points", &IElement::set_number_integration_points)

        /*********************RESULT ACCESS METHODS**************************/

        // double compute_double(ResultData data_name, )

        // ELASTICITY
        .def_property_readonly("supports_strain", &IElement::supports_strain)
        .def("get_strain", &IElement::get_strain)

        .def_property_readonly("supports_stress", &IElement::supports_stress)
        .def("get_stress", &IElement::get_stress)

        ;
    }

    handle.def("create_element",
            &create_element,
            py::arg("shape_type"),
            py::arg("model_type"),
            py::arg("constitutive_type"),
            py::arg("material")=py::none(),
            py::return_value_policy::automatic_reference
        );

    handle.def("move_element_to_Cpp",
    [](const py::object& el) -> IElement_ptr {
        auto cpp = el.cast<IElement_ptr>();
        cpp->py_self = std::make_unique<py::object>(el);
        return cpp;
    });


}