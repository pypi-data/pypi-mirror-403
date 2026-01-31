#include <finelc/matrix.h>

#include <finelc/analysis/analysis.h>
#include <finelc/solver/solver.h>
#include <finelc/result/result.h>

#include <optional>

namespace finelc{

    void StaticSolver::default_solver(){
        /*if(analysis->get_size() > 1'000'000){
            type = std::make_unique<SolverType>(SolverType::Iterative);
        }else{*/
            type = std::make_unique<SolverType>(SolverType::Direct);
       // }
    }

    StaticResult StaticSolver::solve(){

        if(!type) default_solver();

        #ifdef USE_PETSC
            PetscObjects& obj = analysis->get_PETSc_objects();
            obj.Kmat = &analysis->get_PETSc_K();
            KSPSetOperators(obj.ksp, *obj.Kmat, *obj.Kmat);
            PCSetReusePreconditioner(obj.pc,PETSC_TRUE);
            PCFactorSetReuseOrdering(obj.pc, PETSC_TRUE);
            PCFactorSetReuseFill(obj.pc, PETSC_TRUE);
            Vector u = petsc_solve_direct(
                analysis->fg(), 
                obj);
            return StaticResult(std::move(u),analysis); 
        #else

        if(!solver){
            Matrix Kg = analysis->Kg();
            solver = std::make_unique<Solver>(Kg,*type);
        }

        const Vector& fg = analysis->fg();
        Vector u = solver->solve(fg);
        return StaticResult(std::move(u),analysis);
        #endif

        

    }

} // namespace finelc

