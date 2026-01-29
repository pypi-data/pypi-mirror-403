#pragma once

#include <memory>
#include <span>
#include "tensor.h"
#include <omp.h>

// 内部使用的 B-spline 核心功能
// 这个头文件不对外导出，只在库内部使用

namespace bspmap {

// Cox-de Boor computation for B-spline basis functions
// knot_vector: the knot vector
// num_nodes: number of control points
// degree: degree of the B-spline, represent as the maximum degree of the polynomial basis functions
// Returns a vector of basis function values
Tensor3D deboor_cox(std::span<const double> knot_vector, int num_nodes, int degree);

Tensor3D basis_derivative(const Tensor3D& basis);

} // namespace bspmap
