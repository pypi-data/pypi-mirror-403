
#include <finelc/matrix.h>
#include <finelc/enumerations.h>

#include <finelc/mesh/mesh.h>
#include <finelc/elements/element.h>
#include <finelc/analysis/analysis.h>

#include <finelc/result/result.h>

#include <memory>
#include <cmath>


namespace finelc{


    

    double get_sigma_xx(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_stress(loc,ue);
        return stress(0);
    }

    double get_sigma_yy(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_stress(loc,ue);
        if(stress.size()==1){
            return stress(0);
        }else{
            return stress(1);
        }
    }

    double get_sigma_zz(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_stress(loc,ue);
        if(stress.size()==1){
            return stress(0);
        }else if(stress.size()==3){
            return 0;
        }else{
            return stress(2);
        }
    }

    double get_sigma_xy(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_stress(loc,ue);
        if(stress.size()==1){
            return 0;
        }else if(stress.size()==3){
            return stress(2);
        }else{
            return stress(3);
        }
    }

    double get_sigma_xz(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_stress(loc,ue);
        if(stress.size()==6){
            return stress(4);
        }else{
            return 0;
        }
    }

    double get_sigma_yz(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_stress(loc,ue);
        if(stress.size()==6){
            return stress(5);
        }else{
            return 0;
        }
    }

    double get_epsilon_xx(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_strain(loc,ue);
        return stress(0);
    }

    double get_epsilon_yy(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_strain(loc,ue);
        if(stress.size()==1){
            return stress(0);
        }else{
            return stress(1);
        }
    }

    double get_epsilon_zz(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_strain(loc,ue);
        if(stress.size()==1){
            return stress(0);
        }else if(stress.size()==3){
            return 0;
        }else{
            return stress(2);
        }
    }

    double get_epsilon_xy(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_strain(loc,ue);
        if(stress.size()==1){
            return 0;
        }else if(stress.size()==3){
            return stress(2);
        }else{
            return stress(3);
        }
    }

    double get_epsilon_xz(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_strain(loc,ue);
        if(stress.size()==6){
            return stress(4);
        }else{
            return 0;
        }
    }

    double get_epsilon_yz(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector stress = el->get_strain(loc,ue);
        if(stress.size()==6){
            return stress(5);
        }else{
            return 0;
        }
    }

    double get_dof_data(const Vector& loc, const Vector& ue, IElement_ptr el, DOFType name){

        std::vector<DOFType> dofs = el->dofs();
        auto it = std::find(dofs.begin(), dofs.end(), name);
        if (it == dofs.end()) {
            throw std::runtime_error("Requested DOF not found in element");
        }
        int dof_number = std::distance(dofs.begin(), it);
        Vector ur = el->interpolate_result(loc,ue);
        
        return ur(dof_number);
    }

    double get_ux(const Vector& loc, const Vector& ue, IElement_ptr el){
        return get_dof_data(loc,ue,el,DOFType::UX);
    }

    double get_uy(const Vector& loc, const Vector& ue, IElement_ptr el){
        return get_dof_data(loc,ue,el,DOFType::UY);
    }

    double get_uz(const Vector& loc, const Vector& ue, IElement_ptr el){
        return get_dof_data(loc,ue,el,DOFType::UZ);
    }
    
    double get_thetax(const Vector& loc, const Vector& ue, IElement_ptr el){
        return get_dof_data(loc,ue,el,DOFType::THETAX);
    }

    double get_thetay(const Vector& loc, const Vector& ue, IElement_ptr el){
        return get_dof_data(loc,ue,el,DOFType::THETAY);
    }

    double get_thetaz(const Vector& loc, const Vector& ue, IElement_ptr el){
        return get_dof_data(loc,ue,el,DOFType::THETAZ);
    }

