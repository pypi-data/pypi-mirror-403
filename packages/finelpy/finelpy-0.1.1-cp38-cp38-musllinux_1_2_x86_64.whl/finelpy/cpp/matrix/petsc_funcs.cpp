#ifdef USE_PETSC

#include <finelc/matrix.h>

#include <vector>
#include <stdexcept>

#include <petsc.h>
#include <petscmat.h>
#include <petscksp.h>
#include <petscpc.h>

#include <numeric>
#include <algorithm>

namespace finelc{

    Vector petsc_solve_direct(const Vector& rhs,
                   PetscObjects& obj){

        // RHS vector
        Vec b, x;
        PetscInt n = obj.n;
        VecCreateSeq(PETSC_COMM_SELF, n, &b);
        VecCreateSeq(PETSC_COMM_SELF, n, &x);

        // Index list
        std::vector<PetscInt> idx(n);
        std::iota(idx.begin(), idx.end(), 0);

        VecSetValues(b, n, idx.data(), rhs.data(), INSERT_VALUES);
        VecAssemblyBegin(b); VecAssemblyEnd(b);

        // Solver and preconditioner
        KSP& ksp = obj.ksp;
        PC& pc = obj.pc;
        
        KSPSolve(ksp, b, x);

        // Extract solution
        Vector sol(n);
        VecGetValues(x, n, idx.data(), sol.data());

        VecDestroy(&b);
        VecDestroy(&x);

        return sol;
    }

    // Vector petsc_solve_iterative(const Vector& rhs,
    //                const IterativeProperties &prop,
    //                const Matrix *Mat,
    //                 PETSC_METHOD method){

    //     const SparseMatrix& M = Mat->get_sparse_data();
    //     Mat A = eigen_to_petsc(M);

    //     PetscInt n = M.rows();

    //     // RHS vector
    //     Vec b, x;
    //     VecCreateSeq(PETSC_COMM_SELF, n, &b);
    //     VecCreateSeq(PETSC_COMM_SELF, n, &x);

    //     // Index list
    //     std::vector<PetscInt> idx(n);
    //     std::iota(idx.begin(), idx.end(), 0);

    //     VecSetValues(b, n, idx.data(), rhs.data(), INSERT_VALUES);
    //     VecAssemblyBegin(b); VecAssemblyEnd(b);

    //     // KSP solver
    //     KSP ksp;
    //     KSPCreate(PETSC_COMM_SELF, &ksp);
    //     KSPSetOperators(ksp, A, A);

    //     // Solver type: CG
    //     if (method==PETSC_METHOD::CG){
    //         KSPSetType(ksp, KSPCG);
    //     }

    //     // Preconditioner: ILU
    //     PC pc;
    //     KSPGetPC(ksp, &pc);
    //     PCSetType(pc, PCILU);

    //     // Tolerances
    //     KSPSetTolerances(ksp,
    //         prop.tol,
    //         PETSC_DEFAULT,
    //         PETSC_DEFAULT,
    //         prop.max_iter
    //     );

    //     KSPSetFromOptions(ksp);
    //     KSPSolve(ksp, b, x);

    //     // Extract solution
    //     Vector sol(n);
    //     VecGetValues(x, n, idx.data(), sol.data());

    //     VecDestroy(&b);
    //     VecDestroy(&x);
    //     MatDestroy(&A);
    //     KSPDestroy(&ksp);

    //     return sol;
    //}


    
} // namespace finelc

#endif