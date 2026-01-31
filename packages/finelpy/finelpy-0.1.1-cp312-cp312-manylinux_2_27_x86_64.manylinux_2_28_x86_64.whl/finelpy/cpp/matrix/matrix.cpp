
#include <vector>
#include <stdexcept>
#include <string>
#include <variant>

#include <finelc/matrix.h>

namespace finelc{


    Matrix::Matrix(): type(MatrixType::Dense){
        new (&data.dense) DenseMatrix();
    }

    Matrix::Matrix(int rows, int cols, MatrixType type_): type(type_){
        if(type==MatrixType::Dense){
            new (&data.dense) DenseMatrix(rows,cols);
        }else{
            new (&data.sparse) SparseMatrix(rows,cols);
        }
    }

    Matrix::Matrix(const DenseMatrix& mat): type(MatrixType::Dense) { new (&data.dense)  DenseMatrix(mat); }
    Matrix::Matrix(DenseMatrix&& mat): type(MatrixType::Dense) { new (&data.dense)  DenseMatrix(std::move(mat)); }

    Matrix::Matrix(const SparseMatrix& mat): type(MatrixType::Sparse) { new (&data.sparse)  SparseMatrix(mat); }
    Matrix::Matrix(SparseMatrix&& mat): type(MatrixType::Sparse) { new (&data.sparse)  SparseMatrix(std::move(mat)); }


    Matrix::Matrix(const Matrix& other): type(other.type){
        if(type==MatrixType::Dense){
            new (&data.dense) DenseMatrix(other.data.dense);
        }else{
            new (&data.sparse) SparseMatrix(other.data.sparse);
        }
    }

    Matrix::Matrix(Matrix&& other): type(other.type){
        if(type==MatrixType::Dense){
            new (&data.dense) DenseMatrix(other.data.dense);
        }else{
            new (&data.sparse) SparseMatrix(other.data.sparse);
        }
    }

    Matrix::~Matrix(){
        destroy();
    }

    Matrix& Matrix::operator=(const Matrix& mat){
        if(this==&mat) return *this;
        destroy();
        type = mat.type;

        if(type==MatrixType::Dense){
            new (&data.dense) DenseMatrix(std::move(mat.data.dense));
        }else{
            new (&data.sparse) SparseMatrix(std::move(mat.data.sparse));
        }
        return *this;
    }

    Matrix& Matrix::operator=(Matrix&& mat) noexcept {
        if(this==&mat) return *this;
        destroy();
        type = mat.type;
        
        if(type==MatrixType::Dense){
            new (&data.dense) DenseMatrix(mat.data.dense);
        }else{
            new (&data.sparse) SparseMatrix(mat.data.sparse);
        }
        return *this;
    }

    void Matrix::destroy() noexcept {
        if(type==MatrixType::Dense){
            data.dense.~DenseMatrix();
        }else{
            data.sparse.~SparseMatrix();
        }
    }

    const DenseMatrix& Matrix::get_dense_data()const {
        return data.dense;
    }

    const SparseMatrix& Matrix::get_sparse_data()const {
        return data.sparse;
    }

    DenseMatrix& Matrix::get_mutable_dense_data() {
        return data.dense;
    }

    SparseMatrix& Matrix::get_mutable_sparse_data() {
        return data.sparse;
    }

    Matrix Matrix::as_dense() const{
        if(type==MatrixType::Dense){
            return Matrix(data.dense);
        }else{
            return Matrix(DenseMatrix(data.sparse));
        }
    }

    Matrix Matrix::as_sparse() const{
        if(type==MatrixType::Dense){
            return Matrix(SparseMatrix(data.dense.sparseView()));
        }else{
            return Matrix(data.sparse);
        }
    }

    double Matrix::det()const{
        if(type==MatrixType::Dense){
            return data.dense.determinant();
        }else{
            DenseMatrix dense(data.sparse);
            return dense.determinant();
        }
    }

    Matrix Matrix::transpose()const{
        if(type==MatrixType::Dense){
            return Matrix(data.dense.transpose().eval());
        }else{
            SparseMatrix C = data.sparse.transpose().eval();
            return Matrix(std::move(C));
        }
    }

    int Matrix::rows() const{
        if(type==MatrixType::Dense){
            return data.dense.rows();
        }else{
            return data.sparse.rows();
        }
    }