    double get_abs_u(const Vector& loc, const Vector& ue, IElement_ptr el){

        double sum = 0;
        if(el->has_dof(DOFType::UX)){
            double ux = get_dof_data(loc,ue,el,DOFType::UX);
            sum += ux*ux;
        }

        if(el->has_dof(DOFType::UY)){
            double uy = get_dof_data(loc,ue,el,DOFType::UY);
            sum += uy*uy;
        }

        if(el->has_dof(DOFType::UZ)){
            double uz = get_dof_data(loc,ue,el,DOFType::UZ);
            sum += uz*uz;
        }
        return std::sqrt(sum);

    }

    double get_nx(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector nx =  el->get_NX(loc,ue);
        return nx(0);
    }

    double get_mz(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector mz =  el->get_MZ(loc,ue);
        return mz(0);
    }

    double get_vy(const Vector& loc, const Vector& ue, IElement_ptr el){
        Vector vy =  el->get_VY(loc,ue);
        return vy(0);
    }


    SupportFn get_support_func(ResultData id){

        switch (id) {

            case ResultData::UX:
            case ResultData::UY:
            case ResultData::UZ:
            case ResultData::THETAX:
            case ResultData::THETAY:
            case ResultData::THETAZ:
            case ResultData::ABS_U:
                return &IElement::supports_displacement;
                break;


            case ResultData::EPSILON_XX:
            case ResultData::EPSILON_YY:
            case ResultData::EPSILON_ZZ:
            case ResultData::EPSILON_XY:
            case ResultData::EPSILON_XZ:
            case ResultData::EPSILON_YZ:
                return &IElement::supports_strain;
                break;

            case ResultData::SIGMA_XX:
            case ResultData::SIGMA_YY:
            case ResultData::SIGMA_ZZ:
            case ResultData::SIGMA_XY:
            case ResultData::SIGMA_XZ:
            case ResultData::SIGMA_YZ:
            case ResultData::SIGMA_VONMISES:
                return &IElement::supports_stress;
                break;

            case ResultData::NX:
                return &IElement::supports_NX;
                break;

            case ResultData::MZ:
                return &IElement::supports_MZ;
                break;

            case ResultData::VY:
                return &IElement::supports_VY;
                break;

            default:
                return &IElement::supports_displacement;
        }
    }

    EvalFnPtr get_eval_func(ResultData id){

        switch (id) {

            case ResultData::UX:
                return &get_ux;
                break;

            case ResultData::UY:
                return &get_uy;
                break;
            case ResultData::UZ:
                return &get_uz;
                break;

            case ResultData::THETAX:
                return &get_thetax;
                break;

            case ResultData::THETAY:
                return &get_thetay;
                break;
            case ResultData::THETAZ :
                return &get_thetaz;
                break;


            case ResultData::ABS_U:
                return &get_abs_u;
                break;

            case ResultData::EPSILON_XX:
                return &get_epsilon_xx;
                break;

            case ResultData::EPSILON_YY:
                return &get_epsilon_yy;
                break;

            case ResultData::EPSILON_ZZ:
                return &get_epsilon_zz;
                break;

            case ResultData::EPSILON_XY:
                return &get_epsilon_xy;
                break;

            case ResultData::EPSILON_XZ:
                return &get_epsilon_xz;
                break;

            case ResultData::EPSILON_YZ:
                return &get_epsilon_yz;
                break;

            case ResultData::SIGMA_XX:
                return &get_sigma_xx;
                break;

            case ResultData::SIGMA_YY:
                return &get_sigma_yy;
                break;

            case ResultData::SIGMA_ZZ:
                return &get_sigma_zz;
                break;

            case ResultData::SIGMA_XY:
                return &get_sigma_xy;
                break;

            case ResultData::SIGMA_XZ:
                return &get_sigma_xz;
                break;

            case ResultData::SIGMA_YZ:
                return &get_sigma_yz;
                break;

            // case ResultData::SIGMA_VONMISES:
            //     return &IElement::supports_stress;
            //     break;

            case ResultData::NX:
                return &get_nx;
                break;

            case ResultData::MZ:
                return &get_mz;
                break;


            case ResultData::VY:
                return &get_vy;
                break;


            default:
                throw std::runtime_error("Unsupported ResultData in get_eval_func");

        }
    }

