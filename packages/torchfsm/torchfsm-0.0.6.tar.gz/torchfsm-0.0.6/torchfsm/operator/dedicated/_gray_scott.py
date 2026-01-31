import torch
from torch import Tensor
from ...mesh import FourierMesh
from ...operator._base import LinearCoef,NonlinearFunc,LinearOperator, NonlinearOperator, CoreGenerator
from ..._type import FourierTensor, SpatialTensor
from typing import Union, Optional, Sequence

class _ChannelWisedDiffusionCore(LinearCoef):
    r"""
    Implementation of the ChannelWisedDiffusion operator.
    """

    def __init__(self,
                 viscosities: Sequence[Union[Tensor, float]]) -> None:
        super().__init__()
        self.viscosities= viscosities
        
    
    def __call__(self, 
                 f_mesh: FourierMesh, 
                 n_channel: int) -> FourierTensor["B C H ..."]:
        return torch.cat([viscosity*f_mesh.laplacian() for viscosity in self.viscosities],dim=1)

class _ChannelWisedDiffusionGenerator(CoreGenerator):

    r"""
    Generator of the ChannelWisedDiffusion operator. It ensures that the operator is only applied to fields with the same number of channels as the number of viscosities.
    """

    def __init__(self, viscosities: Sequence[Union[Tensor, float]]) -> None:
        self.viscosities = viscosities

    def __call__(self, f_mesh: FourierMesh, n_channel: int) -> LinearCoef:
        if n_channel != len(self.viscosities):
            raise ValueError(f"Number of channels {n_channel} does not match number of viscosities {len(self.viscosities)} for ChannelWisedDiffusion.")
        return _ChannelWisedDiffusionCore(self.viscosities)

class ChannelWisedDiffusion(LinearOperator):

    r"""
    The ChannelWisedDiffusion operator applies different diffusion coefficients to each channel of a field.
    It is defined as: $\nabla^2 \phi_i = \nu_i \nabla^2 \phi_i$ for each channel $i$.
    Note that this class is an operator wrapper. The real implementation of the diffusion is in the `_ChannelWisedDiffusionCore` class.
    """

    def __init__(self,viscosities: Sequence[Union[Tensor, float]]):
        super().__init__(_ChannelWisedDiffusionGenerator(viscosities))

class _GrayScottSourceCore(NonlinearFunc):

    r"""
    Implementation of the Gray-Scott source term.
    """
    
    def __init__(self, 
                 feed_rate: Union[Tensor, float],
                 kill_rate: Union[Tensor, float]) -> None:
        super().__init__()
        self.feed_rate = feed_rate
        self.kill_rate = kill_rate
    
    def __call__(
            self,
            u_fft: FourierTensor["B C H ..."],
            f_mesh: FourierMesh,
            u: Optional[SpatialTensor["B C H ..."]] = None,
        ) -> FourierTensor["B C H ..."]:
        u0u12 = u[:, 0, ...] * u[:, 1, ...]* u[:, 1, ...]
        return  f_mesh.fft(torch.stack(
            [
                self.feed_rate *(1 - u[:, 0, ...]) - u0u12,
                u0u12-(self.kill_rate + self.feed_rate) * u[:, 1, ...]
            ],
            dim=1
        ))

class _GrayScottSourceGenerator(CoreGenerator):
    
    r""" 
    Generator of the GrayScottSource operator. It ensures that the operator is only applied to fields with exactly
    """
    
    def __init__(self, 
                 feed_rate: Union[Tensor, float],
                 kill_rate: Union[Tensor, float]) -> None:
        self.feed_rate = feed_rate
        self.kill_rate = kill_rate
    
    def __call__(self, f_mesh: FourierMesh, n_channel: int) -> NonlinearFunc:
        if n_channel != 2:
            raise ValueError(f"Gray-Scott source term requires exactly 2 channels, got {n_channel}.")
        return _GrayScottSourceCore(self.feed_rate, self.kill_rate)

class GrayScottSource(NonlinearOperator):
    
    r"""
    The Gray-Scott source term operator for a two-channel field.
    It is defined as: $\left[\begin{matrix}f (1 - \phi_0) - \phi_0 \phi_1^2 \\ \phi_0 \phi_1^2 - (f + k) \phi_1 \end{matrix}\right]$
    Note that this class is an operator wrapper. The real implementation of the source term is in the `_GrayScottSource` class.
    """

    def __init__(self, 
                 feed_rate: Union[Tensor, float],
                 kill_rate: Union[Tensor, float]) -> None:
        super().__init__(_GrayScottSourceGenerator(feed_rate, kill_rate))