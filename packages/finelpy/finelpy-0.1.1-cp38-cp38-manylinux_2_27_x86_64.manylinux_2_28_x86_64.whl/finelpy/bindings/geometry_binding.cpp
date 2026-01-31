#include <finelc/binding/bindings.h>
#include <finelc/binding/geometry_binding.h>
#include <finelc/geometry/geometry.h>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <iostream>
#include <vector>
#include <memory>


using namespace finelc;
namespace py = pybind11;




void bind_geometry(py::module_& handle){

    py::enum_<AreaType>(handle, "AreaType")

        .value("POLYGON", AreaType::POLYGON)
        .value("RECTANGLE", AreaType::RECTANGLE);

    {
    py::class_<IGeometry, std::shared_ptr<IGeometry>>
    (handle, "IGeometry")

        .def_property_readonly("nodes",
            [](IGeometry &self) -> py::array {

                int number_of_nodes = (int)self.number_of_nodes();

                std::vector<int> nodes(number_of_nodes);

                int k = 0;

                for(auto node_iterator=self.begin(); node_iterator!=self.end(); ++node_iterator){
                    nodes[k++] = node_iterator.value();
                }

                py::array_t<int> arr(number_of_nodes);
                if(number_of_nodes > 0){
                    std::memcpy(arr.mutable_data(), nodes.data(), sizeof(int) * number_of_nodes);
                }
                return arr;

            })

        ;
    }

    {
    py::class_<Line, IGeometry, std::shared_ptr<Line>>
    (handle, "Line")

            .def(py::init<Point, Point>(),
                py::arg("point_1"),
                py::arg("point_2"))

            .def(py::init([](const double L) {
                Point p1(0,0,0);
                Point p2(L,0,0);
                return std::make_shared<Line>(p1,p2);
                }))

            .def(py::init([](const double x1, const double x2) {
                Point p1(x1,0,0);
                Point p2(x2,0,0);
                return std::make_shared<Line>(p1,p2);
                }))
    
            .def_property_readonly("len", &Line::length)
            .def_property_readonly("p1", [](const Line& self){return self.p1;})
            .def_property_readonly("p2", [](const Line& self){return self.p2;})
    ;
    }

        
    {
    py::class_<IArea, IGeometry, std::shared_ptr<IArea>>
    (handle, "IArea")

        .def(py::init<const std::vector<Point>&>())

        .def("name", 
            [](IArea& self){
                    return self.name();
            })

        .def_property_readonly("num_vertices",
            [](IArea &self) -> size_t {
                return self.get_num_vertices();
            })

        .def_property_readonly("vertices",
            [](IArea &self) -> std::vector<Point> {
                return *self.get_vertices();
            })

        .def_property_readonly("nodes",
            [](IArea &self) -> py::array {

                int number_of_nodes = (int)self.number_of_nodes();

                std::vector<int> nodes(number_of_nodes);

                int k = 0;

                for(auto node_iterator=self.begin(); node_iterator!=self.end(); ++node_iterator){
                    nodes[k++] = node_iterator.value();
                }

                py::array_t<int> arr(number_of_nodes);
                if(number_of_nodes > 0){
                    std::memcpy(arr.mutable_data(), nodes.data(), sizeof(int) * number_of_nodes);
                }
                return arr;

            })

        .def_property_readonly("lines",
            [](IArea &self) -> std::vector<Line> {
                return *self.get_lines();
            })

        .def("is_inside", &IArea::is_inside)
        ;
    }

    {py::class_<Rectangle,IArea,std::shared_ptr<Rectangle>>
        (handle,"Rectangle")

        .def(py::init<Point, 
            Point>())
        
        .def_property_readonly("dimensions", &Rectangle::get_dimension)

        .def_property_readonly("origin", &Rectangle::get_origin)

        .def_static("static_name", &Rectangle::static_name)

        .def_property_readonly("lower_side", &Rectangle::lower_side)
        .def_property_readonly("right_side", &Rectangle::right_side)
        .def_property_readonly("upper_side", &Rectangle::upper_side)
        .def_property_readonly("left_side", &Rectangle::left_side)

        ;
    }


}