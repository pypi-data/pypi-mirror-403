#include <finelc/matrix.h>
#include <finelc/enumerations.h>

#include <finelc/analysis/analysis.h>
#include <finelc/analysis/interpolation.h>

#include <finelc/binding/bindings.h>
#include <finelc/binding/matrix_binding.h>
#include <finelc/binding/geometry_binding.h>


#include <pybind11/pybind11.h>
#include <pybind11/numpy.h> 
#include <pybind11/stl.h>

#include <stdexcept>
#include <vector>
#include <memory>

using namespace finelc;
namespace py = pybind11;

void bind_analysis(py::module_& handle){

    py::enum_<DOFType>(handle, "DOFType")
        .value("UX", DOFType::UX)
        .value("UY", DOFType::UY)
        .value("UZ", DOFType::UZ)
        .value("THETAX", DOFType::THETAX)
        .value("THETAY", DOFType::THETAY)
        .value("THETAZ", DOFType::THETAZ)
        .value("T", DOFType::T)
        .value("P", DOFType::P)
        ;

    py::enum_<InterpolationScheme>(handle, "InterpolationScheme")
        .value("NONE", InterpolationScheme::NONE)
        .value("SIMP", InterpolationScheme::SIMP)
        ;

    py::enum_<InterpolationParameters>(handle, "InterpolationParameters")
        .value("P_EXPONENT", InterpolationParameters::P_EXPONENT)
        .value("X_MIN", InterpolationParameters::X_MIN)
        .value("BETA", InterpolationParameters::BETA)
        .value("THRESHOLD", InterpolationParameters::THRESHOLD)
        ;


    py::class_<IInterpolationScheme, std::shared_ptr<IInterpolationScheme>>(handle,"IInterpolationScheme");
    
    {
    py::class_<Analysis, std::shared_ptr<Analysis>>
    (handle, "Analysis")
        .def_property_readonly("ID",
        [](const Analysis& self) -> Matrix {

            const IDMat& orig_ID = self.get_ID();

            Matrix ID(orig_ID.rows,orig_ID.cols);

            for(int i=0; i<orig_ID.rows; i++){
                for(int j=0; j<orig_ID.cols; j++){
                    ID(i,j) = orig_ID(i,j);
                }
            }
            return ID;
        })

        .def_property_readonly("mesh", &Analysis::get_mesh)
        .def_property_readonly("num_bc_dofs", &Analysis::bc_size)
        .def_property_readonly("num_free_dofs", &Analysis::get_size)
        .def_property_readonly("num_total_dofs", &Analysis::total_size)
        .def_property_readonly("interpolation_scheme", &Analysis::get_interpolation_name)
        // .def_property_readonly("rho", &Analysis::get_pseudo_density)
        
        .def_property_readonly("free_dofs", 
            [](const Analysis& self) -> py::array_t<int> {
                return py::cast(self.get_free_dofs());
            })

        .def_property_readonly("bc_dofs", 
            [](const Analysis& self) -> py::array_t<int> {
                return py::cast(self.get_bc_dofs());
            }            )

        .def("destroy", &Analysis::destroy)

        .def("set_interpolation", &Analysis::set_interpolation)

        .def("update_interpolation", &Analysis::update_interpolation)

        .def("update_pseudo_density", 
            py::overload_cast<double>(&Analysis::update_pseudo_density))

        .def("update_pseudo_density", 
            py::overload_cast<const Vector&>(&Analysis::update_pseudo_density))

        .def("Kg", &Analysis::Kg)
        .def("Mg", &Analysis::Mg)
        .def("fg", &Analysis::fg)

        
        ;
    }

    py::class_<AnalysisBuilder, std::shared_ptr<AnalysisBuilder>>
    (handle, "AnalysisBuilder")

        .def(py::init<Mesh_ptr>(),
             py::arg("mesh"))

        .def("add_boundary_condition", 
            py::overload_cast<DOFType, int, double>(&AnalysisBuilder::add_boundary_condition))

        .def("add_boundary_condition", 
            py::overload_cast<DOFType, std::vector<int>, double>(&AnalysisBuilder::add_boundary_condition))

        .def("add_boundary_condition", 
            py::overload_cast<DOFType, IGeometry_ptr, double>(&AnalysisBuilder::add_boundary_condition))

        .def("add_force", 
            py::overload_cast<DOFType, int, double>(&AnalysisBuilder::add_force))

        .def("add_force", 
            py::overload_cast<DOFType, std::vector<int>, double>(&AnalysisBuilder::add_force))

        .def("add_force", 
            py::overload_cast<DOFType, IGeometry_ptr, double, int>(&AnalysisBuilder::add_force),
            py::arg("dof_type"),
            py::arg("domain"),
            py::arg("value"),
            py::arg("number_of_integration")=10)

        .def("add_force", 
            py::overload_cast<DOFType, IGeometry_ptr, Evalfn, int>(&AnalysisBuilder::add_force),
            py::arg("dof_type"),
            py::arg("domain"),
            py::arg("function"),
            py::arg("number_of_integration")=10)

        .def("build", &AnalysisBuilder::build)

        ;

}