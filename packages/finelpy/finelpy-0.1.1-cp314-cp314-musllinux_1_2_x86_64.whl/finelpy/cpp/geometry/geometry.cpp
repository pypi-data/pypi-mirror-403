#include <finelc/geometry/geometry.h>

#include <iostream>
#include <cmath>

namespace finelc{

    Point Point::operator+(const Point& p2) const{
        return Point(x+p2.x, y+p2.y, z+p2.z);
    }

    Point Point::operator-(const Point& p2) const{
        return Point(x-p2.x, y-p2.y, z-p2.z);
    }

    Point Point::operator*(const Point& p2) const{
        return Point(x*p2.x, y*p2.y, z*p2.z);
    }

    Point Point::operator*(const double val) const{
        return Point(x*val, y*val, z*val);
    }

    double dist(const Point& p1, const Point& p2){
        Point diff = p2-p1;
        return std::sqrt(diff.x*diff.x + diff.y*diff.y + diff.z*diff.z);
    }

    double Line::length()const{
        return dist(p1,p2);
    }

    

    bool IArea::is_inside(const Point& p)const{

        double minimum_x = p.x;
        double minimum_y = p.y;

        for(auto& point: *vertices){
            minimum_x = minimum_x>point.x ? point.x : minimum_x;
            minimum_y = minimum_y>point.y ? point.y : minimum_y;
        }

        Line x_line = Line(Point(minimum_x,p.y,p.z), p);
        size_t num_intersect_x = 0;
        for(auto& line : *lines){
            if(line.is_inside(p)) return true;
            if(get_line_intersection(x_line, line).is_intersect){
                num_intersect_x++;
            };
        }

        if(num_intersect_x%2){
            Line y_line = Line(Point(p.x,minimum_y,p.z), p);
            size_t num_intersect_y = 0;
            for(auto& line : *lines){
                if(get_line_intersection(y_line, line).is_intersect){
                    num_intersect_y++;
                };
            }
            if(num_intersect_y%2){
                return true;
            }
        }
        return false;
    }
    
    void Rectangle::create_rectangle(){

        vertices = std::make_unique<std::vector<Point>>(4);
        lines = std::make_unique<std::vector<Line>>(4);
        auto& vert = *vertices;
        auto& line = *lines;

        vert[0] = origin;
        vert[1] = origin + Point(dimension.x,0,0);
        vert[2] = origin + Point(dimension.x,dimension.y,0);
        vert[3] = origin + Point(0,dimension.y,0);

        line[0] = Line(vert[0],vert[1]);
        line[1] = Line(vert[1],vert[2]);
        line[2] = Line(vert[2],vert[3]);
        line[3] = Line(vert[3],vert[0]);
    }

    LineIntesectResult get_line_intersection(Line l1, Line l2, double tolerance){

        Point A = l1.p2 - l1.p1;
        Point B = l2.p1 - l2.p2;
        Point C = l1.p1 - l2.p1;

        double numerator = B.y*C.x - B.x*C.y;
        double denominator = A.y*B.x - A.x*B.y;

        if (denominator>tolerance){
            if (numerator<0 || numerator>denominator){
                return{false, Point(0,0,0)};
            }else{
                return{true, l1.p1+A*(numerator/denominator)};
            }
        }else if(denominator<tolerance){
            if (numerator>0 || numerator<denominator){
                return{false, Point(0,0,0)};
            }else{
                return{true, l1.p1+A*(numerator/denominator)};
            }
        }else{
            return{false,Point(0,0,0)};
        }
    }

    IArea& add_geometries(IArea& geo1, IArea& geo2){
        return geo1;
    }
    
} // namespace finel