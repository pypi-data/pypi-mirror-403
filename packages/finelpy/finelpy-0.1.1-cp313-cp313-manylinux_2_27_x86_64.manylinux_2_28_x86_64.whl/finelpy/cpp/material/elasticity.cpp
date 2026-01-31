
//     Matrix PlaneStrain::get_material_matrix(const Vector& u) const{

//         double E = get_property(MaterialProperties::YOUNGS_MOD);
//         double nu = get_property(MaterialProperties::POISSON);

//         DenseMatrix D(3,3);
//         D <<  1-nu,   nu,      0,
//                 nu, 1-nu,      0,
//                 0,    0, 1-2*nu;
//         D*= E/((1+nu)*(1-2*nu));

//         return D;
//     }

//     Matrix IsotropicLinearElasticity::get_material_matrix(const Vector& u) const{

//         double E = get_property(MaterialProperties::YOUNGS_MOD);
//         double nu = get_property(MaterialProperties::POISSON);

//         DenseMatrix D(6,6);
//         D <<  1-nu,   nu,   nu,      0,      0,      0,
//                 nu, 1-nu,   nu,      0,      0,      0,
//                 nu,   nu, 1-nu,      0,      0,      0,
//                 0,    0,    0, 1-2*nu,      0,      0,
//                 0,    0,    0,      0, 1-2*nu,      0,
//                 0,    0,    0,      0,      0, 1-2*nu;
//         D*= E/((1+nu)*(1-2*nu));

//         return D;
//     }