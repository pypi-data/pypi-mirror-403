import torch
from ...mesh import FourierMesh
from .._base import LinearCoef, LinearOperator
from ..._type import FourierTensor

class _HyperDiffusionCore(LinearCoef):
    r"""
    Implementation of the Hyper Diffusion operator.
    """

    def __call__(
        self, f_mesh: FourierMesh, n_channel: int
    ) -> FourierTensor["B C H ..."]:
        return torch.cat([f_mesh.laplacian()] * n_channel,dim=1)**2


class HyperDiffusion(LinearOperator):
    r"""
    `HyperDiffusion` calculates the hyper diffusion of a vector field.

    It is defined as $\nabla^4\mathbf{u} = \left[\begin{matrix}\sum_i \frac{\partial^4 u_x}{\partial i^4 } \\\sum_i \frac{\partial^4 u_y}{\partial i^4 } \\\cdots \\\sum_i \frac{\partial^4 u_I}{\partial i^4 } \\\end{matrix}\right]$
    Note that this class is an operator wrapper. The actual implementation of the operator is in the `_HyperDiffusionCore` class.
    """

    def __init__(self) -> None:
        super().__init__(_HyperDiffusionCore())