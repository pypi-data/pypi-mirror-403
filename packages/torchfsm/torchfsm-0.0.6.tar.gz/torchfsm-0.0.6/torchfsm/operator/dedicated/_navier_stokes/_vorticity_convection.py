from ..._base import (
    CoreGenerator,
    NonlinearFunc,
    NonlinearOperator,
)
from ....mesh import FourierMesh
from typing import Optional
from ...._type import FourierTensor, SpatialTensor
from ...._type import FourierTensor, SpatialTensor


# Vorticity Convection
class _VorticityConvectionCore(NonlinearFunc):

    r"""
    Implementation of the VorticityConvection operator.
    """

    def __init__(self) -> None:
        super().__init__()

    def __call__(
        self,
        u_fft: FourierTensor["B C H ..."],
        f_mesh: FourierMesh,
        u: Optional[SpatialTensor["B C H ..."]]=None,
    ) -> FourierTensor["B C H ..."]:
        return f_mesh.fft(self.spatial_value(u_fft, f_mesh, u))

    def spatial_value(
        self,
        u_fft: FourierTensor["B C H ..."],
        f_mesh: FourierMesh,
        u: Optional[SpatialTensor["B C H ..."]]=None,
    ) -> SpatialTensor["B C H ..."]:
        psi = -u_fft * f_mesh.invert_laplacian()
        ux = f_mesh.ifft(f_mesh.grad(1, 1) * psi).real
        uy = f_mesh.ifft(-f_mesh.grad(0, 1) * psi).real
        grad_x_w = f_mesh.ifft(f_mesh.grad(0, 1) * u_fft).real
        grad_y_w = f_mesh.ifft(f_mesh.grad(1, 1) * u_fft).real
        return ux * grad_x_w + uy * grad_y_w


class _VorticityConvectionGenerator(CoreGenerator):

    r"""
    Generator of the VorticityConvection operator. 
        It ensures that the operator is only applied to scalar vorticity fields in 2D.
    """

    def __call__(self, f_mesh: FourierMesh, n_channel: int) -> NonlinearFunc:
        if f_mesh.n_dim != 2 or n_channel != 1:
            raise ValueError("Only vorticity in 2Dmesh is supported")
        return _VorticityConvectionCore()


class VorticityConvection(NonlinearOperator):

    r"""
    Operator for vorticity convection in 2D. 
        It is defined as $(\mathbf{u}\cdot\nabla) \omega$ where $\omega$ is the vorticity and $\mathbf{u}$ is the velocity.
        Note that this class is an operator wrapper. The real implementation of the source term is in the `_VorticityConvectionCore` class.
    """

    def __init__(self) -> None:
        super().__init__(_VorticityConvectionGenerator())