    int Matrix::cols() const{
        if(type==MatrixType::Dense){
            return data.dense.cols();
        }else{
            return data.sparse.cols();
        }
    }

    void Matrix::setZero(){
        if(type==MatrixType::Dense){
            data.dense.setZero();
        }else{
            data.sparse.setZero();
        }
    }

    double Matrix::operator()(int row, int col) const{
        if(type==MatrixType::Dense){
            return data.dense.coeff(row,col);
        }else{
            return data.sparse.coeff(row,col);
        }
    }

    double& Matrix::operator()(int row, int col){
        if(type==MatrixType::Dense){
            return data.dense.coeffRef(row,col);
        }else{
            return data.sparse.coeffRef(row,col);
        }
    }

    Matrix Matrix::operator-()const{
        if(type==MatrixType::Dense){
            return Matrix(-data.dense);
        }else{
            SparseMatrix C = -data.sparse;
            return Matrix(std::move(C));
        }
    }

     Matrix& Matrix::operator+=(const Matrix& B){

        // Dense + Dense
        if(type==MatrixType::Dense && B.type == MatrixType::Dense){
            data.dense += B.data.dense;
            return *this;
        }
        // Sparse + Sparse
        else if(type==MatrixType::Sparse && B.type == MatrixType::Sparse){
            data.sparse += B.data.sparse;
            data.sparse.makeCompressed();
            return *this;
        }
        // Dense + Sparse
        else if(type==MatrixType::Dense && B.type == MatrixType::Sparse){
            data.dense += B.data.sparse;
            return *this;
        }
        // Sparse + Dense
        else{
            DenseMatrix dense_mat = data.sparse + B.data.dense;
            destroy();
            type = MatrixType::Dense;
            new (&data.dense) DenseMatrix(std::move(dense_mat));
            return *this;
        }
    }

    Matrix& Matrix::operator-=(const Matrix& B){
        // Dense - Dense
        if(type==MatrixType::Dense && B.type == MatrixType::Dense){
            data.dense -= B.data.dense;
            return *this;
        }
        // Sparse - Sparse
        else if(type==MatrixType::Sparse && B.type == MatrixType::Sparse){
            data.sparse -= B.data.sparse;
            data.sparse.makeCompressed();
            return *this;
        }
        // Dense - Sparse
        else if(type==MatrixType::Dense && B.type == MatrixType::Sparse){
            data.dense -= B.data.sparse;
            return *this;
        }
        // Sparse - Dense
        else{
            DenseMatrix dense_mat = data.sparse - B.data.dense;
            destroy();
            type = MatrixType::Dense;
            new (&data.dense) DenseMatrix(std::move(dense_mat));
            return *this;
        }
    }

    Matrix& Matrix::operator*=(double scalar){
        if(type==MatrixType::Dense){
            data.dense *= scalar;
            return *this;
        }else{
            data.sparse *= scalar;
            return *this;
        }
    }

    Matrix& Matrix::operator/=(double scalar){
        if(type==MatrixType::Dense){
            data.dense /= scalar;
            return *this;
        }else{
            data.sparse /= scalar;
            return *this;
        }
    }

    Vector Matrix::get_col(int col) const{

        if(type==MatrixType::Dense){
            Vector extracted_col(rows());
            for(int row=0; row<rows(); row++){
                extracted_col(row) = data.dense(row,col);
            }
            return extracted_col;

        }else{
            throw std::runtime_error("Not implemented");
        }
    }

    Vector Matrix::get_row(int row) const{
        if(type==MatrixType::Dense){
            Vector extracted_col(cols());
            for(int col=0; col<cols(); col++){
                extracted_col(col) = data.dense(row,col);
            }
            return extracted_col;
            
        }else{
            throw std::runtime_error("Not implemented");
        }
    }

