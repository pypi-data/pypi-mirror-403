#include <finelc/enumerations.h>
#include <finelc/compatibility.h>

#include <finelc/elements/integration.h>
#include <finelc/elements/element.h>
#include <finelc/elements/element_matrix.h>

#include <finelc/element_geometry/element_geometry.h>
#include <finelc/element_geometry/quad.h>
#include <finelc/element_geometry/tri.h>

#include <finelc/element_physics/element_physics.h>
#include <finelc/element_physics/plane.h>

#include <finelc/material/constitutive.h>
#include <finelc/material/elastic.h>

#include <cmath>

namespace finelc{

    const VectorNodes& IElement::get_mesh_nodes()const{
        if(mesh_nodes->size()==0){
            throw std::runtime_error("Uninitialized element, nodes not defined.");
        }
        return *mesh_nodes;
    }

    void IElement::check_node_numbering(const std::vector<int>& node_numbering_)const{
        if(number_of_nodes() != node_numbering_.size()){
            throw std::runtime_error("node_numbering must be compatible with shape number of nodes.");
        }
    }

    void IElement::set_node_numbering(const std::vector<int>& node_numbering_, 
                            const VectorNodes& mesh_nodes_){
        mesh_nodes = &mesh_nodes_;
        set_node_numbering(node_numbering_);
    }

    void IElement::set_node_numbering(const std::vector<int>& node_numbering_){
        check_node_numbering(node_numbering_);
        node_numbering = node_numbering_;
    }

    const std::vector<int>& IElement::get_node_numbering()const{
        if(node_numbering.empty()){
            throw std::runtime_error("Uninitialized element, nodes not defined.");
        }
        return node_numbering;
    }

    VectorNodes IElement::get_nodes()const{

        VectorNodes nodes;
        nodes.reserve(number_of_nodes());

        for(auto& node_ind: get_node_numbering()){
            nodes.emplace_back(get_mesh_nodes().at(node_ind));
        }

        return nodes;
    }

    bool IElement::is_linear()const{
        return linear_physics() && linear_material();
    }

    int IElement::displacement_size()const{
        return number_of_nodes()*dofs_per_node();
    }

    double IElement::interpolate_nodal_values(const Vector& loc, 
                                    const Vector& ue)const{
        return N_shape(loc).dot(ue);
    }

    Vector IElement::interpolate_result(const Vector& loc, 
                                    const Vector& ue)const{
        // std::cerr << N(loc,ue) << " * " << ue << " = " << N(loc,ue) * ue << std::endl;
        return N(loc,ue) * ue;
    }

    
    Point IElement::geometric_center()const{
        Point coordinate;
        const std::vector<int>& node_numbering_ = get_node_numbering();
        const VectorNodes& mesh_nodes_ = get_mesh_nodes();
        for(int nd=0; nd<number_of_nodes(); nd++){
            coordinate += (*mesh_nodes_[node_numbering_[nd]]);
        }
        coordinate /= number_of_nodes();
        return coordinate;
    }

    
    Vector IElement::local_to_global(const Vector& loc)const{
                
        const VectorNodes& element_nodes = get_nodes();
        Vector Nmat = N_shape(loc);
        Vector gloc = Vector::Zero(3);

        for(int i=0; i<Nmat.size(); i++){
            gloc(0) += element_nodes[i]->x * Nmat(i);
            gloc(1) += element_nodes[i]->y * Nmat(i);
            gloc(2) += element_nodes[i]->z * Nmat(i);
        }
        return gloc;
    }

    Point IElement::local_to_global(const Point& loc)const{
                
        const VectorNodes& element_nodes = get_nodes();
        Vector Nmat = N_shape(loc.as_vector());

        Point gloc(0,0,0);

        for(int i=0; i<Nmat.size(); i++){
            gloc.x += element_nodes[i]->x * Nmat(i);
            gloc.y += element_nodes[i]->y * Nmat(i);
            gloc.z += element_nodes[i]->z * Nmat(i);
        }
        return gloc;
    }

    void IElement::set_number_integration_points(int number_points){
        if(number_points<=0) throw std::runtime_error("Number of integration points must be a natural non-zero number.");
        num_int_pts=number_points;
    }

    int IElement::get_number_integration_points()const{
        return num_int_pts;
    }

    std::vector<PointWeight> IElement::integration_pair(int number_points)const{

        if(number_points==0){
            number_points = get_number_integration_points();
        }

        return get_gauss_points(
            get_integration_domain(),
            number_points,
            number_of_dimensions());
        
    }

    std::vector<Point> IElement::integration_points(int number_points)const{

        std::vector<PointWeight> pairs = integration_pair(number_points);
        std::vector<Point> points;
        points.reserve(pairs.size());

        for(auto& pair : pairs){
            points.emplace_back(pair.point);
        }

        return points;
    }

