#include"multidimfunc.h"
#include <span>
#include <vector>
#include <omp.h>
#include "tensor.h"

namespace bspmap {

    Tensor3D two_dim_weights(Tensor2D weight1, Tensor2D weight2){


        auto result = Tensor3D(weight1.get_shape()[0], weight1.get_shape()[1], weight2.get_shape()[1]);

#pragma omp parallel for
        for(auto ptidx=0;ptidx<weight1.get_shape()[0]; ++ptidx){
            for(auto j=0;j<weight1.get_shape()[1]; ++j){
                for(auto k=0;k<weight2.get_shape()[1]; ++k){
                    result.at(ptidx,j,k) = weight1.at(ptidx,j) * weight2.at(ptidx,k);
                }
            }
        }

        return result;
    }


}