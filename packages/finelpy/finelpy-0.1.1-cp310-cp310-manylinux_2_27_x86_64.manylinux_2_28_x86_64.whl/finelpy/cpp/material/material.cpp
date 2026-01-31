#include <finelc/material/material.h>
#include <finelc/matrix.h>


namespace finelc{

    std::shared_ptr<MaterialCatalogue> MaterialCatalogue::catalogue;
    std::mutex MaterialCatalogue::mtx;

    Material& Material::add_property(const MaterialProperties& identifier, const double value){
        properties_map[identifier] = value;
        return *this;
    }

    double  Material::get_property(const MaterialProperties& identifier) const{

        auto it = properties_map.find(identifier);
        if (it == properties_map.end()) {
            throw std::out_of_range("Property '" + std::to_string(static_cast<int>(identifier)) + "' not found in MaterialModel.");
        }
        return it->second;
    }

    std::shared_ptr<Material> MaterialCatalogue::get_material(const std::string& material_id){

        return this->materials.at(material_id);
    }

    std::shared_ptr<Material> MaterialCatalogue::create_material(const std::string& material_id){

        return (this->materials[material_id] = std::make_shared<Material>());
    }
    
} // namespace finel