
#include <finelc/elements/integration.h>

#include <vector>
#include <cmath>
#include <algorithm>

#ifdef MACOS
    #include <boost/math/special_functions/legendre.hpp>
#endif

namespace finelc{

    std::vector<PointWeight> legendre_roots(int n, double tol) {

        std::vector<std::pair<double,double>> pairs;
        pairs.reserve(n);

        static const double PI = 3.14159265358979323846;

        for (int k = 1; k <= n; ++k) {
            // initial guess (Good initial estimate)
            double x = std::cos(PI * (k - 0.25) / (n + 0.5));
            for (;;) {
                #ifdef MACOS
                    double Pn = boost::math::legendre_p(n, x);
                    double Pn1 = boost::math::legendre_p(n-1, x);
                #else
                    double Pn = std::legendre(n, x);
                    double Pn1 = std::legendre(n - 1, x); 
                #endif
                double dPn = n * (x * Pn - Pn1) / (x * x - 1);
                double dx = -Pn / dPn;
                x += dx;
                if (std::abs(dx) < tol) {
                    double w = 2.0/((1.0 - x*x) * dPn * dPn);
                    pairs.emplace_back(x, w);
                    break;
                }
            }
        }

        // sort by abscissa
        std::sort(pairs.begin(), pairs.end(), [](auto &a, auto &b){ return a.first < b.first; });

        // build PointWeight vector
        std::vector<PointWeight> points;
        points.reserve(pairs.size());
        for (auto &pr : pairs){
            points.emplace_back(pr.first, pr.second);
        }

        return points;
    }
    

    PointWeight convolve_points(const PointWeight& p1, 
        const PointWeight& p2, 
        const PointWeight& p3){
            return PointWeight(
                Point(p1.point.x,p2.point.x,p3.point.x), 
                p1.weight*p2.weight*p3.weight);
        }
    
    
    std::vector<PointWeight> get_gauss_points(
        IntegrationGeometry geometry,
        int num_pts, 
        int dimensions){


        std::vector<PointWeight> pts;

        switch(geometry){
            case IntegrationGeometry::REGULAR:
                if(dimensions==1) pts = get_gauss_pair<IntegrationGeometry::REGULAR,1>(num_pts);
                if(dimensions==2) pts = get_gauss_pair<IntegrationGeometry::REGULAR,2>(num_pts);
                if(dimensions==3) pts = get_gauss_pair<IntegrationGeometry::REGULAR,3>(num_pts);
                break;

            case IntegrationGeometry::TRIANGLE:
                if(dimensions==2) pts = get_gauss_pair<IntegrationGeometry::TRIANGLE,2>(num_pts);
                break;

            default:
                throw std::runtime_error("Unsupported integration domain/dimension");
        }

        return pts;

    }

} // namespace finelc 