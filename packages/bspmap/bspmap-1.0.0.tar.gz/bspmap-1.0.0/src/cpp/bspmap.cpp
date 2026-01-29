#include <bspmap.h>
#include "basisfunc.h"
#include <iostream>
#include "tensor.h"
#include "mappingfunc.h"
#include <span>
#include <vector>
#include <omp.h>

namespace bspmap {

const char* get_version() {
    return "0.1.0";
}

// TODO: 这里添加主要的 C++ API 实现

} // namespace bspmap

// ==================== C API 导出 ====================
// 所有的 C API 集中在这里，方便 ctypes 调用
// 策略：C API 是薄包装层，内部调用 C++ 函数

extern "C" {

    // ===== 版本信息 =====
    BSPMAP_API const char* bspmap_get_version() {
        return bspmap::get_version();
    }

    // ===== B-spline basis function =====
    BSPMAP_API void bspmap_deboor_cox(
        const double* knot_vector,
        int knot_vector_size,
        int num_nodes,
        int degree,
        double* result  // output array
    ) {
        // call C++ function, using std::span to wrap pointers
        bspmap::Tensor basis = bspmap::deboor_cox(
            std::span<const double>(knot_vector, static_cast<size_t>(knot_vector_size)),
            num_nodes,
            degree
        );

        // copy results to output array
        const size_t size = basis.size();
        for (size_t i = 0; i < size; ++i) {
            result[i] = basis[i];
        }
    }

    // ===== basis derivative =====
    BSPMAP_API void bspmap_basis_derivative(
        double* basis_data,
        int dim1,
        int dim2,
        int dim3,
        double* result  // output array
    ) {
        // wrap basis_data into Tensor3D
        size_t total_size = static_cast<size_t>(dim1) * static_cast<size_t>(dim2) * static_cast<size_t>(dim3);
        std::span<double> basis_span(basis_data, total_size);
        bspmap::Tensor3D basis(dim1, dim2, dim3, basis_span);

        // call C++ function
        bspmap::Tensor3D derivative = bspmap::basis_derivative(std::move(basis));

        // copy results to output array
        const size_t deriv_size = derivative.size();
        for (size_t i = 0; i < deriv_size; ++i) {
            result[i] = derivative[i];
        }
    }

    // ===== interval finding function =====
    BSPMAP_API void bspmap_find_interval(
        const double* knot_vector,
        int knot_vector_size,
        int degree,
        double* x,
        int size_x,
        int* interval_index  // output
    ) {
#pragma omp parallel for
        for (int i = 0; i < size_x; ++i) {
            int index = bspmap::find_interval(
                std::span<const double>(knot_vector, static_cast<size_t>(knot_vector_size)),
                degree,
                x[i]
            );
            interval_index[i] = index;
        }
    }

    // ===== weight computation =====
    BSPMAP_API void bspmap_compute_weight(
        const double* basis_data,
        int dim1,
        int dim2,
        int dim3,
        const double* knot_vector,
        int knot_vector_size,
        double* x,
        int size_x,
        double* weights,  // output array [ptidx, degree]
        int* interval_index  // output [ptidx]
    ) {

        // wrap basis_data into Tensor3D
        size_t total_size = static_cast<size_t>(dim1) * static_cast<size_t>(dim2) * static_cast<size_t>(dim3);
        std::span<double> basis_span(const_cast<double*>(basis_data), total_size);
        bspmap::Tensor3D basis(dim1, dim2, dim3, basis_span);


        // call C++ function

#pragma omp parallel for
        for (int i = 0; i < size_x; ++i) {
               
            double* weight_ptr = weights + i * dim2;

            int interval_index_now = bspmap::find_interval(
                std::span<const double>(knot_vector, static_cast<size_t>(knot_vector_size)),
                dim2 - 1,  // degree = num_nodes - 1
                x[i]
            );
            std::vector<double> weight_vec = bspmap::compute_weight(
                basis,
                interval_index_now,
                x[i]
            );

            // copy results to output array
            for (size_t j = 0; j < weight_vec.size(); ++j) {
                weight_ptr[j] = weight_vec[j];
            }

            interval_index[i] = interval_index_now;


        }
    }

    // ===== debug =====
    BSPMAP_API void bspmap_debug_print(const char* msg) {
        std::cout << "[bspmap debug] " << msg << std::endl;
    }

} // extern "C"
