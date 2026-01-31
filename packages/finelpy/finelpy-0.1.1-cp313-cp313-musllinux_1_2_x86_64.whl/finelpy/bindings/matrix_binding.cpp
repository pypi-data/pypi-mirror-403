
#include <finelc/matrix.h>

#include <finelc/binding/bindings.h>
#include <finelc/binding/matrix_binding.h>

#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/numpy.h> 
#include <pybind11/stl.h>
#include <pybind11/eigen.h> 

#include <variant>
#include <memory>
#include <utility>
#include <Eigen/Dense>
#include <Eigen/Sparse>

#include <iostream>

namespace py = pybind11;

namespace finelc{

    SparseMatrix scipy_to_eigen(py::object scipy_mat){

        py::module_ scipy_sparse = py::module_::import("scipy.sparse");
        if (!scipy_sparse.attr("isspmatrix_csc")(scipy_mat).cast<bool>()) {
            scipy_mat = scipy_mat.attr("tocsc")();
        }

        py::array_t<double> data = scipy_mat.attr("data").cast<py::array_t<double>>();
        py::array_t<int> indices = scipy_mat.attr("indices").cast<py::array_t<int>>();
        py::array_t<int> indptr  = scipy_mat.attr("indptr").cast<py::array_t<int>>();

        int rows = scipy_mat.attr("shape").attr("__getitem__")(0).cast<int>();
        int cols = scipy_mat.attr("shape").attr("__getitem__")(1).cast<int>();

        SparseMatrix mat(rows,cols);
        std::vector<Triplet> triplets;

        auto data_ptr = data.unchecked<1>();
        auto indices_ptr = indices.unchecked<1>();
        auto indptr_ptr = indptr.unchecked<1>();

        for (int col = 0; col < cols; col++) {
            int start = indptr_ptr(col);
            int end = indptr_ptr(col + 1);
            for (int idx = start; idx < end; idx++) {
                int row = indices_ptr(idx);
                double val = data_ptr(idx);
                triplets.emplace_back(row, col, val);
            }
        }

        mat.setFromTriplets(triplets.begin(), triplets.end());
        return mat;

    }

    py::object eigen_to_scipy(const Matrix& mat){

        py::module_ scipy_sparse = py::module_::import("scipy.sparse");

        const SparseMatrix& spmat = mat.get_sparse_data();
        const int nnz = spmat.nonZeros();

        py::array_t<double> data = py::array_t<double>(nnz);
        py::array_t<int> rows = py::array_t<int>(nnz);
        py::array_t<int> cols  = py::array_t<int>(nnz);

        auto data_mut = data.mutable_unchecked<1>();
        auto cols_mut = cols.mutable_unchecked<1>();
        auto rows_mut = rows.mutable_unchecked<1>();

        int idx = 0;
        for(int col=0; col<spmat.outerSize(); ++col){
            for(SparseMatrix::InnerIterator it(spmat,col); it; ++it){
                data_mut(idx) = it.value();
                cols_mut(idx) = it.col();
                rows_mut(idx) = it.row();
                idx++;
            }
        }

        py::tuple shape = py::make_tuple(mat.rows(), mat.cols());
        py::object result = scipy_sparse.attr("coo_matrix")(
            py::make_tuple(data, py::make_tuple(rows, cols)), py::arg("shape") = shape);

        return result;

    }

    Matrix from_python_to_matrix(py::object py_mat){

        if (py::isinstance<py::array>(py_mat)){
            return Matrix(py_mat.cast<DenseMatrix>());
        } else if (py::module_::import("scipy.sparse").attr("issparse")(py_mat).cast<bool>()) {
            return Matrix(scipy_to_eigen(py_mat));
        } else {
            throw std::runtime_error("Input must be a NumPy array or SciPy sparse matrix.");
        }
    }

    py::object from_matrix_to_python(const Matrix& mat){

        if (mat.is_sparse()){
            return eigen_to_scipy(mat);
        }else{
            return py::cast(mat.get_dense_data());
        }
    }
    
} // namespace finelc



