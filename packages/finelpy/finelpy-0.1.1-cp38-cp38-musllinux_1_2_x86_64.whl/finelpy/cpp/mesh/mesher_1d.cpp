
#include <finelc/enumerations.h>

#include <finelc/mesh/mesh.h>
#include <finelc/mesh/meshers.h>

#include <finelc/mesh/element_finder.h>
#include <finelc/mesh/node_iterators.h>

#include <finelc/elements/element.h>



#include <exception>
#include <iostream>

namespace finelc{


    MeshBuilderLine::MeshBuilderLine(
        std::shared_ptr<Line> domain_, 
        IElement_ptr el_): 
        MeshBuilder(el_){

        if(!domain_){
            throw std::runtime_error("Null domain passed to MeshBuilderLine");
        }

        domain = domain_;
        Line_ptr line = std::dynamic_pointer_cast<Line>(domain);


        if(element->get_shape() != ShapeType::LINE){
            throw std::runtime_error("Rectangle Mesh builder only accepts LINE elements.");
        }

        L = line->length();

    }

    void MeshBuilderLine::create_line(){

        int int_nodes = element->number_of_nodes()-2;

        int num_nodes = num_elements+1 + int_nodes*num_elements;
        double dx = L/(num_nodes-1);

        VectorNodes nodes;
        nodes.reserve(num_nodes);

        Line_ptr line = std::dynamic_pointer_cast<Line>(domain);

        // Calculating nodes
        const Point& origin = line->p1;
        for(int nd=0; nd<num_nodes; nd++){
            Node_ptr node = std::make_shared<Node>(   
                        dx * nd + origin.x,
                        origin.y,
                        origin.z);
            nodes.emplace_back(node);
        }
        mesh->set_nodes(std::move(nodes));

        // Calculating nodes from geometry objects
        IteratorParameters iterator(num_nodes,0,1);
        domain->set_iterator(iterator);

        // Calculating elements
        VectorElements elements;
        elements.reserve(num_elements);

        std::vector<int> elem_nodes(2+int_nodes);
        int nd = 0;
        for(int i_el=0; i_el<num_elements; i_el++){
            elem_nodes[0] = nd++;
            for(int i_int=0; i_int<int_nodes; i_int++){
                elem_nodes[2+i_int] = nd++;
            }
            elem_nodes[1] = nd++;
            element->set_node_numbering(elem_nodes,mesh->get_nodes());
            elements.emplace_back(element->copy(true));
            nd--;
        }

        mesh->set_elements(elements);
        
        ElementFinder_uptr finder = std::make_unique<LineElementFinder>(l);
        mesh->set_finder(std::move(finder));


    }

    

    void MeshBuilderLine::create_from_element_num(int n){
        num_elements = n;
        l = L/n;
    }

    void MeshBuilderLine::create_from_element_size(double dL){
            l = dL<L ? dL : L;
            num_elements = L/dL;
    }

    Mesh_ptr MeshBuilderLine::build(){
        create_line();
        return mesh;
    }


    void MeshBuilderFrame::create_frame(){
        mesh->set_nodes(nodes);

        VectorElements elements;
        elements.reserve(inci.size());

        for(std::vector<int> elem_nodes:inci){
            element->set_node_numbering(elem_nodes,mesh->get_nodes());
            elements.emplace_back(element->copy(false));
        }
        mesh->set_elements(elements);
    }


    MeshBuilderFrame::MeshBuilderFrame(
        IElement_ptr el_,
        VectorNodes nodes_,
        std::vector<std::vector<int>> inci_): 
        MeshBuilder(el_), inci(inci_), nodes(nodes_){ }


    Mesh_ptr MeshBuilderFrame::build(){
        create_frame();
        return mesh;
    }

    
} // namespace finelc
