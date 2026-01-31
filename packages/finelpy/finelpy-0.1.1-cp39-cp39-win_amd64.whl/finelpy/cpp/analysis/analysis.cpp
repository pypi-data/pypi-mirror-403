
#include <finelc/enumerations.h>

#include <finelc/matrix.h>
#include <finelc/analysis/analysis.h>
#include <finelc/analysis/interpolation.h>

#include <stdexcept>
#include <unordered_set>
#include <memory>

namespace finelc{

    std::unique_ptr<IInterpolationScheme> create_interpolation(InterpolationScheme name = InterpolationScheme::NONE){

        switch (name)
        {
        case InterpolationScheme::NONE:
            return std::make_unique<InterpolationSchemeAdapter<NoInterpolation>>();
            break;
        
        case InterpolationScheme::SIMP:
            return std::make_unique<InterpolationSchemeAdapter<SIMPInterpolationScheme>>();
            break;
        
        default:
            throw std::runtime_error("Invalid interpolation scheme given.");
            break;
        }

    }

    Analysis::Analysis( Mesh_ptr mesh_,
                        IDMat ID_,
                        std::vector<BoundaryCondition> bcs_,
                        std::vector<Force> forces_,
                        int num_free_dofs_):
        mesh(mesh_),ID(ID_),bcs(bcs_),
        forces(forces_),
        num_free_dofs(num_free_dofs_),
        interp(create_interpolation())
        {}

    Analysis::Analysis(Analysis&& other){

        mesh = std::move(other.mesh);
        ID = std::move(other.ID);
        bcs = std::move(other.bcs);
        forces = std::move(other.forces);
        interp = std::move(other.interp);
        num_free_dofs = other.num_free_dofs;

        Kg_data = std::move(other.Kg_data);
        Mg_data = std::move(other.Mg_data);
        fg_data = std::move(other.fg_data);
        fg_bc   = std::move(other.fg_bc);

        #ifdef USE_PETSC
            K = std::move(other.K);
            M = std::move(other.M);
            obj = std::move(other.obj);
        #endif
    }

    Analysis::~Analysis(){
    }

    void Analysis::destroy() noexcept{
        #ifdef USE_PETSC
            if(obj){
                KSPDestroy(&obj->ksp);
            }
            obj = nullptr;
            if(K) MatDestroy(&(*K));
            K = nullptr;
            if(M) MatDestroy(&(*M));
            M = nullptr;
        #endif
    }

    std::vector<std::pair<DOFType,int>> Analysis::get_dof_order(const IElement& el, int rows){

        const std::vector<int>& node_numbering = el.get_node_numbering();
        std::vector<DOFType> dofs = el.dofs();

        std::vector<std::pair<DOFType,int>> dof_order;
        dof_order.reserve(rows);
        for(auto& node: node_numbering){
            for(auto& dof: dofs){
                dof_order.emplace_back(std::make_pair(dof,node));
            }
        }
        return dof_order;
    }

    void Analysis::insert_triplets( std::vector<Triplet>& triplets, 
                                    const std::vector<std::pair<DOFType,int>>& dof_order,
                                    const Matrix& Mat,
                                    int rows,
                                    double interp_const){

        for(int i=0; i<rows; i++){
                auto& pair_i = dof_order[i];
                int dofi = ID(pair_i.first,pair_i.second);
                if(dofi<0) continue;
                for(int j=0; j<rows; j++){
                    auto& pair_j = dof_order[j];
                    int dofj = ID(pair_j.first,pair_j.second);
                    if(dofj>=0){
                        triplets.push_back(Triplet(dofi,dofj,Mat(i,j)*interp_const));
                    }else{
                        double bc_val = bcs[-dofj-1].value;
                        if(bc_val == 0) continue;
                        (*fg_bc)(dofi) -= bc_val*Mat(i,j)*interp_const;
                    }
                }
                
            }
    }

