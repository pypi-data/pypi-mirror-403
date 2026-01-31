#include <finelc/material/material.h>

#include <finelc/binding/bindings.h>
#include <finelc/binding/matrix_binding.h>

#include <pybind11/pybind11.h>
#include <pybind11/eigen.h> 
#include <pybind11/numpy.h> 
#include <pybind11/stl.h>

#include <stdexcept>

using namespace finelc;
namespace py = pybind11;


void bind_material(py::module_& handle){

     py::enum_<MaterialProperties>(handle, "MaterialProperties")

          .value("RHO", MaterialProperties::RHO)
          .value("YOUNGS_MOD", MaterialProperties::YOUNGS_MOD)
          .value("YOUNGS_MOD_XX", MaterialProperties::YOUNGS_MOD_XX)
          .value("YOUNGS_MOD_YY", MaterialProperties::YOUNGS_MOD_YY)
          .value("YOUNGS_MOD_ZZ", MaterialProperties::YOUNGS_MOD_ZZ)
          .value("POISSON", MaterialProperties::POISSON)
          .value("POISSON_XY", MaterialProperties::POISSON_XY)
          .value("POISSON_XZ", MaterialProperties::POISSON_XZ)
          .value("POISSON_YZ", MaterialProperties::POISSON_YZ)
          .value("THERMAL_COND_X", MaterialProperties::THERMAL_COND_X)
          .value("THERMAL_COND_Y", MaterialProperties::THERMAL_COND_Y)
          .value("THERMAL_COND_Z", MaterialProperties::THERMAL_COND_Z)

          .value("IZZ", MaterialProperties::IZZ)
          .value("A", MaterialProperties::A)
          
          ;

     py::class_<Material, std::shared_ptr<Material>> (handle, "Material")

          .def(py::init<>())

          .def_property_readonly("rho",
          [](const Material& self) -> double {
               return self.get_property(MaterialProperties::RHO);
          })

          .def_property_readonly("E",
          [](const Material& self) -> double {
               return self.get_property(MaterialProperties::YOUNGS_MOD);
          })

          .def_property_readonly("nu",
          [](const Material& self) -> double {
               return self.get_property(MaterialProperties::POISSON);
          })

          .def_property_readonly("A",
          [](const Material& self) -> double {
               return self.get_property(MaterialProperties::A);
          })

          .def_property_readonly("IZZ",
          [](const Material& self) -> double {
               return self.get_property(MaterialProperties::IZZ);
          })

          .def("add_property", 
               [](Material& self, MaterialProperties prop, double value) -> Material& {
                    return self.add_property(prop, value);
               },
               "Add or update a material property")

          .def("add_property", 
               [](Material& self, py::dict prop_dict) -> Material& {
                    for(auto& prop: prop_dict){
                         MaterialProperties key = py::cast<MaterialProperties>(prop.first);
                         double value = py::cast<double>(prop.second);
                         self.add_property(key, value);
                    }
                    return self;
               },
               "Add or update a material property")


          .def("get_property", &Material::get_property,
               "Get a material property value")
             
          ;


     py::class_<MaterialCatalogue, std::shared_ptr<MaterialCatalogue>> (handle, "MaterialCatalogue")

          .def_static("get_catalogue", &MaterialCatalogue::get_catalogue,
                         "Get the singleton MaterialCatalogue")

          .def("create_material", &MaterialCatalogue::create_material,
               py::return_value_policy::reference_internal,
               "Create a new material and return a reference to it")

          .def("get_material", &MaterialCatalogue::get_material,
               py::return_value_policy::reference_internal,
               "Get an existing material by name")
          ;

}