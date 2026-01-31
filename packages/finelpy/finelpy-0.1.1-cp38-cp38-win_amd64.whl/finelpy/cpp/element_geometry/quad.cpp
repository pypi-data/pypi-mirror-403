#include <finelc/matrix.h>
#include <finelc/element_geometry/quad.h>

#include <vector>
#include <iostream>

namespace finelc{

    Vector Quad4::N(const Vector& loc){

        double xi = loc(0);
        double eta = loc(1);

        Vector N(4);

        N(0) = 0.25*(1-xi)*(1-eta);
        N(1) = 0.25*(1+xi)*(1-eta);
        N(2) = 0.25*(1+xi)*(1+eta);
        N(3) = 0.25*(1-xi)*(1+eta);

        return N;

    }

    Matrix Quad4::dNdxi(const Vector& loc){

        double xi = loc(0);
        double eta = loc(1);

        DenseMatrix dNdxi(2,4);

        dNdxi(0,0) = -0.25*(1-eta);
        dNdxi(0,1) =  0.25*(1-eta);
        dNdxi(0,2) =  0.25*(1+eta);
        dNdxi(0,3) = -0.25*(1+eta);

        dNdxi(1,0) =  -0.25*(1-xi);
        dNdxi(1,1) =  -0.25*(1+xi);
        dNdxi(1,2) =  0.25*(1+xi);
        dNdxi(1,3) =  0.25*(1-xi);

        return dNdxi;

    }

    Matrix Quad4::dNdx( const VectorNodes& element_nodes,
                        const Vector& loc){

        Matrix dN_dxi = dNdxi(loc);
        Matrix Jacobian = J(element_nodes, loc);

        return Solver(Jacobian).solve(dN_dxi).transpose();

    }

    Matrix Quad4::J(const VectorNodes& element_nodes,
            const Vector& loc){

        double x1 = element_nodes[0]->x;
        double x2 = element_nodes[1]->x;
        double x3 = element_nodes[2]->x;
        double x4 = element_nodes[3]->x;

        double y1 = element_nodes[0]->y;
        double y2 = element_nodes[1]->y;
        double y3 = element_nodes[2]->y;
        double y4 = element_nodes[3]->y;
        
        double xi = loc(0);
        double eta = loc(1);

        double xA = 0.25*(-x1+x2+x3-x4);
        double xB = 0.25*(-x1-x2+x3+x4);
        double xC = 0.25*( x1-x2+x3-x4);

        double yA = 0.25*(-y1+y2+y3-y4);
        double yB = 0.25*(-y1-y2+y3+y4);
        double yC = 0.25*( y1-y2+y3-y4);

        DenseMatrix J = DenseMatrix(2,2);

        J(0,0) = xA + xC*eta;
        J(1,0) = xB + xC*xi;

        J(0,1) = yA + yC*eta;
        J(1,1) = yB + yC*xi;

        return J;
    }

    double Quad4::detJ(const VectorNodes& element_nodes,
                const Vector& loc){
        return J(element_nodes,loc).det();
    }









    Vector Quad9::N(const Vector& loc){

        double xi = loc(0);
        double eta = loc(1);


        Vector N(number_of_nodes);

        double N1_xi = 0.5*xi*(xi-1);
        double N2_xi = (1-xi*xi);
        double N3_xi = 0.5*xi*(xi+1);

        double N1_eta = 0.5*eta*(eta-1);
        double N2_eta = (1-eta*eta);
        double N3_eta = 0.5*eta*(eta+1);

        N(0) = N1_xi*N1_eta;
        N(1) = N3_xi*N1_eta;
        N(2) = N3_xi*N3_eta;
        N(3) = N1_xi*N3_eta;

        N(4) = N2_xi*N1_eta;
        N(5) = N3_xi*N2_eta;
        N(6) = N2_xi*N3_eta;
        N(7) = N1_xi*N2_eta;
        N(8) = N2_xi*N2_eta;

        return N;

    }

    Matrix Quad9::dNdxi(const Vector& loc){

        double xi = loc(0);
        double eta = loc(1);

        double N1_xi = 0.5*xi*(xi-1);
        double N2_xi = (1-xi*xi);
        double N3_xi = 0.5*xi*(xi+1);

        double dN1_xi = xi-0.5;
        double dN2_xi = -2*xi;
        double dN3_xi = xi+0.5;

        double N1_eta = 0.5*eta*(eta-1);
        double N2_eta = (1-eta*eta);
        double N3_eta = 0.5*eta*(eta+1);

        double dN1_eta = eta-0.5;
        double dN2_eta = -2*eta;
        double dN3_eta = eta+0.5;


        DenseMatrix dNdxi(2,number_of_nodes);

        dNdxi(0,0) = dN1_xi*N1_eta;
        dNdxi(0,1) = dN3_xi*N1_eta;
        dNdxi(0,2) = dN3_xi*N3_eta;
        dNdxi(0,3) = dN1_xi*N3_eta;
        dNdxi(0,4) = dN2_xi*N1_eta;
        dNdxi(0,5) = dN3_xi*N2_eta;
        dNdxi(0,6) = dN2_xi*N3_eta;
        dNdxi(0,7) = dN1_xi*N2_eta;
        dNdxi(0,8) = dN2_xi*N2_eta;

        dNdxi(1,0) = N1_xi*dN1_eta;
        dNdxi(1,1) = N3_xi*dN1_eta;
        dNdxi(1,2) = N3_xi*dN3_eta;
        dNdxi(1,3) = N1_xi*dN3_eta;
        dNdxi(1,4) = N2_xi*dN1_eta;
        dNdxi(1,5) = N3_xi*dN2_eta;
        dNdxi(1,6) = N2_xi*dN3_eta;
        dNdxi(1,7) = N1_xi*dN2_eta;
        dNdxi(1,8) = N2_xi*dN2_eta;

        return dNdxi;

    }

    Matrix Quad9::dNdx( const VectorNodes& element_nodes,
                        const Vector& loc){

        Matrix dN_dxi = dNdxi(loc);
        Matrix Jacobian = J(element_nodes, loc);

        return Solver(Jacobian).solve(dN_dxi).transpose();

    }

    Matrix Quad9::J(const VectorNodes& element_nodes,
            const Vector& loc){


        Matrix dN_dxi = dNdxi(loc);

        Matrix nodes(number_of_nodes,2);
        for(int i=0; i<number_of_nodes; i++){
            nodes(i,0) = element_nodes[i]->x;
            nodes(i,1) = element_nodes[i]->y;
        }

        return dN_dxi * nodes;
    }

    double Quad9::detJ(const VectorNodes& element_nodes,
                const Vector& loc){
        return J(element_nodes,loc).det();
    }
    

} // namespace finel