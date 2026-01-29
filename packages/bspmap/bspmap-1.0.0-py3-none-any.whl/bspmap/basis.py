import numpy as np
from . import capi


class BasisFactory:
    """工厂类，用于根据类型名称创建 Basis 对象
    
    所有 Basis 子类会通过元类自动注册到此工厂。
    """
    
    _registry = {}
    
    @classmethod
    def create(cls, basis_type: str, num_cps: int, degree: int):
        """Create a Basis object based on the type name
        
        Args:
            basis_type: the name of the Basis type
            num_cps: number of control points
            degree: degree of the B-spline
            
        Returns:
            the created Basis object
        """
        from . import basis as basis_module
        BasisClass = cls._registry.get(basis_type)
        if BasisClass is None:
            # fallback to the base Basis class
            BasisClass = getattr(basis_module, 'Basis')
        return BasisClass(num_cps=num_cps, degree=degree)
    
    @classmethod
    def register(cls, name: str, basis_class: type):
        """
        register a Basis subclass in the factory.
        
        Args:
            name: the name of the Basis type
            basis_class: Basis subclass
        """
        cls._registry[name] = basis_class


class BasisMeta(type):
    """metaclass of Basis to auto-register subclasses in BasisFactory"""
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        # register the class in the factory
        BasisFactory.register(name, cls)
        return cls


class Basis(metaclass=BasisMeta):
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
    
    def get_weight(self, x: np.ndarray, derivative: int = 0) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute the weights and indices for the given input points.

        Args:
            x (np.ndarray): Input points tensor. 
                - shape: (num_points,)
        Returns:
            tuple[np.ndarray, np.ndarray]: Weights and indices tensors.
        """
        if derivative == 0:
            basis = self.basis
        elif derivative == 1:
            basis = self.basis_d1
        elif derivative == 2:
            basis = self.basis_d2
        else:
            raise ValueError("Only support derivative 0, 1, 2.")

        weights, indices0 = capi.compute_weight(
            basis=basis,
            knot_vector=self.knots,
            x=x.flatten(),
        )

        indices = indices0.reshape((x.size, 1)) + np.arange(self.degree + 1).reshape((1, self.degree + 1))
        return weights, indices

class BasisCircular(Basis):
    def __init__(self, num_cps: int, degree: int):
        super().__init__(num_cps + degree, degree)
        self.num_cps = num_cps

    def get_weight(self, x: np.ndarray, derivative: int = 0):
        weight, indices = super().get_weight(x, derivative)
        indices = indices % (self.num_cps)
        return weight, indices

class BasisClamped(Basis):
    def _build_knots(self, degree: int, num_cps: int) -> np.ndarray:
        knots = super()._build_knots(degree, num_cps)
        knots[:degree] = 0.0
        knots[-degree:] = 1.0
        return knots