    Matrix Matrix::slice_by_column(const std::vector<int>& column_index)const{
        if(type==MatrixType::Dense){
            DenseMatrix new_mat(rows(),column_index.size());

            for(int new_col=0; new_col<column_index.size();new_col++){
                int column = column_index[new_col];
                for(int row=0; row<rows(); row++){
                    new_mat.coeffRef(row,new_col) = data.dense(row,column);
                }
            }

            return Matrix(std::move(new_mat));

        }else{
            std::vector<Triplet> triplets;

            for(int new_col=0; new_col<column_index.size();new_col++){
                int column = column_index[new_col];
                for(auto it=this->begin(column);it!=this->end();++it){
                    if(it.col()!=column) break;
                    triplets.emplace_back(it.row(),new_col,it.value());
                }
            }

            SparseMatrix new_mat(rows(),column_index.size());
            new_mat.setFromTriplets(triplets.begin(),triplets.end());
            new_mat.makeCompressed();
            return Matrix(std::move(new_mat));
        }
    }

    Matrix Matrix::slice_by_column(int start, int end)const{

        if(type==MatrixType::Dense){

            DenseMatrix new_mat(rows(),end-start);
                new_mat.setZero();
                
                int new_col = 0;
                for(int column=start; column<end;column++){
                    for(int row=0; row<rows(); row++){
                        new_mat.coeffRef(row,new_col) = data.dense(row,column);
                    }
                    new_col++;
                }
                return Matrix(std::move(new_mat));

            
        }else{

            std::vector<Triplet> triplets;
            int new_col = 0;
            for(int column=start; column<end;column++){
                for(auto it=this->begin(column);it!=this->end();++it){
                    if(it.col()!=column) break;
                    triplets.emplace_back(it.row(),new_col,it.value());
                }
                new_col++;
            }

            SparseMatrix new_mat(rows(),end-start);
            new_mat.setFromTriplets(triplets.begin(),triplets.end());
            new_mat.makeCompressed();
            return Matrix(std::move(new_mat));

        }
    }

    void Matrix::hstack(const Matrix& B){

        // Check size
        if(rows() != B.rows()){
            throw std::runtime_error("Matrices with incompatible sizes for hstack");
        }

        int orig_cols = cols();

        // Dense | Dense
        if(type==MatrixType::Dense && B.type ==MatrixType::Dense){
            data.dense.conservativeResize(rows(), orig_cols + B.cols());
            data.dense.block(0, orig_cols, rows(), B.cols()) = B.data.dense;
        }
        // Sparse | Sparse
        else if(type==MatrixType::Sparse && B.type==MatrixType::Sparse){
            for (int col = 0; col < B.data.sparse.outerSize(); ++col) {
                for(SparseMatrix::InnerIterator it(B.data.sparse, col); it; ++it){
                    data.sparse.insert(it.row(),it.col()+orig_cols) = it.value();
                }
            }
            data.sparse.makeCompressed();
        }
        // Dense | Sparse
        else if(type==MatrixType::Dense && B.type ==MatrixType::Sparse){
            this->hstack(B.as_dense());
        }
        // Sparse | Dense
        else{
            DenseMatrix C = data.sparse;
            destroy();
            type = MatrixType::Dense;
            new (&data.dense) DenseMatrix(std::move(C));
            hstack(B);
        }
    }

    void Matrix::vstack(const Matrix& B){

        // Check size
        if(cols() != B.cols()){
            throw std::runtime_error("Matrices with incompatible sizes for vstack");
        }

        int orig_rows = rows();

        // Dense | Dense
        if(type==MatrixType::Dense && B.type ==MatrixType::Dense){
            data.dense.conservativeResize(orig_rows + B.rows(), cols());
            data.dense.block(orig_rows, 0, B.rows(), cols()) = B.data.dense;
        }
        // Sparse | Sparse
        else if(type==MatrixType::Sparse && B.type==MatrixType::Sparse){
            for (int col = 0; col < B.data.sparse.outerSize(); ++col) {
                for(SparseMatrix::InnerIterator it(B.data.sparse, col); it; ++it){
                    data.sparse.insert(it.row()+orig_rows,it.col()) = it.value();
                }
            }
            data.sparse.makeCompressed();
        }
        // Dense | Sparse
        else if(type==MatrixType::Dense && B.type ==MatrixType::Sparse){
            this->vstack(B.as_dense());
        }
        // Sparse | Dense
        else{
            DenseMatrix C = data.sparse;
            destroy();
            type = MatrixType::Dense;
            new (&data.dense) DenseMatrix(std::move(C));
            vstack(B);
        }
    }

    Matrix hstack(const Matrix& A, const Matrix& B) {
        Matrix C(A);
        C.hstack(B);
        return C;
    }