    std::vector<Triplet> Analysis::assemble(Assembler type){

        // TODO insert get ue logic here
        OptionalVector ue = std::nullopt;


        int non_zero_vals = 0;
        const VectorElements& elements = mesh->get_elements();
        for(auto& el: elements){
            non_zero_vals += el->displacement_size()*el->displacement_size();
        }

        using ElementMatrixFn = const Matrix& (IElement::*)(OptionalVector);
        ElementMatrixFn getMatrix = nullptr;

        switch (type) {
            case Assembler::Stiffness:
                getMatrix = &IElement::Ke;
                fg_bc = std::make_unique<Vector>(num_free_dofs);
                fg_bc->setZero();
                break;
            case Assembler::Mass:
                getMatrix = &IElement::Me;
                break;
        }

        std::vector<Triplet> triplets;
        triplets.reserve(non_zero_vals);

        Vector interps;
        bool has_interp = interp->name() != InterpolationScheme::NONE;
        if(has_interp){
            interps = interp->apply(*rho);
        }else{
            interps = Vector::Ones(1);
        }

        for(int el=0; el<elements.size(); el++){

            IElement& element = *elements[el];
            const Matrix& Mat_e = ((element).*getMatrix)(ue);
            int rows = Mat_e.rows();

            double rho_el = has_interp? interps(el):interps(0);

            std::vector<std::pair<DOFType,int>> dof_order = get_dof_order(element,rows);

            insert_triplets(triplets, dof_order,Mat_e, rows, rho_el);
        }

        return triplets;
    
    }

    Matrix Analysis::Eigen_Matrix_from_triplets(const std::vector<Triplet>& triplets){
        
        SparseMatrix Mat(num_free_dofs,num_free_dofs);
        Mat.setFromTriplets(triplets.begin(), triplets.end());
        return Matrix(Mat);
    }


    Vector Analysis::assemble_fg(){

        // TODO insert get ue logic here
        OptionalVector ue = std::nullopt;

        Vector fg = *fg_bc;

        for(auto& force : forces){

            if(force.get_type() == ForceType::Nodal){

                const std::vector<int>& nodes = force.get_nodes_or_elements();
                DOFType dof = force.get_dof_type();
                double val = force.get_value_at(Point());
                
                for(auto& node : nodes){
                    int loc = ID(dof,node);
                    if(loc>=0){
                        fg(loc) += val;
                    }
                }

            }else if (force.get_type() == ForceType::Function ||
                       force.get_type() == ForceType::Constant){

                const std::vector<int>& elements = force.get_nodes_or_elements();
                DOFType dof = force.get_dof_type();
                for(auto& el_number : elements){

                    IElement_ptr el = get_element(el_number);
                    const std::vector<int> node_numbering = el->get_node_numbering();

                    std::vector<PointWeight> gauss_pts = el->integration_pair(
                        force.get_integration_points());


                    int size = el->number_of_nodes()*el->dofs_per_node();
                    int dofs_per_node = el->dofs_per_node();
                    Vector fe(size);
                    fe.setZero();

                    std::vector<DOFType> eldofs = el->dofs();
                    auto it = std::find(eldofs.begin(),eldofs.end(), dof);
                    if(it == eldofs.end()) continue;
                    int dof_number = std::distance(eldofs.begin(), it);
                    
                    for(auto& gp : gauss_pts){
                        Vector gp_vec = gp.point.as_vector();
                        Vector N = el->N(gp_vec,std::nullopt).get_row(dof_number);
                        double double_val = force.get_value_at(el->local_to_global(gp.point));
                        double detJ = el->detJ(gp_vec);
                        fe += N*double_val*detJ*gp.weight;
                    }

                    int k=0;
                    for(auto& node : node_numbering){
                        for(auto& eldof: eldofs){
                            int loc = ID(eldof,node);
                            if(loc>=0){
                                fg(loc) += fe(k);
                            }
                            k++;
                        }
                    }
                }

            }
        }
        

        return fg;
    }

    void Analysis::set_ug(const Vector& u){
        Kg_data = nullptr;
        Mg_data = nullptr;
        fg_data = nullptr;
        fg_bc   = nullptr;
        ug      = std::make_unique<Vector>(u);
    }

    Matrix Analysis::Kg(){

        if(!Kg_data){
            Kg_data = std::make_unique<std::vector<Triplet>>(assemble(Assembler::Stiffness));
        }
        return Eigen_Matrix_from_triplets(*Kg_data);

    }

