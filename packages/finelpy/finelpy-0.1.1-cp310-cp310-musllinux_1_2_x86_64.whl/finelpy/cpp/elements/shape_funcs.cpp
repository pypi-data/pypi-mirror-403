
#include <finelc/matrix.h>
#include <finelc/elements/shape_func.h>


#include <vector>
#include <memory>
#include <algorithm>
#include <iostream>
#include <cmath>


namespace finelc{

    Vector compute_lagrange_weights(int order){

        const double start = -1;
        const double dx = 2. / order;

        int n = order+1;
        Vector wi(n);

        for(int j=0; j<n;j++){

            double xj = start + dx * j;
            double prod = 1.0;

            for (int i = 0; i < n; i++) {
                if (i == j) continue;
                double xi = start + dx * i;
                prod *= (xj - xi);
            }
            wi(j) = 1/prod;
        }
        return wi;
    }

    double eval_lagrange_polynomial_barycentric(
        double x, 
        int order, 
        int number, 
        const Vector& wi){
        
        const double start = -1;
        const double dx = 2. / order;
        const double eps = 1e-14;

        double xj = start+dx*number;

        // If it is current node
        if (fabs(x - xj) < eps)
            return 1.0;

        // If it is another node
        for (int k = 0; k <= order; k++) {
            if (k == number) continue;
            double xm = start + dx * k;
            if (fabs(x - xm) < eps)
                return 0.0;
        }
    
        double num = wi(number)/(x-xj);
        double den = 0.0;

        for (int i = 0; i <= order; i++) {
            double xi = start + dx * i;
            den += wi(i) / (x - xi);
        }
        return num/den;
    }

    double eval_lagrange_polynomial(double x, int order, int number){
        Vector wi = compute_lagrange_weights(order);
        return eval_lagrange_polynomial_barycentric(x,order,number,wi);
    }

    double eval_lagrange_polynomial_derivative_barycentric(
        double x, 
        int order, 
        int number,
        double lj,
        const Vector& wi){
        
        const double start = -1;
        const double dx = 2. / order;
        const double eps = 1e-3;

        int n = order+1;
        double xj = start + dx * number;

        // If it is current node
        if (fabs(x - xj) < eps) {
            double sum = 0.0;
            for (int i = 0; i < n; i++) {
                if (i == number) continue;
                double xi = start + dx * i;
                sum += wi(i) / (xj - xi);
            }
            return -sum / wi(number);
        }

        // If it is another node
        for (int k = 0; k<=order; k++) {
            if (k == number) continue;
            double xk = start + dx * k;
            if (fabs(x - xk) < eps) {
                return wi(number) / wi(k) / (xk - xj);
            }
        }

        // General case
        double S1 = 0.0;
        double S2 = 0.0;

        for (int i = 0; i < n; i++) {
            double xi = start + dx * i;
            double dx_i = x - xi;
            double t = wi(i) / dx_i;
            S1 += t;
            S2 += t / dx_i;
        }

        double result = -lj * ( 1.0/(x - xj) - S2 / S1 );
        return result;


    }

    double eval_lagrange_polynomial_derivative(double x, int order, int number){
        Vector wi = compute_lagrange_weights(order);
        double lj = eval_lagrange_polynomial_barycentric(x,order,number,wi);
        return eval_lagrange_polynomial_derivative_barycentric(x,order,number,lj,wi);
    }

    Vector eval_lagrange_polynomials(double x, int order){

        Vector N(order+1);
        Vector wi = compute_lagrange_weights(order);

        N(0) = eval_lagrange_polynomial_barycentric(x,order,0,wi);
        N(1) = eval_lagrange_polynomial_barycentric(x,order,order,wi);
        for(int i=1; i<order; i++){
            N(i+1) = eval_lagrange_polynomial_barycentric(x,order,i,wi);
        }
        return N;

    }

    Vector eval_lagrange_polynomials_derivatives(double x, int order){

        Vector dN(order+1);
        Vector wi = compute_lagrange_weights(order);

        double li = eval_lagrange_polynomial_barycentric(x,order,0,wi);
        dN(0) = eval_lagrange_polynomial_derivative_barycentric(x,order,0,li,wi);

        li = eval_lagrange_polynomial_barycentric(x,order,order,wi);
        dN(1) = eval_lagrange_polynomial_derivative_barycentric(x,order,order,li,wi);
        
        for(int i=1; i<order; i++){
            li = eval_lagrange_polynomial_barycentric(x,order,i,wi);
            dN(i+1) = eval_lagrange_polynomial_derivative_barycentric(x,order,i,li,wi);
        }
        return dN;

    }

} // namespace finelc

