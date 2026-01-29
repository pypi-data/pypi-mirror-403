import numpy as np
from .basis import Basis
from . import capi

class BSP:
    def __init__(self, 
                 basis: list[Basis] | tuple[Basis, ...],
                 degree: int,
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

        self._degree: int = degree

        assert len(basis) == len(self._size), \
            "Length of basis should be equal to input dimension."
        assert control_points.shape[0] == np.prod(self._size), \
            "Control points tensor shape is not compatible with the size."
        assert all(self._basis[d].num_cps == self._size[d] for d in range(len(self._size))), \
            "Number of control points in basis does not match size."
        assert all(self._basis[d].degree == self._degree for d in range(len(self._size))), \
            "Degree of basis functions should be equal to the degree."

    @property
    def degree(self) -> int:
        """
        Get the degree of the B-spline.

        Returns:
            int: Degree of the B-spline.
        """
        return self._degree

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

    def _get_weights(self, weight_dim: list[np.ndarray], index_dim: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        """
        Combine weights and indices from each dimension.

        Args:
            weight_dim (list[np.ndarray]): List of weights tensors for each dimension.
                - each shape: (num_points, num_control_points_per_point_in_dimension)
        index_dim (list[np.ndarray]): List of indices tensors for each dimension.
                - each shape: (num_points, num_control_points_per_point_in_dimension)
        Returns:
            tuple[np.ndarray, np.ndarray]: Combined weights and indices tensors.
                - weights shape: (num_points, num_control_points_per_point)
                - indices shape: (num_points, num_control_points_per_point), the flat indices of the affected control points.
        """
        
        weights = weight_dim[0]
        indices = index_dim[0]
        for d in range(1, len(self._basis)):
            weight_now = weight_dim[d]
            index_now = index_dim[d]

            # Combine weights using outer product
            weights: np.ndarray = np.einsum('pi,pj->pij', weights, weight_now)
            # Combine indices using cartesian product
            indices = indices.reshape(list(indices.shape) + [1]) * self._size[d] + index_now.reshape([index_now.shape[0], 1, -1])

            weights = weights.reshape((weights.shape[0], -1))
            indices = indices.reshape((indices.shape[0], -1))

        return weights, indices

    def get_weights(self, x: np.ndarray, derivative: list[int] = None) -> tuple[np.ndarray, np.ndarray]:
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

        if derivative is None:
            derivative = [0] * self.input_dimension

        assert len(derivative) == self.input_dimension \
            , "Length of derivative should be equal to input dimension."

        weight_dim: list[np.ndarray] = []
        index_dim: list[np.ndarray] = []
        for dim, b in enumerate(self._basis):
            w, i = b.get_weight(x[:, dim], derivative[dim])
            weight_dim.append(w)
            index_dim.append(i)

        weights, indices = self._get_weights(weight_dim, index_dim)
        
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
    
    def map(self, x: np.ndarray, derivative: list[int] = None) -> np.ndarray:
        """
        Map the input points to output points.

        Args:
            x (np.ndarray): Input points tensor. 
                - shape: (num_points, input_dimension)

        Returns:
            np.ndarray: Output points tensor.
                - shape: (num_points, output_dimension)
        """
        weights, indices = self.get_weights(x, derivative)
        return self._map(weights, indices)
        
    def save(self, file) -> None:
        """
        Save the BSP mapping to a file or file-like object.

        Args:
            file (str | file-like): Path to the file or a file-like object (e.g., BytesIO).
        """
        # 收集每个维度的 knots 和 basis 类型
        knots_arrays = {}
        basis_types = []
        
        for i, basis in enumerate(self._basis):
            knots_arrays[f'knots_{i}'] = basis.knots
            basis_types.append(basis.__class__.__name__)
        
        # 保存到压缩的 npz 文件
        np.savez_compressed(
            file,
            control_points=self._control_points,
            degree=np.array([self._degree]),
            size=np.array(self._size),
            basis_types=np.array(basis_types),
            **knots_arrays
        )
    
    @staticmethod
    def load(file) -> 'BSP':
        """
        Load the BSP mapping from a file or file-like object.

        Args:
            file (str | file-like): Path to the file or a file-like object (e.g., BytesIO).
        
        Returns:
            BSP: The loaded BSP mapping.
        """
        from .basis import BasisFactory

        # 加载数据
        data = np.load(file, allow_pickle=False)
        
        control_points = data['control_points']
        degree = int(data['degree'][0])
        size = tuple(data['size'])
        basis_types = data['basis_types']
        
        # 重建 basis 对象
        basis_list = []
        
        for i, basis_type in enumerate(basis_types):
            knots = data[f'knots_{i}']
            num_cps = size[i]
            
            # 使用工厂创建对应类型的 basis
            basis_obj = BasisFactory.create(str(basis_type), num_cps=num_cps, degree=degree)
            
            # 如果 knots 不同，说明可能被自定义了，需要重新赋值
            # （通常标准构造函数会自动生成 knots，这里确保一致性）
            if not np.allclose(basis_obj.knots, knots):
                basis_obj.knots = knots
                # 重新计算 basis
                basis_obj.basis = capi.deboor_cox(basis_obj.knots, num_cps, degree)
                basis_obj.basis_d1 = capi.basis_derivative(basis_obj.basis)
                basis_obj.basis_d2 = capi.basis_derivative(basis_obj.basis_d1)
            
            basis_list.append(basis_obj)
        
        return BSP(
            basis=basis_list,
            degree=degree,
            size=size,
            control_points=control_points
        )
        