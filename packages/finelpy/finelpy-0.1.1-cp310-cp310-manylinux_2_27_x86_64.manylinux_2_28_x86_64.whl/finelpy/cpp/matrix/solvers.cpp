
#include <finelc/matrix.h>

#include <vector>
#include <stdexcept>
#include <string>
#include <variant>

#include <iostream>


namespace finelc{


    Vector default_iterative_sparse_solver(IterativeSolver& iterative_solver, 
                                            const Vector& rhs, 
                                            const IterativeProperties& prop){
            
        iterative_solver.setMaxIterations(prop.max_iter);
        iterative_solver.setTolerance(prop.tol);
        return iterative_solver.solve(rhs);
    }

    Matrix default_iterative_sparse_solver(IterativeSolver& iterative_solver, 
                                            const DenseMatrix& rhs, 
                                            const IterativeProperties& prop){
            
        iterative_solver.setMaxIterations(prop.max_iter);
        iterative_solver.setTolerance(prop.tol);
        return Matrix(iterative_solver.solve(rhs));
    }


    Vector default_direct_sparse_solver(SparseSolver& sparse_solver, const Vector& rhs, const Matrix& Mat){
        sparse_solver.factorize(Mat.get_sparse_data());
        return sparse_solver.solve(rhs);
    }

    Matrix default_direct_sparse_solver(SparseSolver& sparse_solver, const DenseMatrix& rhs, const Matrix& Mat){
        sparse_solver.factorize(Mat.get_sparse_data());
        return Matrix(sparse_solver.solve(rhs));
    }

    Vector Solver::dense_solver(const Vector& rhs){
        return solver.dense.solve(rhs);
    }

    Matrix Solver::dense_solver(const DenseMatrix& rhs){
        
        return Matrix(solver.dense.solve(rhs));
    }

    Vector Solver::sparse_solver(const Vector& rhs){
        if(type == SolverType::Iterative){
            return default_iterative_sparse_solver(solver.iterative,rhs,prop);
        }else{
            return default_direct_sparse_solver(solver.sparse,rhs,Mat);
        }
    }

    Matrix Solver::sparse_solver(const DenseMatrix& rhs){

        if(type == SolverType::Iterative){

            return default_iterative_sparse_solver(solver.iterative,rhs,prop);

        }else{
            return default_direct_sparse_solver(solver.sparse,rhs,Mat);
        }
    }



    Solver::Solver(Matrix mat_obj, SolverType type_, IterativeProperties properties_): 
    Mat(mat_obj), type(type_), prop(properties_)
    {
        if(Mat.is_dense()){
            new (&solver.dense) DenseSolver();
            solver.dense.compute(Mat.get_dense_data());
        }else{
            if(type == SolverType::Iterative){
                new (&solver.iterative) IterativeSolver();
                solver.iterative.compute(Mat.get_sparse_data());

            }else{
                new (&solver.sparse) SparseSolver();
                solver.sparse.analyzePattern(Mat.get_sparse_data());
            }
        }
    }

    Vector Solver::solve(const Vector& rhs){
        if(Mat.is_dense()){
            return dense_solver(rhs);
        }else{
            return sparse_solver(rhs);
        }
    }

    Matrix Solver::solve(const Matrix& rhs){

        if(rhs.is_sparse()){
            return solve(rhs.as_dense());
        }

        if(Mat.is_dense()){
            return dense_solver(rhs.get_dense_data());
        }else{
            return sparse_solver(rhs.get_dense_data());
        }
    }

    
} // namespace finelc
