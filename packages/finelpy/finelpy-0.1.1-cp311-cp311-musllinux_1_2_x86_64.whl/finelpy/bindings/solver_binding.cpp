#include <finelc/matrix.h>
#include <finelc/enumerations.h>

#include <finelc/analysis/analysis.h>
#include <finelc/solver/solver.h>
#include <finelc/result/result.h>

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h> 
#include <pybind11/stl.h>

#include <finelc/binding/bindings.h>
#include <finelc/binding/matrix_binding.h>
#include <finelc/binding/geometry_binding.h>


#include <stdexcept>
#include <vector>
#include <memory>

using namespace finelc;
namespace py = pybind11;


void bind_solver(py::module_& handle){

    py::enum_<SolverType>(handle, "SolverType")
        .value("Direct", SolverType::Direct)
        .value("Iterative", SolverType::Iterative)
        ;

    py::enum_<ResultData>(handle, "ResultData")
        .value("UX", ResultData::UX)
        .value("UY", ResultData::UY)
        .value("UZ", ResultData::UZ)
        .value("THETAX", ResultData::THETAX)
        .value("THETAY", ResultData::THETAY)
        .value("THETAZ", ResultData::THETAZ)

        .value("ABS_U", ResultData::ABS_U)
        .value("EPSILON_XX", ResultData::EPSILON_XX)
        .value("EPSILON_YY", ResultData::EPSILON_YY)
        .value("EPSILON_ZZ", ResultData::EPSILON_ZZ)
        .value("EPSILON_XY", ResultData::EPSILON_XY)
        .value("EPSILON_XZ", ResultData::EPSILON_XZ)
        .value("EPSILON_YZ", ResultData::EPSILON_YZ)
        .value("SIGMA_XX", ResultData::SIGMA_XX)
        .value("SIGMA_YY", ResultData::SIGMA_YY)
        .value("SIGMA_ZZ", ResultData::SIGMA_ZZ)
        .value("SIGMA_XY", ResultData::SIGMA_XY)
        .value("SIGMA_XZ", ResultData::SIGMA_XZ)
        .value("SIGMA_YZ", ResultData::SIGMA_YZ)
        .value("SIGMA_VONMISES", ResultData::SIGMA_VONMISES)
        .value("NX", ResultData::NX)
        .value("VY", ResultData::VY)
        .value("MZ", ResultData::MZ)
        ;


    py::class_<StaticResult, std::shared_ptr<StaticResult>>
    (handle, "StaticResult", py::dynamic_attr())

        .def_property_readonly("u",&StaticResult::u)
        .def_property_readonly("nodes",&StaticResult::nodes)
        .def_property_readonly("elements",&StaticResult::elements)
        .def_property_readonly("analysis",&StaticResult::get_analysis)

        .def("get_points", &StaticResult::get_points,
            py::arg("internal_pts")=10)

        .def("grid_data", &StaticResult::grid_data,
            py::arg("result_id"),
            py::arg("internal_pts")=10)

        .def("get_max", &StaticResult::get_max,
            py::arg("result_id"),
            py::arg("internal_pts")=10)
        
        .def("get_min", &StaticResult::get_min,
            py::arg("result_id"),
            py::arg("internal_pts")=10)

        .def("element_mean", &StaticResult::element_mean,
            py::arg("result_id"),
            py::arg("gauss_pts")=10)

        .def("compliance", &StaticResult::get_compliance)

        .def("compliance_sensitivity", &StaticResult::compliance_derivative)
         
        #ifdef USE_VTK
            .def("plot_2D_grid", &StaticResult::plot_2D_grid,
                py::arg("result_id"),
                py::arg("internal_pts")=10,
                py::arg("show_edges")=false,
                py::arg("show_nodes")=false)
        #endif
        ;

    
    py::class_<StaticSolver, std::shared_ptr<StaticSolver>>
    (handle, "StaticSolver")

        .def(py::init<Analysis_ptr>(),
             py::arg("analysis"))
        .def(py::init<Analysis_ptr, SolverType>(),
             py::arg("analysis"),
             py::arg("solver_type"))

        .def("solve", &StaticSolver::solve);
}