    Matrix Analysis::Mg(){

        if(!Mg_data){
            Mg_data = std::make_unique<std::vector<Triplet>>(assemble(Assembler::Mass));
        }
        return Eigen_Matrix_from_triplets(*Mg_data);
    }


    const Vector& Analysis::fg(){

        if(!fg_data){
            if(!fg_bc){
                Kg_data = std::make_unique<std::vector<Triplet>>(assemble(Assembler::Stiffness));
            }
            fg_data = std::make_unique<Vector>(assemble_fg());
        }
        return *fg_data;

    }

    std::vector<int> Analysis::get_free_dofs()const{

        std::vector<int> free_dofs;
        free_dofs.reserve(num_free_dofs);

        int k=0;
        for(auto& val: ID){
            if(val>=0){
                free_dofs.emplace_back(k);
            }
            k++;
        }
        return free_dofs;
    }

    void Analysis::set_interpolation(InterpolationScheme name){
        interp = create_interpolation(name);
        if(interp->name()==InterpolationScheme::NONE){
            rho = nullptr;
        }else{
            rho = std::make_unique<Vector>();
            *rho = Vector::Ones(mesh->number_of_elements());
        }
    }

    void Analysis::update_interpolation(
                InterpolationParameters identifier, 
                const double value){
        interp->update_property(identifier,value);
    }


    Vector Analysis::get_element_ue(const Vector& U, int el_number)const{

        IElement_ptr el = get_element(el_number);
        std::vector<DOFType> el_dofs = el->dofs();
        const std::vector<int> node_numbering = el->get_node_numbering();

        int ue_size = el->displacement_size();
        Vector ue(ue_size);

        
        int k=0;
        for(auto& node: node_numbering){
            for(auto& dof: el_dofs){
                int loc = ID(dof,node);
                if(loc >= 0){
                    ue(k) = U(loc);
                }else{
                    ue(k) = bcs[-loc-1].value;
                }
                k++;
            }
        }
        return ue;
    }

    Vector Analysis::reconstruct_ug(const Vector& U)const{

        Vector ug(total_size());
        int k=0;
        for(int node=0; node<ID.cols; node++){
            for (int dof=0; dof<ID.rows; dof++){
                int loc = ID(dof,node);
                if(loc>=0){
                    ug(k) = U(loc);
                }else{
                    ug(k) = bcs[-loc-1].value;
                }
                k++;
            }
        }
        return ug;
    }



    int Analysis::bc_size()const{
        int num_bcs =0;
        for(auto& bc : bcs){
            num_bcs += bc.nodes.size();
        }
        return num_bcs;
    }

    std::vector<int> Analysis::get_bc_dofs()const{

        std::vector<int> bc_dofs;
        bc_dofs.reserve(bc_size());

        int k=0;
        for(auto& val: ID){
            if(val<0){
                bc_dofs.emplace_back(k);
            }
            k++;
        }
        return bc_dofs;
    }

    

    void AnalysisBuilder::get_degrees_of_freedom(){

        std::unordered_set<DOFType> seen;

        for(auto& el : mesh->get_elements()){
            std::vector<DOFType> dofs = el->dofs();
            for(auto& dof : dofs){
                if (seen.insert(dof).second) {
                    unique_dofs.push_back(dof);
                }
            }
        }
        
    }

    void AnalysisBuilder::create_id_matrix(){

        size_t cols = mesh->number_of_nodes();
        ID = IDMat(unique_dofs,cols);
    }


    void AnalysisBuilder::populate_id_matrix(){

        for(int i=0; i<bc_vector.size(); i++){
            DOFType type = bc_vector[i].type;
            for(auto& node: bc_vector[i].nodes){
                ID(type,node) = -i-1;
            }
        }
        
        num_free_dofs = 0;
        for(auto& id_val:ID){
            if(id_val==0){
                id_val = num_free_dofs++;
            }
        }


    }


    void AnalysisBuilder::add_boundary_condition(DOFType dof, int node_number, double value){
        bc_vector.push_back(BoundaryCondition(dof,node_number,value));
    }

    void AnalysisBuilder::add_boundary_condition(DOFType dof, std::vector<int> nodes, double value){
        for(auto& node_number : nodes){
            bc_vector.push_back(BoundaryCondition(dof,node_number,value));
        }
    }

