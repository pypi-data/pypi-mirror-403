#include <finelc/matrix.h>
#include <finelc/element_physics/plane.h>

#include <array>
#include <vector>

namespace finelc{

    Matrix PlaneStructural::N(const Vector& N_geo, const Vector& loc){

        int num_nodes = N_geo.size();
        Matrix Nmat(dof_per_node,dof_per_node*num_nodes);
        Nmat.setZero();

        for(int i=0; i<num_nodes; i++){
            Nmat(0,2*i)   = N_geo(i);
            Nmat(1,2*i+1) = N_geo(i);
        }

        return Nmat;

    }

    Matrix PlaneStructural::dNdx(const Matrix& dNdx_geo, const Vector& loc){
        return dNdx_geo;
    }

    Matrix PlaneStructural::B(const Matrix& dNdx,const Vector& loc){

        int num_nodes = dNdx.rows();
        Matrix B(3,num_nodes*dof_per_node);
        B.setZero();

        for(int i=0; i<num_nodes; i++){
            B(0,2*i)   = dNdx(i,0);
            B(1,2*i+1) = dNdx(i,1);
            B(2,2*i)   = dNdx(i,1);
            B(2,2*i+1) = dNdx(i,0);
        }
        return B;

    }

    Vector PlaneStructural::strain(   const Vector& loc, 
                            const Vector& ue,
                            const Matrix& dNdx){
        Vector strn(6);
        Vector strain2D = B(dNdx, loc) * ue;

        strn.setZero();
        strn(0) = strain2D(0);
        strn(1) = strain2D(1);
        strn(3) = strain2D(3);

        return strn;
    }

    Vector PlaneStructural::stress(   const Vector& loc, 
                            const Vector& ue,
                            const Matrix& dNdx,
                            const Matrix& D){

        Vector strs(6);
        Vector stress2D = D * strain(loc,ue,dNdx);

        strs.setZero();
        strs(0) = stress2D(0);
        strs(1) = stress2D(1);
        strs(3) = stress2D(3);

        return strs;
    }

    Vector PlaneStructural::compute( Tag_get_strain, 
                    const Vector& loc, 
                    const Vector& ue,
                    const Matrix& dNdx,
                    const Matrix&){
        
        return strain(loc,ue,dNdx);

    }

    Vector PlaneStructural::compute( Tag_get_stress, 
                    const Vector& loc, 
                    const Vector& ue,
                    const Matrix& dNdx,
                    const Matrix& D){
        return stress(loc,ue,dNdx,D);
    }

} // namespace finelc