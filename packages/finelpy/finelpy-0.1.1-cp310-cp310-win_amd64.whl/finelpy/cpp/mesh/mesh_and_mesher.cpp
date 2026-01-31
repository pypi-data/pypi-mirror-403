
#include <finelc/mesh/mesh.h>
#include <finelc/mesh/meshers.h>


namespace finelc{


    void Mesh::add_element(IElement_ptr new_el){
        elements.emplace_back(new_el);
    }

    void Mesh::add_elements(const VectorElements& new_els){
        elements.reserve(elements.size() + new_els.size());
        for(const auto& new_el: new_els){
            add_element(new_el);
        }
    }

    void Mesh::set_elements(const VectorElements& els){
        elements = els;
    }

    void Mesh::add_node(Node_ptr new_node){
        nodes.emplace_back(new_node);
    }

    void Mesh::add_nodes(const VectorNodes& new_nodes){
        nodes.reserve(nodes.size() + new_nodes.size());
        for(const auto& new_node: new_nodes){
            add_node(new_node);
        }
    }

    void Mesh::set_nodes(const VectorNodes& nds){
        nodes = nds;
    }

    void Mesh::set_finder(ElementFinder_uptr find){finder = std::move(find);}

    IElement_ptr Mesh::get_element(int el)const{
        return elements.at(el);
    }    

    Node_ptr Mesh::get_node(int nd)const{
        return nodes.at(nd);
    }    

    const VectorNodes& Mesh::get_nodes() const{
        return nodes;
    }

    const VectorElements& Mesh::get_elements() const{
        return elements;
    }

    size_t Mesh::number_of_nodes() const{
        return nodes.size();
    }

    size_t Mesh::number_of_elements() const{
        return elements.size();
    }

    int Mesh::find_element(const Vector& loc) const{
        return finder->find_element(loc);
    }


} // namespace finelc
