#include "basisfunc.h"
#include <cmath>
#include <vector>
#include <span>
#include "tensor.h"
#include <iostream>

namespace bspmap {


Tensor3D deboor_cox(std::span<const double> knot_vector, int num_nodes, int degree) {

    // number of influencing control points per knot interval
    auto num_control_points_interval = degree + 1;

    // 1, 2, 3, 4, ..., 4, 3, 2, 1 (degree = 3)
    // number of interval = num_nodes + degree
    // i-th inverval with knot[i] to knot[i+1]
    auto interval_size = num_nodes + degree;

    // basis function result placeholder
    // size: [knot_interval(initial for extra degree), control_points_interval, degree]
    Tensor3D result({interval_size, num_control_points_interval, degree + 1});

    // temporary storage for the previous degree basis functions
    Tensor3D previews({interval_size, num_control_points_interval, degree + 1});

    // initialize degree 0 basis functions
    for (int i = 0; i < interval_size; ++i) {
        result[{i, degree, 0}] = 1.0;
    }

    // Cox-de Boor recursion from degree 1 to degree p
    for (int degree_now = 1; degree_now <= degree; ++degree_now){

        std::cout << "Computing degree " << degree_now << " basis functions..." << std::endl;

        // swap result and previews for next degree
        std::swap(result, previews);

        // for each knot interval
        for(int interval_now = degree; interval_now < interval_size - degree; ++interval_now){
            
            // for each control point in this interval
            for(int cp_now = 0; cp_now <= degree; ++cp_now){

				int pt_index = interval_now - degree + cp_now;

                // compute the knot differences
                double delta_knot1 = knot_vector[pt_index + degree_now] - knot_vector[pt_index];
                double delta_knot2 = knot_vector[pt_index + degree_now + 1] - knot_vector[pt_index + 1];

                double factor1 = (delta_knot1 == 0.0) ? 0.0 : 1.0 / delta_knot1;
                double factor2 = (delta_knot2 == 0.0) ? 0.0 : 1.0 / delta_knot2;
                

                // for each order of basis function in this interval (constant term)
                for (int order_now = 0; order_now <= degree_now; ++order_now) {


                    double temp = -knot_vector[pt_index] * factor1 * previews[{interval_now, cp_now, order_now}];
                    if (cp_now + 1 <= degree)
                        temp += knot_vector[pt_index + degree_now + 1] * factor2 * previews[{interval_now, cp_now + 1, order_now}];

                    if (order_now >= 1) {
                        temp += previews[{interval_now, cp_now, order_now - 1}] * factor1;
                        if (cp_now + 1 <= degree)
                            temp -= previews[{interval_now, cp_now + 1, order_now - 1}] * factor2;
                    }
                
                    
                    result[{interval_now, cp_now, order_now}] = temp;
                }
            }
        }

    }


    return result;
}

Tensor3D basis_derivative(const Tensor3D& basis){

    Tensor3D result = Tensor3D(
        basis.get_shape()[0],
        basis.get_shape()[1],
        basis.get_shape()[2]
    );

#pragma omp parallel for
    for(auto interval_now=0; interval_now<basis.get_shape()[0]; ++interval_now){
        for(auto degree_now = 0;degree_now<basis.get_shape()[2]-1; ++degree_now){
            for(auto cp_now=0; cp_now<basis.get_shape()[1]; ++cp_now){

                result.at(interval_now,cp_now,degree_now) = 
                    (degree_now + 1) * basis.at(interval_now,cp_now,degree_now + 1);

            }
        }
    }
    return result;
}
    

} // namespace bspmap
