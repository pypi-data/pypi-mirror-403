#pragma once

#include <span>
#include <vector>
#include <tensor.h>


namespace bspmap {

// find the knot span index for a given x
// if x < knot_vector[0] or x > knot_vector[n], return 0 or n
int find_interval(const std::span<const double>& knot_vector, int degree, double x);

std::vector<double> compute_weight(Tensor3D& basis, int interval_index, double x);


} // namespace bspmap