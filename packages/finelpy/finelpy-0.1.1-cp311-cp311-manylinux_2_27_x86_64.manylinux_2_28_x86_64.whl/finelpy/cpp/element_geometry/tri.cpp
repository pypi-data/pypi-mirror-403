#include <finelc/matrix.h>
#include <finelc/element_geometry/tri.h>

#include <vector>
#include <iostream>

namespace finelc{

    Vector Tri3::N(const Vector& loc){

        double xi = loc(0);
        double eta = loc(1);

        Vector N(3);

        N(0) = -0.5*(xi+eta);
        N(1) = 0.5*(1+xi);
        N(2) = 0.5*(1+eta);

        return N;

    }

    Matrix Tri3::dNdxi(const Vector&){

        DenseMatrix dNdxi(2,3);

        dNdxi(0,0) = -0.5;
        dNdxi(0,1) =  0.5;
        dNdxi(0,2) =  0;

        dNdxi(1,0) =  -0.5;
        dNdxi(1,1) =  0;
        dNdxi(1,2) =  0.5;

        return dNdxi;

    }

    Matrix Tri3::dNdx( const VectorNodes& element_nodes,
                        const Vector& loc){

        Matrix dN_dxi = dNdxi(loc);
        Matrix Jacobian = J(element_nodes, loc);

        return Solver(Jacobian).solve(dN_dxi).transpose();

    }

    Matrix Tri3::J(const VectorNodes& element_nodes,
            const Vector&){

        double x1 = element_nodes[0]->x;
        double x2 = element_nodes[1]->x;
        double x3 = element_nodes[2]->x;

        double y1 = element_nodes[0]->y;
        double y2 = element_nodes[1]->y;
        double y3 = element_nodes[2]->y;

        DenseMatrix J = DenseMatrix(2,2);

        J(0,0) = 0.5*(x2-x1);
        J(1,0) = 0.5*(x3-x1);

        J(0,1) = 0.5*(y2-y1);
        J(1,1) = 0.5*(y3-y1);

        return J;
    }

    double Tri3::detJ(const VectorNodes& element_nodes,
                const Vector& loc){
        return J(element_nodes,loc).det();
    }


} // namespace finel