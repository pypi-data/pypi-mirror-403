

#include <span>
#include <vector>
#include "tensor.h"
#include "mappingfunc.h"

namespace bspmap {
    
int find_interval(const std::span<const double>& knot_vector, int degree, double x) {
    int n = static_cast<int>(knot_vector.size()) - 1;
    if (x < knot_vector[0]) {
        return 0;
    }
    if (x > knot_vector[n]) {
        return n - degree;
    }

    // Binary search
    int low = 0;
    int high = n;
    while (low <= high) {
        int mid = (low + high) / 2;
        if (knot_vector[mid] <= x && x <= knot_vector[mid + 1]) {
            int result = mid-degree;
            if(result<0)
                return 0;
            else
                if (mid-degree > n - 2*degree - 1)
                    return n - 2*degree - 1;
                else
                    return mid - degree;
        } else if (x < knot_vector[mid]) {
            high = mid - 1;
        } else {
            low = mid + 1;
        }
    }
    return -1; // should not reach here
}

std::vector<double> compute_weight(Tensor3D& basis, int interval_index, double x) {
    auto basis_interval = basis.slice(interval_index);
    std::vector<double> weights(basis_interval[0].size(), 0.0);

    // compute weights for each control point in this interval
    for (size_t cp_idx = 0; cp_idx < basis_interval.size(); ++cp_idx) {
        double weight = 0.0;
        auto basis_now = basis_interval[cp_idx];

        for (int deg = static_cast<int>(basis_now.size()) - 1; deg >= 0; --deg) {
            weight = weight * x + basis_now[deg];
        }

        weights.at(cp_idx) = weight;
    }
    return weights;
}


} // namespace bspmap