    std::vector<Point> create_grid(int internal_pts, int num_dimensions, IntegrationGeometry geom){

        int aux = 0;
        if(geom == IntegrationGeometry::TRIANGLE){
            aux = 1;
        }

        std::vector<Point> pts;

        std::vector<double> linspace;
        int size = internal_pts+2;
        linspace.reserve(size);

        double start = -0.9999999;
        double end = 0.99999999;
        double dv = (end-start)/(size-1.);
        for(int i=0;i<size;i++){
            linspace.emplace_back(start + i*dv);
        }

        switch (num_dimensions)
        {
        case 1:
            for(int i=0;i<size;i++){
                pts.push_back(Point(linspace[i]));
            }
            break;
        
        case 2:
            for(int i=0;i<size;i++){
                for(int j=0;j<size-i*aux;j++){
                    pts.push_back(Point(linspace[i],linspace[j]));
                }
            }
            break;

        case 3:
            for(int i=0;i<size;i++){
                for(int j=0;j<size-i*aux;j++){
                    for(int k=0;k<size-j*aux;k++){
                        pts.push_back(Point(linspace[i],linspace[j],linspace[k]));
                    }
                }
            }
            break;
        
        default:
            break;
        }
        return pts;

    }
  
    std::vector<Point> StaticResult::get_points(int internal_pts)const{

        std::vector<Point> points;
        
        for(int el_number=0; el_number<analysis->number_of_elements(); el_number++){

            IElement_ptr el = analysis->get_element(el_number);

            std::vector<Point> grid = create_grid(internal_pts, el->number_of_dimensions(), el->get_integration_domain());
            for(auto& pt:grid){
                Point gpt = el->local_to_global(pt);
                points.emplace_back(gpt);
            }
        }
        return points;
    }

    GridData compute_grid(const Vector& U, Analysis_ptr analysis, ResultData id, int internal_pts){

        GridData grid_data;

        SupportFn support_func = get_support_func(id);
        EvalFnPtr eval_func = get_eval_func(id);
        
        for(int el_number=0; el_number<analysis->number_of_elements(); el_number++){

            IElement_ptr el = analysis->get_element(el_number);

            if(!((*el).*support_func)())
                continue;
            
            std::vector<Point> points = create_grid(internal_pts, el->number_of_dimensions(), el->get_integration_domain());
            Vector ue = analysis->get_element_ue(U,el_number);
            for(auto& pt:points){
                
                Point gpt = el->local_to_global(pt);
                Vector vecpt = pt.as_vector();
                double value = eval_func(vecpt,ue,el);
                grid_data.push_back(std::make_pair(gpt,value));
            }
            
        }

        if(grid_data.size() == 0){
            throw std::runtime_error("No element supports this type result");
        }


        return grid_data;

    }

    Vector compute_mean(const Vector& U, Analysis_ptr analysis, ResultData id, int gauss_pts){

        Vector mean_val(analysis->number_of_elements());
        SupportFn support_func = get_support_func(id);
        EvalFnPtr eval_func = get_eval_func(id);

        for(int el_number=0; el_number<analysis->number_of_elements(); el_number++){

            IElement_ptr el = analysis->get_element(el_number);

            if(!((*el).*support_func)()){
                continue;
            }
                
            std::vector<PointWeight> points_weights = el->integration_pair(gauss_pts);
            Vector ue = analysis->get_element_ue(U,el_number);

            double area = 0;
            double value = 0;
            for(auto& pt : points_weights){

                Vector vecpt = pt.point.as_vector();
                value += eval_func(vecpt,ue,el) * el->detJ(vecpt) * pt.weight;
                area  += el->detJ(vecpt) * pt.weight;
            }
            mean_val(el_number) = value/area;
        }
        return mean_val;
    }
            

} // namespace finelc