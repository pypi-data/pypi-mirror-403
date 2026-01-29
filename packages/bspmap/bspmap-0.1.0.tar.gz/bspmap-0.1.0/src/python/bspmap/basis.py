import numpy as np
from . import capi

class Basis:
    """
    Class representing a B-spline basis function.
    The knot vector ranges from 0.0 to 1.0.
    """

    def __init__(self, num_cps: int, degree: int):
        """
        Initialize the B-spline basis function.

        Args:
            num_cps (int): Number of control points.
            degree (int): Degree of the B-spline.
        """

        self.degree: int = degree
        """
        The degree of the B-spline.
        """

        self.num_cps: int = num_cps
        """
        The number of control points.
        """

        self.knots = self._build_knots(degree, num_cps)
        """
        The knot vector for the B-spline.
        """

        self.basis: np.ndarray = capi.deboor_cox(self.knots, num_cps, degree)
        """
        The computed B-spline basis functions.
        """

        self.basis_d1: np.ndarray = capi.basis_derivative(self.basis)
        """
        The first derivative of the B-spline basis functions.
        """

        self.basis_d2: np.ndarray = capi.basis_derivative(self.basis_d1)
        """
        The second derivative of the B-spline basis functions.
        """

    def _build_knots(self, degree: int, num_cps: int) -> np.ndarray:
        """
        Build knot vector for B-spline.

        Args:
            degree (int): Degree of the B-spline.
            num_cps (int): Number of cps.
            clamed (bool): Whether to use clamped cps.
        Returns:
            np.ndarray: Knot vector.
        """
        knots_vector = np.linspace(0.0, 1.0, num_cps + degree + 1)
        knots_vector = (knots_vector - knots_vector[degree]) / (knots_vector[-degree-1] - knots_vector[degree])

        return knots_vector
    
    def get_weight(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute the weights and indices for the given input points.

        Args:
            x (np.ndarray): Input points tensor. 
                - shape: (num_points,)
        Returns:
            tuple[np.ndarray, np.ndarray]: Weights and indices tensors.
        """
        weights, indices0 = capi.compute_weight(
            basis=self.basis,
            knot_vector=self.knots,
            x=x.flatten(),
        )

        indices = indices0.reshape((x.size, 1)) + np.arange(self.degree + 1).reshape((1, self.degree + 1))
        return weights, indices

class BasisCircular(Basis):
    def __init__(self, num_cps: int, degree: int):
        super().__init__(num_cps + degree, degree)
        self.num_cps = num_cps

    def get_weight(self, x):
        weight, indices = super().get_weight(x)
        indices = indices % (self.num_cps)
        return weight, indices

class BasisClamped(Basis):
    def _build_knots(self, degree: int, num_cps: int) -> np.ndarray:
        knots = super()._build_knots(degree, num_cps)
        knots[:degree] = 0.0
        knots[-degree:] = 1.0
        return knots