    Matrix vstack(const Matrix& A, const Matrix& B) {
        Matrix C(A);
        C.vstack(B);
        return C;
    }


    Matrix operator+(const Matrix& A, const Matrix& B){
        // Dense + Dense
        if(A.is_dense() && B.is_dense()){
            DenseMatrix C = A.get_dense_data() + B.get_dense_data();
            return Matrix(std::move(C));
        }
        // Sparse + Sparse
        else if(A.is_sparse() && B.is_sparse()){
            SparseMatrix C = A.get_sparse_data() + B.get_sparse_data();
            C.makeCompressed();
            return Matrix(std::move(C));
        }
        // Dense + Sparse
        else if(A.is_dense() && B.is_sparse()){
            DenseMatrix C = A.get_dense_data() + B.get_sparse_data();
            return Matrix(std::move(C));
        }
        // Sparse + Dense
        else{
            DenseMatrix C = A.get_sparse_data() + B.get_dense_data();
            return Matrix(std::move(C));
        }
    }

    Matrix operator-(const Matrix& A, const Matrix& B){
        // Dense - Dense
        if(A.is_dense() && B.is_dense()){
            DenseMatrix C = A.get_dense_data() - B.get_dense_data();
            return Matrix(std::move(C));
        }
        // Sparse - Sparse
        else if(A.is_sparse() && B.is_sparse()){
            SparseMatrix C = A.get_sparse_data() - B.get_sparse_data();
            C.makeCompressed();
            return Matrix(std::move(C));
        }
        // Dense - Sparse
         else if(A.is_dense() && B.is_sparse()){
            DenseMatrix C = A.get_dense_data() - B.get_sparse_data();
            return Matrix(std::move(C));
        }
        // Sparse - Dense
        else{
            DenseMatrix C = A.get_sparse_data() - B.get_dense_data();
            return Matrix(std::move(C));
        }
    }

    Vector operator*(const Matrix& A, const Vector& v){
        if(A.is_dense()){
            return A.get_dense_data().operator*(v).eval();
        }else{
            return A.get_sparse_data().operator*(v).eval();
        }
    }

    Vector operator*(const Vector& v, const Matrix& A){
        if(A.is_dense()){
            return A.get_dense_data().transpose().operator*(v).eval();
        }else{
            return A.get_sparse_data().transpose().operator*(v).eval();
        }
    }

    Matrix operator*(const Matrix& A, double scalar){
        if(A.is_dense()){
            return Matrix(A.get_dense_data()*scalar);
        }else{
            SparseMatrix C = A.get_sparse_data() * scalar;
            return Matrix(std::move(C));
        }
    }

    Matrix operator*(double scalar, const Matrix& A){
        return A * scalar;
    }

    Matrix operator/(const Matrix& A, double scalar){
         if(A.is_dense()){
            return Matrix(A.get_dense_data()/scalar);
        }else{
            SparseMatrix C = A.get_sparse_data() / scalar;
            return Matrix(std::move(C));
        }
    }

    Matrix operator*(const Matrix& A, const Matrix& B){
        // Check size
        if(A.cols() != B.rows()){
            throw std::runtime_error("Matrices with incompatible sizes for multiplication");
        }

        // Dense * Dense
        if(A.is_dense() && B.is_dense()){
            DenseMatrix C = A.get_dense_data() * B.get_dense_data();
            return Matrix(std::move(C));
        }
        // Sparse * Sparse
        else if(A.is_sparse() && B.is_sparse()){
            SparseMatrix C = A.get_sparse_data() * B.get_sparse_data();
            C.makeCompressed();
            return Matrix(std::move(C));
        }
        // Dense * Sparse
        else if(A.is_dense() && B.is_sparse()){
            DenseMatrix C = A.get_dense_data() * B.get_sparse_data();
            return Matrix(std::move(C));
        }
        // Sparse * Dense
        else{
            DenseMatrix C = A.get_sparse_data() * B.get_dense_data();
            return Matrix(std::move(C));
        }
    }

    std::ostream& operator<<(std::ostream& os, const Matrix& A){
        if(A.is_dense()){
            os << A.get_dense_data();
        }else{
            os << A.get_sparse_data();
        }
        return os;
    }
    
} // namespace finelc
