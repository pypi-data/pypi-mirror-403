
#include <finelc/enumerations.h>

#include <finelc/mesh/mesh.h>
#include <finelc/mesh/meshers.h>

#include <finelc/mesh/element_finder.h>
#include <finelc/mesh/node_iterators.h>

#include <finelc/elements/element.h>



#include <exception>
#include <iostream>

namespace finelc{


    MeshBuilderRectangle::MeshBuilderRectangle(
        std::shared_ptr<IArea> domain_, 
        IElement_ptr el_): 
        MeshBuilder(el_){

        if(!domain_){
            throw std::runtime_error("Null domain passed to MeshBuilderRectangle");
        }

        if(domain_->name() != AreaType::RECTANGLE){
            throw std::runtime_error("Incorrect geometry type. This mesher only accepts rectangle meshes.");
        }

        domain = domain_;
        Rectangle_ptr rectangle = std::dynamic_pointer_cast<Rectangle>(domain);

        if(!rectangle){
            throw std::runtime_error("Domain is not a Rectangle instance");
        }

        if(element->get_shape() != ShapeType::QUAD4 && 
        element->get_shape() != ShapeType::TRI3 && 
        element->get_shape() != ShapeType::QUAD9){
            throw std::runtime_error("Rectangle Mesh builder only accepts QUAD4 and TRI3 elements.");
        }

        const Point dimensions = rectangle->get_dimension();
        Lx = dimensions.x;
        Ly = dimensions.y;

    }

    void MeshBuilderRectangle::create_square(){

        int num_nodes;
        int ndx, ndy;
        double dx, dy;
        if(element->get_shape() == ShapeType::QUAD9){
            num_nodes = (2*nx+1)*(2*ny+1);
            dx = lx/2.;
            dy = ly/2.;
            ndx = 2*nx+1;
            ndy = 2*ny+1;
        }else{
            num_nodes = (nx+1)*(ny+1);
            dx = lx;
            dy = ly;
            ndx = nx+1;
            ndy = ny+1;
        }
        
        VectorNodes nodes;
        nodes.reserve(num_nodes);

        Rectangle_ptr rectangle = std::dynamic_pointer_cast<Rectangle>(domain);

        // Calculating nodes
        Point origin = rectangle->get_origin();
        for(int y=0; y<ndy; y++){
            for(int x=0; x<ndx; x++){
                Node_ptr node = std::make_shared<Node>(   
                            dx * x + origin.x,
                            dy * y + origin.y,
                            origin.z);
                nodes.emplace_back(node);
            }
        }
        mesh->set_nodes(std::move(nodes));

        // Calculating nodes from geometry objects
        IteratorParameters iterator(num_nodes,0,1);
        domain->set_iterator(iterator);

        std::shared_ptr<std::vector<Line>> lines = rectangle->get_lines();

        iterator = IteratorParameters(ndx,0,1);
        (*lines)[0].set_iterator(iterator);

        iterator = IteratorParameters(ndy,ndx-1,ndx);
        (*lines)[1].set_iterator(iterator);

        iterator = IteratorParameters(ndx,ndx*(ndy-1),1);
        (*lines)[2].set_iterator(iterator);

        iterator = IteratorParameters(ndy,0,ndx);
        (*lines)[3].set_iterator(iterator);


        // Calculating elements
        if(element->get_shape() == ShapeType::QUAD4){
            populate_quad4();
        }else if (element->get_shape() == ShapeType::TRI3){
            populate_tri3();
        }else if (element->get_shape() == ShapeType::QUAD9){
            populate_quad9();
        }
        
        ElementFinder_uptr finder = std::make_unique<GridRectangleElementFinder>(lx,ly,nx,ny);
        mesh->set_finder(std::move(finder));
    }

    void MeshBuilderRectangle::populate_quad4(){

        VectorElements elements;
        int num_elements = nx*ny;
        elements.reserve(num_elements);
        std::vector<int> elem_nodes(4);
        for(int y=0; y<ny; y++){
            int offset = y*(nx+1);
            for(int x=0; x<nx; x++){
                elem_nodes[0] = x + offset;
                elem_nodes[1] = elem_nodes[0]+1;
                elem_nodes[3] = elem_nodes[0] + (nx+1);
                elem_nodes[2] = elem_nodes[3]+1;
                element->set_node_numbering(elem_nodes, mesh->get_nodes());
                elements.emplace_back(element->copy(true));
            }
        }
        mesh->set_elements(elements);
    }

    void MeshBuilderRectangle::populate_quad9(){

        VectorElements elements;
        int num_elements = nx*ny;
        elements.reserve(num_elements);
        std::vector<int> elem_nodes(9);
        for(int y=0; y<2*ny; y+=2){
            int offset = y*(2*nx+1);
            for(int x=0; x<2*nx; x+=2){
                elem_nodes[0] = x + offset;
                elem_nodes[4] = elem_nodes[0]+1;
                elem_nodes[1] = elem_nodes[0]+2;

                elem_nodes[7] = elem_nodes[0] + (2*nx+1);
                elem_nodes[8] = elem_nodes[7]+1;
                elem_nodes[5] = elem_nodes[7]+2;

                elem_nodes[3] = elem_nodes[0] + 2*(2*nx+1);
                elem_nodes[6] = elem_nodes[3]+1;
                elem_nodes[2] = elem_nodes[3]+2;
                element->set_node_numbering(elem_nodes, mesh->get_nodes());
                elements.emplace_back(element->copy(true));
            }
        }
        mesh->set_elements(elements);
    }

    void MeshBuilderRectangle::populate_tri3(){

        VectorElements elements;
        int num_elements = nx*ny * 2;
        elements.reserve(num_elements);

        std::vector<int> quad_nodes(4);
        std::vector<int> elem_nodes(3);
        element->set_node_numbering(elem_nodes, mesh->get_nodes());
        IElement_ptr el2 = element->copy(false);
        for(int y=0; y<ny; y++){
            int offset = y*(nx+1);
            for(int x=0; x<nx; x++){
                quad_nodes[0] = x + offset;
                quad_nodes[1] = quad_nodes[0]+1;
                quad_nodes[3] = quad_nodes[0] + (nx+1);
                quad_nodes[2] = quad_nodes[3]+1;

                elem_nodes = {quad_nodes[0], quad_nodes[1], quad_nodes[3]};
                element->set_node_numbering(elem_nodes, mesh->get_nodes());
                elements.emplace_back(element->copy(true));

                elem_nodes = {quad_nodes[2], quad_nodes[3], quad_nodes[1]};
                el2->set_node_numbering(elem_nodes, mesh->get_nodes());
                elements.emplace_back(el2->copy(true));
            }
        }
        mesh->set_elements(elements);
    }

    void MeshBuilderRectangle::set_size_from_grid(){
        lx = Lx/nx;
        ly = Ly/ny;
    }

    void MeshBuilderRectangle::set_element_size(double lx_, double ly_){
            lx = lx_<Lx ? lx_ : Lx;
            ly = ly_<Ly ? ly_ : Ly;

            nx = Lx/lx;
            ny = Ly/ly;
            set_size_from_grid();
    }

    void MeshBuilderRectangle::set_grid(int nx_, int ny_){
        nx = nx_;
        ny = ny_;

        set_size_from_grid();
    }

    Mesh_ptr MeshBuilderRectangle::build(){
        create_square();
        return mesh;
    }

    
} // namespace finelc