    std::vector<double> IElement::integration_weights(int number_points)const{

        std::vector<PointWeight> pairs = integration_pair(number_points);
        std::vector<double> weights;
        weights.reserve(pairs.size());

        for(auto& pair : pairs){
            weights.emplace_back(pair.weight);
        }
        
        return weights;
    }

    bool IElement::has_dof(DOFType type)const{
        for(auto& dof:dofs()){
            if(dof == type){
                return true;
            }
        }
        return false;
    }

    const Matrix& Element::Ke(OptionalVector ue){
        if(is_linear() && ue.has_value()){
            ue = std::nullopt;
        }

        return matrices->get_Ke(ue,
                                displacement_size(),
                                [this]() {
                                    return this->integration_pair();
                                },
                                
                                [this](const Vector& a, const OptionalVector& b) {
                                    return this->B(a, b);
                                },

                                [this](const OptionalVector& a, const OptionalVector& b) {
                                    return this->D(a, b);
                                },

                                [this](const OptionalVector& a) {
                                    return this->detJ(a);
                                });
                
    }

    const Matrix& Element::Me(OptionalVector ue){
        if(is_linear() && ue.has_value()){
            ue = std::nullopt;
        }

        return matrices->get_Me(ue,
                                displacement_size(),
                                [this]() {
                                    return this->get_property(MaterialProperties::RHO);
                                },
                                [this]() {
                                    return this->integration_pair();
                                },

                                [this](const Vector& a, const OptionalVector& b) {
                                    return this->N(a, b);
                                },
                                [this](const OptionalVector& a) {
                                    return this->detJ(a);
                                });
                
    }

    void ElementBuilder::check_compatibility(ShapeType shape_type,
                                            ModelType physics_type,
                                            ConstitutiveType const_type){
        element_compatibility(shape_type,physics_type,const_type);
    }

    ElementBuilder::ElementBuilder( std::variant<ShapeType, IElementShape_ptr> shape_input,
                            std::variant<ModelType, IElementPhysics_ptr> physics_input,
                            std::variant<ConstitutiveType, IConstitutiveModel_ptr> const_input,
                            Material_ptr mat){

        ShapeType shape_type;
        if(std::holds_alternative<ShapeType>(shape_input)){
            shape_type = std::get<ShapeType>(shape_input);
            shape = build_shape(shape_type);
        }else{
            shape = std::get<IElementShape_ptr>(shape_input);
            shape_type = shape->shape();
        }

        ModelType physics_type;
        if(std::holds_alternative<ModelType>(physics_input)){
            physics_type = std::get<ModelType>(physics_input);
            physics = build_physics(physics_type);
        }else{
            physics = std::get<IElementPhysics_ptr>(physics_input);
            physics_type = physics->get_model();
        }

        ConstitutiveType const_type;
        if(std::holds_alternative<ConstitutiveType>(const_input)){
            const_type = std::get<ConstitutiveType>(const_input);
            if(!mat) throw std::runtime_error("Must provide a built contitutive model or a material.");
            material = build_constitutive(const_type,mat);
        }else{
            material = std::get<IConstitutiveModel_ptr>(const_input);
            const_type = material->contitutive_model();
        }

        check_compatibility(shape_type,physics_type,const_type);
    }


    void ElementBuilder::create_element(){
        built_element = std::make_shared<Element>(shape,physics,material);
    }

    IElement_ptr ElementBuilder::build(){
        create_element();
        return built_element;
    }

    IElementShape_ptr ElementBuilder::build_shape(ShapeType shape_type){

        switch (shape_type){

            case ShapeType::QUAD4:
                return std::make_shared<ElementShapeAdapter<Quad4>>();
                break;

            case ShapeType::QUAD9:
                return std::make_shared<ElementShapeAdapter<Quad9>>();
                break;

            case ShapeType::TRI3:
                return std::make_shared<ElementShapeAdapter<Tri3>>();
                break;
        
        }

        throw std::runtime_error("Invalid element shape");
    }

    IElementPhysics_ptr ElementBuilder::build_physics(ModelType physics_type){

        switch (physics_type){

            case ModelType::PLANE_STRUCTURAL:
                return std::make_shared<ElementPhysicsAdapter<PlaneStructural>>();
                break;
        
        }

        throw std::runtime_error("Invalid element physics");
    }

    IConstitutiveModel_ptr ElementBuilder::build_constitutive(ConstitutiveType const_type, Material_ptr mat){

        switch (const_type){

            case ConstitutiveType::PLANE_STRAIN:
                return std::make_shared<ConstitutiveModelAdapter<PlaneStrain>>(mat);
                break;

            case ConstitutiveType::PLANE_STRESS:
                return std::make_shared<ConstitutiveModelAdapter<PlaneStress>>(mat);
                break;

        }

        throw std::runtime_error("Invalid constitutive model");
    }

} // namespace finel