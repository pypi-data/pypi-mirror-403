


if __name__ == "__main__":
    import bspmap
    import numpy as np

    numV = 6
    numU = 4

    basis1 = bspmap.BasisClamped(num_cps=numV, degree=3)
    basis2 = bspmap.BasisClamped(num_cps=numU, degree=3)

    cps = np.meshgrid(
        np.linspace(0.0, 1.0, numV),
        np.linspace(0.0, 1.0, numU),
        indexing='ij'
    )
    cpz = np.sin(np.pi * cps[0]) * np.cos(np.pi * cps[1])
    cps = (cps[0].flatten(), cps[1].flatten(), cpz.flatten())

    cps = np.stack(cps, axis=-1).reshape((-1, 3))
    bsp = bspmap.BSP(
        basis=[basis1, basis2],
        degree=3,
        size=[numV, numU],
        control_points=cps
    )

    x = np.meshgrid(
        np.linspace(0.0, 1.0, 10),
        np.linspace(0.0, 1.0, 10),
        indexing='ij'
    )
    x = np.stack(x, axis=-1).reshape((-1, 2))

    weights, indices = bsp.get_weights(x)
    print("Weights:", weights.shape)
    print("Indices:", indices.shape)

    z_new = bsp._map(weights, indices)

    # Test derivative
    derivative = [1, 0]
    weights_d, indices_d = bsp.get_weights(x, derivative)
    print("Weights (derivative):", weights_d.shape)

    z_new_dv = bsp._map(weights_d, indices_d)
    print("Output (derivative):", z_new_dv.shape)
    print("Output (derivative):", z_new_dv)

    # Test mapping directly
    x_v = x.copy()
    x_v[:, 0] += 0.01
    x_v[x_v[:, 0] > 1.0, 0] = 1.0
    z_diff_ = bsp.map(x_v)
    print("Mapped Output:", z_diff_.shape)

    diff = (z_diff_ - z_new) / 0.01
    delta = z_new_dv - diff
    print("Difference between numerical and analytical derivative:", np.abs(delta).max())



