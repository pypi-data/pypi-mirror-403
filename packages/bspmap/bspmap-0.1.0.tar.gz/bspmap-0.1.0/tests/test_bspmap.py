


if __name__ == "__main__":
    import bspmap
    import numpy as np

    numV = 4
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
        size=[numV, numU],
        control_points=cps
    )

    x = np.meshgrid(
        np.linspace(0.0, 1.0, 5),
        np.linspace(0.0, 1.0, 5),
        indexing='ij'
    )
    x = np.stack(x, axis=-1).reshape((-1, 2))

    weights, indices = bsp.get_weights(x)
    print("Weights:", weights.shape)
    print("Indices:", indices.shape)

    z_new = bsp._map(weights, indices)

