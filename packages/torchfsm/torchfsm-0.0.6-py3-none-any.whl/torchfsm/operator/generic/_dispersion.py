import torch
from ...mesh import FourierMesh
from .._base import LinearCoef, LinearOperator
from ..._type import FourierTensor

class _DispersionCore(LinearCoef):
    r"""
    Implementation of the Dispersion operator.
    """

    def __call__(
        self, f_mesh: FourierMesh, n_channel: int
    ) -> FourierTensor["B C H ..."]:
        return torch.sum(
            f_mesh.nabla_vector(1) * torch.cat([f_mesh.laplacian()] * n_channel, dim=1),
            dim=1,
            keepdim=True,
        )


class Dispersion(LinearOperator):
    r"""
    `Dispersion` calculates the Laplacian of a vector field.

    It is defined as $\nabla \cdot (\nabla^2\mathbf{u}) = \left[\begin{matrix}\sum_j^I \frac{\partial}{\partial j}\sum_i^I \frac{\partial^2 u_x}{\partial i^2 } \\ \sum_j^I \frac{\partial}{\partial j}\sum_i^I \frac{\partial^2 u_y}{\partial i^2 } \\ \cdots \\ \sum_j^I \frac{\partial}{\partial j}\sum_i^I \frac{\partial^2 u_I}{\partial i^2 } \\ \end{matrix} \right]$
    Note that this class is an operator wrapper. The actual implementation of the operator is in the `_LaplacianCore` class.
    """

    def __init__(self) -> None:
        super().__init__(_DispersionCore())