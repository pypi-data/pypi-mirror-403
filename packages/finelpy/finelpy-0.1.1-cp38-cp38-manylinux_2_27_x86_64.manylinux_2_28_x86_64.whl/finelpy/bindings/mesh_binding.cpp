

#include <finelc/enumerations.h>
#include <finelc/mesh/mesh.h>
#include <finelc/mesh/meshers.h>

#include <finelc/elements/element.h>

#include <finelc/binding/bindings.h>
#include <finelc/binding/matrix_binding.h>
#include <finelc/binding/geometry_binding.h>

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h> 
#include <pybind11/eigen.h>
#include <pybind11/stl.h>

// #include <stdexcept>
#include <vector>
#include <memory>
#include <optional>
#include <cmath>

using namespace finelc;
namespace py = pybind11;




void bind_mesh(py::module_& handle){


    {
    py::class_<Mesh, Mesh_ptr>
    (handle, "Mesh", py::dynamic_attr())


        .def_property_readonly("number_of_elements",
            &Mesh::number_of_elements)

        .def_property_readonly("number_of_nodes",
            &Mesh::number_of_nodes)

        .def_property_readonly("nodes", &Mesh::get_nodes)

        .def_property_readonly("elements", 
            [](const Mesh &self) {

            const VectorElements& elements = self.get_elements(); 

            // Create a numpy array of shape (N, 3)
            int n = elements.size();
            py::list els(n); 

            for (int i = 0; i < n; ++i) {
                els[i] = py::cast( elements[i], py::return_value_policy::reference_internal);
            }

            return els;
        })

        .def_property_readonly("element_nodes", 
            [](const Mesh &self) {

            VectorElements elements = self.get_elements(); 

            // Create a numpy array of shape (N, 3)
            int n = elements.size();
            py::list els(n); 

            for (int i = 0; i < n; ++i) {
                els[i] = py::cast(elements[i]->get_node_numbering(), py::return_value_policy::reference_internal);
            }

            return els;
        })
    

        .def_property_readonly("centers", &Mesh::element_center)
        
        .def("find_element", &Mesh::find_element)

        .def_property_readonly("ravel_elements",
            [](const Mesh &self) -> std::vector<std::vector<std::vector<double>>> {

                std::vector<std::vector<std::vector<double>>> element_ravel;
                element_ravel.reserve(self.number_of_elements());

                for(auto& el: self.get_elements()){

                    const VectorNodes& nodes = el->get_nodes();

                    std::vector<std::vector<double>> el_poly;
                    el_poly.reserve(nodes.size());

                    for(int n_vert=0; n_vert<el->number_of_vertices(); n_vert++){
                        el_poly.push_back({nodes[n_vert]->x, nodes[n_vert]->y});
                    }
                    element_ravel.emplace_back(std::move(el_poly));
                }

                return element_ravel;
            })

    //     .def("interpolate_gauss_point_values",
    //         [](const Mesh &self, Vector nodal_values, int num_gauss_points=3) -> py::array_t<double> {

    //             const VectorElements& elements = self.get_elements();

    //             int estimate_points=0;

    //             for(auto& element: elements){
    //                 estimate_points += std::pow(num_gauss_points,element->number_of_dimensions()) + 10*(num_gauss_points+1);
    //             }

    //             py::array_t<double> vec({estimate_points,4});
    //             auto arr = vec.mutable_unchecked<2>();

    //             int k = 0;
    //             for(auto& element: elements){
    //                 std::vector<PointWeight> gauss_points = get_gauss_points(   element->get_integration_domain(),
    //                                                                             num_gauss_points, 
    //                                                                             element->number_of_dimensions(),
    //                                                                             true);

    //                 Vector local_values = element->get_nodal_values_scalar(nodal_values);
    //                 for(auto& p: gauss_points){
    //                     Vector loc = p.point.as_vector();
    //                     Vector coords = element->local_to_global(loc);
    //                     arr(k,0) = coords(0);
    //                     arr(k,1) = coords(1);
    //                     arr(k,2) = coords(2);
    //                     arr(k,3) = element->interpolate_nodal_values(loc,local_values);
    //                     k++;
    //                 }
    //             }

    //             auto buf = vec.request();
    //             return py::array_t<double>({k,4},
    //                                         {buf.strides[0], buf.strides[1]},
    //                                         static_cast<double*>(buf.ptr),
    //                                         vec );
    //         }
    //     )

        ;
    }

    {
    py::class_<MeshBuilder, std::shared_ptr<MeshBuilder>>
    (handle, "MeshBuilder")

        .def("build", 
            &MeshBuilder::build)
        ;
    }

    {
    py::class_<MeshBuilderLine, MeshBuilder, std::shared_ptr<MeshBuilderLine>>
    (handle, "LineMesh")

        .def(py::init<std::shared_ptr<Line>, IElement_ptr>(),
             py::arg("line"),
             py::arg("element"))

        .def("create_from_element_num", 
            &MeshBuilderLine::create_from_element_num)

            
        .def("create_from_element_size",
            &MeshBuilderLine::create_from_element_size)

        ;
    }

    {
    py::class_<MeshBuilderRectangle, MeshBuilder, std::shared_ptr<MeshBuilderRectangle>>
    (handle, "RectangularMesh")

        .def(py::init<std::shared_ptr<IArea>, IElement_ptr>(),
             py::arg("domain"),
             py::arg("element"))

        .def("set_element_size", 
            &MeshBuilderRectangle::set_element_size)

            
        .def("set_grid",
            &MeshBuilderRectangle::set_grid)
        ;
    }

    {
    py::class_<MeshBuilderFrame, MeshBuilder, std::shared_ptr<MeshBuilderFrame>>
    (handle, "FrameMesh")

        .def(py::init<IElement_ptr, VectorNodes, std::vector<std::vector<int>>>(),
            py::arg("element"),
            py::arg("node_coord"),
            py::arg("inci"))
        ;
    }

}