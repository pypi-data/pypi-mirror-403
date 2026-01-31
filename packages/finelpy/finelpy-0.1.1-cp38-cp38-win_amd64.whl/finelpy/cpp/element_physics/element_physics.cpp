
#include <finelc/element_physics/element_physics.h>

#include <iostream>
#include <stdexcept>
#include <string>

namespace finelc{


    Vector IElementPhysics::get_stress( const Vector& loc, 
                                                const Vector& ue, 
                                                const Matrix& dNdx,
                                                const Matrix& D)const{
        error_message("get_stress()");
        return Vector();
    }

    Vector IElementPhysics::get_strain( const Vector& loc, 
                                                const Vector& ue, 
                                                const Matrix& dNdx,
                                                const Matrix& D)const{
        error_message("get_strain()");
        return Vector();
    }

    Vector IElementPhysics::get_NX( const Vector& loc, 
                                                const Vector& ue, 
                                                const Matrix& dNdx,
                                                const Matrix& D)const{
        error_message("get_NX()");
        return Vector();
    }

    Vector IElementPhysics::get_MZ( const Vector& loc, 
                                                const Vector& ue, 
                                                const Matrix& dNdx,
                                                const Matrix& D)const{
        error_message("get_MZ()");
        return Vector();
    }


    Vector IElementPhysics::get_VY( const Vector& loc, 
                                                const Vector& ue, 
                                                const Matrix& dNdx,
                                                const Matrix& D)const{
        error_message("get_VY()");
        return Vector();
    }



} // namespace finelc