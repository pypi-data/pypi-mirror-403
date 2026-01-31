import torch
from torch import Tensor
from ....mesh import FourierMesh
from ..._base import LinearCoef, NonlinearOperator, CoreGenerator, NonlinearFunc
from ...._type import FourierTensor, SpatialTensor
from typing import Optional, Union

class _LerayCore(NonlinearFunc):

    r"""
    Implementation of the Leray projection operator.
    """

    def __init__(self):
        super().__init__(False)
        """
        Although the Leray projection is implemented as a nonlinear function, 
        it is actually a linear operation where dealising is not required.
        We implement it as a nonlinear function since its linear feature is a dot product operation, which is not supported by the spectral method.
        """

    def __call__(self, u_fft, f_mesh, u=None):
        return u_fft - f_mesh.nabla_vector(1) * f_mesh.invert_laplacian() * torch.sum(
            f_mesh.nabla_vector(1) * u_fft, dim=1, keepdim=True
        )
    
class _LerayGenerator(CoreGenerator):
    r"""
    Generator of the Leray peojection operator.
        It ensures that the operator only works for vector fields with the same dimension as the mesh.
    """

    def __call__(
        self, f_mesh: FourierMesh, n_channel: int
    ) -> Union[LinearCoef, NonlinearFunc]:
        if f_mesh.n_dim != n_channel:
            raise ValueError(
                f"Leray projection only works for vector field with the same dimension as mesh"
            )
        return _LerayCore()
    
class Leray(NonlinearOperator):
    r"""
    `Leray` calculates the Leray projection of a vector field.
        It is defined as $\mathbf{u} - \nabla \nabla^{-2} \nabla \cdot \mathbf{u}$.
        This operator only works for vector fields with the same dimension as the mesh.
        Note that this class is an operator wrapper. The actual implementation of the operator is in the `_LerayCore` class.
    """

    def __init__(self) -> None:
        super().__init__(_LerayGenerator())