    void AnalysisBuilder::add_boundary_condition(DOFType dof, IGeometry_ptr geometry, double value){
        std::vector<int> nodes;
        for(auto it = geometry->begin(); it!=geometry->end(); ++it){
            nodes.emplace_back(it.value());
        }
        bc_vector.push_back(BoundaryCondition(dof,nodes,value));
    }

    void AnalysisBuilder::add_force(DOFType dof, int node_number, double value){
        forces.push_back(Force(dof,node_number,value));
    }

    void AnalysisBuilder::add_force(DOFType dof, std::vector<int> nodes, double value){
        for(auto& node_number : nodes){
            forces.push_back(Force(dof,node_number,value));
        }
    }

    void AnalysisBuilder::add_force(DOFType dof, IGeometry_ptr geometry, double value, int integration_points){

        Force force(dof,geometry,value,integration_points);
        force.get_elements_from_geometry(mesh);
        forces.push_back(force);

    }

    void AnalysisBuilder::add_force(DOFType dof, IGeometry_ptr geometry, Evalfn func, int integration_points){

        Force force(dof,geometry,func,integration_points);
        force.get_elements_from_geometry(mesh);
        forces.push_back(force);
        
    }


    Analysis AnalysisBuilder::build(){

        get_degrees_of_freedom();
        create_id_matrix();
        populate_id_matrix();

        return Analysis(
            mesh,
            ID,
            bc_vector,
            forces,
            num_free_dofs);
    }

    #ifdef USE_PETSC

        std::unique_ptr<Mat> create_PETSc_Matrix_from_triplets(const std::vector<Triplet>& triplets, int n){

            std::unique_ptr<Mat> A = std::make_unique<Mat>();

            std::vector<int> nnz_per_row(n,0);
            for(const auto& triplet : triplets){
                if(nnz_per_row[triplet.row()] < n)
                    nnz_per_row[triplet.row()]++;
            }

            MatCreateSeqAIJ(PETSC_COMM_SELF, n, n, 0, nnz_per_row.data(), A.get());


            // Insert sparsity pattern only ONCE
            for (const auto& triplet : triplets) {
                int i = triplet.row();
                int j = triplet.col();
                double value = triplet.value();
                MatSetValues(*A, 1, &i, 1, &j, &value, ADD_VALUES);
            }

            MatAssemblyBegin(*A, MAT_FINAL_ASSEMBLY);
            MatAssemblyEnd(*A, MAT_FINAL_ASSEMBLY);

            return A;
        }

        const Mat& Analysis::get_PETSc_K(){

            // Create PETSc matrix K if it does not exist
            if(!Kg_data){
                Kg_data = std::make_unique<std::vector<Triplet>>(assemble(Assembler::Stiffness));
                if(K) MatDestroy(&(*K));
                K = create_PETSc_Matrix_from_triplets(*Kg_data, num_free_dofs);
            }
            else if(!K){
                K = create_PETSc_Matrix_from_triplets(*Kg_data, num_free_dofs);
            }
            return *K;
        }
        const Mat& Analysis::get_PETSc_M(){

            if(!Mg_data){
                Mg_data = std::make_unique<std::vector<Triplet>>(assemble(Assembler::Mass));
                if(M) MatDestroy(&(*M));
                M = create_PETSc_Matrix_from_triplets(*Mg_data, num_free_dofs);
            }
            else if(!M){
                M = create_PETSc_Matrix_from_triplets(*Mg_data, num_free_dofs);
            }
            return *M;
        }
        PetscObjects& Analysis::get_PETSc_objects(){

            if(!obj){

                const Mat* Kmat = &get_PETSc_K();
                obj = std::make_unique<PetscObjects>();
                obj->Kmat = Kmat;
                obj->n = num_free_dofs;
                KSPCreate(PETSC_COMM_SELF, &obj->ksp);
                KSPSetOperators(obj->ksp, *obj->Kmat, *obj->Kmat);  // A as matrix and preconditioner
                KSPSetType(obj->ksp, KSPPREONLY);
                KSPGetPC(obj->ksp, &obj->pc);
                PCSetType(obj->pc, PCLU);
                KSPSetUp(obj->ksp);

            }
            return *obj;
        }
    #endif

} // namespace finelc
