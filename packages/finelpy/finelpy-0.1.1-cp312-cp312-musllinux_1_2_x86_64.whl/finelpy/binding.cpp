
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>


#include <finelc/binding/bindings.h>


#ifdef USE_PETSC
    #include <petscsys.h>
#endif



PYBIND11_MODULE(core, mod) {
    mod.doc() = "finite element module";


    #ifdef USE_PETSC
        PetscBool initialized;
        PetscInitialized(&initialized);

        if (!initialized) {
            PetscOptionsInsertString(nullptr,
                "-no_signal_handler -no_signal_handler_internal "
                "-malloc_debug 0 -malloc_dump 0");

            PetscInitialize(nullptr, nullptr, nullptr, nullptr);
        }
        mod.def("petsc_enabled", []() { return true; });
    #else
        mod.def("petsc_enabled", []() { return false; });
    #endif

    
    #ifdef USE_VTK
        mod.def("vtk_enabled", []() { return true; });
    #else
        mod.def("vtk_enabled", []() { return false; });
    #endif

    

    // Create submodules
    py::module_ geo_sub = mod.def_submodule("geometry", "Geometry submodule");
    py::module_ mat_sub = mod.def_submodule("material", "Material submodule");
    py::module_ mesh_sub = mod.def_submodule("mesh", "Mesh submodule");
    py::module_ element_sub = mod.def_submodule("element", "Element submodule");
    py::module_ analysis_sub = mod.def_submodule("analysis", "Analysis submodule");
    py::module_ solver_sub = mod.def_submodule("solver", "Solver submodule");
    
    bind_geometry(geo_sub);
    bind_material(mat_sub);
    bind_element(element_sub);
    bind_mesh(mesh_sub);
    bind_analysis(analysis_sub);
    bind_solver(solver_sub);

}