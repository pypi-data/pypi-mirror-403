import numpy as np
from .basis import Basis

class BSP:
    def __init__(self, 
                 basis: list[Basis] | tuple[Basis, ...],
                 size: list[int] | tuple[int, ...],
                 control_points: np.ndarray,
                 ):
        """
        Initialize the BSP mapping.

        Args:
            input_dimension (int): Dimension of the input space.
            output_dimension (int): Dimension of the output space.
            size (list[int]): Size of the grid in each dimension.
                - length should be equal to input_dimension.
                - each size should be >= degree + 1.
            control_points (np.ndarray): Control points tensor. 
                - shape: (size_[0]*size_[1]*...*size, output_dimension)
            degree (int): Degree of the B-spline.
        """

        self._basis: tuple[Basis, ...] = tuple(basis)
        """
        The basis functions for each dimension.
        """

        self._size: tuple[int, ...] = tuple(size)
        """
        The size of the grid in each dimension.
        """

        self._control_points: np.ndarray = control_points.reshape((-1, control_points.shape[-1]))
        """
        The control points tensor.
        """

        assert len(basis) == len(self._size), \
            "Length of basis should be equal to input dimension."
        assert control_points.shape[0] == np.prod(self._size), \
            "Control points tensor shape is not compatible with the size."
        assert all(self._basis[d].num_cps == self._size[d] for d in range(len(self._size))), \
            "Number of control points in basis does not match size."

    @property
    def input_dimension(self) -> int:
        """
        Get the input dimension.

        Returns:
            int: Input dimension.
        """
        return len(self._size)
    
    @property
    def output_dimension(self) -> int:
        """
        Get the output dimension.

        Returns:
            int: Output dimension.
        """
        return self._control_points.shape[1]
    
    @property
    def size(self) -> tuple[int, ...]:
        """
        Get the size of the grid in each dimension.

        Returns:
            tuple[int, ...]: Size of the grid.
        """
        return self._size
    
    @property
    def control_points(self) -> np.ndarray:
        """
        Get the control points tensor.

        Returns:
            np.ndarray: Control points tensor.
        """
        return self._control_points
    
    @control_points.setter
    def control_points(self, value: np.ndarray) -> None:
        """
        Set the control points tensor.

        Args:
            value (np.ndarray): New control points tensor.
        """
        assert value.shape[1] == self._control_points.shape[1], \
            "Control points tensor shape is not compatible with the output dimension."
        assert value.shape[0] == np.prod(self._size), \
            "Control points tensor shape is not compatible with the size."
        self._control_points = value.reshape((-1, value.shape[-1]))

    def get_weights(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute the weights and indices for the given input points.

        Args:
            x (np.ndarray): Input points tensor. 
                - shape: (num_points, input_dimension)
        Returns:
            tuple[np.ndarray, np.ndarray]: Weights and indices tensors.
                - weights shape: (num_points, num_control_points_per_point)
                - indices shape: (num_points, num_control_points_per_point), the flat indices of the affected control points.
        """
        weight_dim = []
        index_dim = []
        for dim, b in enumerate(self._basis):
            w, i = b.get_weight(x[:, dim])
            weight_dim.append(w)
            index_dim.append(i)

        weights = weight_dim[0]
        indices = index_dim[0]
        for d in range(1, len(self._basis)):
            weight_now = weight_dim[d]
            index_now = index_dim[d]

            # Combine weights using outer product
            weights = np.einsum('pi,pj->pij', weights, weight_now)
            # Combine indices using cartesian product
            indices = indices.reshape(list(indices.shape) + [1]) * self._size[d] + index_now.reshape([index_now.shape[0], 1, -1])

            weights = weights.reshape((weights.shape[0], -1))
            indices = indices.reshape((indices.shape[0], -1))

        return weights, indices

    def _map(self, weights: np.ndarray, indices: np.ndarray) -> np.ndarray:
        """
        Map the input points to output points using the computed weights and indices.

        Args:
            weights (np.ndarray): Weights tensor.
                - shape: (num_points, num_control_points_per_point)
            indices (np.ndarray): Indices tensor.
                - shape: (num_points, num_control_points_per_point)

        Returns:
            np.ndarray: Output points tensor.
        """

        result = np.zeros((weights.shape[0], self.output_dimension), dtype=self._control_points.dtype)
        for i in range(weights.shape[1]):
            cp = self._control_points[indices[:, i], :]
            w = weights[:, i].reshape((-1, 1))
            result += w * cp
        return result
    
    def map(self, x: np.ndarray) -> np.ndarray:
        """
        Map the input points to output points.

        Args:
            x (np.ndarray): Input points tensor. 
                - shape: (num_points, input_dimension)

        Returns:
            np.ndarray: Output points tensor.
                - shape: (num_points, output_dimension)
        """
        weights, indices = self.get_weights(x)
        return self._map(weights, indices)
        

