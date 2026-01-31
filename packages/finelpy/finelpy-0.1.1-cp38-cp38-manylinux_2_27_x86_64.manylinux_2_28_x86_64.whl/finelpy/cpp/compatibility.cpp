#include <finelc/enumerations.h>
#include <finelc/compatibility.h>

#include <stdexcept>


namespace finelc{

    void element_compatibility( ShapeType shape_type,
                                ModelType physics_type,
                                ConstitutiveType const_type){

        if(shape_type != ShapeType::PYTHON_SHAPE && physics_type != ModelType::PYTHON_PHYSICS){
            auto it = valid_shape_model.find(shape_type);
            if (it == valid_shape_model.end() || (it->second.find(physics_type) == it->second.end())){
                throw std::runtime_error("Invalid shape and physics combination");
            }
        }

        if(physics_type != ModelType::PYTHON_PHYSICS && const_type != ConstitutiveType::PYTHON_CONSTITUTIVE){
            auto it = valid_model_constitutive.find(physics_type);
            if (it == valid_model_constitutive.end() || (it->second.find(const_type) == it->second.end())){
                throw std::runtime_error("Invalid model and constitutive model combination");
            }
        }

    }

} // namespace finelc