
import numpy as np


if __name__ == "__main__":
    from bspmap import Basis, BasisCircular, BasisClamped
    import numpy as np

    basis = BasisCircular(num_cps=4, degree=3)

    u = np.linspace(0.0, 1.0, 10)
    print("Knots:", basis.knots)
    print("Basis:", basis.basis.shape)
    print("Basis d1:", basis.basis_d1.shape)
    print("Basis d2:", basis.basis_d2.shape)

    print("Compute weights and indices:")
    weights, indices = basis.get_weight(u)
    print(f"U: {u} Weights: {weights} Indices: {indices}")
